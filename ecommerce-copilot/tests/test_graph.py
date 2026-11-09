"""
LangGraph 状态机单元测试
"""
import pytest
from app.graph import run_conversation, build_graph, get_graph
from app.models.conversation import IntentType, ConversationState
from app.mock_llm import get_mock_llm


class TestMockLLM:
    """MockLLM测试"""

    def test_classify_intent_shopping(self):
        """测试商品导购意图识别"""
        llm = get_mock_llm()
        intent, confidence, ranking = llm.classify_intent("推荐一款无线耳机")
        assert intent == IntentType.PRODUCT_SHOPPING
        assert confidence > 0

    def test_classify_intent_order(self):
        """测试订单查询意图识别"""
        llm = get_mock_llm()
        intent, confidence, _ = llm.classify_intent("我的订单到哪了")
        assert intent == IntentType.ORDER_QUERY

    def test_classify_intent_after_sale(self):
        """测试售后意图识别"""
        llm = get_mock_llm()
        intent, confidence, _ = llm.classify_intent("我要退货")
        assert intent == IntentType.AFTER_SALE

    def test_classify_intent_policy(self):
        """测试政策QA意图识别"""
        llm = get_mock_llm()
        intent, confidence, _ = llm.classify_intent("七天无理由退货政策")
        # 可能识别为POLICY_QA或AFTER_SALE
        assert intent in (IntentType.POLICY_QA, IntentType.AFTER_SALE)

    def test_classify_intent_chitchat(self):
        """测试闲聊意图识别"""
        llm = get_mock_llm()
        intent, confidence, _ = llm.classify_intent("你好")
        assert intent == IntentType.CHITCHAT

    def test_classify_intent_human_handoff(self):
        """测试人工接管意图识别"""
        llm = get_mock_llm()
        intent, confidence, _ = llm.classify_intent("转人工")
        assert intent == IntentType.HUMAN_HANDOFF

    def test_extract_slots_order_id(self):
        """测试提取订单号槽位"""
        llm = get_mock_llm()
        slots = llm.extract_slots("查一下订单ORD202401001", IntentType.ORDER_QUERY)
        assert slots.order_id == "ORD202401001"

    def test_extract_slots_price_range(self):
        """测试提取价格区间槽位"""
        llm = get_mock_llm()
        slots = llm.extract_slots("100到500元的耳机", IntentType.PRODUCT_SHOPPING)
        assert slots.min_price == 100
        assert slots.max_price == 500

    def test_extract_slots_brand(self):
        """测试提取品牌槽位"""
        llm = get_mock_llm()
        slots = llm.extract_slots("华为手机", IntentType.PRODUCT_SHOPPING)
        assert slots.brand == "华为"


class TestGraphBuild:
    """状态图构建测试"""

    def test_build_graph(self):
        """测试构建状态图"""
        graph = build_graph()
        assert graph is not None

    def test_get_graph_singleton(self):
        """测试获取编译后的图"""
        g1 = get_graph()
        g2 = get_graph()
        assert g1 is g2


class TestConversationFlow:
    """对话流程测试"""

    def test_product_shopping_flow(self):
        """测试商品导购流程"""
        state = run_conversation(
            user_id="user_001",
            message="推荐一款无线耳机",
            conversation_id="test_conv_1",
        )
        assert state.intent == IntentType.PRODUCT_SHOPPING
        assert "search_products" in state.tools_used
        assert state.response_text != ""
        assert state.trace_id != ""
        assert state.processing_time_ms > 0

    def test_order_query_flow(self):
        """测试订单查询流程"""
        state = run_conversation(
            user_id="user_001",
            message="我的订单",
            conversation_id="test_conv_2",
        )
        assert state.intent == IntentType.ORDER_QUERY
        assert state.response_text != ""

    def test_chitchat_flow(self):
        """测试闲聊流程"""
        state = run_conversation(
            user_id="user_001",
            message="你好",
            conversation_id="test_conv_3",
        )
        assert state.intent == IntentType.CHITCHAT
        assert state.response_text != ""
        assert "chitchat" in state.tools_used

    def test_human_handoff_flow(self):
        """测试人工接管流程"""
        state = run_conversation(
            user_id="user_001",
            message="转人工",
            conversation_id="test_conv_4",
        )
        assert state.intent == IntentType.HUMAN_HANDOFF
        assert state.needs_human is True
        assert state.handoff_package != {}

    def test_policy_qa_flow(self):
        """测试政策QA流程"""
        state = run_conversation(
            user_id="user_001",
            message="七天无理由退货政策是什么",
            conversation_id="test_conv_5",
        )
        # 可能是POLICY_QA或AFTER_SALE
        assert state.intent in (IntentType.POLICY_QA, IntentType.AFTER_SALE)
        assert state.response_text != ""

    def test_after_sale_flow_no_order_id(self):
        """测试售后流程（缺少订单号）"""
        state = run_conversation(
            user_id="user_001",
            message="我要退货",
            conversation_id="test_conv_6",
        )
        assert state.intent == IntentType.AFTER_SALE
        # 缺少订单号，应该询问用户
        assert state.after_sale_step == "waiting_order_id"

    def test_conversation_has_trace_id(self):
        """测试对话有trace_id"""
        state = run_conversation(
            user_id="user_001",
            message="你好",
            conversation_id="test_conv_7",
        )
        assert state.trace_id != ""
        assert len(state.trace_id) > 10  # UUID长度

    def test_conversation_has_processing_time(self):
        """测试对话有处理时间"""
        state = run_conversation(
            user_id="user_001",
            message="你好",
            conversation_id="test_conv_8",
        )
        assert state.processing_time_ms > 0
