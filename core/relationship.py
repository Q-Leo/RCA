import networkx as nx
from tqdm import tqdm

from core.clustering import Clustering
from core.scanner import TemplateScanner
from core.topology import Topology
from settings import Settings
import numpy as np
import json
import os
import pandas as pd
from core.utils import echarts_from_nx

from pgmpy.estimators import HillClimbSearch, BicScore, BayesianEstimator
from pgmpy.models import BayesianModel
from pgmpy.inference import VariableElimination


class Relationship:
    def __init__(self, tpl: TemplateScanner, top: Topology):
        self._tpl = tpl
        self._top = top
        self._dag = self._get_dag()
        self._model = self._train_bn()
        self._model_infer = VariableElimination(self._model)

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

    def _get_dag(self, inject_expert_edges=False):
        g = nx.DiGraph()

        dag_path = '{}/.dag'.format(Settings.training_data_path)
        if os.path.exists(dag_path):
            g_file = json.load(open(dag_path, 'r'))
            g.add_nodes_from(g_file['nodes'])
            for u, v in g_file['edges']:
                g.add_edge(u, v)

            return g

        training_data = self._get_training_data()
        estimated = HillClimbSearch(training_data, scoring_method=BicScore(training_data)).estimate()

        if inject_expert_edges:
            edges = []
            times = {}
            for i in tqdm(range(Settings.n_training_data)):
                self._tpl.init('{}/{}.csv'.format(Settings.training_data_path, i), True)
                cls = Clustering(self._tpl, self._top)
                root_cause = cls.get_root_cause()
                mapping = cls.get_node_to_log_mapping()
                if root_cause is None:
                    continue
                for u in cls.cluster_by_topology(root_cause['node']).nodes:
                    for log in mapping[u]:
                        s = str(root_cause['template'])
                        t = str(log['template'])
                        if (s, t) not in times:
                            times[s, t] = 0
                        times[s, t] += 1
                        if times[s, t] > 1:
                            edges.append((s, t, times[s, t]))
            sorted(edges, key=lambda x: x[2], reverse=True)

            for u, v, w in edges:
                try:
                    if not nx.has_path(g, v, u):
                        g.add_edge(u, v)
                except nx.NodeNotFound:
                    g.add_edge(u, v)

        g.add_nodes_from(estimated.nodes())
        for u, v in estimated.edges():
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

    def get_possibility_when(self, caused_by, variables):
        return self._model_infer.query(variables=[str(x) for x in variables], evidence={
            str(caused_by): 1
        })

    def draw(self):
        nx_desc = nx.DiGraph()
        nx_desc.add_nodes_from((self._tpl.get_message_by_template(int(node)) for node in self._dag.nodes))
        for u, v in self._dag.edges:
            nx_desc.add_edge(self._tpl.get_message_by_template(int(u)), self._tpl.get_message_by_template(int(v)))
        echarts_from_nx(nx_desc, 'relationship.html', '因果关系图')
