"""Reranker 重排序器 - 基于规则的简易重排序."""
from __future__ import annotations

import re
import jieba
from typing import List, Dict, Any


class Reranker:
    """基于多特征融合的重排序器.

    由于不使用外部LLM，这里实现一个基于规则的重排序：
    - 标题匹配权重更高
    - 关键词命中数量
    - 关键词密度
    - 文档长度归一化
    - 分类匹配
    """

    def __init__(self):
        pass

    def _tokenize(self, text: str) -> List[str]:
        """中文分词."""
        return [token for token in jieba.cut(text) if token.strip() and len(token) > 0]

    def _compute_title_score(self, query_tokens: List[str], title: str) -> float:
        """计算标题匹配得分."""
        title_lower = title.lower()
        score = 0.0
        for token in query_tokens:
            if token in title_lower:
                score += 2.0
        return score

    def _compute_keyword_density(self, query_tokens: List[str], content: str) -> float:
        """计算关键词密度."""
        if not content:
            return 0.0
        content_lower = content.lower()
        content_len = len(content_lower)
        if content_len == 0:
            return 0.0

        hit_count = 0
        for token in query_tokens:
            hit_count += content_lower.count(token.lower())

        return hit_count / content_len * 1000  # 放大系数

    def _compute_category_match(self, query: str, category: str, tags: str) -> float:
        """计算分类匹配得分."""
        score = 0.0
        query_lower = query.lower()
        if category and category.lower() in query_lower:
            score += 1.0
        if tags:
            for tag in tags.split(","):
                if tag.strip().lower() in query_lower:
                    score += 0.5
        return score

    def rerank(self, query: str, documents: List[Dict[str, Any]], top_k: int = 5) -> List[Dict[str, Any]]:
        """对检索结果进行重排序.

        Args:
            query: 查询文本
            documents: 待排序文档列表
            top_k: 返回数量

        Returns:
            重排序后的文档列表
        """
        if not documents:
            return []

        query_tokens = self._tokenize(query)

        reranked = []
        for doc in documents:
            # 原始检索得分（归一化）
            original_score = doc.get("score", 0.0)

            # 标题匹配得分
            title_score = self._compute_title_score(query_tokens, doc.get("title", ""))

            # 关键词密度
            density_score = self._compute_keyword_density(query_tokens, doc.get("content", ""))

            # 分类匹配
            category_score = self._compute_category_match(
                query,
                doc.get("category", ""),
                doc.get("tags", "")
            )

            # 综合得分（加权融合）
            final_score = (
                original_score * 1.0 +
                title_score * 0.8 +
                density_score * 0.5 +
                category_score * 0.6
            )

            doc = dict(doc)
            doc["rerank_score"] = round(float(final_score), 4)
            doc["title_score"] = round(title_score, 4)
            doc["density_score"] = round(density_score, 4)
            doc["category_score"] = round(category_score, 4)
            reranked.append(doc)

        reranked.sort(key=lambda x: x["rerank_score"], reverse=True)
        return reranked[:top_k]
