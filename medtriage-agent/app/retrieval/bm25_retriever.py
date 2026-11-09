"""BM25 检索器."""
from __future__ import annotations

import jieba
from rank_bm25 import BM25Okapi
from typing import List, Dict, Any, Optional


class BM25Retriever:
    """基于 BM25 的文本检索器."""

    def __init__(self):
        self.bm25: Optional[BM25Okapi] = None
        self.documents: List[Dict[str, Any]] = []
        self.tokenized_corpus: List[List[str]] = []

    def build_index(self, documents: List[Dict[str, Any]]):
        """构建 BM25 索引.

        Args:
            documents: 文档列表，每个文档包含 id, title, content 等字段
        """
        self.documents = documents
        self.tokenized_corpus = []

        for doc in documents:
            text = doc.get("title", "") + " " + doc.get("content", "") + " " + doc.get("tags", "")
            tokens = self._tokenize(text)
            self.tokenized_corpus.append(tokens)

        self.bm25 = BM25Okapi(self.tokenized_corpus)

    def _tokenize(self, text: str) -> List[str]:
        """中文分词."""
        return [token for token in jieba.cut(text) if token.strip() and len(token) > 0]

    def search(self, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """检索相关文档.

        Args:
            query: 查询文本
            top_k: 返回结果数量

        Returns:
            相关文档列表，包含 score 字段
        """
        if self.bm25 is None or not self.documents:
            return []

        query_tokens = self._tokenize(query)
        scores = self.bm25.get_scores(query_tokens)

        # 按分数排序
        scored_docs = []
        for i, score in enumerate(scores):
            if score > 0:
                doc = dict(self.documents[i])
                doc["score"] = float(score)
                doc["retriever"] = "bm25"
                scored_docs.append(doc)

        scored_docs.sort(key=lambda x: x["score"], reverse=True)
        return scored_docs[:top_k]

    def __len__(self) -> int:
        return len(self.documents)
