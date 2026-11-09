"""
模拟LLM - 基于规则和模板生成响应
无需API Key即可演示完整流程
"""
from __future__ import annotations

import re
import random
from typing import Dict, Any, List, Optional, Tuple

from .models.conversation import IntentType, ExtractedSlots


class MockLLM:
    """模拟LLM，基于规则和模板生成响应"""

    def __init__(self):
        self.intent_keywords = self._build_intent_keywords()

    @staticmethod
    def _build_intent_keywords() -> Dict[IntentType, List[str]]:
        """构建意图关键词映射"""
        return {
            IntentType.PRODUCT_SHOPPING: [
                "推荐", "买", "选购", "找", "搜索", "有什么", "哪款", "哪个好",
                "性价比", "便宜", "优惠", "商品", "耳机", "手机", "电脑", "衣服",
                "多少钱", "价格", "品牌", "怎么样", "好不好",
            ],
            IntentType.ORDER_QUERY: [
                "订单", "我的订单", "查订单", "订单号", "物流", "快递", "到哪了",
                "发货了吗", "什么时候到", "配送", "收货", "签收", "包裹",
            ],
            IntentType.AFTER_SALE: [
                "退货", "退款", "换货", "售后", "退了", "不要了", "退钱",
                "质量问题", "坏了", "破损", "不合适", "尺码不对", "申请售后",
                "七天无理由", "保修", "维修", "退回",
            ],
            IntentType.POLICY_QA: [
                "政策", "规则", "怎么退", "运费", "发票", "会员", "积分",
                "隐私", "安全", "能退吗", "可以退吗", "怎么算", "什么是",
                "多久", "多少天", "怎么算",
            ],
            IntentType.HUMAN_HANDOFF: [
                "人工", "客服", "转人工", "找你们经理", "投诉", "举报",
                "解决不了", "没用", "我要真人", "不是机器人",
            ],
            IntentType.CHITCHAT: [
                "你好", "在吗", "嗨", "哈喽", "你是谁", "你叫什么", "谢谢",
                "再见", "拜拜", "早上好", "晚上好", "天气", "吃饭了吗",
            ],
        }

    def classify_intent(self, message: str) -> Tuple[IntentType, float, List[Dict[str, Any]]]:
        """
        意图分类（规则版）

        Returns:
            (主意图, 置信度, 意图排序列表)
        """
        message_lower = message.lower().strip()

        if not message_lower:
            return IntentType.UNKNOWN, 0.0, []

        scores = {}
        for intent, keywords in self.intent_keywords.items():
            score = 0.0
            matched_kw = []
            for kw in keywords:
                if kw in message_lower:
                    # 关键词长度越长，权重越高
                    weight = min(len(kw) / 10.0, 1.0) + 0.1
                    score += weight
                    matched_kw.append(kw)

            # 归一化（简单处理）
            if matched_kw:
                score = min(score / 3.0, 1.0)

            scores[intent] = {
                "score": score,
                "matched_keywords": matched_kw,
            }

        # 排序
        ranking = sorted(
            scores.items(),
            key=lambda x: x[1]["score"],
            reverse=True,
        )

        top_intent, top_info = ranking[0]
        top_score = top_info["score"]

        # 处理特殊情况
        if top_score < 0.08:
            # 分数太低，判断为未知或闲聊
            # 如果是短句，可能是闲聊
            if len(message_lower) < 6:
                top_intent = IntentType.CHITCHAT
                top_score = 0.5
            else:
                top_intent = IntentType.UNKNOWN
                top_score = 0.3

        # 构造ranking列表
        ranking_list = [
            {"intent": intent.value, "score": round(info["score"], 4),
             "matched_keywords": info["matched_keywords"]}
            for intent, info in ranking
        ]

        return top_intent, round(top_score, 4), ranking_list

    def extract_slots(self, message: str, intent: IntentType) -> ExtractedSlots:
        """
        槽位提取（规则版）
        """
        slots = ExtractedSlots(raw_query=message)
        confidence = {}

        # 订单号提取：ORD开头 + 数字
        order_match = re.search(r'ORD[0-9]{8,}', message.upper())
        if order_match:
            slots.order_id = order_match.group()
            confidence["order_id"] = 0.95

        # 价格范围提取
        price_match = re.search(r'(\d+(?:\.\d+)?)\s*[元块]?\s*[以到~-]\s*(\d+(?:\.\d+)?)\s*[元块]?', message)
        if price_match:
            slots.min_price = float(price_match.group(1))
            slots.max_price = float(price_match.group(2))
            confidence["min_price"] = 0.8
            confidence["max_price"] = 0.8

        # 最低价提取
        min_price_match = re.search(r'(?:最低|不少于|大于|以上)\s*(\d+(?:\.\d+)?)\s*[元块]?', message)
        if min_price_match and not slots.min_price:
            slots.min_price = float(min_price_match.group(1))
            confidence["min_price"] = 0.7

        # 最高价提取
        max_price_match = re.search(r'(?:最高|不超过|少于|低于|以内|以下)\s*(\d+(?:\.\d+)?)\s*[元块]?', message)
        if max_price_match and not slots.max_price:
            slots.max_price = float(max_price_match.group(1))
            confidence["max_price"] = 0.7

        # 品牌提取（常见品牌）
        brands = ["苹果", "华为", "小米", "耐克", "阿迪达斯", "索尼", "三星", "OPPO", "vivo",
                  "美的", "海尔", "格力", "联想", "戴尔", "惠普", "优衣库", "李宁", "安踏"]
        for brand in brands:
            if brand in message:
                slots.brand = brand
                confidence["brand"] = 0.85
                break

        # 商品名称/关键词提取
        product_keywords = ["耳机", "手机", "电脑", "笔记本", "平板", "手表", "衣服", "鞋子",
                           "电视", "空调", "冰箱", "洗衣机", "书", "咖啡", "牛奶", "口红",
                           "面膜", "篮球", "瑜伽垫", "积木", "沙发", "椅子", "笔", "书包"]
        for kw in product_keywords:
            if kw in message:
                slots.product_name = kw
                confidence["product_name"] = 0.8
                break

        # 分类推断
        categories_map = {
            "电子产品": "electronics", "数码": "electronics",
            "服装": "clothing", "衣服": "clothing",
            "家电": "home_appliances", "电器": "home_appliances",
            "图书": "books", "书": "books",
            "食品": "food", "零食": "food",
            "美妆": "beauty", "化妆品": "beauty",
            "运动": "sports", "健身": "sports",
            "玩具": "toys",
            "家具": "furniture",
            "文具": "stationery",
        }
        for kw, cat in categories_map.items():
            if kw in message:
                slots.category = cat
                confidence["category"] = 0.75
                break

        # 售后类型提取
        if any(kw in message for kw in ["退货", "退了", "退回", "不要了"]):
            slots.after_sale_type = "return"
            confidence["after_sale_type"] = 0.85
        elif any(kw in message for kw in ["换货", "换一个", "调换"]):
            slots.after_sale_type = "exchange"
            confidence["after_sale_type"] = 0.85
        elif any(kw in message for kw in ["退款", "退钱", "仅退款"]):
            slots.after_sale_type = "refund"
            confidence["after_sale_type"] = 0.8
        elif any(kw in message for kw in ["维修", "保修", "修理"]):
            slots.after_sale_type = "repair"
            confidence["after_sale_type"] = 0.8

        # 退货原因提取
        reasons = ["质量问题", "商品破损", "功能故障", "不喜欢", "尺码不合适",
                  "效果不好", "描述不符", "拍错了", "不想要了"]
        for reason in reasons:
            if reason in message:
                slots.return_reason = reason
                confidence["return_reason"] = 0.9
                break

        # 政策主题提取
        policy_topics = {
            "退货": "after_sale", "售后": "after_sale",
            "物流": "delivery", "配送": "delivery", "快递": "delivery",
            "支付": "payment", "退款": "payment",
            "会员": "membership", "积分": "membership",
            "发票": "invoice",
            "隐私": "privacy", "个人信息": "privacy",
        }
        for kw, topic in policy_topics.items():
            if kw in message:
                slots.policy_topic = topic
                confidence["policy_topic"] = 0.7
                break

        # 计算缺失槽位
        if intent == IntentType.PRODUCT_SHOPPING:
            if not slots.product_name and not slots.category and not slots.brand:
                slots.missing_slots.append("product_name")
        elif intent == IntentType.ORDER_QUERY:
            # 订单查询可以不需要订单号（查列表）
            pass
        elif intent == IntentType.AFTER_SALE:
            if not slots.order_id:
                slots.missing_slots.append("order_id")

        slots.confidence = confidence
        return slots

    def generate_product_response(self, search_result: Dict[str, Any], query: str) -> str:
        """生成商品导购响应"""
        if not search_result.get("success") or not search_result.get("products"):
            return f"抱歉，没有找到与「{query}」相关的商品。您可以尝试其他关键词，或者告诉我您的具体需求，我来帮您推荐。"

        products = search_result["products"]
        total = search_result["total"]

        parts = [f"为您找到 {total} 件相关商品，以下是为您推荐的：\n"]

        for i, p in enumerate(products[:5], 1):
            price_info = f"¥{p['price']}"
            if p.get("original_price"):
                discount = f"{int(p['discount_rate'] * 10)}折" if p.get("discount_rate") else ""
                price_info += f" (原价¥{p['original_price']}, {discount})"

            stock_info = ""
            if p["stock"] > 0:
                stock_info = f" 库存:{p['stock']}"
            else:
                stock_info = " 暂时缺货"

            parts.append(
                f"{i}. 【{p['name']}】\n"
                f"   品牌：{p['brand']} | 评分：{p['rating']}分 | 销量：{p['sales_volume']}\n"
                f"   价格：{price_info}{stock_info}\n"
                f"   标签：{'、'.join(p['tags'][:3])}\n"
            )

        if len(products) > 5 or search_result.get("has_more"):
            parts.append(f"\n还有更多商品，您可以告诉我更多偏好（如价格区间、品牌等）来缩小范围哦~")

        parts.append("\n请问您对哪款商品感兴趣？或者需要我帮您对比几款商品吗？")

        return "".join(parts)

    def generate_order_response(self, order_result: Dict[str, Any], query: str) -> str:
        """生成订单查询响应"""
        if not order_result.get("success"):
            return f"查询失败：{order_result.get('error', '未知错误')}"

        orders = order_result.get("orders", [])

        if not orders:
            return "您目前没有相关订单。您可以前往商城选购心仪的商品哦~"

        if order_result.get("is_single"):
            order = orders[0]
            parts = [f"订单 {order['order_id']} 的详情如下：\n"]
            parts.append(f"状态：{order['status_text']}\n")
            parts.append(f"实付金额：¥{order['actual_payment']}\n")

            parts.append("\n商品清单：\n")
            for item in order["items"]:
                parts.append(
                    f"  - {item['product_name']} x{item['quantity']}  ¥{item['subtotal']}\n"
                )

            if order.get("logistics"):
                logistics = order["logistics"]
                parts.append(f"\n物流信息：\n")
                parts.append(f"  物流公司：{logistics['carrier']}\n")
                parts.append(f"  物流单号：{logistics['tracking_number']}\n")
                parts.append(f"  当前状态：{logistics['status_text']} - {logistics['current_location']}\n")

            parts.append(f"\n下单时间：{order['create_time'][:19]}\n")

            if order.get("can_return"):
                parts.append("温馨提示：该订单支持退换货，如有需要请告诉我哦~")

            return "".join(parts)
        else:
            parts = [f"您共有 {order_result['total']} 个相关订单：\n"]
            for i, order in enumerate(orders[:10], 1):
                items_preview = "、".join(
                    item["product_name"][:10] for item in order["items"][:2]
                )
                parts.append(
                    f"{i}. {order['order_id']} | {order['status_text']} | "
                    f"¥{order['actual_payment']} | {items_preview}...\n"
                )

            if order_result.get("has_more"):
                parts.append("\n还有更多订单，您可以告诉我订单号来查询具体详情~")

            return "".join(parts)

    def generate_logistics_response(self, logistics_result: Dict[str, Any]) -> str:
        """生成物流查询响应"""
        if not logistics_result.get("success"):
            return f"查询失败：{logistics_result.get('error', '未知错误')}"

        logistics = logistics_result["logistics"]
        parts = [f"物流信息如下：\n"]
        parts.append(f"物流公司：{logistics['carrier']}\n")
        parts.append(f"物流单号：{logistics['tracking_number']}\n")
        parts.append(f"当前状态：{logistics['status_text']}\n")
        parts.append(f"当前位置：{logistics['current_location']}\n")

        if logistics.get("estimated_delivery"):
            parts.append(f"预计送达：{logistics['estimated_delivery'][:10]}\n")

        if logistics.get("updates"):
            parts.append("\n物流轨迹：\n")
            for update in logistics["updates"][-5:]:  # 最新5条
                parts.append(f"  [{update['time'][:19]}] {update['location']} - {update['status']}\n")

        return "".join(parts)

    def generate_after_sale_response(self, result: Dict[str, Any], step: str = "evaluate") -> str:
        """生成售后响应"""
        if not result.get("success"):
            return f"操作失败：{result.get('error', '未知错误')}"

        if step == "evaluate":
            if result.get("eligible"):
                parts = [f"✅ 您的订单符合售后条件\n\n"]
                parts.append(f"售后类型：{result.get('after_sale_type_text', '')}\n")
                parts.append(f"预估金额：¥{result.get('estimated_amount', 0)}\n")
                parts.append(f"风险等级：{_get_risk_text(result.get('risk_level', 'low'))}\n")

                if result.get("auto_approve"):
                    parts.append(f"审核方式：自动审核通过\n")
                else:
                    parts.append(f"审核方式：人工审核\n")

                if result.get("reasons"):
                    parts.append(f"\n说明：\n")
                    for reason in result["reasons"]:
                        parts.append(f"  - {reason}\n")

                if result.get("warnings"):
                    parts.append(f"\n注意事项：\n")
                    for warning in result["warnings"]:
                        parts.append(f"  ⚠️ {warning}\n")

                parts.append(f"\n请问您确认要申请{result.get('after_sale_type_text', '售后')}吗？")
                return "".join(parts)
            else:
                parts = ["❌ 很抱歉，您的订单暂时不符合售后条件\n\n"]
                if result.get("reasons"):
                    for reason in result["reasons"]:
                        parts.append(f"  - {reason}\n")
                parts.append("\n您可以联系人工客服了解更多详情，或者告诉我其他需求~")
                return "".join(parts)

        elif step == "draft":
            app = result.get("application", {})
            parts = [f"📝 售后草稿已创建\n\n"]
            parts.append(f"申请编号：{app.get('application_id')}\n")
            parts.append(f"售后类型：{_get_type_text(app.get('after_sale_type', ''))}\n")
            parts.append(f"申请金额：¥{app.get('amount', 0)}\n")
            if app.get("product_name"):
                parts.append(f"商品：{app.get('product_name')}\n")
            if app.get("reason"):
                parts.append(f"原因：{app.get('reason')}\n")

            if result.get("is_idempotent"):
                parts.append(f"\nℹ️ {result.get('message', '')}\n")

            parts.append(f"\n请确认以上信息是否正确？确认后我将为您提交审核。")
            return "".join(parts)

        elif step == "confirm":
            parts = []
            status = result.get("status", "")
            status_text = result.get("status_text", "")

            if status == "approved":
                parts.append(f"✅ 售后申请已通过\n\n")
                parts.append(f"申请编号：{result.get('application_id')}\n")
                parts.append(f"退款金额：¥{result.get('approved_amount', 0)}\n")
                parts.append(f"预计到账时间：1-3个工作日\n")
                parts.append(f"\n退款将原路退回您的支付账户，请留意查收~")
            elif status == "pending_review":
                parts.append(f"⏳ 售后申请已提交\n\n")
                parts.append(f"申请编号：{result.get('application_id')}\n")
                parts.append(f"当前状态：{status_text}\n")
                parts.append(f"预计处理时间：{result.get('estimated_processing_time', '24小时内')}\n")
                parts.append(f"\n审核结果将通过消息通知您，请耐心等待~")
            elif status == "need_human":
                parts.append(f"👤 已为您转接人工客服\n\n")
                parts.append(f"原因：{result.get('handoff_reason', '')}\n")
                parts.append(f"申请编号：{result.get('application_id')}\n")
                parts.append(f"\n人工客服会在工作时间内尽快与您联系，请稍候~")
            elif status == "rejected":
                parts.append(f"❌ 售后申请未通过\n\n")
                if result.get("reasons"):
                    for reason in result["reasons"]:
                        parts.append(f"  - {reason}\n")
                parts.append(f"\n您可以联系人工客服申诉，或者了解更多售后政策~")
            elif status == "cancelled":
                parts.append(f"已取消售后申请。\n\n如有其他问题，请随时告诉我~")

            return "".join(parts)

        return "售后操作完成。"

    def generate_policy_response(self, rag_result: Dict[str, Any], query: str) -> str:
        """生成政策问答响应"""
        if not rag_result.get("success") or not rag_result.get("has_answer"):
            return f"抱歉，没有找到与「{query}」相关的政策信息。您可以尝试换个问法，或者联系人工客服获取帮助。"

        parts = [rag_result.get("answer", "") + "\n"]

        # 添加引用来源
        sources = rag_result.get("sources", [])
        if sources:
            parts.append("\n📚 参考来源：\n")
            for i, src in enumerate(sources[:3], 1):
                parts.append(f"  {i}. 《{src['doc_title']}》- {src['section_path']}\n")

        # 相关问题
        related = rag_result.get("related_questions", [])
        if related:
            parts.append("\n💡 您可能还想了解：\n")
            for q in related:
                parts.append(f"  • {q}\n")

        parts.append(f"\n以上回答仅供参考，具体以实际政策为准。如有疑问，建议联系人工客服确认。")

        return "".join(parts)

    def generate_chitchat_response(self, message: str) -> str:
        """生成闲聊响应"""
        message_lower = message.lower()

        greetings = ["你好", "您好", "嗨", "哈喽", "在吗", "hi", "hello"]
        if any(g in message_lower for g in greetings):
            return "你好呀！我是您的电商智能助手小商~ 我可以帮您：\n\n" \
                   "🛍️  商品导购和推荐\n" \
                   "📦  查询订单和物流\n" \
                   "🔄  办理退换货售后\n" \
                   "📋  解答政策相关问题\n\n" \
                   "请问有什么可以帮您的吗？"

        thanks = ["谢谢", "感谢", "多谢", "thanks", "thank you"]
        if any(t in message_lower for t in thanks):
            return "不客气~ 很高兴能帮到您！如果还有其他问题，随时来找我哦~ 😊"

        byes = ["再见", "拜拜", "bye", "88", "晚安"]
        if any(b in message_lower for b in byes):
            return "再见！祝您购物愉快，生活顺心~ 👋"

        who_are_you = ["你是谁", "你叫什么", "你是机器人吗", "你是真人吗"]
        if any(q in message_lower for q in who_are_you):
            return "我是小商，您的专属电商智能助手！我基于AI技术打造，可以帮您处理购物相关的各种问题。" \
                   "如果我解决不了您的问题，还可以帮您转接人工客服哦~"

        # 默认回复
        default_responses = [
            "嗯嗯，我在呢~ 请问有什么可以帮您的？",
            "好的，我明白了。您还有其他购物相关的问题吗？",
            "收到~ 有什么我能帮您的，尽管说哦！",
            "好的好的~ 需要什么帮助随时告诉我。",
        ]
        return random.choice(default_responses)

    def generate_handoff_response(self, handoff_package: Dict[str, Any], reason: str) -> str:
        """生成人工接管响应"""
        parts = [
            "👤 好的，已为您转接人工客服\n\n",
            f"转接原因：{reason}\n",
            "\n正在为您分配专属客服，请稍候...\n",
            "\n📋 已为您准备好相关信息：\n",
        ]

        if handoff_package.get("user_id"):
            parts.append(f"  • 用户ID：{handoff_package['user_id']}\n")
        if handoff_package.get("order_id"):
            parts.append(f"  • 订单号：{handoff_package['order_id']}\n")
        if handoff_package.get("after_sale_type"):
            parts.append(f"  • 售后类型：{_get_type_text(handoff_package['after_sale_type'])}\n")
        if handoff_package.get("amount"):
            parts.append(f"  • 涉及金额：¥{handoff_package['amount']}\n")
        if handoff_package.get("risk_tags"):
            parts.append(f"  • 风险标签：{', '.join(handoff_package['risk_tags'])}\n")

        parts.append("\n人工客服会尽快与您联系，请您耐心等待~")
        return "".join(parts)

    def generate_unknown_response(self, message: str) -> str:
        """生成未知意图响应"""
        return (
            "抱歉，我不太明白您的意思~ 🤔\n\n"
            "我可以帮您处理以下事情：\n"
            "🛍️  商品搜索和推荐\n"
            "📦  查询订单和物流\n"
            "🔄  申请退换货售后\n"
            "📋  解答政策相关问题\n\n"
            "您可以试试这样问我：\n"
            "• \"推荐一款无线耳机\"\n"
            "• \"我的订单到哪了\"\n"
            "• \"我要退货\"\n"
            "• \"七天无理由是什么政策？\""
        )


def _get_risk_text(level: str) -> str:
    """风险等级中文"""
    return {"low": "低风险", "medium": "中风险", "high": "高风险"}.get(level, level)


def _get_type_text(after_sale_type: str) -> str:
    """售后类型中文"""
    type_map = {
        "return": "退货退款",
        "exchange": "换货",
        "refund": "仅退款",
        "repair": "维修",
    }
    return type_map.get(after_sale_type, after_sale_type)


# 全局单例
_mock_llm_instance: Optional[MockLLM] = None


def get_mock_llm() -> MockLLM:
    """获取MockLLM单例"""
    global _mock_llm_instance
    if _mock_llm_instance is None:
        _mock_llm_instance = MockLLM()
    return _mock_llm_instance
