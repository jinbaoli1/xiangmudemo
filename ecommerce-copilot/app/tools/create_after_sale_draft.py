"""
创建售后草稿工具
"""
from __future__ import annotations

import uuid
import hashlib
from datetime import datetime
from typing import Dict, Any, Optional, List

from ..models.after_sale import (
    AfterSaleApplication, AfterSaleStatus, AfterSaleType
)
from ..services.order_service import OrderService


# 内存存储（实际项目用数据库）
_after_sale_storage: Dict[str, AfterSaleApplication] = {}
_idempotency_index: Dict[str, str] = {}  # idempotency_key -> application_id


def create_after_sale_draft_tool(
    user_id: str,
    order_id: str,
    after_sale_type: str,
    sku_id: Optional[str] = None,
    reason: str = "",
    description: str = "",
    evidence_images: Optional[List[str]] = None,
    idempotency_key: Optional[str] = None,
) -> Dict[str, Any]:
    """
    创建售后申请草稿

    功能：创建售后申请草稿，支持幂等操作
    注意：
    - 相同的幂等键只会创建一个草稿
    - 草稿状态为 DRAFT，需要确认后才提交审核

    Args:
        user_id: 用户ID（服务端注入）
        order_id: 订单号
        after_sale_type: 售后类型 (return/exchange/refund/repair)
        sku_id: 商品SKU ID（可选）
        reason: 售后原因
        description: 详细描述
        evidence_images: 凭证图片URL列表
        idempotency_key: 幂等键（建议传，不传则自动生成）

    Returns:
        售后申请草稿信息
    """
    order_service = OrderService.get_instance()

    # 1. 验证订单归属
    order, error = order_service.get_order_by_id(order_id, user_id)
    if error:
        return {
            "success": False,
            "error": error,
            "application": None,
        }

    if not order:
        return {
            "success": False,
            "error": "订单不存在",
            "application": None,
        }

    # 2. 生成幂等键
    if not idempotency_key:
        idempotency_key = hashlib.md5(
            f"{user_id}_{order_id}_{after_sale_type}_{sku_id or 'all'}_{datetime.now().strftime('%Y%m%d%H%M%S')}".encode()
        ).hexdigest()

    # 3. 幂等检查
    if idempotency_key in _idempotency_index:
        app_id = _idempotency_index[idempotency_key]
        existing = _after_sale_storage.get(app_id)
        if existing:
            return {
                "success": True,
                "application": _format_application(existing),
                "is_idempotent": True,
                "message": "已存在相同申请，返回已有草稿",
            }

    # 4. 计算金额和商品信息
    amount = 0.0
    product_name = None
    quantity = 1

    if sku_id:
        for item in order.items:
            if item.sku_id == sku_id:
                amount = item.subtotal
                product_name = item.product_name
                quantity = item.quantity
                break
    else:
        amount = order.actual_payment
        if order.items:
            product_name = order.items[0].product_name
            quantity = sum(i.quantity for i in order.items)

    # 5. 生成申请ID
    application_id = f"AS{datetime.now().strftime('%Y%m%d%H%M%S')}{uuid.uuid4().hex[:6].upper()}"

    # 6. 确定风险标签
    risk_tags = []
    if amount >= 5000:
        risk_tags.append("high_value")
    if reason in ["质量问题", "功能故障", "商品破损"]:
        risk_tags.append("quality_issue")
    if description and len(description) > 200:
        risk_tags.append("detailed_description")

    # 7. 创建申请
    application = AfterSaleApplication(
        application_id=application_id,
        order_id=order_id,
        user_id=user_id,
        after_sale_type=AfterSaleType(after_sale_type),
        status=AfterSaleStatus.DRAFT,
        sku_id=sku_id,
        product_name=product_name,
        quantity=quantity,
        amount=round(amount, 2),
        reason=reason,
        description=description,
        evidence_images=evidence_images or [],
        idempotency_key=idempotency_key,
        risk_tags=risk_tags,
    )

    # 8. 存储
    _after_sale_storage[application_id] = application
    _idempotency_index[idempotency_key] = application_id

    return {
        "success": True,
        "application": _format_application(application),
        "is_idempotent": False,
        "message": "售后草稿创建成功，请确认后提交",
        "next_step": "请确认申请信息无误后，调用 confirm_after_sale 工具提交审核",
    }


def _format_application(app: AfterSaleApplication) -> Dict[str, Any]:
    """格式化售后申请"""
    return {
        "application_id": app.application_id,
        "order_id": app.order_id,
        "after_sale_type": app.after_sale_type.value,
        "status": app.status.value,
        "status_text": _get_status_text(app.status.value),
        "sku_id": app.sku_id,
        "product_name": app.product_name,
        "quantity": app.quantity,
        "amount": app.amount,
        "reason": app.reason,
        "description": app.description,
        "evidence_count": len(app.evidence_images),
        "risk_tags": app.risk_tags,
        "create_time": app.create_time.isoformat(),
        "idempotency_key": app.idempotency_key,
    }


def _get_status_text(status: str) -> str:
    """状态中文描述"""
    status_map = {
        "draft": "草稿",
        "pending_review": "待审核",
        "approved": "已通过",
        "rejected": "已拒绝",
        "processing": "处理中",
        "completed": "已完成",
        "cancelled": "已取消",
        "need_human": "需人工介入",
    }
    return status_map.get(status, status)


def get_after_sale_application(application_id: str) -> Optional[AfterSaleApplication]:
    """获取售后申请（内部使用）"""
    return _after_sale_storage.get(application_id)
