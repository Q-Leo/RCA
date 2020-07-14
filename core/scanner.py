import json
import os
import sys

import numpy as np
import pandas as pd
from tqdm import tqdm

sys.setrecursionlimit(100000)


class UnionSet:
    """
    并查集实现类
    """

    def __init__(self, n):
        """
        构造函数
        :param n: 并查集内元素的个数
        :return: 无
        """
        self._root = [i for i in range(0, n)]
        self.n_components = n

    def iter_roots(self):
        """
        遍历所有根节点
        :return: 一个Python Generator，表示所有根节点
        """
        for i in range(len(self._root)):
            if self._root[i] == i:
                yield i

    def find(self, a):
        """
        查找一个节点对应的根节点
        :param a: 带查找的节点
        :return: 对应的根节点
        """
        if a == self._root[a]:
            return a

        self._root[a] = self.find(self._root[a])
        return self._root[a]

    def merge(self, a, b):
        """
        合并两个集合
        :param a: 集合1的代表节点
        :param b: 集合2的代表节点
        :return: 无
        """
        x = self.find(a)
        y = self.find(b)

        if x == y:
            return

        self._root[x] = y
        self.n_components -= 1


def calc_similarity(a: str, b: str):
    """
    计算两个字符串的余弦相似度
    :param a: 第一个字符串
    :param b: 第二个字符串
    :return: 余弦相似度的值
    """

    if a == b:
        return 1.0

    s_a = set(a)
    s_b = set(b)
    vec = s_a.union(s_b)

    vec_a = np.array(list({x: 1 if x in s_a else 0 for x in vec}.values()))
    vec_b = np.array(list({x: 1 if x in s_b else 0 for x in vec}.values()))

    return vec_a.dot(vec_b.T) / np.linalg.norm(vec_a) / np.linalg.norm(vec_b)


class TemplateScanner:
    """
    模板扫描器
    """

    # 相似度阈值
    log_parse_similarity_threshold = 0.80

    def __init__(self, tpl_source):
        """
        构造函数，加载日志模板配置，如果不存在缓存，则根据日志模板训练目录训练并生成日志模板配置文件，如果存在缓存则直接从缓存中加载
        :param tpl_source: 日志模板训练目录
        """

        self._tpl_source = tpl_source
        self._templates = []
        self._log_parse_similarity_threshold = self.log_parse_similarity_threshold
        self._source_log_entries = []
        self._log_entries = []
        self._template_freq = {}
        self._freq_total = 0

        path_templates_cache = '{}/.tpls'.format(tpl_source)
        if not os.path.exists(path_templates_cache):
            print('找不到缓存')
            self._scan_tpl_source()
            self._get_templates()
            json.dump({
                'info': self._templates,
                'freq': self._template_freq
            }, open(path_templates_cache, 'w'))
        else:
            print('从缓存加载日志模板')
            cached = json.load(open(path_templates_cache, 'r'))
            self._templates = [(name, index) for name, index in cached['info']]
            self._template_freq = {int(index): freq for index, freq in cached['freq'].items()}

        self._templates_dict = {index: name for name, index in self._templates}
        for freq in self._template_freq.values():
            self._freq_total += freq

    def get_freq(self, tpl_id):
        """
        获取某个日志模板分类ID出现的总频率
        往往用于按照频率过滤噪声时
        :param tpl_id: 日志模板分类ID
        :return: 频率
        """

        return self._template_freq[tpl_id] / self._freq_total

    def get_message_by_template(self, tpl_id):
        """
        通过日志模板分类ID获取代表该分类的事件内容主体的文字信息（往往用于调试）
        :param tpl_id: 日志模板分类ID
        :return: 代表的文字信息
        """
        return self._templates_dict[tpl_id]

    def get_template_id(self, message):
        """
        获取某个事件内容主体文字信息对应的日志模板分类ID
        :param message: 事件内容主体文字信息
        :return: 对应的日志模板分类id，如果不存在则返回None
        """
        for target_message, idx in self._templates:
            if calc_similarity(target_message, message) > self.log_parse_similarity_threshold:
                return idx

    def init(self, log_file_path, root_cause_label=False):
        """
        初始化某一个训练/测试数据文件，该过程将该文件（csv）中的所有数据结构化，存储到self._log_entries中，通过get_logs获取
        :param log_file_path: 日志文件路径
        :param root_cause_label: 是否添加根因标记，对于训练数据需要添加，测试数据不需要（因为测试数据本来就要人为添加这个）
        :return: 无
        """
        self._log_entries = []
        df = pd.read_csv(log_file_path)
        for index, event in df.iterrows():
            msg_raw = event['triggername'].split(' ', 1)
            tmp = {
                'node': int(msg_raw[0].split('_')[1]),
                'message': msg_raw[1],
                'template': self.get_template_id(msg_raw[1])
            }
            if root_cause_label:
                tmp['is_root'] = int(event['is_root']) == 1
            self._log_entries.append(tmp)

    def get_logs(self):
        """
        获取所有结构化的日志信息
        :return: 结构化的日志信息
        """
        return self._log_entries

    def get_templates(self):
        """
        获取所有日志模板
        :return: 所有日志模板
        """
        return self._templates

    def _scan_tpl_source(self):
        print('正在扫描日志...')
        files = os.scandir(self._tpl_source)
        for file in files:
            df = pd.read_csv(file)
            for index, event in df.iterrows():
                log = event['triggername'].split(' ', 1)[1]
                self._source_log_entries.append(log)

    def _get_templates(self):
        log_entries = self._source_log_entries

        print('正在解析日志模板...')
        cnt = len(log_entries)
        components = UnionSet(cnt)

        print('正在进行第一趟解析，根据重复项建立模板')
        for entry_id_1 in tqdm(range(cnt)):
            for entry_id_2 in range(cnt):
                if entry_id_1 == entry_id_2:
                    continue
                if log_entries[entry_id_1] != log_entries[entry_id_2]:
                    continue
                components.merge(entry_id_1, entry_id_2)

        print('正在进行第二趟解析，根据文本相似度大小进一步建立模板')
        roots_list = list(components.iter_roots())
        for root1 in tqdm(roots_list):
            for root2 in roots_list:
                if root1 == root2:
                    continue
                if calc_similarity(log_entries[root1], log_entries[root2]) > self._log_parse_similarity_threshold:
                    components.merge(root1, root2)

        index = 0
        for root in components.iter_roots():
            self._templates.append((log_entries[root], index))
            self._template_freq[index] = 0
            index += 1

        print('正在统计出现频率')
        for entry in tqdm(self._source_log_entries):
            self._template_freq[self.get_template_id(entry)] += 1

        print('发现{}个日志模板'.format(index))
