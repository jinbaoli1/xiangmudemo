"""融合检索器 - BM25 + TF-IDF + Reranker."""
from __future__ import annotations

from typing import List, Dict, Any, Optional

from app.retrieval.bm25_retriever import BM25Retriever
from app.retrieval.tfidf_retriever import TFIDFRetriever
from app.retrieval.reranker import Reranker


class EnsembleRetriever:
    """融合检索器.

    策略：
    1. BM25 和 TF-IDF 分别召回
    2. 结果融合（加权合并）
    3. Reranker 重排序
    """

    def __init__(self):
        self.bm25 = BM25Retriever()
        self.tfidf = TFIDFRetriever()
        self.reranker = Reranker()
        self._built = False

    def build_index(self, documents: List[Dict[str, Any]]):
        """构建索引."""
        self.bm25.build_index(documents)
        self.tfidf.build_index(documents)
        self._built = True

    @property
    def is_built(self) -> bool:
        return self._built

    def search(
        self,
        query: str,
        top_k: int = 5,
        bm25_top_k: int = 20,
        tfidf_top_k: int = 20,
        use_rerank: bool = True,
    ) -> List[Dict[str, Any]]:
        """检索文档.

        Args:
            query: 查询文本
            top_k: 最终返回数量
            bm25_top_k: BM25 召回数量
            tfidf_top_k: TF-IDF 召回数量
            use_rerank: 是否使用重排序

        Returns:
            相关文档列表
        """
        if not self._built:
            return []

        # 1. 分别召回
        bm25_results = self.bm25.search(query, top_k=bm25_top_k)
        tfidf_results = self.tfidf.search(query, top_k=tfidf_top_k)

        # 2. 归一化分数
        self._normalize_scores(bm25_results)
        self._normalize_scores(tfidf_results)

        # 3. 融合结果
        merged = self._merge_results(bm25_results, tfidf_results)

        # 4. 重排序
        if use_rerank and merged:
            merged = self.reranker.rerank(query, merged, top_k=top_k * 2)

        # 5. 返回top_k
        return merged[:top_k]

    def _normalize_scores(self, results: List[Dict[str, Any]]):
        """将分数归一化到 [0, 1] 区间."""
        if not results:
            return
        max_score = max(r["score"] for r in results)
        if max_score > 0:
            for r in results:
                r["norm_score"] = r["score"] / max_score
        else:
            for r in results:
                r["norm_score"] = 0.0

    def _merge_results(
        self,
        bm25_results: List[Dict[str, Any]],
        tfidf_results: List[Dict[str, Any]],
        bm25_weight: float = 0.6,
        tfidf_weight: float = 0.4,
    ) -> List[Dict[str, Any]]:
        """融合两路检索结果，使用加权和 + 互惠排名融合."""
        doc_map = {}

        # BM25 结果
        for rank, doc in enumerate(bm25_results):
            doc_id = doc["id"]
            bm25_norm = doc.get("norm_score", 0.0)
            # 互惠排名分数
            reciprocal_rank = 1.0 / (rank + 1)

            if doc_id not in doc_map:
                doc_map[doc_id] = dict(doc)
                doc_map[doc_id]["bm25_score"] = doc["score"]
                doc_map[doc_id]["bm25_rank"] = rank
                doc_map[doc_id]["tfidf_score"] = 0.0
                doc_map[doc_id]["tfidf_rank"] = 9999
                doc_map[doc_id]["fused_score"] = 0.0

            doc_map[doc_id]["bm25_score"] = doc["score"]
            doc_map[doc_id]["bm25_rank"] = rank
            doc_map[doc_id]["fused_score"] += bm25_norm * bm25_weight + reciprocal_rank * 0.3

        # TF-IDF 结果
        for rank, doc in enumerate(tfidf_results):
            doc_id = doc["id"]
            tfidf_norm = doc.get("norm_score", 0.0)
            reciprocal_rank = 1.0 / (rank + 1)

            if doc_id not in doc_map:
                doc_map[doc_id] = dict(doc)
                doc_map[doc_id]["bm25_score"] = 0.0
                doc_map[doc_id]["bm25_rank"] = 9999
                doc_map[doc_id]["tfidf_score"] = doc["score"]
                doc_map[doc_id]["tfidf_rank"] = rank
                doc_map[doc_id]["fused_score"] = 0.0

            doc_map[doc_id]["tfidf_score"] = doc["score"]
            doc_map[doc_id]["tfidf_rank"] = rank
            doc_map[doc_id]["fused_score"] += tfidf_norm * tfidf_weight + reciprocal_rank * 0.3
            # 标记同时被两路召回的
            if doc_map[doc_id]["bm25_score"] > 0:
                doc_map[doc_id]["fused_score"] += 0.5  # 交叉召回加分

        merged = list(doc_map.values())
        merged.sort(key=lambda x: x["fused_score"], reverse=True)

        # 用融合分作为 score
        for doc in merged:
            doc["score"] = doc["fused_score"]
            doc["retriever"] = "ensemble"

        return merged

    def __len__(self) -> int:
        return len(self.bm25)
