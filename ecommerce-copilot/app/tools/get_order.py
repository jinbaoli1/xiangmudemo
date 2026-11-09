"""
订单查询工具 - 带ownership校验
"""
from __future__ import annotations

from typing import Dict, Any, Optional
from ..services.order_service import OrderService


def get_order_tool(
    user_id: str,
    order_id: Optional[str] = None,
    status: Optional[str] = None,
    page: int = 1,
    page_size: int = 10,
) -> Dict[str, Any]:
    """
    订单查询工具

    功能：查询用户订单，支持按订单号查询或按状态查询列表
    注意：所有查询都经过ownership校验，用户只能查看自己的订单

    Args:
        user_id: 用户ID（服务端注入，不可伪造）
        order_id: 订单号（可选，指定则查单个订单详情）
        status: 订单状态（可选，用于列表过滤）
            pending_payment: 待支付
            paid: 已支付
            shipped: 已发货
            delivered: 已签收
            completed: 已完成
            cancelled: 已取消
            refunding: 退款中
            refunded: 已退款
        page: 页码
        page_size: 每页数量

    Returns:
        订单信息字典
    """
    order_service = OrderService.get_instance()

    # 单个订单查询
    if order_id:
        order, error = order_service.get_order_by_id(order_id, user_id)
        if error:
            return {
                "success": False,
                "error": error,
                "orders": [],
                "total": 0,
            }

        if not order:
            return {
                "success": False,
                "error": "订单不存在",
                "orders": [],
                "total": 0,
            }

        return {
            "success": True,
            "orders": [_format_order(order)],
            "total": 1,
            "is_single": True,
        }

    # 列表查询
    orders, total = order_service.get_user_orders(
        user_id=user_id,
        status=status,
        page=page,
        page_size=page_size,
    )

    return {
        "success": True,
        "orders": [_format_order(o) for o in orders],
        "total": total,
        "page": page,
        "page_size": page_size,
        "has_more": page * page_size < total,
        "is_single": False,
    }


def _format_order(order) -> Dict[str, Any]:
    """格式化订单信息"""
    items_info = []
    for item in order.items:
        items_info.append({
            "sku_id": item.sku_id,
            "product_name": item.product_name,
            "quantity": item.quantity,
            "unit_price": item.unit_price,
            "subtotal": item.subtotal,
            "attributes": item.attributes,
        })

    logistics_info = None
    if order.logistics:
        logistics_info = {
            "tracking_number": order.logistics.tracking_number,
            "carrier": order.logistics.carrier,
            "status": order.logistics.status,
            "current_location": order.logistics.current_location,
            "estimated_delivery": order.logistics.estimated_delivery.isoformat() if order.logistics.estimated_delivery else None,
        }

    return {
        "order_id": order.order_id,
        "status": order.status.value,
        "status_text": _get_status_text(order.status.value),
        "items": items_info,
        "total_amount": order.total_amount,
        "discount_amount": order.discount_amount,
        "shipping_fee": order.shipping_fee,
        "actual_payment": order.actual_payment,
        "shipping_address": order.shipping_address,
        "payment_method": order.payment_method,
        "payment_time": order.payment_time.isoformat() if order.payment_time else None,
        "shipping_time": order.shipping_time.isoformat() if order.shipping_time else None,
        "delivery_time": order.delivery_time.isoformat() if order.delivery_time else None,
        "create_time": order.create_time.isoformat(),
        "logistics": logistics_info,
        "remark": order.remark,
        "can_cancel": order.can_cancel,
        "can_return": order.can_return,
        "can_refund": order.can_refund,
        "days_since_delivery": order.days_since_delivery,
    }


def _get_status_text(status: str) -> str:
    """获取状态中文描述"""
    status_map = {
        "pending_payment": "待支付",
        "paid": "已支付",
        "shipped": "已发货",
        "delivered": "已签收",
        "completed": "已完成",
        "cancelled": "已取消",
        "refunding": "退款中",
        "refunded": "已退款",
    }
    return status_map.get(status, status)
