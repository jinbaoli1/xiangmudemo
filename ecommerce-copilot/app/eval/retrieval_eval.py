"""
检索效果评测
评估商品检索的召回率、精确率、MRR、NDCG
"""
from __future__ import annotations

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from app.services.product_service import ProductService
from app.models.product import ProductSearchParams


# 测试查询：(query, 期望命中的商品特征, 至少应包含的SKU关键字)
RETRIEVAL_TEST_CASES = [
    {
        "query": "无线蓝牙耳机",
        "expected_keywords": ["耳机", "蓝牙", "无线"],
        "category": "electronics",
        "min_expected": 10,
    },
    {
        "query": "华为手机",
        "expected_keywords": ["华为", "手机"],
        "category": "electronics",
        "min_expected": 3,
    },
    {
        "query": "纯棉T恤",
        "expected_keywords": ["T恤", "纯棉"],
        "category": "clothing",
        "min_expected": 5,
    },
    {
        "query": "空气炸锅",
        "expected_keywords": ["空气炸锅"],
        "category": "home_appliances",
        "min_expected": 3,
    },
    {
        "query": "Python编程书",
        "expected_keywords": ["编程", "技术"],
        "category": "books",
        "min_expected": 2,
    },
    {
        "query": "三只松鼠坚果",
        "expected_keywords": ["三只松鼠", "坚果"],
        "category": "food",
        "min_expected": 2,
    },
    {
        "query": "兰蔻精华液",
        "expected_keywords": ["兰蔻", "精华"],
        "category": "beauty",
        "min_expected": 2,
    },
    {
        "query": "瑜伽垫健身",
        "expected_keywords": ["瑜伽", "健身"],
        "category": "sports",
        "min_expected": 2,
    },
    {
        "query": "乐高积木",
        "expected_keywords": ["积木"],
        "category": "toys",
        "min_expected": 2,
    },
    {
        "query": "人体工学办公椅",
        "expected_keywords": ["办公椅", "人体工学"],
        "category": "furniture",
        "min_expected": 2,
    },
]


def evaluate_retrieval(verbose: bool = True) -> dict:
    """
    评估检索效果

    Returns:
        评估结果字典
    """
    product_service = ProductService.get_instance()

    results = []
    total_recall_at_10 = 0
    total_precision_at_10 = 0
    total_mrr = 0
    total_ndcg = 0
    total_search_time = 0

    for i, test_case in enumerate(RETRIEVAL_TEST_CASES):
        query = test_case["query"]
        expected_keywords = test_case["expected_keywords"]
        expected_category = test_case["category"]
        min_expected = test_case["min_expected"]

        # 执行检索
        params = ProductSearchParams(
            query=query,
            page_size=20,
        )
        search_result = product_service.search_products(params)
        products = search_result.products
        total_search_time += search_result.search_time_ms

        # 计算相关性：商品名或描述中包含关键词即认为相关
        def is_relevant(product) -> bool:
            text = f"{product.name} {product.description} {product.brand}"
            # 至少匹配一半关键词
            matches = sum(1 for kw in expected_keywords if kw in text)
            return matches >= len(expected_keywords) // 2 or product.category.value == expected_category

        relevant_items = [p for p in products if is_relevant(p)]

        # Recall@10: 前10个结果中相关的数量 / 期望的最少相关数
        top_10 = products[:10]
        relevant_in_top_10 = sum(1 for p in top_10 if is_relevant(p))
        recall_at_10 = min(relevant_in_top_10 / max(min_expected, 1), 1.0)

        # Precision@10
        precision_at_10 = relevant_in_top_10 / 10 if len(top_10) > 0 else 0

        # MRR (Mean Reciprocal Rank): 第一个相关结果的排名的倒数
        mrr = 0.0
        for rank, p in enumerate(products, 1):
            if is_relevant(p):
                mrr = 1.0 / rank
                break

        # NDCG@10 (简化版)
        dcg = 0.0
        for rank, p in enumerate(products[:10], 1):
            rel = 1.0 if is_relevant(p) else 0.0
            dcg += rel / (rank if rank == 1 else __import__('math').log2(rank + 1))

        # 理想DCG（假设前10个都相关）
        idcg = sum(1.0 / (r if r == 1 else __import__('math').log2(r + 1)) for r in range(1, 11))
        ndcg = dcg / idcg if idcg > 0 else 0

        total_recall_at_10 += recall_at_10
        total_precision_at_10 += precision_at_10
        total_mrr += mrr
        total_ndcg += ndcg

        results.append({
            "query": query,
            "total_found": search_result.total,
            "returned": len(products),
            "relevant_in_top_10": relevant_in_top_10,
            "recall@10": round(recall_at_10, 4),
            "precision@10": round(precision_at_10, 4),
            "mrr": round(mrr, 4),
            "ndcg@10": round(ndcg, 4),
            "search_time_ms": search_result.search_time_ms,
            "top_result": products[0].name if products else "无结果",
        })

    num_cases = len(RETRIEVAL_TEST_CASES)
    avg_recall = total_recall_at_10 / num_cases if num_cases > 0 else 0
    avg_precision = total_precision_at_10 / num_cases if num_cases > 0 else 0
    avg_mrr = total_mrr / num_cases if num_cases > 0 else 0
    avg_ndcg = total_ndcg / num_cases if num_cases > 0 else 0
    avg_search_time = total_search_time / num_cases if num_cases > 0 else 0

    eval_result = {
        "num_queries": num_cases,
        "avg_recall@10": round(avg_recall, 4),
        "avg_precision@10": round(avg_precision, 4),
        "avg_mrr": round(avg_mrr, 4),
        "avg_ndcg@10": round(avg_ndcg, 4),
        "avg_search_time_ms": round(avg_search_time, 2),
        "details": results,
    }

    if verbose:
        print("=" * 70)
        print("检索效果评测结果")
        print("=" * 70)
        print(f"查询数量: {num_cases}")
        print(f"平均 Recall@10:    {avg_recall:.2%}")
        print(f"平均 Precision@10: {avg_precision:.2%}")
        print(f"平均 MRR:          {avg_mrr:.4f}")
        print(f"平均 NDCG@10:      {avg_ndcg:.4f}")
        print(f"平均搜索耗时:      {avg_search_time:.2f}ms")
        print()
        print("各查询详情:")
        print(f"{'Query':<20} {'Recall':>8} {'Prec':>8} {'MRR':>8} {'NDCG':>8} {'Time':>8}  Top1")
        print("-" * 90)
        for r in results:
            print(f"{r['query']:<20} {r['recall@10']:>7.1%} {r['precision@10']:>7.1%} {r['mrr']:>8.4f} {r['ndcg@10']:>8.4f} {r['search_time_ms']:>7.0f}ms  {r['top_result'][:30]}")

    return eval_result


if __name__ == "__main__":
    evaluate_retrieval()
