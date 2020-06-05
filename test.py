import networkx as nx
from tqdm import tqdm

from core.clustering import Clustering
from core.relationship import Relationship
from core.scanner import TemplateScanner
from core.topology import Topology
from core.utils import echarts_from_nx
from settings import Settings

if __name__ == '__main__':
    top = Topology('data/topology/topology_edges_node.json')
    ts = TemplateScanner('data/test')
    print(ts.get_templates())

    re = Relationship(ts, top)
    re.draw()
    print(re.get_possibility_when(21, [22]))
