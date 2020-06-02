import networkx as nx
from tqdm import tqdm

from core.clustering import Clustering
from core.scanner import TemplateScanner
from core.topology import Topology
from core.utils import echarts_from_nx
from settings import Settings

import os
import json


class Relationship:
    infer_threshold = 1
    graph_name = '因果关系图'
    n_training_data = 99

    def __init__(self, template_scanner: TemplateScanner, top: Topology):
        self._template_scanner = template_scanner
        self._top = top
        self._get_relationship_pairs()

    def _get_relationship_pairs(self):
        rl_path = '{}/.relationship'.format(Settings.training_data_path)
        if os.path.exists(rl_path):
            self._g_relationship = nx.DiGraph()
            edges = json.load(open(rl_path, 'r'))
            for u, v in edges:
                self._g_relationship.add_edge(u, v)
            return

        infer = nx.DiGraph()
        times = {}
        for i in tqdm(range(Settings.n_training_data)):
            path = '{}/{}.csv'.format(Settings.training_data_path, i)
            self._template_scanner.init(path, True)
            cs = Clustering(self._template_scanner, self._top)
            root_cause = cs.get_root_cause()
            if root_cause is None:
                continue
            sg = cs.cluster_by_topology(root_cause['node'])
            if sg is None:
                continue
            mapping = cs.get_node_to_log_mapping()
            for u, v in sg.edges:
                for s in mapping[u]:
                    for t in mapping[v]:
                        uu = s['template']
                        vv = t['template']

                        if (uu, vv) not in times:
                            times[(uu, vv)] = 0
                        times[(uu, vv)] += 1

        cache = []
        for u, v in times.keys():
                infer.add_edge(u, v)
                cache.append((u, v))

        self._g_relationship = infer
        json.dump(cache, open(rl_path, 'w'))

    def have_relationship(self, t1, t2):
        return (t1, t2) in self._g_relationship.edges

    def generate_relationship_graph(self, path):
        echarts_from_nx(self._g_relationship, path, self.graph_name)
