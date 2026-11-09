"""
数据初始化脚本
运行：python seed_data.py
"""
from __future__ import annotations

import sys
import os
import time

# 确保app目录在路径中
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "app"))

from app.data.products import generate_products
from app.data.orders import generate_orders
from app.data.after_sale_rules import get_after_sale_rules
from app.data.policies import get_policy_documents, get_policy_chunks
from app.services.product_service import ProductService
from app.services.order_service import OrderService
from app.services.inventory_service import InventoryService
from app.services.after_sale_rule_service import AfterSaleRuleService
from app.tools.policy_rag import _get_searcher as get_policy_searcher


def main():
    print("=" * 60)
    print("Commerce Copilot - 数据初始化")
    print("=" * 60)

    start_time = time.time()

    # 1. 商品数据
    print("\n[1/6] 生成商品数据...")
    products = generate_products()
    print(f"  ✓ 生成 {len(products)} 个商品SKU")

    # 按分类统计
    from collections import Counter
    cat_counter = Counter(p.category.value for p in products)
    for cat, count in sorted(cat_counter.items()):
        print(f"    - {cat}: {count} 个")

    # 2. 订单数据
    print("\n[2/6] 生成订单数据...")
    orders = generate_orders()
    print(f"  ✓ 生成 {len(orders)} 个订单")

    status_counter = Counter(o.status.value for o in orders)
    for status, count in sorted(status_counter.items()):
        print(f"    - {status}: {count} 个")

    # 3. 售后规则
    print("\n[3/6] 加载售后规则...")
    rules = get_after_sale_rules()
    print(f"  ✓ 加载 {len(rules)} 条售后规则")

    # 4. 政策文档
    print("\n[4/6] 加载政策文档...")
    docs = get_policy_documents()
    chunks = get_policy_chunks()
    print(f"  ✓ 加载 {len(docs)} 篇政策文档，{len(chunks)} 个文本切片")

    # 5. 初始化服务（构建索引）
    print("\n[5/6] 初始化服务和检索索引...")

    print("  商品服务...", end=" ", flush=True)
    t0 = time.time()
    product_service = ProductService.get_instance()
    print(f"✓ ({(time.time()-t0)*1000:.0f}ms)")

    print("  订单服务...", end=" ", flush=True)
    t0 = time.time()
    order_service = OrderService.get_instance()
    print(f"✓ ({(time.time()-t0)*1000:.0f}ms)")

    print("  库存服务...", end=" ", flush=True)
    t0 = time.time()
    inventory_service = InventoryService.get_instance()
    print(f"✓ ({(time.time()-t0)*1000:.0f}ms)")

    print("  售后规则服务...", end=" ", flush=True)
    t0 = time.time()
    rule_service = AfterSaleRuleService.get_instance()
    print(f"✓ ({(time.time()-t0)*1000:.0f}ms)")

    print("  政策RAG检索器...", end=" ", flush=True)
    t0 = time.time()
    policy_searcher = get_policy_searcher()
    print(f"✓ ({(time.time()-t0)*1000:.0f}ms)")

    # 6. 快速检索测试
    print("\n[6/6] 检索功能测试...")

    # 商品检索测试
    print("  商品检索测试...", end=" ", flush=True)
    t0 = time.time()
    from app.models.product import ProductSearchParams
    result = product_service.search_products(
        ProductSearchParams(query="无线耳机", page_size=3)
    )
    elapsed = (time.time() - t0) * 1000
    print(f"✓ 找到{result.total}个结果，耗时{elapsed:.0f}ms")

    # 政策RAG测试
    print("  政策RAG测试...", end=" ", flush=True)
    t0 = time.time()
    from app.tools.policy_rag import policy_rag_tool
    rag_result = policy_rag_tool("七天无理由退货", top_k=2)
    elapsed = (time.time() - t0) * 1000
    print(f"✓ 找到{rag_result.get('total_chunks_found', 0)}个相关片段，耗时{elapsed:.0f}ms")

    total_time = time.time() - start_time
    print("\n" + "=" * 60)
    print(f"数据初始化完成！总耗时: {total_time:.2f}s")
    print("=" * 60)
    print("\n下一步：")
    print("  cd app")
    print("  uvicorn main:app --reload --port 8000")
    print("\n或者运行测试：")
    print("  pytest tests/ -v")


if __name__ == "__main__":
    main()
