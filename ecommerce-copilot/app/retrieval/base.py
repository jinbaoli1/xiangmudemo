"""
检索基类
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Any, Dict, Generic, TypeVar
from dataclasses import dataclass, field

T = TypeVar('T')


@dataclass
class RetrievalResult(Generic[T]):
    """检索结果"""
    item: T
    score: float = 0.0
    rank: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


class BaseRetriever(ABC, Generic[T]):
    """检索器基类"""

    def __init__(self, items: List[T] = None):
        self._items: List[T] = []
        self._built = False
        if items:
            self.build_index(items)

    @abstractmethod
    def build_index(self, items: List[T]) -> None:
        """构建索引"""
        pass

    @abstractmethod
    def search(self, query: str, top_k: int = 10, **kwargs) -> List[RetrievalResult[T]]:
        """检索"""
        pass

    @property
    def is_built(self) -> bool:
        return self._built

    @property
    def item_count(self) -> int:
        return len(self._items)
