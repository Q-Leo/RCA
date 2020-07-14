import json
import os

import networkx as nx
import numpy as np
import pandas as pd
from pgmpy.estimators import BayesianEstimator
from pgmpy.inference import VariableElimination
from pgmpy.models import BayesianModel
from tqdm import tqdm

from core.clustering import Clustering
from core.scanner import TemplateScanner
from core.topology import Topology
from core.utils import echarts_from_nx
from settings import Settings


class Relationship:
    """
    构建根因推理图（贝叶斯网络）以及推理模型（变量消解）
    """

    def __init__(self, tpl: TemplateScanner, top: Topology):
        """
        构造函数，该方法内将会自动调用类中的_get_dag，_train_bn等私有成员，完成根因推理图的构建和推理模型的初始化
        :param tpl: 日志模板扫描器类
        :param top: 拓扑结构类
        """

        self._tpl = tpl
        self._top = top
        self._dag = self._get_dag()
        self._model = self._train_bn()
        self._model_infer = VariableElimination(self._model)

    def get_possibility_when(self, evidence, variable):
        """
        计算后验概率 P(variable | evidence1, evidence2, ...)
        :param evidence: 条件
        :param variable: 变量
        :return: 后验概率值
        """

        return self._model_infer.query(variables=[str(variable)], evidence={
            str(x): 1 for x in evidence
        })

    def draw(self, path):
        """
        绘制推理图（调试时用）
        :param path 存储图的路径
        :return: 无
        """

        nx_desc = nx.DiGraph()
        nx_desc.add_nodes_from((self._tpl.get_message_by_template(int(node)) for node in self._dag.nodes))
        for u, v in self._dag.edges:
            nx_desc.add_edge(self._tpl.get_message_by_template(int(u)), self._tpl.get_message_by_template(int(v)))
        echarts_from_nx(nx_desc, path, '推理图')

    def _get_training_data(self):
        cache_path = '{}/.rel_td'.format(Settings.training_data_path)

        if not os.path.exists(cache_path):
            raw_training_data = []

            for i in tqdm(range(Settings.n_training_data)):
                self._tpl.init('{}/{}.csv'.format(Settings.training_data_path, i), True)
                cls = Clustering(self._tpl, self._top)
                root_cause = cls.get_root_cause()
                mapping = cls.get_node_to_log_mapping()
                if root_cause is None:
                    continue
                data = []
                for u in cls.cluster_by_topology(root_cause['node']).nodes:
                    for log in mapping[u]:
                        data.append(log['template'])

                raw_training_data.append({
                    'data': data,
                    'root': root_cause['template']
                })

            json.dump(raw_training_data, open(cache_path, 'w'))
        else:
            raw_training_data = json.load(open(cache_path, 'r'))

        size = len(raw_training_data)
        training_data = np.zeros(shape=(size, len(self._tpl.get_templates())))
        for i in range(size):
            for hot in raw_training_data[i]['data']:
                training_data[i][hot] = 1 if hot != raw_training_data[i]['root'] else 1

        cols = [tpl[1] for tpl in self._tpl.get_templates()]
        training_data = pd.DataFrame(training_data, columns=[str(x) for x in cols])
        return training_data

    def _get_dag(self):
        g = nx.DiGraph()
        dag_path = '{}/.dag'.format(Settings.training_data_path)
        if os.path.exists(dag_path):
            g_file = json.load(open(dag_path, 'r'))
            g.add_nodes_from(g_file['nodes'])
            for u, v in g_file['edges']:
                g.add_edge(u, v)

            return g

        g.add_nodes_from(str(x[1]) for x in self._tpl.get_templates())
        edges = []
        times = {}
        for i in tqdm(range(Settings.n_training_data)):
            self._tpl.init('{}/{}.csv'.format(Settings.training_data_path, i), True)
            cls = Clustering(self._tpl, self._top)
            root_cause = cls.get_root_cause()
            mapping = cls.get_node_to_log_mapping()
            if root_cause is None:
                continue
            top = cls.cluster_by_topology(root_cause['node'])
            '''
            for u, v in top.edges:
                for logu in mapping[u]:
                    for logv in mapping[v]:
                        s = str(logu['template'])
                        t = str(logv['template'])
                        if s == t:
                            continue
                        if (s, t) not in times:
                            times[s, t] = 0
                        times[s, t] += 1
                        if times[s, t] >= 9:
                            edges.append((s, t, times[s, t]))
            '''
            s = str(root_cause['template'])
            for node in top.nodes:
                for log in mapping[node]:
                    t = str(log['template'])
                    if s == t:
                        continue
                    if (s, t) not in times:
                        times[s, t] = 0
                    times[s, t] += 1
                    if times[s, t] >= 3:
                        edges.append((s, t, times[s, t]))

        sorted(edges, key=lambda x: x[2], reverse=True)

        for u, v, w in edges:
            try:
                if not nx.has_path(g, v, u):
                    g.add_edge(u, v)
            except nx.NodeNotFound:
                g.add_edge(u, v)

        json.dump({
            'edges': list(g.edges),
            'nodes': list(g.nodes)
        }, open(dag_path, 'w'))

        return g

    def _train_bn(self):
        model = BayesianModel(self._dag.edges)
        model.add_nodes_from(self._dag.nodes)
        model.fit(self._get_training_data(), BayesianEstimator, prior_type='BDeu')
        return model
