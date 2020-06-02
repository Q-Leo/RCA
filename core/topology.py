import json

import networkx as nx


class Topology:

    def __init__(self, node_topology_json_path):
        graph = json.load(open(node_topology_json_path, 'r'))
        self.nx = nx.DiGraph()

        for node, children in graph.items():
            u = int(node.split('_')[1])
            for child in children:
                v = int(child.split('_')[1])
                self.nx.add_edge(u, v)

    def dfs(self, source, is_available=lambda u, v: True, depth_limit=None):
        if source is None:
            nodes = self.nx
        else:
            nodes = [source]
        visited = set()
        if depth_limit is None:
            depth_limit = len(self.nx)
        for start in nodes:
            if start in visited:
                continue
            visited.add(start)
            stack = [(start, depth_limit, iter(self.nx[start]))]
            while stack:
                parent, depth_now, children = stack[-1]
                try:
                    child = next(children)
                    if child not in visited and is_available(parent, child):
                        yield parent, child
                        visited.add(child)
                        if depth_now > 1:
                            stack.append((child, depth_now - 1, iter(self.nx[child])))
                except StopIteration:
                    stack.pop()

    def subgraph_around(self, source, is_available=lambda u, v: True, depth_limit=3):
        subgraph = nx.DiGraph()

        for u, v in self.dfs(source, is_available, depth_limit):
            subgraph.add_edge(u, v)

        return subgraph
