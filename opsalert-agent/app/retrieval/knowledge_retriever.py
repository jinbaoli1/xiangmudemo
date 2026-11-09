"""故障知识库检索器 - BM25 + TF-IDF 混合检索"""
import re
import math
from typing import List, Dict, Any, Tuple
from collections import Counter


def _tokenize(text: str) -> List[str]:
    """简单分词：英文按空格+标点，中文按字（模拟）"""
    if not text:
        return []
    # 转小写
    text = text.lower()
    # 提取英文单词
    words = re.findall(r'[a-zA-Z][a-zA-Z0-9_+\-]+', text)
    # 提取中文字符（单字分词）
    chars = re.findall(r'[\u4e00-\u9fff]', text)
    # 提取数字
    numbers = re.findall(r'\d+', text)
    return words + chars + numbers


class BM25Okapi:
    """BM25 实现"""

    def __init__(self, corpus: List[List[str]], k1: float = 1.5, b: float = 0.75):
        self.corpus_size = len(corpus)
        self.avgdl = sum(len(doc) for doc in corpus) / self.corpus_size if self.corpus_size > 0 else 1
        self.corpus = corpus
        self.k1 = k1
        self.b = b
        self.doc_freqs = []
        self.idf = {}
        self.doc_len = []
        self._initialize()

    def _initialize(self):
        nd = Counter()
        for doc in self.corpus:
            self.doc_len.append(len(doc))
            frequencies = Counter(doc)
            self.doc_freqs.append(frequencies)
            for word in frequencies:
                nd[word] += 1
        for word, freq in nd.items():
            self.idf[word] = math.log(self.corpus_size - freq + 0.5) - math.log(freq + 0.5)

    def get_scores(self, query: List[str]) -> List[float]:
        scores = [0.0] * self.corpus_size
        for q in query:
            if q not in self.idf:
                continue
            idf = self.idf[q]
            for i in range(self.corpus_size):
                freq = self.doc_freqs[i].get(q, 0)
                if freq == 0:
                    continue
                dl = self.doc_len[i]
                numerator = freq * (self.k1 + 1)
                denominator = freq + self.k1 * (1 - self.b + self.b * dl / self.avgdl)
                scores[i] += idf * (numerator / denominator)
        return scores


class TfidfRetriever:
    """TF-IDF 检索实现"""

    def __init__(self, corpus: List[List[str]]):
        self.corpus = corpus
        self.corpus_size = len(corpus)
        self.doc_freqs = []
        self.idf = {}
        self.doc_norms = []
        self._initialize()

    def _initialize(self):
        df = Counter()
        for doc in self.corpus:
            frequencies = Counter(doc)
            self.doc_freqs.append(frequencies)
            for word in frequencies:
                df[word] += 1
        for word, freq in df.items():
            self.idf[word] = math.log((self.corpus_size + 1) / (freq + 1)) + 1
        for i in range(self.corpus_size):
            norm = 0.0
            for word, freq in self.doc_freqs[i].items():
                tf = freq / max(len(self.corpus[i]), 1)
                tfidf = tf * self.idf.get(word, 0)
                norm += tfidf * tfidf
            self.doc_norms.append(math.sqrt(norm) if norm > 0 else 1.0)

    def get_scores(self, query: List[str]) -> List[float]:
        query_freq = Counter(query)
        query_norm = 0.0
        for word, freq in query_freq.items():
            tf = freq / max(len(query), 1)
            tfidf = tf * self.idf.get(word, 0)
            query_norm += tfidf * tfidf
        query_norm = math.sqrt(query_norm) if query_norm > 0 else 1.0

        scores = []
        for i in range(self.corpus_size):
            score = 0.0
            for word, q_freq in query_freq.items():
                if word not in self.idf:
                    continue
                q_tfidf = (q_freq / max(len(query), 1)) * self.idf[word]
                d_freq = self.doc_freqs[i].get(word, 0)
                d_tfidf = (d_freq / max(len(self.corpus[i]), 1)) * self.idf[word]
                score += q_tfidf * d_tfidf
            # 余弦相似度
            score = score / (query_norm * self.doc_norms[i])
            scores.append(score)
        return scores


class KnowledgeRetriever:
    """故障知识库混合检索器"""

    def __init__(self, knowledge_entries: List[Dict[str, Any]]):
        self.entries = knowledge_entries
        self._build_index()

    def _build_index(self):
        """构建索引"""
        self.documents = []
        for entry in self.entries:
            # 组合检索字段
            text = " ".join([
                entry.get("title", ""),
                entry.get("symptom", ""),
                entry.get("root_cause", ""),
                entry.get("solution", ""),
                " ".join(entry.get("tags", [])),
                " ".join(entry.get("keywords", [])),
                " ".join(entry.get("steps", [])),
            ])
            self.documents.append(text)

        self.tokenized_docs = [_tokenize(doc) for doc in self.documents]
        self.bm25 = BM25Okapi(self.tokenized_docs)
        self.tfidf = TfidfRetriever(self.tokenized_docs)

    def search(
        self,
        query: str,
        top_k: int = 5,
        category: str = None,
        service: str = None,
        bm25_weight: float = 0.6,
        tfidf_weight: float = 0.4,
    ) -> List[Dict[str, Any]]:
        """
        混合检索
        :param query: 查询文本
        :param top_k: 返回数量
        :param category: 分类过滤
        :param service: 服务过滤
        :param bm25_weight: BM25权重
        :param tfidf_weight: TF-IDF权重
        :return: 排序后的结果列表
        """
        if not query or not self.entries:
            return []

        query_tokens = _tokenize(query)
        if not query_tokens:
            return []

        # BM25 分数
        bm25_scores = self.bm25.get_scores(query_tokens)
        # TF-IDF 分数
        tfidf_scores = self.tfidf.get_scores(query_tokens)

        # 归一化 BM25 分数
        max_bm25 = max(bm25_scores) if bm25_scores and max(bm25_scores) > 0 else 1.0
        norm_bm25 = [s / max_bm25 for s in bm25_scores]

        # 混合打分
        combined_scores = []
        for i in range(len(self.entries)):
            score = bm25_weight * norm_bm25[i] + tfidf_weight * tfidf_scores[i]
            combined_scores.append((i, score))

        # 过滤和排序
        filtered = []
        for idx, score in combined_scores:
            entry = self.entries[idx]
            if category and entry.get("category") != category:
                continue
            if service:
                affected = entry.get("affected_services", [])
                if "all" not in affected and service not in affected:
                    score *= 0.7  # 服务不匹配，降权
            filtered.append((idx, score))

        filtered.sort(key=lambda x: x[1], reverse=True)

        results = []
        for idx, score in filtered[:top_k]:
            entry = self.entries[idx].copy()
            entry["retrieval_score"] = round(score, 4)
            results.append(entry)

        return results

    def search_by_tags(self, tags: List[str], top_k: int = 5) -> List[Dict[str, Any]]:
        """按标签检索"""
        scored = []
        for entry in self.entries:
            entry_tags = set(entry.get("tags", []))
            query_tags = set(tags)
            overlap = len(entry_tags & query_tags)
            if overlap > 0:
                score = overlap / max(len(query_tags), 1)
                scored.append((entry, score))
        scored.sort(key=lambda x: x[1], reverse=True)
        results = []
        for entry, score in scored[:top_k]:
            entry_copy = entry.copy()
            entry_copy["retrieval_score"] = round(score, 4)
            results.append(entry_copy)
        return results
