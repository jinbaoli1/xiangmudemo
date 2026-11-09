"""
物流查询工具
"""
from __future__ import annotations

from typing import Dict, Any
from ..services.order_service import OrderService


def get_logistics_tool(
    user_id: str,
    order_id: str,
) -> Dict[str, Any]:
    """
    物流查询工具

    功能：查询订单的物流信息，包括物流轨迹、当前位置、预计送达时间等
    注意：经过ownership校验，用户只能查看自己订单的物流信息

    Args:
        user_id: 用户ID（服务端注入）
        order_id: 订单号

    Returns:
        物流信息字典
    """
    order_service = OrderService.get_instance()

    logistics, error = order_service.get_logistics(order_id, user_id)

    if error:
        return {
            "success": False,
            "error": error,
            "logistics": None,
        }

    if not logistics:
        return {
            "success": False,
            "error": "暂无物流信息",
            "logistics": None,
        }

    return {
        "success": True,
        "logistics": {
            "tracking_number": logistics.tracking_number,
            "carrier": logistics.carrier,
            "status": logistics.status,
            "status_text": _get_status_text(logistics.status),
            "current_location": logistics.current_location,
            "estimated_delivery": logistics.estimated_delivery.isoformat() if logistics.estimated_delivery else None,
            "updates": logistics.updates,
        },
    }


def _get_status_text(status: str) -> str:
    """物流状态中文描述"""
    status_map = {
        "pending": "待发货",
        "in_transit": "运输中",
        "out_for_delivery": "派送中",
        "delivered": "已签收",
        "failed": "派送失败",
        "returned": "已退回",
    }
    return status_map.get(status, status)
