"""
库存服务 - 库存查询、扣减、预占
"""
from __future__ import annotations

import threading
from typing import Optional, Dict
from ..models.product import Product
from .product_service import ProductService


class InventoryService:
    """库存服务（简单内存实现）"""

    _instance: Optional["InventoryService"] = None

    def __init__(self):
        self._lock = threading.Lock()
        self._preoccupied: Dict[str, int] = {}  # 预占库存
        self._initialized = False

    @classmethod
    def get_instance(cls) -> "InventoryService":
        """获取单例"""
        if cls._instance is None:
            cls._instance = cls()
            cls._instance.initialize()
        return cls._instance

    def initialize(self) -> None:
        """初始化"""
        if self._initialized:
            return
        # 确保ProductService初始化
        ProductService.get_instance()
        self._initialized = True

    def get_available_stock(self, sku_id: str) -> int:
        """获取可用库存（总库存 - 预占库存）"""
        product_service = ProductService.get_instance()
        product = product_service.get_product_by_sku(sku_id)
        if not product:
            return 0

        preoccupied = self._preoccupied.get(sku_id, 0)
        return max(0, product.stock - preoccupied)

    def get_total_stock(self, sku_id: str) -> int:
        """获取总库存"""
        product_service = ProductService.get_instance()
        product = product_service.get_product_by_sku(sku_id)
        if not product:
            return 0
        return product.stock

    def is_in_stock(self, sku_id: str, quantity: int = 1) -> bool:
        """检查是否有足够库存"""
        return self.get_available_stock(sku_id) >= quantity

    def preoccupy_stock(self, sku_id: str, quantity: int) -> bool:
        """
        预占库存

        Returns:
            是否预占成功
        """
        with self._lock:
            available = self.get_available_stock(sku_id)
            if available < quantity:
                return False
            self._preoccupied[sku_id] = self._preoccupied.get(sku_id, 0) + quantity
            return True

    def release_preoccupation(self, sku_id: str, quantity: int) -> None:
        """释放预占库存"""
        with self._lock:
            current = self._preoccupied.get(sku_id, 0)
            self._preoccupied[sku_id] = max(0, current - quantity)

    def deduct_stock(self, sku_id: str, quantity: int, use_preoccupation: bool = True) -> bool:
        """
        扣减库存（实际出库）

        Args:
            sku_id: 商品SKU
            quantity: 数量
            use_preoccupation: 是否使用预占库存（如果有预占，先扣预占）

        Returns:
            是否扣减成功
        """
        product_service = ProductService.get_instance()
        product = product_service.get_product_by_sku(sku_id)
        if not product:
            return False

        with self._lock:
            if use_preoccupation:
                preoccupied = self._preoccupied.get(sku_id, 0)
                if preoccupied >= quantity:
                    # 从预占中扣减
                    self._preoccupied[sku_id] = preoccupied - quantity
                    product.stock -= quantity
                    return True
                elif preoccupied > 0:
                    # 部分使用预占
                    remaining = quantity - preoccupied
                    if product.stock - preoccupied >= remaining:
                        product.stock -= quantity
                        self._preoccupied[sku_id] = 0
                        return True
                    return False

            # 直接扣减
            if product.stock >= quantity:
                product.stock -= quantity
                return True
            return False

    def add_stock(self, sku_id: str, quantity: int) -> bool:
        """增加库存（入库）"""
        product_service = ProductService.get_instance()
        product = product_service.get_product_by_sku(sku_id)
        if not product:
            return False

        with self._lock:
            product.stock += quantity
            return True

    def get_preoccupied_stock(self, sku_id: str) -> int:
        """获取预占库存数量"""
        return self._preoccupied.get(sku_id, 0)
