"""
工具层单元测试
"""
import pytest
from app.tools.search_products import search_products_tool
from app.tools.get_order import get_order_tool
from app.tools.get_logistics import get_logistics_tool
from app.tools.evaluate_after_sale import evaluate_after_sale_tool
from app.tools.create_after_sale_draft import create_after_sale_draft_tool
from app.tools.confirm_after_sale import confirm_after_sale_tool
from app.tools.policy_rag import policy_rag_tool
from app.models.order import OrderStatus


class TestSearchProductsTool:
    """商品搜索工具测试"""

    def test_search_products_success(self):
        """测试成功搜索商品"""
        result = search_products_tool(query="无线耳机", page_size=3)
        assert result["success"] is True
        assert "products" in result
        assert "total" in result
        assert len(result["products"]) <= 3

    def test_search_products_with_filters(self):
        """测试带过滤的搜索"""
        result = search_products_tool(
            query="耳机",
            category="electronics",
            min_price=100,
            max_price=1000,
            page_size=5,
        )
        assert result["success"] is True

    def test_search_products_empty(self):
        """测试搜索无结果（极端过滤）"""
        result = search_products_tool(
            query="不存在的商品xyz123",
            page_size=10,
        )
        # 可能有结果也可能没有，但结构正确
        assert "success" in result
        assert "products" in result


class TestGetOrderTool:
    """订单查询工具测试"""

    def test_get_order_list(self):
        """测试获取订单列表"""
        result = get_order_tool(user_id="user_001", page_size=5)
        assert result["success"] is True
        assert "orders" in result
        assert "total" in result

    def test_get_order_by_id(self):
        """测试按订单号查询"""
        # 先获取一个订单号
        list_result = get_order_tool(user_id="user_001", page_size=1)
        if list_result["orders"]:
            order_id = list_result["orders"][0]["order_id"]
            result = get_order_tool(user_id="user_001", order_id=order_id)
            assert result["success"] is True
            assert result["is_single"] is True
            assert result["orders"][0]["order_id"] == order_id

    def test_get_order_unauthorized(self):
        """测试越权访问订单"""
        # 获取user_001的一个订单
        list_result = get_order_tool(user_id="user_001", page_size=1)
        if list_result["orders"]:
            order_id = list_result["orders"][0]["order_id"]
            # 用user_999访问
            result = get_order_tool(user_id="user_999", order_id=order_id)
            assert result["success"] is False
            assert "无权" in result["error"]


class TestGetLogisticsTool:
    """物流查询工具测试"""

    def test_get_logistics_for_shipped_order(self):
        """测试查询已发货订单的物流"""
        # 找一个已发货的订单
        order_result = get_order_tool(
            user_id="user_001",
            status="shipped",
            page_size=1,
        )
        if not order_result["orders"]:
            order_result = get_order_tool(
                user_id="user_001",
                status="delivered",
                page_size=1,
            )

        if order_result["orders"]:
            order_id = order_result["orders"][0]["order_id"]
            result = get_logistics_tool(user_id="user_001", order_id=order_id)
            # 可能有物流也可能没有，但结构正确
            assert "success" in result
            assert "logistics" in result


class TestEvaluateAfterSaleTool:
    """售后评估工具测试"""

    def test_evaluate_after_sale_basic(self):
        """测试基本售后评估"""
        # 获取一个已签收的订单
        order_result = get_order_tool(
            user_id="user_001",
            status="delivered",
            page_size=1,
        )
        if not order_result["orders"]:
            order_result = get_order_tool(
                user_id="user_001",
                status="completed",
                page_size=1,
            )

        if order_result["orders"]:
            order_id = order_result["orders"][0]["order_id"]
            result = evaluate_after_sale_tool(
                user_id="user_001",
                order_id=order_id,
                after_sale_type="return",
                user_intent="我要退货",
            )
            assert "eligible" in result
            assert "after_sale_type" in result


class TestCreateAfterSaleDraftTool:
    """创建售后草稿工具测试"""

    def test_create_draft_basic(self):
        """测试创建基本售后草稿"""
        order_result = get_order_tool(
            user_id="user_001",
            status="delivered",
            page_size=1,
        )
        if not order_result["orders"]:
            order_result = get_order_tool(
                user_id="user_001",
                status="completed",
                page_size=1,
            )

        if order_result["orders"]:
            order_id = order_result["orders"][0]["order_id"]
            result = create_after_sale_draft_tool(
                user_id="user_001",
                order_id=order_id,
                after_sale_type="return",
                reason="七天无理由",
                idempotency_key=f"test_draft_{order_id}",
            )
            assert result["success"] is True
            assert "application" in result
            assert result["application"]["status"] == "draft"

    def test_create_draft_idempotent(self):
        """测试幂等性"""
        order_result = get_order_tool(
            user_id="user_001",
            status="delivered",
            page_size=1,
        )
        if order_result["orders"]:
            order_id = order_result["orders"][0]["order_id"]
            idem_key = f"test_idem_{order_id}_v2"

            # 第一次创建
            r1 = create_after_sale_draft_tool(
                user_id="user_001",
                order_id=order_id,
                after_sale_type="return",
                idempotency_key=idem_key,
            )
            # 第二次创建（相同幂等键）
            r2 = create_after_sale_draft_tool(
                user_id="user_001",
                order_id=order_id,
                after_sale_type="return",
                idempotency_key=idem_key,
            )
            assert r2.get("is_idempotent") is True
            assert r1["application"]["application_id"] == r2["application"]["application_id"]


class TestPolicyRAGTool:
    """政策RAG工具测试"""

    def test_policy_rag_basic(self):
        """测试政策RAG基本功能"""
        result = policy_rag_tool(query="七天无理由退货", top_k=3)
        assert result["success"] is True
        assert "chunks" in result
        assert "sources" in result

    def test_policy_rag_has_answer(self):
        """测试政策RAG有答案的情况"""
        result = policy_rag_tool(query="退货政策", top_k=3)
        # 应该能找到相关结果
        assert "has_answer" in result
        assert "confidence" in result

    def test_policy_rag_related_questions(self):
        """测试相关问题生成"""
        result = policy_rag_tool(query="物流配送", top_k=3)
        assert "related_questions" in result
        assert isinstance(result["related_questions"], list)
