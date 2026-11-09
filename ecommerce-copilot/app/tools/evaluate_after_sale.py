"""
售后资格评估工具 - 规则引擎判断是否符合售后条件
"""
from __future__ import annotations

from typing import Dict, Any, Optional
from ..models.after_sale import AfterSaleType
from ..services.order_service import OrderService
from ..services.after_sale_rule_service import AfterSaleRuleService


def evaluate_after_sale_tool(
    user_id: str,
    order_id: str,
    after_sale_type: Optional[str] = None,
    sku_id: Optional[str] = None,
    reason: str = "",
    is_vip: bool = False,
    user_intent: str = "",
) -> Dict[str, Any]:
    """
    售后资格评估工具

    功能：基于规则引擎判断订单是否符合售后条件，返回评估结果和建议

    Args:
        user_id: 用户ID（服务端注入）
        order_id: 订单号
        after_sale_type: 售后类型 (return/exchange/refund/repair)，不填则根据意图判断
        sku_id: 商品SKU ID（可选，针对单个商品申请）
        reason: 售后原因
        is_vip: 是否VIP用户
        user_intent: 用户原始意图描述（用于推断售后类型）

    Returns:
        评估结果字典
    """
    order_service = OrderService.get_instance()
    rule_service = AfterSaleRuleService.get_instance()

    # 1. 获取订单（带鉴权）
    order, error = order_service.get_order_by_id(order_id, user_id)
    if error:
        return {
            "success": False,
            "error": error,
            "eligible": False,
        }

    if not order:
        return {
            "success": False,
            "error": "订单不存在",
            "eligible": False,
        }

    # 2. 确定售后类型
    if after_sale_type:
        try:
            as_type = AfterSaleType(after_sale_type)
        except ValueError:
            as_type = rule_service.determine_after_sale_type(order, user_intent)
    else:
        as_type = rule_service.determine_after_sale_type(order, user_intent)

    # 3. 评估资格
    evaluation = rule_service.evaluate_eligibility(
        order=order,
        after_sale_type=as_type,
        sku_id=sku_id,
        reason=reason,
        is_vip=is_vip,
    )

    # 4. 构造返回
    return {
        "success": True,
        "eligible": evaluation.eligible,
        "after_sale_type": evaluation.after_sale_type.value,
        "after_sale_type_text": _get_type_text(evaluation.after_sale_type.value),
        "estimated_amount": evaluation.estimated_amount,
        "risk_level": evaluation.risk_level,
        "auto_approve": evaluation.auto_approve,
        "reasons": evaluation.reasons,
        "warnings": evaluation.warnings,
        "matched_rule": {
            "rule_id": evaluation.matched_rule.rule_id,
            "name": evaluation.matched_rule.name,
            "description": evaluation.matched_rule.description,
        } if evaluation.matched_rule else None,
        "order_info": {
            "order_id": order.order_id,
            "status": order.status.value,
            "actual_payment": order.actual_payment,
            "delivery_time": order.delivery_time.isoformat() if order.delivery_time else None,
            "days_since_delivery": order.days_since_delivery,
        },
    }


def _get_type_text(after_sale_type: str) -> str:
    """售后类型中文描述"""
    type_map = {
        "return": "退货退款",
        "exchange": "换货",
        "refund": "仅退款",
        "repair": "维修",
    }
    return type_map.get(after_sale_type, after_sale_type)
