"""医学RAG工具."""
from __future__ import annotations

from typing import Dict, Any, List
from app.services.knowledge_service import get_knowledge_service


class MedicalRAGTool:
    """医学RAG问答工具.

    基于医学知识库的问答，支持引用溯源
    """

    name = "medical_rag"
    description = "医学知识库问答工具，基于BM25+TF-IDF+Reranker检索，支持引用溯源"

    def __init__(self):
        self.knowledge_service = get_knowledge_service()

    def query(self, question: str, top_k: int = 5) -> Dict[str, Any]:
        """医学知识问答.

        Args:
            question: 问题
            top_k: 返回结果数量

        Returns:
            问答结果
        """
        result = self.knowledge_service.answer(question, top_k=top_k)
        return {
            "question": question,
            "answer": result["answer"],
            "sources": result["sources"],
            "total_results": result["total_results"],
        }

    def search(self, query: str, top_k: int = 10) -> Dict[str, Any]:
        """搜索相关知识条目.

        Args:
            query: 查询关键词
            top_k: 返回数量

        Returns:
            检索结果
        """
        results = self.knowledge_service.search(query, top_k=top_k)

        documents = []
        for doc in results:
            documents.append({
                "id": doc["id"],
                "title": doc["title"],
                "category": doc.get("category", ""),
                "tags": doc.get("tags", ""),
                "source": doc.get("source", ""),
                "score": round(doc.get("score", 0), 4),
                "snippet": doc.get("content", "")[:200] + "...",
            })

        return {
            "query": query,
            "results": documents,
            "total_count": len(documents),
        }

    def get_detail(self, kb_id: int) -> Dict[str, Any]:
        """获取知识条目详情."""
        doc = self.knowledge_service.get_by_id(kb_id)
        if not doc:
            return {"found": False, "document": None}

        return {
            "found": True,
            "document": {
                "id": doc["id"],
                "title": doc["title"],
                "content": doc["content"],
                "category": doc.get("category", ""),
                "tags": doc.get("tags", ""),
                "source": doc.get("source", ""),
            },
        }

    def list_categories(self) -> Dict[str, Any]:
        """获取知识分类."""
        categories = self.knowledge_service.list_categories()
        return {"categories": categories}
