"""
政策RAG工具 - 基于TF-IDF的简单向量检索 + 引用溯源
"""
from __future__ import annotations

import time
from typing import Dict, Any, List, Optional
from ..models.policy import PolicyChunk
from ..data.policies import get_policy_chunks
from ..retrieval.hybrid_search import HybridSearcher


_policy_searcher: Optional[HybridSearcher] = None
_policy_chunks_cache: List[PolicyChunk] = []


def _get_searcher() -> HybridSearcher:
    """获取或初始化政策检索器"""
    global _policy_searcher, _policy_chunks_cache

    if _policy_searcher is not None:
        return _policy_searcher

    _policy_chunks_cache = get_policy_chunks()
    _policy_searcher = HybridSearcher(
        items=_policy_chunks_cache,
        text_extractor=lambda c: c.search_text,
        title_extractor=lambda c: c.section_path,
        tag_extractor=lambda c: c.tags,
        popularity_extractor=lambda c: 0.0,  # 政策文档不按热度排序
        rating_extractor=lambda c: 0.0,
        bm25_weight=1.0,
        tfidf_weight=1.2,  # 政策文档语义更重要
        rrf_k=60,
    )

    return _policy_searcher


def policy_rag_tool(
    query: str,
    top_k: int = 3,
    return_sources: bool = True,
) -> Dict[str, Any]:
    """
    政策问答RAG工具

    功能：基于政策文档库进行检索式问答，返回相关政策片段和引用来源
    使用混合检索：BM25关键词 + TF-IDF语义 + RRF融合

    Args:
        query: 用户问题
        top_k: 返回最相关的k个片段
        return_sources: 是否返回来源信息

    Returns:
        RAG结果字典，包含答案片段、来源引用等
    """
    start_time = time.time()

    searcher = _get_searcher()

    # 1. 检索相关片段
    results = searcher.search(
        query=query,
        top_k=top_k,
        candidate_k=20,
        use_rerank=True,
    )

    search_time_ms = (time.time() - start_time) * 1000

    if not results:
        return {
            "success": True,
            "has_answer": False,
            "answer": "抱歉，没有找到相关的政策信息。建议您联系人工客服获取帮助。",
            "chunks": [],
            "sources": [],
            "confidence": 0.0,
            "search_time_ms": round(search_time_ms, 2),
        }

    # 2. 构造答案（基于检索结果的片段组装）
    chunks_info = []
    sources = []
    doc_ids = set()

    for result in results:
        chunk = result.item
        chunks_info.append({
            "chunk_id": chunk.chunk_id,
            "doc_id": chunk.doc_id,
            "doc_title": chunk.doc_title,
            "section_path": chunk.section_path,
            "content": chunk.content,
            "score": result.score,
            "rank": result.rank,
        })

        doc_ids.add(chunk.doc_id)

        if return_sources:
            sources.append({
                "doc_id": chunk.doc_id,
                "doc_title": chunk.doc_title,
                "section_path": chunk.section_path,
                "relevance_score": round(result.score, 4),
            })

    # 3. 计算置信度（基于最高分）
    max_score = max(r.score for r in results) if results else 0
    confidence = min(max_score / 0.5, 1.0)  # 假设0.5分以上为高置信

    # 4. 生成参考答案（基于最相关的片段）
    top_chunk = results[0].item if results else None
    answer_parts = []
    if top_chunk:
        answer_parts.append(f"根据《{top_chunk.doc_title}》的相关规定：")
        # 提取关键内容（简化版：直接返回内容摘要）
        content = top_chunk.content
        if len(content) > 300:
            content = content[:300] + "..."
        answer_parts.append(content)

    # 5. 相关问题建议
    related_questions = _generate_related_questions(query, results)

    return {
        "success": True,
        "has_answer": len(results) > 0,
        "answer": "\n\n".join(answer_parts) if answer_parts else "",
        "chunks": chunks_info,
        "sources": sources,
        "confidence": round(confidence, 4),
        "related_questions": related_questions,
        "total_chunks_found": len(results),
        "unique_docs": len(doc_ids),
        "search_time_ms": round(search_time_ms, 2),
    }


def _generate_related_questions(query: str, results: List) -> List[str]:
    """生成相关问题（简单规则版）"""
    related = []

    # 基于检索结果的文档标题生成
    doc_titles = set()
    for r in results:
        doc_titles.add(r.item.doc_title)

    if "七天无理由" in query or "退货" in query:
        related.extend([
            "质量问题怎么退货？",
            "退货运费谁承担？",
            "退款多久到账？",
        ])
    elif "物流" in query or "配送" in query or "快递" in query:
        related.extend([
            "发货时间是什么时候？",
            "运费怎么算？",
            "可以修改收货地址吗？",
        ])
    elif "支付" in query or "退款" in query or "钱" in query:
        related.extend([
            "支持哪些支付方式？",
            "可以开发票吗？",
            "部分退款怎么算？",
        ])
    elif "会员" in query or "积分" in query or "VIP" in query:
        related.extend([
            "怎么升级会员？",
            "积分有什么用？",
            "会员有哪些权益？",
        ])

    return related[:3]
