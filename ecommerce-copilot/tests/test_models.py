"""
数据模型单元测试
"""
import pytest
from datetime import datetime
from app.models.product import Product, ProductCategory, ProductSearchParams
from app.models.order import Order, OrderItem, OrderStatus, LogisticsInfo
from app.models.after_sale import AfterSaleApplication, AfterSaleStatus, AfterSaleType
from app.models.conversation import ConversationState, IntentType, UserContext, ExtractedSlots
from app.models.policy import PolicyDocument, PolicyChunk


class TestProductModel:
    """商品模型测试"""

    def test_create_product(self):
        """测试创建商品"""
        product = Product(
            sku_id="SKU00001",
            name="测试商品",
            category=ProductCategory.ELECTRONICS,
            price=99.99,
            brand="TestBrand",
            stock=100,
        )
        assert product.sku_id == "SKU00001"
        assert product.name == "测试商品"
        assert product.category == ProductCategory.ELECTRONICS
        assert product.price == 99.99
        assert product.is_on_sale is True

    def test_product_discount_rate(self):
        """测试折扣率计算"""
        product = Product(
            sku_id="SKU00001",
            name="测试商品",
            category=ProductCategory.ELECTRONICS,
            price=80.0,
            original_price=100.0,
        )
        assert product.discount_rate == 0.8

    def test_product_no_original_price(self):
        """测试无原价时折扣率为None"""
        product = Product(
            sku_id="SKU00001",
            name="测试商品",
            category=ProductCategory.ELECTRONICS,
            price=99.99,
        )
        assert product.discount_rate is None

    def test_product_search_text(self):
        """测试搜索文本生成"""
        product = Product(
            sku_id="SKU00001",
            name="无线耳机",
            description="高品质音效",
            category=ProductCategory.ELECTRONICS,
            price=99.99,
            brand="苹果",
            tags=["新品", "热销"],
        )
        text = product.search_text
        assert "无线耳机" in text
        assert "苹果" in text
        assert "新品" in text

    def test_product_invalid_price(self):
        """测试无效价格"""
        with pytest.raises(Exception):
            Product(
                sku_id="SKU00001",
                name="测试",
                category=ProductCategory.ELECTRONICS,
                price=-10,
            )

    def test_product_original_price_less_than_price(self):
        """测试原价低于现价时报错"""
        with pytest.raises(Exception):
            Product(
                sku_id="SKU00001",
                name="测试",
                category=ProductCategory.ELECTRONICS,
                price=100,
                original_price=50,
            )

    def test_search_params_validation(self):
        """测试搜索参数验证"""
        params = ProductSearchParams(
            query="耳机",
            min_price=100,
            max_price=500,
            page=1,
            page_size=20,
        )
        assert params.query == "耳机"
        assert params.min_price == 100
        assert params.max_price == 500


class TestOrderModel:
    """订单模型测试"""

    def test_create_order(self):
        """测试创建订单"""
        item = OrderItem(
            sku_id="SKU00001",
            product_name="测试商品",
            quantity=2,
            unit_price=50.0,
            subtotal=100.0,
        )
        order = Order(
            order_id="ORD202400001",
            user_id="user_001",
            status=OrderStatus.PAID,
            items=[item],
            total_amount=100.0,
            actual_payment=100.0,
        )
        assert order.order_id == "ORD202400001"
        assert order.user_id == "user_001"
        assert order.status == OrderStatus.PAID
        assert len(order.items) == 1

    def test_order_can_cancel(self):
        """测试订单可取消状态"""
        order = Order(
            order_id="ORD001",
            user_id="u1",
            status=OrderStatus.PENDING_PAYMENT,
            items=[],
            total_amount=0,
            actual_payment=0,
        )
        assert order.can_cancel is True

        order.status = OrderStatus.DELIVERED
        assert order.can_cancel is False

    def test_order_can_return(self):
        """测试订单可退货状态"""
        order = Order(
            order_id="ORD001",
            user_id="u1",
            status=OrderStatus.DELIVERED,
            items=[],
            total_amount=0,
            actual_payment=0,
        )
        assert order.can_return is True

        order.status = OrderStatus.SHIPPED
        assert order.can_return is False

    def test_logistics_info(self):
        """测试物流信息"""
        logistics = LogisticsInfo(
            tracking_number="SF1234567890",
            carrier="顺丰速运",
            status="in_transit",
            current_location="北京转运中心",
        )
        assert logistics.tracking_number == "SF1234567890"
        assert logistics.carrier == "顺丰速运"


class TestAfterSaleModel:
    """售后模型测试"""

    def test_create_after_sale_application(self):
        """测试创建售后申请"""
        app = AfterSaleApplication(
            application_id="AS001",
            order_id="ORD001",
            user_id="user_001",
            after_sale_type=AfterSaleType.RETURN,
            idempotency_key="test-key-123",
        )
        assert app.application_id == "AS001"
        assert app.status == AfterSaleStatus.DRAFT
        assert app.after_sale_type == AfterSaleType.RETURN

    def test_handoff_package(self):
        """测试人工接管包生成"""
        app = AfterSaleApplication(
            application_id="AS001",
            order_id="ORD001",
            user_id="user_001",
            after_sale_type=AfterSaleType.RETURN,
            idempotency_key="test-key",
            amount=100.0,
            risk_tags=["high_value"],
        )
        package = app.to_handoff_package()
        assert package["application_id"] == "AS001"
        assert package["order_id"] == "ORD001"
        assert "high_value" in package["risk_tags"]


class TestConversationModel:
    """对话模型测试"""

    def test_create_user_context(self):
        """测试创建用户上下文"""
        ctx = UserContext(user_id="user_001", nickname="测试用户")
        assert ctx.user_id == "user_001"
        assert ctx.risk_level == "low"
        assert ctx.is_vip is False

    def test_conversation_state_defaults(self):
        """测试对话状态默认值"""
        state = ConversationState(
            conversation_id="conv_001",
            trace_id="trace_001",
            user_context=UserContext(user_id="u1"),
        )
        assert state.intent == IntentType.UNKNOWN
        assert state.current_node == "start"
        assert state.needs_human is False
        assert len(state.tools_used) == 0

    def test_extracted_slots(self):
        """测试提取槽位"""
        slots = ExtractedSlots(
            order_id="ORD001",
            raw_query="我要退货",
        )
        assert slots.order_id == "ORD001"
        assert slots.raw_query == "我要退货"
        assert slots.after_sale_type is None


class TestPolicyModel:
    """政策模型测试"""

    def test_create_policy_document(self):
        """测试创建政策文档"""
        doc = PolicyDocument(
            doc_id="POL001",
            title="测试政策",
            content="这是政策内容",
            category="test",
        )
        assert doc.doc_id == "POL001"
        assert doc.title == "测试政策"
        assert doc.is_active is True

    def test_policy_chunk(self):
        """测试政策切片"""
        chunk = PolicyChunk(
            chunk_id="CHUNK001",
            doc_id="POL001",
            doc_title="测试政策",
            content="切片内容",
        )
        assert chunk.chunk_id == "CHUNK001"
        assert "测试政策" in chunk.search_text
