"""
混合检索：RRF融合 + 简单Reranker
"""
from __future__ import annotations

import re
from typing import List, Dict, Any, Callable, Optional
from collections import defaultdict

from .base import BaseRetriever, RetrievalResult
from .bm25_retriever import BM25Retriever
from .tfidf_retriever import TFIDFRetriever


class RRFCombiner:
    """
    Reciprocal Rank Fusion (RRF) 排序融合算法
    公式：score = sum(1 / (k + rank)) for each result list
    k 通常设为 60
    """

    def __init__(self, k: int = 60):
        self.k = k

    def combine(
        self,
        result_lists: List[List[RetrievalResult]],
        weights: Optional[List[float]] = None,
        top_k: int = 20,
    ) -> List[RetrievalResult]:
        """
        融合多个检索结果列表

        Args:
            result_lists: 多个检索结果列表
            weights: 每个列表的权重，默认均等
            top_k: 返回前k个结果

        Returns:
            融合后的结果列表
        """
        if not result_lists:
            return []

        if weights is None:
            weights = [1.0] * len(result_lists)

        # 确保权重数量匹配
        while len(weights) < len(result_lists):
            weights.append(1.0)

        # 聚合分数
        item_scores: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            "item": None,
            "score": 0.0,
            "methods": [],
            "ranks": [],
        })

        for list_idx, results in enumerate(result_lists):
            weight = weights[list_idx]
            for result in results:
                # 使用item的id作为key
                item_id = self._get_item_id(result.item)
                entry = item_scores[item_id]
                if entry["item"] is None:
                    entry["item"] = result.item

                # RRF分数
                rrf_score = weight / (self.k + result.rank)
                entry["score"] += rrf_score
                entry["methods"].append(result.metadata.get("method", "unknown"))
                entry["ranks"].append(result.rank)

        # 排序
        sorted_items = sorted(
            item_scores.values(),
            key=lambda x: x["score"],
            reverse=True,
        )

        # 构造结果
        combined_results = []
        for rank, entry in enumerate(sorted_items[:top_k]):
            combined_results.append(RetrievalResult(
                item=entry["item"],
                score=entry["score"],
                rank=rank + 1,
                metadata={
                    "method": "rrf",
                    "methods_used": entry["methods"],
                    "ranks": entry["ranks"],
                },
            ))

        return combined_results

    @staticmethod
    def _get_item_id(item) -> str:
        """获取item的唯一标识"""
        # 尝试常见的id字段
        for attr in ["sku_id", "chunk_id", "doc_id", "id", "order_id", "application_id"]:
            if isinstance(item, dict):
                if attr in item:
                    return str(item[attr])
            elif hasattr(item, attr):
                return str(getattr(item, attr))

        # 如果是dict，尝试用内容hash作为id
        if isinstance(item, dict):
            import hashlib
            # 用id字段或所有值的hash
            if "id" in item:
                return str(item["id"])
            content = str(sorted(item.items()))
            return hashlib.md5(content.encode()).hexdigest()

        return str(id(item))


class SimpleReranker:
    """
    简易Reranker：基于多项特征加权重排
    特征包括：
    - 原始检索分数
    - 标题匹配度（关键词命中数）
    - 业务权重（销量、评分、价格等）
    - 标签匹配度
    """

    def __init__(
        self,
        title_extractor: Callable[[any], str] = None,
        tag_extractor: Callable[[any], List[str]] = None,
        popularity_extractor: Callable[[any], float] = None,
        rating_extractor: Callable[[any], float] = None,
        weights: Dict[str, float] = None,
    ):
        self._title_extractor = title_extractor or (lambda x: str(x))
        self._tag_extractor = tag_extractor or (lambda x: getattr(x, "tags", []))
        self._popularity_extractor = popularity_extractor or (lambda x: getattr(x, "sales_volume", 0))
        self._rating_extractor = rating_extractor or (lambda x: getattr(x, "rating", 5.0))

        self._weights = weights or {
            "retrieval_score": 0.5,    # 原始检索分数权重
            "title_match": 0.25,       # 标题匹配权重
            "tag_match": 0.1,          # 标签匹配权重
            "popularity": 0.1,         # 人气权重
            "rating": 0.05,            # 评分权重
        }

    def rerank(
        self,
        results: List[RetrievalResult],
        query: str,
        top_k: int = 10,
    ) -> List[RetrievalResult]:
        """
        重排检索结果

        Args:
            results: 原始检索结果
            query: 查询词
            top_k: 返回前k个

        Returns:
            重排后的结果
        """
        if not results:
            return []

        query_keywords = self._extract_keywords(query)

        # 归一化原始分数
        max_score = max(r.score for r in results) if results else 1.0
        if max_score == 0:
            max_score = 1.0

        # 归一化人气（销量）
        max_popularity = max(
            self._popularity_extractor(r.item) for r in results
        ) if results else 1.0
        if max_popularity == 0:
            max_popularity = 1.0

        reranked = []
        for result in results:
            item = result.item

            # 1. 原始检索分数（归一化）
            retrieval_score = result.score / max_score

            # 2. 标题匹配度
            title = self._title_extractor(item)
            title_match_score = self._compute_title_match(title, query_keywords)

            # 3. 标签匹配度
            tags = self._tag_extractor(item)
            tag_match_score = self._compute_tag_match(tags, query_keywords)

            # 4. 人气分数（归一化）
            popularity = self._popularity_extractor(item)
            popularity_score = popularity / max_popularity if max_popularity > 0 else 0

            # 5. 评分分数（归一化到0-1）
            rating = self._rating_extractor(item)
            rating_score = rating / 5.0

            # 加权求和
            final_score = (
                self._weights["retrieval_score"] * retrieval_score +
                self._weights["title_match"] * title_match_score +
                self._weights["tag_match"] * tag_match_score +
                self._weights["popularity"] * popularity_score +
                self._weights["rating"] * rating_score
            )

            reranked.append(RetrievalResult(
                item=item,
                score=final_score,
                rank=0,  # 后面重算
                metadata={
                    **result.metadata,
                    "rerank_features": {
                        "retrieval_score": retrieval_score,
                        "title_match": title_match_score,
                        "tag_match": tag_match_score,
                        "popularity": popularity_score,
                        "rating": rating_score,
                    },
                    "original_score": result.score,
                    "original_rank": result.rank,
                },
            ))

        # 按最终分数排序
        reranked.sort(key=lambda x: x.score, reverse=True)
        for i, r in enumerate(reranked):
            r.rank = i + 1

        return reranked[:top_k]

    @staticmethod
    def _extract_keywords(query: str) -> List[str]:
        """从查询中提取关键词"""
        keywords = set()
        # 英文按空格分割
        for word in query.lower().split():
            if word and len(word) > 1:
                keywords.add(word)
        # 中文按字和二元组
        chinese_chars = re.findall(r'[\u4e00-\u9fff]+', query)
        for chars in chinese_chars:
            keywords.update(list(chars))
            for i in range(len(chars) - 1):
                keywords.add(chars[i:i+2])
        return list(keywords)

    @staticmethod
    def _compute_title_match(title: str, keywords: List[str]) -> float:
        """计算标题匹配度"""
        if not keywords or not title:
            return 0.0

        title_lower = title.lower()
        matches = 0
        for kw in keywords:
            if kw.lower() in title_lower:
                # 更长的关键词匹配权重更高
                matches += len(kw)

        # 归一化：匹配的总字符数 / 标题长度
        max_possible = len(title_lower)
        if max_possible == 0:
            return 0.0
        return min(matches / max_possible, 1.0)

    @staticmethod
    def _compute_tag_match(tags: List[str], keywords: List[str]) -> float:
        """计算标签匹配度"""
        if not keywords or not tags:
            return 0.0

        tag_set = set(t.lower() for t in tags)
        matches = sum(1 for kw in keywords if kw.lower() in tag_set)
        return matches / len(keywords) if keywords else 0.0


class HybridSearcher:
    """
    混合检索器：BM25 + TF-IDF + RRF融合 + Reranker
    """

    def __init__(
        self,
        items: List = None,
        text_extractor: Callable[[any], str] = None,
        title_extractor: Callable[[any], str] = None,
        tag_extractor: Callable[[any], List[str]] = None,
        popularity_extractor: Callable[[any], float] = None,
        rating_extractor: Callable[[any], float] = None,
        bm25_weight: float = 1.0,
        tfidf_weight: float = 1.0,
        rrf_k: int = 60,
        rerank_weights: Dict[str, float] = None,
    ):
        self._bm25_weight = bm25_weight
        self._tfidf_weight = tfidf_weight

        self._bm25 = BM25Retriever(text_extractor=text_extractor)
        self._tfidf = TFIDFRetriever(text_extractor=text_extractor)
        self._rrf = RRFCombiner(k=rrf_k)
        self._reranker = SimpleReranker(
            title_extractor=title_extractor or text_extractor,
            tag_extractor=tag_extractor,
            popularity_extractor=popularity_extractor,
            rating_extractor=rating_extractor,
            weights=rerank_weights,
        )

        self._items: List = []
        self._built = False

        if items:
            self.build_index(items)

    def build_index(self, items: List) -> None:
        """构建索引"""
        self._items = items
        self._bm25.build_index(items)
        self._tfidf.build_index(items)
        self._built = True

    def search(
        self,
        query: str,
        top_k: int = 10,
        candidate_k: int = 50,
        use_rerank: bool = True,
        filter_fn: Callable[[any], bool] = None,
    ) -> List[RetrievalResult]:
        """
        混合检索

        Args:
            query: 查询词
            top_k: 返回结果数
            candidate_k: 候选集大小（用于rerank的候选数）
            use_rerank: 是否使用重排
            filter_fn: 过滤函数

        Returns:
            检索结果列表
        """
        if not self._built:
            return []

        # 1. BM25检索
        bm25_results = self._bm25.search(query, top_k=candidate_k)

        # 2. TF-IDF检索
        tfidf_results = self._tfidf.search(query, top_k=candidate_k)

        # 3. RRF融合
        combined = self._rrf.combine(
            [bm25_results, tfidf_results],
            weights=[self._bm25_weight, self._tfidf_weight],
            top_k=candidate_k,
        )

        # 4. 过滤
        if filter_fn:
            combined = [r for r in combined if filter_fn(r.item)]

        # 5. Reranker重排
        if use_rerank and combined:
            final_results = self._reranker.rerank(combined, query, top_k=top_k)
        else:
            final_results = combined[:top_k]
            for i, r in enumerate(final_results):
                r.rank = i + 1

        return final_results

    @property
    def is_built(self) -> bool:
        return self._built

    @property
    def item_count(self) -> int:
        return len(self._items)
