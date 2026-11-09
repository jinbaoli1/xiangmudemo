from __future__ import annotations

from enum import Enum
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class AfterSaleType(str, Enum):
    """售后类型"""
    RETURN = "return"        # 退货退款
    EXCHANGE = "exchange"    # 换货
    REFUND = "refund"        # 仅退款
    REPAIR = "repair"        # 维修


class AfterSaleStatus(str, Enum):
    """售后状态"""
    DRAFT = "draft"              # 草稿
    PENDING_REVIEW = "pending_review"    # 待审核
    APPROVED = "approved"        # 已通过
    REJECTED = "rejected"        # 已拒绝
    PROCESSING = "processing"    # 处理中
    COMPLETED = "completed"      # 已完成
    CANCELLED = "cancelled"      # 已取消
    NEED_HUMAN = "need_human"    # 需人工介入


class AfterSaleRule(BaseModel):
    """售后规则"""
    rule_id: str = Field(..., description="规则ID")
    name: str = Field(..., description="规则名称")
    after_sale_type: AfterSaleType = Field(..., description="售后类型")
    applicable_categories: List[str] = Field(default_factory=list, description="适用分类，空表示全部")
    applicable_brands: List[str] = Field(default_factory=list, description="适用品牌，空表示全部")
    max_days_after_delivery: int = Field(default=7, description="签收后最大天数")
    min_amount: Optional[float] = Field(None, description="最低金额")
    max_amount: Optional[float] = Field(None, description="最高金额")
    requires_reason: bool = Field(default=True, description="是否需要原因")
    requires_evidence: bool = Field(default=False, description="是否需要凭证")
    allowed_reasons: List[str] = Field(default_factory=list, description="允许的原因")
    auto_approve: bool = Field(default=False, description="是否自动通过")
    priority: int = Field(default=0, description="优先级，越大越优先")
    description: str = Field(default="", description="规则描述")
    risk_level: str = Field(default="low", description="风险等级: low/medium/high")


class AfterSaleApplication(BaseModel):
    """售后申请"""
    application_id: str = Field(..., description="售后申请ID")
    order_id: str = Field(..., description="关联订单号")
    user_id: str = Field(..., description="用户ID")
    after_sale_type: AfterSaleType = Field(..., description="售后类型")
    status: AfterSaleStatus = Field(default=AfterSaleStatus.DRAFT, description="状态")
    sku_id: Optional[str] = Field(None, description="商品SKU ID")
    product_name: Optional[str] = Field(None, description="商品名称")
    quantity: int = Field(default=1, description="数量")
    amount: float = Field(default=0, description="申请金额")
    reason: str = Field(default="", description="售后原因")
    description: str = Field(default="", description="详细描述")
    evidence_images: List[str] = Field(default_factory=list, description="凭证图片")
    idempotency_key: str = Field(..., description="幂等键")
    create_time: datetime = Field(default_factory=datetime.now, description="创建时间")
    update_time: datetime = Field(default_factory=datetime.now, description="更新时间")
    review_time: Optional[datetime] = Field(None, description="审核时间")
    reviewer: Optional[str] = Field(None, description="审核人")
    review_comment: Optional[str] = Field(None, description="审核意见")
    risk_tags: List[str] = Field(default_factory=list, description="风险标签")
    handoff_reason: Optional[str] = Field(None, description="转人工原因")

    def to_handoff_package(self) -> Dict[str, Any]:
        """生成人工接管包"""
        return {
            "application_id": self.application_id,
            "order_id": self.order_id,
            "user_id": self.user_id,
            "after_sale_type": self.after_sale_type.value,
            "status": self.status.value,
            "product_name": self.product_name,
            "amount": self.amount,
            "reason": self.reason,
            "description": self.description,
            "risk_tags": self.risk_tags,
            "create_time": self.create_time.isoformat(),
        }


class AfterSaleEvaluationResult(BaseModel):
    """售后资格评估结果"""
    eligible: bool = Field(..., description="是否符合条件")
    after_sale_type: AfterSaleType = Field(..., description="建议售后类型")
    matched_rule: Optional[AfterSaleRule] = Field(None, description="匹配的规则")
    reasons: List[str] = Field(default_factory=list, description="原因说明")
    warnings: List[str] = Field(default_factory=list, description="警告信息")
    risk_level: str = Field(default="low", description="风险等级")
    auto_approve: bool = Field(default=False, description="是否自动通过")
    estimated_amount: float = Field(default=0, description="预估金额")
