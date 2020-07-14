from collections import defaultdict
from copy import deepcopy

import networkx as nx
from matplotlib import pyplot as plt

from core.scanner import TemplateScanner
from core.topology import Topology


class Clustering:
    """
    聚类实现类
    """

    # 频率过滤阈值
    freq_threshold = 0.07

    def __init__(self, template_scanner: TemplateScanner, top: Topology, get_root_cause_only=False):
        """
        构造函数，初始化相关成员变量，并进行过滤高频项、重复项聚类等基本处理
        :param template_scanner: 日志模板扫描器
        :param top: 拓扑图
        :param get_root_cause_only: 是否仅用于获取根因
        """

        self._template_scanner: TemplateScanner = template_scanner
        self._clustered_logs = deepcopy(self._template_scanner.get_logs())
        self._top = top
        self._event_freq = defaultdict(int)

        self._root_cause = None
        for log in self._clustered_logs:
            if 'is_root' in log and log['is_root']:
                self._root_cause = log
                break

        if get_root_cause_only:
            return

        self._remove_high_freq()
        self._remove_duplicate()

        self._node_to_log_mapping = defaultdict(list)
        for log in self._clustered_logs:
            self._node_to_log_mapping[log['node']].append(log)

    def get_event_freq(self, log):
        """
        获取事件频率
        :param log: 事件条目
        :return: 发生频率
        """

        node = log['node']
        template = log['template']
        print(log['node'], log['message'], log['template'], self._event_freq[(log['node'], log['template'])])
        if (node, template) not in self._event_freq:
            return 0
        return self._event_freq[(node, template)]

    def get_root_cause(self):
        """
        获得根因。聚类后根因是唯一确定的，调用该方法获得根因。
        :return: 根因
        """
        return self._root_cause

    def cluster_by_topology(self, node, extra=lambda u, v: True, jumps=2):
        """
        基于拓扑图进行聚类
        :param node: 节点
        :param extra: 搜索的附加条件
        :param jumps: 聚类的跳数
        :return: 子图，节点附近跳树范围之内且存在事件发生的节点和边构成的子图
        """
        return self._top.subgraph_around(node, lambda u, v: v in self._node_to_log_mapping and extra(u, v), jumps)

    def get_node_to_log_mapping(self) -> dict:
        """
        获取一个dict：节点 -> 事件
        :return: dict：节点 -> 事件
        """
        return self._node_to_log_mapping

    def _remove_duplicate(self):
        result = []
        l = len(self._clustered_logs)
        for log in self._clustered_logs:
            self._event_freq[(log['node'], log['template'])] += 1
            if log not in result:
                result.append(log)
        self._event_freq = {k: v / l for k, v in self._event_freq.items()}
        self._clustered_logs = result

    def _remove_high_freq(self):
        result = []
        for log in self._clustered_logs:
            if self._template_scanner.get_freq(log['template']) <= self.freq_threshold:
                result.append(log)
                continue
            print('Removed {}'.format(log['message']))
        self._clustered_logs = result
