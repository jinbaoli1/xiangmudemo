"""
BM25关键词检索器
基于 rank_bm25 库实现
"""
from __future__ import annotations

import re
from typing import List, Callable
from rank_bm25 import BM25Okapi

from .base import BaseRetriever, RetrievalResult


def _default_tokenize(text: str) -> List[str]:
    """简单的分词：按字符+标点分割，支持中英文"""
    # 移除标点符号
    text = re.sub(r'[^\w\s\u4e00-\u9fff]', ' ', text)
    # 简单分词：英文按空格，中文按单字（简易方式）
    tokens = []
    for word in text.split():
        if re.match(r'^[\u4e00-\u9fff]+$', word):
            # 中文：按二元切分（bigram）
            for i in range(len(word) - 1):
                tokens.append(word[i:i+2])
            # 也加入单字
            tokens.extend(list(word))
        else:
            # 英文：转小写
            tokens.append(word.lower())
    return tokens


class BM25Retriever(BaseRetriever):
    """BM25关键词检索器"""

    def __init__(
        self,
        items: List = None,
        text_extractor: Callable[[any], str] = None,
        tokenizer: Callable[[str], List[str]] = None,
    ):
        self._text_extractor = text_extractor or (lambda x: str(x))
        self._tokenizer = tokenizer or _default_tokenize
        self._bm25: BM25Okapi = None
        self._corpus_tokens: List[List[str]] = []
        super().__init__(items)

    def build_index(self, items: List) -> None:
        """构建BM25索引"""
        self._items = items
        self._corpus_tokens = []

        for item in items:
            text = self._text_extractor(item)
            tokens = self._tokenizer(text)
            self._corpus_tokens.append(tokens)

        if self._corpus_tokens:
            self._bm25 = BM25Okapi(self._corpus_tokens)
            self._built = True
        else:
            self._built = False

    def search(self, query: str, top_k: int = 10, **kwargs) -> List[RetrievalResult]:
        """BM25检索"""
        if not self._built or not self._bm25:
            return []

        query_tokens = self._tokenizer(query)
        if not query_tokens:
            return []

        scores = self._bm25.get_scores(query_tokens)

        # 排序并取top_k
        indexed_scores = list(enumerate(scores))
        indexed_scores.sort(key=lambda x: x[1], reverse=True)

        results = []
        for rank, (idx, score) in enumerate(indexed_scores[:top_k]):
            if score <= 0:
                continue
            results.append(RetrievalResult(
                item=self._items[idx],
                score=float(score),
                rank=rank + 1,
                metadata={"method": "bm25", "index": idx},
            ))

        return results

    def add_item(self, item) -> None:
        """添加单个item到索引（重建索引，简单实现）"""
        self._items.append(item)
        text = self._text_extractor(item)
        tokens = self._tokenizer(text)
        self._corpus_tokens.append(tokens)
        if self._corpus_tokens:
            self._bm25 = BM25Okapi(self._corpus_tokens)
            self._built = True
