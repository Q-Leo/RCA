from collections import defaultdict
from copy import deepcopy

import networkx as nx
from matplotlib import pyplot as plt

from core.scanner import TemplateScanner
from core.topology import Topology


class Clustering:
    freq_threshold = 0.1

    def __init__(self, template_scanner: TemplateScanner, top: Topology):
        self._template_scanner: TemplateScanner = template_scanner
        self._clustered_logs = deepcopy(self._template_scanner.get_logs())
        self._top = top

        self._root_cause = None
        for log in self._clustered_logs:
            if 'is_root' in log and log['is_root']:
                self._root_cause = log
                break

        self._remove_high_freq()
        self._remove_duplicate()

        self._node_to_log_mapping = defaultdict(list)
        for log in self._clustered_logs:
            self._node_to_log_mapping[log['node']].append(log)

    def _remove_duplicate(self):
        result = []
        for log in self._clustered_logs:
            if log not in result:
                result.append(log)
        self._clustered_logs = result

    def _remove_high_freq(self):
        result = []
        for log in self._clustered_logs:
            if self._template_scanner.get_freq(log['template']) <= self.freq_threshold:
                result.append(log)
        self._clustered_logs = result

    def get_root_cause(self):
        return self._root_cause

    def cluster_by_topology(self, node, extra=lambda u, v: True):
        return self._top.subgraph_around(node, lambda u, v: v in self._node_to_log_mapping and extra(u, v), 2)

    def get_node_to_log_mapping(self) -> dict:
        return self._node_to_log_mapping

    def draw(self):
        for template in self._template_scanner.get_templates():
            print(template)
        print('Root cause: ', str(self._root_cause))
        labels = {}
        for node in self._clustered_logs.nodes:
            labels[node] = '[' + str(node) + ':' + (
                ';'.join([str(log['template']) for log in self._node_to_log_mapping[node]])) + ']'
        pos = nx.circular_layout(self._clustered_logs)
        nx.draw_networkx(self._clustered_logs, pos=pos, with_labels=False)
        nx.draw_networkx_labels(self._clustered_logs, pos=pos, labels=labels)
        plt.show()
