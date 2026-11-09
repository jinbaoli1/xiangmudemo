"""
确认并提交售后申请工具 - 幂等提交 + 转人工判断
"""
from __future__ import annotations

from datetime import datetime
from typing import Dict, Any, Optional

from ..models.after_sale import AfterSaleStatus
from ..services.after_sale_rule_service import AfterSaleRuleService
from ..services.order_service import OrderService
from .create_after_sale_draft import get_after_sale_application


def confirm_after_sale_tool(
    user_id: str,
    application_id: str,
    confirm: bool = True,
) -> Dict[str, Any]:
    """
    确认并提交售后申请

    功能：
    1. 验证申请归属权
    2. 再次校验资格（防止状态变化）
    3. 幂等提交（重复提交返回相同结果）
    4. 根据风险等级判断是否自动通过或转人工

    Args:
        user_id: 用户ID（服务端注入）
        application_id: 售后申请ID
        confirm: 是否确认提交（True提交，False取消）

    Returns:
        提交结果
    """
    rule_service = AfterSaleRuleService.get_instance()
    order_service = OrderService.get_instance()

    # 1. 获取申请
    application = get_after_sale_application(application_id)
    if not application:
        return {
            "success": False,
            "error": "售后申请不存在",
        }

    # 2. 归属权校验
    if application.user_id != user_id:
        return {
            "success": False,
            "error": "无权操作该售后申请",
        }

    # 3. 取消申请
    if not confirm:
        if application.status == AfterSaleStatus.DRAFT:
            application.status = AfterSaleStatus.CANCELLED
            application.update_time = datetime.now()
            return {
                "success": True,
                "status": "cancelled",
                "status_text": "已取消",
                "application_id": application_id,
                "message": "售后申请已取消",
            }
        else:
            return {
                "success": False,
                "error": f"当前状态为{application.status.value}，无法取消",
            }

    # 4. 幂等检查：已提交则直接返回
    if application.status != AfterSaleStatus.DRAFT:
        return {
            "success": True,
            "status": application.status.value,
            "status_text": _get_status_text(application.status.value),
            "application_id": application_id,
            "is_idempotent": True,
            "message": "申请已提交，请勿重复操作",
            "needs_human": application.status == AfterSaleStatus.NEED_HUMAN,
        }

    # 5. 重新获取订单并校验资格
    order, error = order_service.get_order_by_id(application.order_id, user_id)
    if error or not order:
        return {
            "success": False,
            "error": error or "订单不存在",
        }

    # 6. 再次评估资格
    evaluation = rule_service.evaluate_eligibility(
        order=order,
        after_sale_type=application.after_sale_type,
        sku_id=application.sku_id,
        reason=application.reason,
        is_vip=False,  # 简化处理
    )

    if not evaluation.eligible:
        application.status = AfterSaleStatus.REJECTED
        application.update_time = datetime.now()
        application.review_comment = "; ".join(evaluation.reasons)
        return {
            "success": True,
            "status": "rejected",
            "status_text": "已拒绝",
            "application_id": application_id,
            "reasons": evaluation.reasons,
            "message": "售后申请未通过审核",
        }

    # 7. 判断处理方式
    needs_human = False
    handoff_reason = ""

    if evaluation.risk_level == "high":
        needs_human = True
        handoff_reason = "高风险订单需人工审核"
    elif evaluation.risk_level == "medium" and not evaluation.auto_approve:
        needs_human = True
        handoff_reason = "需人工审核确认"
    elif application.amount >= 5000:
        needs_human = True
        handoff_reason = "大额订单需人工审核"
    elif not evaluation.auto_approve:
        # 低风险但非自动通过，进入待审核状态
        application.status = AfterSaleStatus.PENDING_REVIEW
        application.update_time = datetime.now()
        return {
            "success": True,
            "status": "pending_review",
            "status_text": "待审核",
            "application_id": application_id,
            "estimated_processing_time": "24小时内",
            "message": "售后申请已提交，等待客服审核",
            "needs_human": False,
        }

    if needs_human:
        application.status = AfterSaleStatus.NEED_HUMAN
        application.update_time = datetime.now()
        application.handoff_reason = handoff_reason
        application.risk_tags.append("human_review_required")

        handoff_package = application.to_handoff_package()
        handoff_package.update({
            "evaluation_reasons": evaluation.reasons,
            "handoff_reason": handoff_reason,
            "risk_level": evaluation.risk_level,
        })

        return {
            "success": True,
            "status": "need_human",
            "status_text": "需人工介入",
            "application_id": application_id,
            "needs_human": True,
            "handoff_reason": handoff_reason,
            "handoff_package": handoff_package,
            "message": "已为您转接人工客服，请稍候",
        }

    # 8. 自动通过
    application.status = AfterSaleStatus.APPROVED
    application.update_time = datetime.now()
    application.review_time = datetime.now()
    application.reviewer = "system_auto"
    application.review_comment = "系统自动审核通过"

    return {
        "success": True,
        "status": "approved",
        "status_text": "已通过",
        "application_id": application_id,
        "approved_by": "system_auto",
        "approved_amount": application.amount,
        "message": "售后申请已自动通过，退款将在1-3个工作日内到账",
        "needs_human": False,
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
