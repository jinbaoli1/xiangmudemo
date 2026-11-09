from __future__ import annotations

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class PolicyDocument(BaseModel):
    """政策文档"""
    doc_id: str = Field(..., description="文档ID")
    title: str = Field(..., description="标题")
    category: str = Field(default="general", description="分类")
    content: str = Field(..., description="文档内容")
    version: str = Field(default="1.0", description="版本")
    effective_date: Optional[datetime] = Field(None, description="生效日期")
    expiry_date: Optional[datetime] = Field(None, description="失效日期")
    is_active: bool = Field(default=True, description="是否生效")
    tags: List[str] = Field(default_factory=list, description="标签")
    priority: int = Field(default=0, description="优先级")


class PolicyChunk(BaseModel):
    """政策文档切片"""
    chunk_id: str = Field(..., description="切片ID")
    doc_id: str = Field(..., description="所属文档ID")
    doc_title: str = Field(default="", description="文档标题")
    content: str = Field(..., description="切片内容")
    chunk_index: int = Field(default=0, description="在文档中的索引")
    section_path: str = Field(default="", description="章节路径")
    tags: List[str] = Field(default_factory=list, description="标签")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")

    @property
    def search_text(self) -> str:
        """用于检索的文本"""
        return f"{self.doc_title} {self.section_path} {self.content} {' '.join(self.tags)}"


class PolicySearchResult(BaseModel):
    """政策搜索结果"""
    chunks: List[PolicyChunk] = Field(default_factory=list)
    total: int = Field(default=0)
    scores: List[float] = Field(default_factory=list)
    search_time_ms: float = Field(default=0.0)


class PolicyAnswer(BaseModel):
    """政策问答结果"""
    answer: str = Field(..., description="回答")
    sources: List[Dict[str, Any]] = Field(default_factory=list, description="引用来源")
    confidence: float = Field(default=0.0, description="置信度")
    related_questions: List[str] = Field(default_factory=list, description="相关问题")
