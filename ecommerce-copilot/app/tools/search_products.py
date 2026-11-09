"""
商品搜索工具 - 混合检索：SQL结构化过滤 + BM25 + TF-IDF + RRF + Reranker
"""
from __future__ import annotations

from typing import Dict, Any, Optional
from ..models.product import ProductSearchParams, ProductCategory
from ..services.product_service import ProductService


def search_products_tool(
    query: str = "",
    category: Optional[str] = None,
    brand: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    page: int = 1,
    page_size: int = 5,
    sort_by: str = "relevance",
    in_stock_only: bool = False,
) -> Dict[str, Any]:
    """
    商品搜索工具

    功能：根据关键词和筛选条件搜索商品，使用混合检索（BM25 + TF-IDF + RRF融合 + Reranker）

    Args:
        query: 搜索关键词
        category: 商品分类 (electronics/clothing/home_appliances/books/food/beauty/sports/toys/furniture/stationery)
        brand: 品牌
        min_price: 最低价格
        max_price: 最高价格
        page: 页码
        page_size: 每页数量
        sort_by: 排序方式 (relevance/price_asc/price_desc/sales_desc/rating_desc/newest)
        in_stock_only: 仅显示有货

    Returns:
        搜索结果字典，包含商品列表、总数、耗时等信息
    """
    product_service = ProductService.get_instance()

    # 解析分类
    category_enum = None
    if category:
        try:
            category_enum = ProductCategory(category)
        except ValueError:
            pass

    params = ProductSearchParams(
        query=query,
        category=category_enum,
        brand=brand,
        min_price=min_price,
        max_price=max_price,
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        in_stock_only=in_stock_only,
    )

    result = product_service.search_products(params)

    # 构造返回结果（精简版，便于LLM处理）
    products_info = []
    for p in result.products:
        products_info.append({
            "sku_id": p.sku_id,
            "name": p.name,
            "category": p.category.value,
            "brand": p.brand,
            "price": p.price,
            "original_price": p.original_price,
            "discount_rate": p.discount_rate,
            "stock": p.stock,
            "sales_volume": p.sales_volume,
            "rating": p.rating,
            "review_count": p.review_count,
            "tags": p.tags,
            "description": p.description[:100] + "..." if len(p.description) > 100 else p.description,
        })

    return {
        "success": True,
        "products": products_info,
        "total": result.total,
        "page": result.page,
        "page_size": result.page_size,
        "has_more": result.page * result.page_size < result.total,
        "search_time_ms": result.search_time_ms,
    }
