"""模拟数据层 - 商品、订单、售后规则、政策文档"""
from .products import generate_products, get_all_products
from .orders import generate_orders, get_all_orders
from .after_sale_rules import get_after_sale_rules
from .policies import get_policy_documents, get_policy_chunks

__all__ = [
    "generate_products", "get_all_products",
    "generate_orders", "get_all_orders",
    "get_after_sale_rules",
    "get_policy_documents", "get_policy_chunks",
]
