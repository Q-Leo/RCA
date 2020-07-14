import networkx as nx
from pyecharts.charts import Graph
from pyecharts.options import global_options


def echarts_from_nx(nx: nx.DiGraph, output_path, title):
    """
    对networkx图使用echarts进行可视化（仅供调试时使用，正式的可视化不在这）
    :param nx: networkx图实例
    :param output_path: 输出的HTML文件目录
    :param title: 图表的标题
    :return: 无
    """

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
    graph.add(title, nodes, links, repulsion=8000, edge_symbol=['circle', 'arrow'])
    graph.render(output_path)
