from core.clustering import Clustering
from core.relationship import Relationship
from core.scanner import TemplateScanner
from core.topology import Topology


class Locating:
    def __init__(self, template_scanner: TemplateScanner, top: Topology, relationship: Relationship):
        self._top = top
        self._relationship = relationship
        self._template_scanner = template_scanner
        self._cs = Clustering(template_scanner, top)

    def _have_relationship(self, logs1, logs2):
        for log1 in logs1:
            for log2 in logs2:
                if self._relationship.have_relationship(log1['template'], log2['template']):
                    return True
        return False

    def _get_node_infer(self, node):
        mapping = self._cs.get_node_to_log_mapping()
        return self._cs.cluster_by_topology(node, lambda u, v: self._have_relationship(mapping[u], mapping[v]))

    def locate_rc_node(self):
        max_node = None
        max_size = 0
        for node in self._cs.get_node_to_log_mapping().keys():
            #print(self._get_node_infer(node).edges)
            size = len(self._get_node_infer(node))
            if size > max_size:
                max_node = node
                max_size = size
        return max_node
