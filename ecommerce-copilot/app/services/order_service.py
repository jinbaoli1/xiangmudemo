"""
订单服务 - 订单查询、物流查询、鉴权
"""
from __future__ import annotations

from typing import List, Optional, Tuple
from datetime import datetime
from ..models.order import Order, OrderStatus, LogisticsInfo
from ..data.orders import get_all_orders


class OrderService:
    """订单服务"""

    _instance: Optional["OrderService"] = None

    def __init__(self):
        self._orders: List[Order] = []
        self._order_index: dict = {}
        self._user_orders_index: dict = {}
        self._initialized = False

    @classmethod
    def get_instance(cls) -> "OrderService":
        """获取单例"""
        if cls._instance is None:
            cls._instance = cls()
            cls._instance.initialize()
        return cls._instance

    def initialize(self, orders: List[Order] = None) -> None:
        """初始化服务"""
        if self._initialized:
            return

        self._orders = orders if orders is not None else get_all_orders()

        # 构建订单号索引
        self._order_index = {o.order_id: o for o in self._orders}

        # 构建用户订单索引
        self._user_orders_index = {}
        for order in self._orders:
            if order.user_id not in self._user_orders_index:
                self._user_orders_index[order.user_id] = []
            self._user_orders_index[order.user_id].append(order)

        # 按创建时间倒序
        for user_id in self._user_orders_index:
            self._user_orders_index[user_id].sort(
                key=lambda o: o.create_time, reverse=True
            )

        self._initialized = True

    def get_order_by_id(
        self,
        order_id: str,
        user_id: Optional[str] = None,
    ) -> Tuple[Optional[Order], Optional[str]]:
        """
        根据订单号获取订单

        Args:
            order_id: 订单号
            user_id: 用户ID（用于ownership校验）

        Returns:
            (订单, 错误信息) - 如果鉴权失败，订单为None
        """
        if not self._initialized:
            self.initialize()

        order = self._order_index.get(order_id)
        if not order:
            return None, "订单不存在"

        # ownership校验
        if user_id and order.user_id != user_id:
            return None, "无权访问该订单"

        return order, None

    def get_user_orders(
        self,
        user_id: str,
        status: Optional[OrderStatus] = None,
        page: int = 1,
        page_size: int = 10,
    ) -> Tuple[List[Order], int]:
        """
        获取用户订单列表

        Args:
            user_id: 用户ID
            status: 订单状态过滤
            page: 页码
            page_size: 每页数量

        Returns:
            (订单列表, 总数)
        """
        if not self._initialized:
            self.initialize()

        user_orders = self._user_orders_index.get(user_id, [])

        # 状态过滤
        if status:
            user_orders = [o for o in user_orders if o.status == status]

        total = len(user_orders)

        # 分页
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        page_orders = user_orders[start_idx:end_idx]

        return page_orders, total

    def get_logistics(
        self,
        order_id: str,
        user_id: Optional[str] = None,
    ) -> Tuple[Optional[LogisticsInfo], Optional[str]]:
        """
        获取物流信息

        Args:
            order_id: 订单号
            user_id: 用户ID

        Returns:
            (物流信息, 错误信息)
        """
        order, error = self.get_order_by_id(order_id, user_id)
        if error:
            return None, error

        if not order:
            return None, "订单不存在"

        if not order.logistics:
            return None, "订单尚未发货，暂无物流信息"

        return order.logistics, None

    def verify_ownership(self, order_id: str, user_id: str) -> bool:
        """
        验证订单归属权

        Args:
            order_id: 订单号
            user_id: 用户ID

        Returns:
            是否属于该用户
        """
        if not self._initialized:
            self.initialize()

        order = self._order_index.get(order_id)
        if not order:
            return False
        return order.user_id == user_id

    def get_order_count(self, user_id: str, status: Optional[OrderStatus] = None) -> int:
        """获取用户订单数量"""
        if not self._initialized:
            self.initialize()

        user_orders = self._user_orders_index.get(user_id, [])
        if status:
            return sum(1 for o in user_orders if o.status == status)
        return len(user_orders)

    def get_order_statistics(self, user_id: str) -> dict:
        """获取用户订单统计"""
        if not self._initialized:
            self.initialize()

        user_orders = self._user_orders_index.get(user_id, [])

        stats = {
            "total_orders": len(user_orders),
            "total_spent": 0.0,
            "status_count": {},
        }

        for order in user_orders:
            if order.status in (OrderStatus.COMPLETED, OrderStatus.DELIVERED):
                stats["total_spent"] += order.actual_payment

            status_key = order.status.value
            stats["status_count"][status_key] = stats["status_count"].get(status_key, 0) + 1

        stats["total_spent"] = round(stats["total_spent"], 2)
        return stats

    @property
    def order_count(self) -> int:
        if not self._initialized:
            self.initialize()
        return len(self._orders)
