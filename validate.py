import json
import os

from tqdm import tqdm

from core.clustering import Clustering
from core.scanner import TemplateScanner
from core.topology import Topology

if __name__ == '__main__':
    top = Topology('data/topology/topology_edges_node.json')
    ts = TemplateScanner('data/test')
    current = json.load(open('cur2.json', 'r'))

    n_correct = 0
    n_located = 0
    n_has = 0

    rc_cache = []
    if not os.path.exists('.rccache'):
        for i in tqdm(range(100)):
            ts.init('./data/train/{}.csv'.format(i), root_cause_label=True)
            cl = Clustering(ts, top, True)
            rc_cache.append(cl.get_root_cause())
        json.dump(rc_cache, open('.rccache', 'w'))
    else:
        rc_cache = json.load(open('.rccache', 'r'))

    for i in tqdm(range(100)):
        root_cause = rc_cache[i]
        if root_cause is None:
            if str(i) in current:
                n_located += 1
            continue
        n_has += 1
        if str(i) not in current:
            continue
        n_located += 1
        if current[str(i)][0]['node'] == root_cause['node'] and current[str(i)][0]['root_log']['template'] == root_cause['template']:
            n_correct += 1

    precision = n_correct / n_located
    back = n_correct / n_has

    f1 = 2 * precision * back / (precision + back)
    print(f1)
