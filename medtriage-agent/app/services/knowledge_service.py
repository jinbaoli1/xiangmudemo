"""医学知识库服务."""
from __future__ import annotations

from typing import List, Dict, Any, Optional
from app.database import get_db
from app.retrieval.ensemble import EnsembleRetriever


class KnowledgeService:
    """医学知识库服务."""

    def __init__(self):
        self.retriever = EnsembleRetriever()
        self._loaded = False

    def load(self):
        """从数据库加载知识库并构建索引."""
        if self._loaded:
            return

        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM knowledge_base")
            rows = cursor.fetchall()
            documents = [dict(row) for row in rows]

        if documents:
            self.retriever.build_index(documents)
            self._loaded = True

    @property
    def is_loaded(self) -> bool:
        return self._loaded

    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """检索相关知识."""
        if not self._loaded:
            self.load()
        return self.retriever.search(query, top_k=top_k)

    def answer(self, query: str, top_k: int = 5) -> Dict[str, Any]:
        """基于检索结果生成回答（简单模板式）."""
        results = self.search(query, top_k=top_k)

        if not results:
            return {
                "answer": "抱歉，暂未找到相关的医学知识。建议您咨询专业医生获取更准确的信息。",
                "sources": [],
                "total_results": 0,
            }

        # 简单的回答生成：拼接最相关的内容
        top_result = results[0]
        answer_parts = []

        answer_parts.append(f"根据您的问题「{query}」，为您找到以下相关医学知识：\n")
        answer_parts.append(f"【{top_result['title']}】\n")

        # 截取相关内容片段
        content = top_result["content"]
        # 尝试找到最相关的段落
        relevant_sentences = []
        for sentence in content.split("。"):
            if any(kw in sentence for kw in query.split()) and sentence.strip():
                relevant_sentences.append(sentence.strip() + "。")

        if relevant_sentences:
            answer_parts.append("\n".join(relevant_sentences[:3]))
        else:
            # 返回前200字
            answer_parts.append(content[:300] + "..." if len(content) > 300 else content)

        answer_parts.append(f"\n\n*信息来源：{top_result.get('source', '医学知识库')}*")

        # 引用溯源信息
        sources = []
        for i, doc in enumerate(results[:3]):
            sources.append({
                "index": i + 1,
                "title": doc["title"],
                "category": doc.get("category", ""),
                "score": round(doc.get("score", 0), 4),
                "source": doc.get("source", ""),
                "snippet": doc.get("content", "")[:100] + "...",
            })

        return {
            "answer": "\n".join(answer_parts),
            "sources": sources,
            "total_results": len(results),
        }

    def get_by_id(self, kb_id: int) -> Optional[Dict[str, Any]]:
        """根据ID获取知识条目."""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM knowledge_base WHERE id = ?", (kb_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def list_categories(self) -> List[str]:
        """获取知识分类列表."""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT category FROM knowledge_base WHERE category IS NOT NULL")
            rows = cursor.fetchall()
            return [row["category"] for row in rows]


# 全局单例
_knowledge_service: Optional[KnowledgeService] = None


def get_knowledge_service() -> KnowledgeService:
    """获取知识库服务单例."""
    global _knowledge_service
    if _knowledge_service is None:
        _knowledge_service = KnowledgeService()
        _knowledge_service.load()
    return _knowledge_service
