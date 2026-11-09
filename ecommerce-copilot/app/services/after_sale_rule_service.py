"""
售后规则服务 - 规则匹配、资格评估
"""
from __future__ import annotations

from typing import List, Optional, Tuple
from datetime import datetime
from ..models.after_sale import (
    AfterSaleRule, AfterSaleType, AfterSaleEvaluationResult
)
from ..models.order import Order, OrderStatus
from ..data.after_sale_rules import get_after_sale_rules


class AfterSaleRuleService:
    """售后规则服务"""

    _instance: Optional["AfterSaleRuleService"] = None

    def __init__(self):
        self._rules: List[AfterSaleRule] = []
        self._initialized = False

    @classmethod
    def get_instance(cls) -> "AfterSaleRuleService":
        """获取单例"""
        if cls._instance is None:
            cls._instance = cls()
            cls._instance.initialize()
        return cls._instance

    def initialize(self, rules: List[AfterSaleRule] = None) -> None:
        """初始化服务"""
        if self._initialized:
            return

        self._rules = rules if rules is not None else get_after_sale_rules()
        # 按优先级排序
        self._rules.sort(key=lambda r: r.priority, reverse=True)
        self._initialized = True

    def evaluate_eligibility(
        self,
        order: Order,
        after_sale_type: AfterSaleType,
        sku_id: Optional[str] = None,
        reason: str = "",
        is_vip: bool = False,
    ) -> AfterSaleEvaluationResult:
        """
        评估售后资格

        Args:
            order: 订单
            after_sale_type: 售后类型
            sku_id: 商品SKU（可选，订单内某个商品）
            reason: 售后原因
            is_vip: 是否VIP用户

        Returns:
            评估结果
        """
        if not self._initialized:
            self.initialize()

        reasons = []
        warnings = []
        matched_rule = None
        eligible = False
        risk_level = "low"
        auto_approve = False
        estimated_amount = 0.0

        # 1. 基础检查
        if order.status == OrderStatus.CANCELLED:
            return AfterSaleEvaluationResult(
                eligible=False,
                after_sale_type=after_sale_type,
                reasons=["订单已取消，无法申请售后"],
                risk_level="high",
            )

        if order.status == OrderStatus.PENDING_PAYMENT:
            if after_sale_type == AfterSaleType.REFUND:
                return AfterSaleEvaluationResult(
                    eligible=False,
                    after_sale_type=after_sale_type,
                    reasons=["订单未支付，请先取消订单"],
                    risk_level="low",
                )
            return AfterSaleEvaluationResult(
                eligible=False,
                after_sale_type=after_sale_type,
                reasons=["订单未支付，无法申请该售后类型"],
                risk_level="low",
            )

        # 2. 计算预估金额
        estimated_amount = self._calculate_amount(order, sku_id)

        # 3. 匹配规则
        product_category = None
        product_brand = None
        if sku_id:
            # 从订单商品中获取分类和品牌
            for item in order.items:
                if item.sku_id == sku_id:
                    # 简化：从商品名推断（实际应该从product表查）
                    product_brand = item.product_name.split()[0] if item.product_name else ""
                    break

        days_since_delivery = order.days_since_delivery or 0

        # 特殊：未发货退款
        if after_sale_type == AfterSaleType.REFUND and order.status == OrderStatus.PAID:
            # 匹配"未发货仅退款"规则
            for rule in self._rules:
                if rule.after_sale_type == AfterSaleType.REFUND and rule.auto_approve:
                    matched_rule = rule
                    eligible = True
                    auto_approve = True
                    reasons.append("订单未发货，支持全额退款（自动审核）")
                    risk_level = rule.risk_level
                    break

        if not matched_rule:
            # 遍历规则找匹配
            for rule in self._rules:
                if rule.after_sale_type != after_sale_type:
                    continue

                # VIP规则单独处理
                if "VIP" in rule.name and not is_vip:
                    continue

                # 分类匹配
                if rule.applicable_categories:
                    if product_category and product_category not in rule.applicable_categories:
                        continue

                # 品牌匹配
                if rule.applicable_brands:
                    if product_brand and product_brand not in rule.applicable_brands:
                        continue

                # 金额限制
                if rule.min_amount and estimated_amount < rule.min_amount:
                    continue
                if rule.max_amount and estimated_amount > rule.max_amount:
                    continue

                # 时间限制（签收后天数）
                if order.status in (OrderStatus.DELIVERED, OrderStatus.COMPLETED):
                    if rule.max_days_after_delivery == 0:
                        warnings.append("该类商品不支持无理由退货")
                        continue
                    if days_since_delivery > rule.max_days_after_delivery:
                        warnings.append(f"已超过{rule.max_days_after_delivery}天期限")
                        continue

                # 原因检查
                if rule.requires_reason and not reason:
                    warnings.append("需要填写售后原因")

                # 找到匹配的规则
                matched_rule = rule
                eligible = True
                auto_approve = rule.auto_approve
                risk_level = rule.risk_level
                reasons.append(f"符合规则：{rule.name}")
                reasons.append(rule.description)

                if rule.requires_evidence:
                    warnings.append("需要上传商品问题凭证")

                break

        if not matched_rule:
            eligible = False
            reasons.append("未找到匹配的售后规则")
            if not reasons:
                reasons.append("当前订单状态不支持该类型的售后申请")

        # 大额订单风险
        if estimated_amount >= 5000:
            risk_level = "high"
            warnings.append("大额订单需人工审核")
            auto_approve = False

        return AfterSaleEvaluationResult(
            eligible=eligible,
            after_sale_type=after_sale_type,
            matched_rule=matched_rule,
            reasons=reasons,
            warnings=warnings,
            risk_level=risk_level,
            auto_approve=auto_approve,
            estimated_amount=round(estimated_amount, 2),
        )

    @staticmethod
    def _calculate_amount(order: Order, sku_id: Optional[str] = None) -> float:
        """计算售后金额"""
        if sku_id:
            for item in order.items:
                if item.sku_id == sku_id:
                    return item.subtotal
            return 0.0
        # 全单退款
        return order.actual_payment

    def get_rules_by_type(self, after_sale_type: AfterSaleType) -> List[AfterSaleRule]:
        """按类型获取规则"""
        if not self._initialized:
            self.initialize()
        return [r for r in self._rules if r.after_sale_type == after_sale_type]

    def get_rule_by_id(self, rule_id: str) -> Optional[AfterSaleRule]:
        """根据ID获取规则"""
        if not self._initialized:
            self.initialize()
        for rule in self._rules:
            if rule.rule_id == rule_id:
                return rule
        return None

    def get_all_rules(self) -> List[AfterSaleRule]:
        """获取所有规则"""
        if not self._initialized:
            self.initialize()
        return self._rules

    def determine_after_sale_type(self, order: Order, user_intent: str) -> AfterSaleType:
        """
        根据用户意图判断售后类型

        Args:
            order: 订单
            user_intent: 用户意图描述

        Returns:
            建议的售后类型
        """
        intent_lower = user_intent.lower()

        # 关键词匹配
        if any(kw in intent_lower for kw in ["退货", "退了", "退回", "不要了", "退回去"]):
            return AfterSaleType.RETURN
        if any(kw in intent_lower for kw in ["换货", "换一个", "换款", "调换"]):
            return AfterSaleType.EXCHANGE
        if any(kw in intent_lower for kw in ["退款", "退钱", "仅退款", "不要发货"]):
            if order.status == OrderStatus.PAID and not order.shipping_time:
                return AfterSaleType.REFUND
            return AfterSaleType.RETURN  # 已发货建议退货退款
        if any(kw in intent_lower for kw in ["维修", "修理", "保修", "坏了"]):
            return AfterSaleType.REPAIR

        # 默认根据订单状态判断
        if order.status == OrderStatus.PAID and not order.shipping_time:
            return AfterSaleType.REFUND
        if order.status in (OrderStatus.DELIVERED, OrderStatus.COMPLETED):
            return AfterSaleType.RETURN

        return AfterSaleType.RETURN

    @property
    def rule_count(self) -> int:
        if not self._initialized:
            self.initialize()
        return len(self._rules)
