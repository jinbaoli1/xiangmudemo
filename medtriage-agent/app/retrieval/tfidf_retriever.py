"""TF-IDF 检索器."""
from __future__ import annotations

import jieba
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from typing import List, Dict, Any, Optional


class TFIDFRetriever:
    """基于 TF-IDF + 余弦相似度的文本检索器."""

    def __init__(self):
        self.vectorizer: Optional[TfidfVectorizer] = None
        self.tfidf_matrix = None
        self.documents: List[Dict[str, Any]] = []

    def _tokenize(self, text: str) -> List[str]:
        """中文分词."""
        return [token for token in jieba.cut(text) if token.strip() and len(token) > 0]

    def build_index(self, documents: List[Dict[str, Any]]):
        """构建 TF-IDF 索引.

        Args:
            documents: 文档列表，每个文档包含 id, title, content 等字段
        """
        self.documents = documents
        texts = []

        for doc in documents:
            text = doc.get("title", "") + " " + doc.get("content", "") + " " + doc.get("tags", "")
            texts.append(text)

        # 使用 jieba 分词后的文本
        tokenized_texts = [" ".join(self._tokenize(text)) for text in texts]

        self.vectorizer = TfidfVectorizer(
            max_features=5000,
            ngram_range=(1, 2),
            min_df=1,
        )
        self.tfidf_matrix = self.vectorizer.fit_transform(tokenized_texts)

    def search(self, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """检索相关文档.

        Args:
            query: 查询文本
            top_k: 返回结果数量

        Returns:
            相关文档列表，包含 score 字段
        """
        if self.vectorizer is None or self.tfidf_matrix is None:
            return []

        query_tokens = " ".join(self._tokenize(query))
        query_vector = self.vectorizer.transform([query_tokens])

        # 计算余弦相似度
        similarities = cosine_similarity(query_vector, self.tfidf_matrix)[0]

        # 按分数排序
        scored_docs = []
        for i, score in enumerate(similarities):
            if score > 0:
                doc = dict(self.documents[i])
                doc["score"] = float(score)
                doc["retriever"] = "tfidf"
                scored_docs.append(doc)

        scored_docs.sort(key=lambda x: x["score"], reverse=True)
        return scored_docs[:top_k]

    def __len__(self) -> int:
        return len(self.documents)
