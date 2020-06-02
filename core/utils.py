import networkx as nx
from pyecharts.charts import Graph
from pyecharts.options import global_options


def echarts_from_nx(nx: nx.DiGraph, output_path, title):
    nodes = []
    for node in nx.nodes:
        nodes.append({
            'name': node,
            'symbolSize': 40
        })

    links = []
    for u, v in nx.edges:
        links.append({
            'source': u,
            'target': v
        })

    graph = Graph(global_options.InitOpts(width='1920px', height='1080px'))
    graph.add(title, nodes, links, repulsion=8000, edge_symbol=['arrow'])
    graph.render(output_path)
