"""
TF-IDF向量检索器
基于 scikit-learn TfidfVectorizer 实现
"""
from __future__ import annotations

import re
import numpy as np
from typing import List, Callable
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .base import BaseRetriever, RetrievalResult


def _default_preprocess(text: str) -> str:
    """文本预处理"""
    # 移除标点
    text = re.sub(r'[^\w\s\u4e00-\u9fff]', ' ', text)
    # 中文按字切分（用空格连接，便于TfidfVectorizer处理）
    chars = []
    for ch in text:
        if '\u4e00' <= ch <= '\u9fff':
            chars.append(ch)
        else:
            chars.append(ch.lower())
    return ''.join(chars)


class _ChineseTokenizer:
    """中文分词器：基于字符级n-gram"""

    def __init__(self, ngram_range=(1, 2)):
        self.ngram_range = ngram_range

    def __call__(self, text: str) -> List[str]:
        tokens = []
        words = text.split()
        for word in words:
            if re.match(r'^[\u4e00-\u9fff]+$', word):
                # 中文：生成字符级n-gram
                min_n, max_n = self.ngram_range
                for n in range(min_n, max_n + 1):
                    for i in range(len(word) - n + 1):
                        tokens.append(word[i:i+n])
            else:
                tokens.append(word.lower())
        return tokens


class TFIDFRetriever(BaseRetriever):
    """TF-IDF向量检索器"""

    def __init__(
        self,
        items: List = None,
        text_extractor: Callable[[any], str] = None,
        preprocessor: Callable[[str], str] = None,
        ngram_range=(1, 2),
    ):
        self._text_extractor = text_extractor or (lambda x: str(x))
        self._preprocessor = preprocessor or _default_preprocess
        self._ngram_range = ngram_range
        self._vectorizer: TfidfVectorizer = None
        self._tfidf_matrix = None
        super().__init__(items)

    def build_index(self, items: List) -> None:
        """构建TF-IDF索引"""
        self._items = items

        if not items:
            self._built = False
            return

        texts = [self._text_extractor(item) for item in items]
        processed_texts = [self._preprocessor(t) for t in texts]

        # 根据文档数量调整参数
        n_docs = len(processed_texts)
        min_df = min(1, n_docs)
        max_df = min(0.95, max(2, n_docs) / n_docs) if n_docs > 1 else 1.0

        self._vectorizer = TfidfVectorizer(
            tokenizer=_ChineseTokenizer(self._ngram_range),
            token_pattern=None,  # 使用自定义tokenizer
            lowercase=False,
            max_features=10000,
            min_df=min_df,
            max_df=max_df,
        )

        self._tfidf_matrix = self._vectorizer.fit_transform(processed_texts)
        self._built = True

    def search(self, query: str, top_k: int = 10, **kwargs) -> List[RetrievalResult]:
        """TF-IDF余弦相似度检索"""
        if not self._built or self._vectorizer is None:
            return []

        processed_query = self._preprocessor(query)
        query_vec = self._vectorizer.transform([processed_query])

        # 计算余弦相似度
        similarities = cosine_similarity(query_vec, self._tfidf_matrix)[0]

        # 排序取top_k
        indexed_scores = list(enumerate(similarities))
        indexed_scores.sort(key=lambda x: x[1], reverse=True)

        results = []
        for rank, (idx, score) in enumerate(indexed_scores[:top_k]):
            if score <= 0:
                continue
            results.append(RetrievalResult(
                item=self._items[idx],
                score=float(score),
                rank=rank + 1,
                metadata={"method": "tfidf", "index": idx},
            ))

        return results

    def get_top_features(self, top_n: int = 20) -> List[str]:
        """获取TF-IDF权重最高的特征词"""
        if not self._built or self._vectorizer is None:
            return []

        feature_names = np.array(self._vectorizer.get_feature_names_out())
        idf = self._vectorizer.idf_
        top_indices = np.argsort(idf)[-top_n:][::-1]
        return list(feature_names[top_indices])
