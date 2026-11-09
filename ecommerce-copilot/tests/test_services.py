"""
业务服务层单元测试
"""
import pytest
from app.services.product_service import ProductService
from app.services.order_service import OrderService
from app.services.inventory_service import InventoryService
from app.services.after_sale_rule_service import AfterSaleRuleService
from app.models.product import ProductSearchParams, ProductCategory
from app.models.order import OrderStatus
from app.models.after_sale import AfterSaleType


class TestProductService:
    """商品服务测试"""

    def test_product_service_singleton(self):
        """测试单例模式"""
        s1 = ProductService.get_instance()
        s2 = ProductService.get_instance()
        assert s1 is s2

    def test_product_count(self):
        """测试商品数量（应大于200）"""
        service = ProductService.get_instance()
        assert service.product_count > 200

    def test_search_products(self):
        """测试商品搜索"""
        service = ProductService.get_instance()
        params = ProductSearchParams(query="耳机", page_size=5)
        result = service.search_products(params)
        assert result.total > 0
        assert len(result.products) <= 5
        assert result.search_time_ms >= 0

    def test_search_by_category(self):
        """测试按分类搜索"""
        service = ProductService.get_instance()
        params = ProductSearchParams(category=ProductCategory.ELECTRONICS, page_size=10)
        result = service.search_products(params)
        assert result.total > 0
        for p in result.products:
            assert p.category == ProductCategory.ELECTRONICS

    def test_search_by_price_range(self):
        """测试按价格区间搜索"""
        service = ProductService.get_instance()
        params = ProductSearchParams(
            query="耳机",
            min_price=100,
            max_price=1000,
            page_size=20,
        )
        result = service.search_products(params)
        for p in result.products:
            assert 100 <= p.price <= 1000

    def test_get_product_by_sku(self):
        """测试按SKU查询商品"""
        service = ProductService.get_instance()
        # 获取第一个商品
        params = ProductSearchParams(page_size=1)
        result = service.search_products(params)
        if result.products:
            sku_id = result.products[0].sku_id
            product = service.get_product_by_sku(sku_id)
            assert product is not None
            assert product.sku_id == sku_id

    def test_hot_products(self):
        """测试热门商品"""
        service = ProductService.get_instance()
        hot = service.get_hot_products(limit=5)
        assert len(hot) == 5

    def test_get_all_brands(self):
        """测试获取所有品牌"""
        service = ProductService.get_instance()
        brands = service.get_all_brands()
        assert len(brands) > 0


class TestOrderService:
    """订单服务测试"""

    def test_order_service_singleton(self):
        """测试单例模式"""
        s1 = OrderService.get_instance()
        s2 = OrderService.get_instance()
        assert s1 is s2

    def test_order_count(self):
        """测试订单数量（应大于50）"""
        service = OrderService.get_instance()
        assert service.order_count > 50

    def test_get_user_orders(self):
        """测试获取用户订单"""
        service = OrderService.get_instance()
        orders, total = service.get_user_orders(user_id="user_001", page_size=10)
        assert total >= 0
        assert len(orders) <= 10
        # 所有订单都属于该用户
        for order in orders:
            assert order.user_id == "user_001"

    def test_order_ownership_verification(self):
        """测试订单归属权校验"""
        service = OrderService.get_instance()
        # 获取user_001的一个订单
        orders, _ = service.get_user_orders(user_id="user_001", page_size=1)
        if orders:
            order_id = orders[0].order_id
            # 本人可以访问
            order, err = service.get_order_by_id(order_id, "user_001")
            assert order is not None
            assert err is None
            # 其他人不能访问
            order, err = service.get_order_by_id(order_id, "user_999")
            assert order is None
            assert "无权" in err

    def test_get_logistics(self):
        """测试获取物流信息"""
        service = OrderService.get_instance()
        # 找一个已发货的订单
        orders, _ = service.get_user_orders(
            user_id="user_001",
            status=OrderStatus.SHIPPED,
            page_size=1,
        )
        if not orders:
            orders, _ = service.get_user_orders(
                user_id="user_001",
                status=OrderStatus.DELIVERED,
                page_size=1,
            )
        if orders:
            logistics, err = service.get_logistics(orders[0].order_id, "user_001")
            assert logistics is not None
            assert err is None

    def test_order_statistics(self):
        """测试订单统计"""
        service = OrderService.get_instance()
        stats = service.get_order_statistics("user_001")
        assert "total_orders" in stats
        assert "total_spent" in stats
        assert "status_count" in stats


class TestInventoryService:
    """库存服务测试"""

    def test_inventory_service_singleton(self):
        """测试单例模式"""
        s1 = InventoryService.get_instance()
        s2 = InventoryService.get_instance()
        assert s1 is s2

    def test_get_stock(self):
        """测试获取库存"""
        service = InventoryService.get_instance()
        # 从商品服务获取一个有库存的sku
        from app.services.product_service import ProductService
        ps = ProductService.get_instance()
        params = ProductSearchParams(in_stock_only=True, page_size=1)
        result = ps.search_products(params)
        if result.products:
            sku_id = result.products[0].sku_id
            stock = service.get_available_stock(sku_id)
            assert stock >= 0


class TestAfterSaleRuleService:
    """售后规则服务测试"""

    def test_rule_service_singleton(self):
        """测试单例模式"""
        s1 = AfterSaleRuleService.get_instance()
        s2 = AfterSaleRuleService.get_instance()
        assert s1 is s2

    def test_rule_count(self):
        """测试规则数量"""
        service = AfterSaleRuleService.get_instance()
        assert service.rule_count >= 10

    def test_evaluate_eligibility_return(self):
        """测试退货资格评估"""
        service = AfterSaleRuleService.get_instance()
        order_service = OrderService.get_instance()

        # 找一个已完成的订单
        orders, _ = order_service.get_user_orders(
            user_id="user_001",
            status=OrderStatus.DELIVERED,
            page_size=1,
        )
        if not orders:
            orders, _ = order_service.get_user_orders(
                user_id="user_001",
                status=OrderStatus.COMPLETED,
                page_size=1,
            )

        if orders:
            result = service.evaluate_eligibility(
                order=orders[0],
                after_sale_type=AfterSaleType.RETURN,
            )
            assert hasattr(result, "eligible")
            assert hasattr(result, "estimated_amount")

    def test_get_rules_by_type(self):
        """测试按类型获取规则"""
        service = AfterSaleRuleService.get_instance()
        return_rules = service.get_rules_by_type(AfterSaleType.RETURN)
        assert len(return_rules) > 0
        for rule in return_rules:
            assert rule.after_sale_type == AfterSaleType.RETURN
