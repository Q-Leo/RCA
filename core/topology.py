import json

import networkx as nx


class Topology:
    """
    拓扑结构
    （拓展networkx的相关功能）
    """

    def __init__(self, node_topology_json_path):
        """
        构造函数，从JSON文件中加载拓扑结构
        :param node_topology_json_path: 节点拓扑结构的JSON文件
        """

        graph = json.load(open(node_topology_json_path, 'r'))
        self.nx = nx.DiGraph()

        for node, children in graph.items():
            u = int(node.split('_')[1])
            for child in children:
                v = int(child.split('_')[1])
                self.nx.add_edge(v, u)

    def dfs(self, source, is_available=lambda u, v: True, depth_limit=None):
        """
        进行深度优先遍历
        :param source: 起始节点
        :param is_available: 一个函数闭包，lambda u, v返回True或False，表示在遍历到(u, v)边时是否继续往下（更深）遍历
        :param depth_limit: 深度限制
        :return: 一个Python Generator，所有遍历到的边
        """

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
                    if is_available(parent, child):
                        yield parent, child
                    if child not in visited and is_available(parent, child):
                        visited.add(child)
                        if depth_now > 1:
                            stack.append((child, depth_now - 1, iter(self.nx[child])))
                except StopIteration:
                    stack.pop()

    def subgraph_around(self, source, is_available=lambda u, v: True, depth_limit=3):
        """
        按照深度优先遍历得到的边建立子图
        :param source: 起始节点
        :param is_available: 一个函数闭包，lambda u, v返回True或False，表示在遍历到(u, v)边时是否继续往下（更深）遍历
        :param depth_limit: 深度限制
        :return: 子图
        """

        subgraph = nx.DiGraph()
        subgraph.add_node(source)

        for u, v in self.dfs(source, is_available, depth_limit):
            subgraph.add_edge(u, v)

        return subgraph
