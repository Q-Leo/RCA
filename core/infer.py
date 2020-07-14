from core.clustering import Clustering
from core.relationship import Relationship
from core.scanner import TemplateScanner
from core.topology import Topology


class Infer:
    """
    最终的推理实现类
    """

    def __init__(self, tpl: TemplateScanner, top: Topology, re: Relationship):
        """
        构造方法，初始化
        :param tpl: 模板扫描器
        :param top: 拓扑图
        :param re: 根因推理图
        """
        self._tpl = tpl
        self._top = top
        self._re = re

    def infer(self, path):
        """
        进行推理
        :param path: csv文件路径
        :return: 推理结果，一个元组(节点, 根因告警信息, 节点的局部拓扑子图)
        """

        self._tpl.init(path)
        cl = Clustering(self._tpl, self._top)
        mapping = cl.get_node_to_log_mapping()
        result = []
        for node, root_logs in mapping.items():
            evidence_nodes = set()
            for around in cl.cluster_by_topology(node).nodes:
                evidence_nodes.add(around)
            evidence_nodes.remove(node)

            if len(evidence_nodes) == 0:
                continue

            tot_freq = 0
            evidence = set()
            for evidence_node in evidence_nodes:
                for log in mapping.get(evidence_node):
                    evidence.add(log['template'])
                    tot_freq += cl.get_event_freq(log)

            for root_log in root_logs:
                if root_log['template'] not in (
                        2,
                        9,
                        3,
                        21,
                        0,
                        22,
                        14,
                        10,
                        19
                ):
                    continue
                freq = cl.get_event_freq(root_log)
                if (tot_freq + freq) * freq < 0.01:
                    continue
                print('rca ', root_log['node'], tot_freq + cl.get_event_freq(root_log))
                evidence_query = evidence - {root_log['template']}
                phi = self._re.get_possibility_when(evidence_query, root_log['template'])
                result.append((node, phi.values[1], root_log, list(evidence_nodes), (tot_freq + freq) * freq))

        result.sort(key=lambda x: x[4] * x[1], reverse=True)

        return result[0][0], result[0][2]['message'], cl.cluster_by_topology(result[0][0], lambda u, v: True, 3)
