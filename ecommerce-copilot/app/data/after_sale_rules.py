"""
售后规则数据
"""
from __future__ import annotations

from typing import List
from ..models.after_sale import AfterSaleRule, AfterSaleType


def get_after_sale_rules() -> List[AfterSaleRule]:
    """获取所有售后规则"""
    rules = [
        # 七天无理由退货
        AfterSaleRule(
            rule_id="RULE_001",
            name="七天无理由退货",
            after_sale_type=AfterSaleType.RETURN,
            applicable_categories=[],  # 全品类
            applicable_brands=[],
            max_days_after_delivery=7,
            min_amount=None,
            max_amount=None,
            requires_reason=False,
            requires_evidence=False,
            allowed_reasons=["不喜欢", "尺码不合适", "效果不好", "其他"],
            auto_approve=False,
            priority=10,
            description="签收后7天内，商品完好不影响二次销售，可申请无理由退货。",
            risk_level="low",
        ),
        # 30天质量问题退货
        AfterSaleRule(
            rule_id="RULE_002",
            name="30天质量问题退货",
            after_sale_type=AfterSaleType.RETURN,
            applicable_categories=[],
            applicable_brands=[],
            max_days_after_delivery=30,
            requires_reason=True,
            requires_evidence=True,
            allowed_reasons=["质量问题", "商品破损", "功能故障", "描述不符"],
            auto_approve=False,
            priority=20,
            description="签收后30天内，出现质量问题可申请退货退款，需提供凭证。",
            risk_level="medium",
        ),
        # 电子产品15天换货
        AfterSaleRule(
            rule_id="RULE_003",
            name="电子产品15天换货",
            after_sale_type=AfterSaleType.EXCHANGE,
            applicable_categories=["electronics"],
            applicable_brands=[],
            max_days_after_delivery=15,
            requires_reason=True,
            requires_evidence=True,
            allowed_reasons=["质量问题", "功能故障", "外观瑕疵"],
            auto_approve=False,
            priority=15,
            description="电子产品签收后15天内出现质量问题，可申请换货。",
            risk_level="medium",
        ),
        # 未发货仅退款
        AfterSaleRule(
            rule_id="RULE_004",
            name="未发货仅退款",
            after_sale_type=AfterSaleType.REFUND,
            applicable_categories=[],
            applicable_brands=[],
            max_days_after_delivery=999,  # 未发货无时间限制
            min_amount=None,
            max_amount=None,
            requires_reason=False,
            requires_evidence=False,
            allowed_reasons=["不想要了", "拍错了", "价格太贵", "其他"],
            auto_approve=True,
            priority=30,
            description="订单未发货时，可申请全额退款，自动通过。",
            risk_level="low",
        ),
        # 生鲜食品不支持无理由退货
        AfterSaleRule(
            rule_id="RULE_005",
            name="生鲜食品不支持无理由退货",
            after_sale_type=AfterSaleType.RETURN,
            applicable_categories=["food"],
            applicable_brands=[],
            max_days_after_delivery=3,
            requires_reason=True,
            requires_evidence=True,
            allowed_reasons=["质量问题", "变质", "破损漏液"],
            auto_approve=False,
            priority=25,
            description="生鲜食品不支持七天无理由退货，如有质量问题需在签收后3天内申请。",
            risk_level="high",
        ),
        # 定制商品不支持退货
        AfterSaleRule(
            rule_id="RULE_006",
            name="定制商品不支持退货",
            after_sale_type=AfterSaleType.RETURN,
            applicable_categories=["clothing", "furniture"],
            applicable_brands=[],
            max_days_after_delivery=0,  # 不支持
            requires_reason=True,
            requires_evidence=True,
            allowed_reasons=["质量问题"],
            auto_approve=False,
            priority=5,
            description="定制类商品不支持无理由退货，如有质量问题请联系客服。",
            risk_level="high",
        ),
        # 大家电上门取件
        AfterSaleRule(
            rule_id="RULE_007",
            name="大家电售后上门服务",
            after_sale_type=AfterSaleType.REPAIR,
            applicable_categories=["home_appliances"],
            applicable_brands=["美的", "海尔", "格力", "西门子", "松下"],
            max_days_after_delivery=365,
            requires_reason=True,
            requires_evidence=True,
            allowed_reasons=["质量问题", "功能故障", "安装问题"],
            auto_approve=False,
            priority=15,
            description="大家电产品享受全国联保，保修期内可申请上门维修服务。",
            risk_level="medium",
        ),
        # VIP用户极速售后
        AfterSaleRule(
            rule_id="RULE_008",
            name="VIP用户极速售后",
            after_sale_type=AfterSaleType.RETURN,
            applicable_categories=[],
            applicable_brands=[],
            max_days_after_delivery=15,
            requires_reason=False,
            requires_evidence=False,
            allowed_reasons=[],
            auto_approve=True,
            priority=100,
            description="VIP用户专享：15天内极速退货，自动审核通过，上门取件。",
            risk_level="low",
        ),
        # 大额订单需人工审核
        AfterSaleRule(
            rule_id="RULE_009",
            name="大额订单人工审核",
            after_sale_type=AfterSaleType.RETURN,
            applicable_categories=[],
            applicable_brands=[],
            max_days_after_delivery=30,
            min_amount=5000,
            requires_reason=True,
            requires_evidence=True,
            allowed_reasons=["质量问题", "商品破损"],
            auto_approve=False,
            priority=50,
            description="单笔退款金额超过5000元的订单，需人工审核处理。",
            risk_level="high",
        ),
        # 图书类7天无理由
        AfterSaleRule(
            rule_id="RULE_010",
            name="图书类7天无理由",
            after_sale_type=AfterSaleType.RETURN,
            applicable_categories=["books"],
            applicable_brands=[],
            max_days_after_delivery=7,
            requires_reason=False,
            requires_evidence=False,
            allowed_reasons=["不喜欢", "内容不符", "其他"],
            auto_approve=True,
            priority=10,
            description="图书类商品签收后7天内，未拆封可申请无理由退货。",
            risk_level="low",
        ),
    ]

    return rules
