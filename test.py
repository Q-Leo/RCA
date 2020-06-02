from tqdm import tqdm

from core.clustering import Clustering
from core.locating import Locating
from core.relationship import Relationship
from core.scanner import TemplateScanner
from core.topology import Topology

if __name__ == '__main__':
    top = Topology('data/topology/topology_edges_node.json')
    ts = TemplateScanner('data/test')
    re = Relationship(ts, top)
    re.generate_relationship_graph('./test.html')
    #print(ts.get_templates())

    for i in tqdm(range(100)):
        ts.init('./data/train/{}.csv'.format(i), True)
        lo = Locating(ts, top, re)
        cs = Clustering(ts, top)
        try:
            if lo.locate_rc_node() == cs.get_root_cause()['node']:
                print('ok')
        except TypeError:
            pass
