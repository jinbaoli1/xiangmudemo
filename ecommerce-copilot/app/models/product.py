from __future__ import annotations

from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator


class ProductCategory(str, Enum):
    """商品分类"""
    ELECTRONICS = "electronics"          # 电子产品
    CLOTHING = "clothing"                # 服装
    HOME_APPLIANCES = "home_appliances"  # 家电
    BOOKS = "books"                      # 图书
    FOOD = "food"                        # 食品
    BEAUTY = "beauty"                    # 美妆
    SPORTS = "sports"                    # 运动
    TOYS = "toys"                        # 玩具
    FURNITURE = "furniture"              # 家具
    STATIONERY = "stationery"            # 文具


class Product(BaseModel):
    """商品模型"""
    sku_id: str = Field(..., description="商品SKU ID")
    name: str = Field(..., min_length=1, max_length=200, description="商品名称")
    description: str = Field(default="", max_length=2000, description="商品描述")
    category: ProductCategory = Field(..., description="商品分类")
    price: float = Field(..., gt=0, description="商品价格，单位：元")
    original_price: Optional[float] = Field(None, gt=0, description="原价")
    brand: str = Field(default="", max_length=100, description="品牌")
    stock: int = Field(default=0, ge=0, description="库存数量")
    sales_volume: int = Field(default=0, ge=0, description="销量")
    rating: float = Field(default=5.0, ge=0, le=5, description="评分")
    review_count: int = Field(default=0, ge=0, description="评论数")
    tags: List[str] = Field(default_factory=list, description="标签")
    images: List[str] = Field(default_factory=list, description="图片URL列表")
    attributes: dict = Field(default_factory=dict, description="商品属性")
    is_on_sale: bool = Field(default=True, description="是否在售")

    @field_validator("original_price")
    @classmethod
    def original_price_must_be_greater_than_price(cls, v: Optional[float], info):
        if v is not None and v < info.data.get("price", 0):
            raise ValueError("原价不能低于现价")
        return v

    @property
    def discount_rate(self) -> Optional[float]:
        """折扣率"""
        if self.original_price and self.original_price > 0:
            return round(self.price / self.original_price, 2)
        return None

    @property
    def search_text(self) -> str:
        """用于检索的文本"""
        parts = [
            self.name,
            self.description,
            self.brand,
            self.category.value,
            " ".join(self.tags),
            " ".join(f"{k}:{v}" for k, v in self.attributes.items()),
        ]
        return " ".join(p for p in parts if p)


class ProductSearchParams(BaseModel):
    """商品搜索参数"""
    query: str = Field(default="", description="搜索关键词")
    category: Optional[ProductCategory] = Field(None, description="商品分类")
    brand: Optional[str] = Field(None, description="品牌")
    min_price: Optional[float] = Field(None, ge=0, description="最低价格")
    max_price: Optional[float] = Field(None, ge=0, description="最高价格")
    min_rating: Optional[float] = Field(None, ge=0, le=5, description="最低评分")
    tags: List[str] = Field(default_factory=list, description="标签过滤")
    in_stock_only: bool = Field(default=False, description="仅显示有货")
    sort_by: str = Field(default="relevance", description="排序方式")
    page: int = Field(default=1, ge=1, description="页码")
    page_size: int = Field(default=10, ge=1, le=100, description="每页数量")

    @field_validator("max_price")
    @classmethod
    def max_price_must_be_greater_than_min(cls, v: Optional[float], info):
        min_price = info.data.get("min_price")
        if v is not None and min_price is not None and v < min_price:
            raise ValueError("最高价格不能低于最低价格")
        return v


class ProductSearchResult(BaseModel):
    """商品搜索结果"""
    products: List[Product] = Field(default_factory=list)
    total: int = Field(default=0, ge=0, description="总数")
    page: int = Field(default=1)
    page_size: int = Field(default=10)
    search_time_ms: float = Field(default=0.0, description="搜索耗时(毫秒)")
