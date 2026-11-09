"""
商品服务 - 商品搜索、查询、统计
"""
from __future__ import annotations

import time
from typing import List, Optional, Tuple
from ..models.product import Product, ProductSearchParams, ProductSearchResult, ProductCategory
from ..data.products import get_all_products
from ..retrieval.hybrid_search import HybridSearcher, RetrievalResult


class ProductService:
    """商品服务"""

    _instance: Optional["ProductService"] = None
    _searcher: Optional[HybridSearcher] = None

    def __init__(self):
        self._products: List[Product] = []
        self._searcher: Optional[HybridSearcher] = None
        self._sku_index: dict = {}
        self._initialized = False

    @classmethod
    def get_instance(cls) -> "ProductService":
        """获取单例"""
        if cls._instance is None:
            cls._instance = cls()
            cls._instance.initialize()
        return cls._instance

    def initialize(self, products: List[Product] = None) -> None:
        """初始化服务"""
        if self._initialized:
            return

        self._products = products if products is not None else get_all_products()

        # 构建sku索引
        self._sku_index = {p.sku_id: p for p in self._products}

        # 构建混合检索器
        self._searcher = HybridSearcher(
            items=self._products,
            text_extractor=lambda p: p.search_text,
            title_extractor=lambda p: p.name,
            tag_extractor=lambda p: p.tags,
            popularity_extractor=lambda p: float(p.sales_volume),
            rating_extractor=lambda p: p.rating,
            bm25_weight=1.0,
            tfidf_weight=0.8,
            rrf_k=60,
        )

        self._initialized = True

    def search_products(self, params: ProductSearchParams) -> ProductSearchResult:
        """
        搜索商品

        流程：
        1. SQL结构化过滤（分类、品牌、价格、库存等）
        2. 混合检索（BM25 + TF-IDF + RRF + Reranker）
        3. 分页返回
        """
        start_time = time.time()

        if not self._initialized:
            self.initialize()

        # 1. 结构化过滤
        filtered = self._structured_filter(params)

        # 2. 如果有查询词，使用混合检索
        if params.query and params.query.strip():
            # 在过滤后的结果中检索
            if filtered:
                temp_searcher = HybridSearcher(
                    items=filtered,
                    text_extractor=lambda p: p.search_text,
                    title_extractor=lambda p: p.name,
                    tag_extractor=lambda p: p.tags,
                    popularity_extractor=lambda p: float(p.sales_volume),
                    rating_extractor=lambda p: p.rating,
                )
                results = temp_searcher.search(
                    query=params.query,
                    top_k=params.page_size,
                    candidate_k=min(len(filtered), 100),
                    use_rerank=True,
                )
                products = [r.item for r in results]
                total = len(filtered)
            else:
                products = []
                total = 0
        else:
            # 无查询词，按排序规则排序
            products = self._sort_products(filtered, params.sort_by)
            total = len(products)

        # 3. 分页
        start_idx = (params.page - 1) * params.page_size
        end_idx = start_idx + params.page_size
        page_products = products[start_idx:end_idx]

        search_time_ms = (time.time() - start_time) * 1000

        return ProductSearchResult(
            products=page_products,
            total=total,
            page=params.page,
            page_size=params.page_size,
            search_time_ms=round(search_time_ms, 2),
        )

    def _structured_filter(self, params: ProductSearchParams) -> List[Product]:
        """结构化过滤"""
        products = self._products

        # 只看在售商品
        products = [p for p in products if p.is_on_sale]

        # 分类过滤
        if params.category:
            products = [p for p in products if p.category == params.category]

        # 品牌过滤
        if params.brand:
            brand_lower = params.brand.lower()
            products = [p for p in products if brand_lower in p.brand.lower()]

        # 价格区间
        if params.min_price is not None:
            products = [p for p in products if p.price >= params.min_price]
        if params.max_price is not None:
            products = [p for p in products if p.price <= params.max_price]

        # 最低评分
        if params.min_rating is not None:
            products = [p for p in products if p.rating >= params.min_rating]

        # 标签过滤
        if params.tags:
            products = [
                p for p in products
                if all(tag in p.tags for tag in params.tags)
            ]

        # 仅显示有货
        if params.in_stock_only:
            products = [p for p in products if p.stock > 0]

        return products

    @staticmethod
    def _sort_products(products: List[Product], sort_by: str) -> List[Product]:
        """排序商品"""
        if sort_by == "price_asc":
            return sorted(products, key=lambda p: p.price)
        elif sort_by == "price_desc":
            return sorted(products, key=lambda p: p.price, reverse=True)
        elif sort_by == "sales_desc":
            return sorted(products, key=lambda p: p.sales_volume, reverse=True)
        elif sort_by == "rating_desc":
            return sorted(products, key=lambda p: p.rating, reverse=True)
        elif sort_by == "newest":
            return sorted(products, key=lambda p: p.sku_id, reverse=True)
        else:  # relevance（默认按销量+评分综合）
            return sorted(products, key=lambda p: (p.rating * p.sales_volume), reverse=True)

    def get_product_by_sku(self, sku_id: str) -> Optional[Product]:
        """根据SKU ID获取商品"""
        if not self._initialized:
            self.initialize()
        return self._sku_index.get(sku_id)

    def get_products_by_category(self, category: ProductCategory) -> List[Product]:
        """按分类获取商品"""
        if not self._initialized:
            self.initialize()
        return [p for p in self._products if p.category == category and p.is_on_sale]

    def get_hot_products(self, category: ProductCategory = None, limit: int = 10) -> List[Product]:
        """获取热门商品"""
        if not self._initialized:
            self.initialize()

        products = [p for p in self._products if p.is_on_sale]
        if category:
            products = [p for p in products if p.category == category]

        products.sort(key=lambda p: (p.sales_volume, p.rating), reverse=True)
        return products[:limit]

    def get_product_count(self, category: ProductCategory = None) -> int:
        """获取商品数量"""
        if not self._initialized:
            self.initialize()

        if category:
            return sum(1 for p in self._products if p.category == category and p.is_on_sale)
        return sum(1 for p in self._products if p.is_on_sale)

    def get_all_brands(self, category: ProductCategory = None) -> List[str]:
        """获取所有品牌"""
        if not self._initialized:
            self.initialize()

        products = self._products
        if category:
            products = [p for p in products if p.category == category]

        brands = sorted(set(p.brand for p in products if p.brand))
        return brands

    @property
    def product_count(self) -> int:
        if not self._initialized:
            self.initialize()
        return len(self._products)
