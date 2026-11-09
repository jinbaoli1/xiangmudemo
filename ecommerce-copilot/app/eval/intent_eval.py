"""
意图识别评测
评估意图分类器的准确率、精确率、召回率、F1
"""
from __future__ import annotations

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from collections import defaultdict
from app.mock_llm import get_mock_llm
from app.models.conversation import IntentType


# 测试数据集：(query, expected_intent)
INTENT_TEST_CASES = [
    # 商品导购
    ("推荐一款无线耳机", IntentType.PRODUCT_SHOPPING),
    ("有没有性价比高的手机推荐", IntentType.PRODUCT_SHOPPING),
    ("我想买个笔记本电脑", IntentType.PRODUCT_SHOPPING),
    ("搜索蓝牙耳机", IntentType.PRODUCT_SHOPPING),
    ("这款手表多少钱", IntentType.PRODUCT_SHOPPING),
    ("有没有500元以下的运动鞋", IntentType.PRODUCT_SHOPPING),
    ("小米的电视怎么样", IntentType.PRODUCT_SHOPPING),

    # 订单查询
    ("我的订单到哪了", IntentType.ORDER_QUERY),
    ("查一下订单ORD202401001", IntentType.ORDER_QUERY),
    ("快递什么时候到", IntentType.ORDER_QUERY),
    ("看看我的订单", IntentType.ORDER_QUERY),
    ("物流信息", IntentType.ORDER_QUERY),
    ("发货了吗", IntentType.ORDER_QUERY),
    ("我的包裹在哪", IntentType.ORDER_QUERY),

    # 售后
    ("我要退货", IntentType.AFTER_SALE),
    ("这个商品质量有问题", IntentType.AFTER_SALE),
    ("申请退款", IntentType.AFTER_SALE),
    ("想换货可以吗", IntentType.AFTER_SALE),
    ("七天无理由怎么退", IntentType.AFTER_SALE),
    ("东西坏了要维修", IntentType.AFTER_SALE),
    ("退回去", IntentType.AFTER_SALE),

    # 政策QA
    ("退货政策是什么", IntentType.POLICY_QA),
    ("运费怎么算", IntentType.POLICY_QA),
    ("发票怎么开", IntentType.POLICY_QA),
    ("会员有什么权益", IntentType.POLICY_QA),
    ("积分怎么用", IntentType.POLICY_QA),
    ("退款多久到账", IntentType.POLICY_QA),
    ("个人信息安全吗", IntentType.POLICY_QA),

    # 闲聊
    ("你好", IntentType.CHITCHAT),
    ("谢谢", IntentType.CHITCHAT),
    ("再见", IntentType.CHITCHAT),
    ("你是谁", IntentType.CHITCHAT),
    ("在吗", IntentType.CHITCHAT),
    ("早上好", IntentType.CHITCHAT),

    # 人工接管
    ("转人工", IntentType.HUMAN_HANDOFF),
    ("我要找客服", IntentType.HUMAN_HANDOFF),
    ("你解决不了", IntentType.HUMAN_HANDOFF),
    ("我要投诉", IntentType.HUMAN_HANDOFF),
    ("叫你们经理来", IntentType.HUMAN_HANDOFF),
]


def evaluate_intent_classification(verbose: bool = True) -> dict:
    """
    评估意图分类效果

    Returns:
        评估指标字典
    """
    llm = get_mock_llm()

    # 统计每个意图的 TP, FP, FN
    tp = defaultdict(int)
    fp = defaultdict(int)
    fn = defaultdict(int)
    correct = 0
    total = len(INTENT_TEST_CASES)

    # 详细结果
    details = []

    for query, expected in INTENT_TEST_CASES:
        predicted, confidence, _ = llm.classify_intent(query)

        is_correct = predicted == expected
        if is_correct:
            correct += 1
            tp[expected.value] += 1
        else:
            fp[predicted.value] += 1
            fn[expected.value] += 1

        details.append({
            "query": query,
            "expected": expected.value,
            "predicted": predicted.value,
            "confidence": confidence,
            "correct": is_correct,
        })

    # 计算整体准确率
    accuracy = correct / total if total > 0 else 0

    # 计算每个意图的精确率、召回率、F1
    intent_metrics = {}
    all_intents = set(
        [e.value for e in IntentType] +
        list(tp.keys()) + list(fp.keys()) + list(fn.keys())
    )

    for intent in all_intents:
        precision = tp[intent] / (tp[intent] + fp[intent]) if (tp[intent] + fp[intent]) > 0 else 0
        recall = tp[intent] / (tp[intent] + fn[intent]) if (tp[intent] + fn[intent]) > 0 else 0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0

        intent_metrics[intent] = {
            "tp": tp[intent],
            "fp": fp[intent],
            "fn": fn[intent],
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1": round(f1, 4),
        }

    # 宏平均F1
    macro_f1 = sum(m["f1"] for m in intent_metrics.values()) / len(intent_metrics) if intent_metrics else 0

    result = {
        "total": total,
        "correct": correct,
        "accuracy": round(accuracy, 4),
        "macro_f1": round(macro_f1, 4),
        "intent_metrics": intent_metrics,
        "details": details,
    }

    if verbose:
        print("=" * 60)
        print("意图识别评测结果")
        print("=" * 60)
        print(f"总样本数: {total}")
        print(f"正确数: {correct}")
        print(f"准确率: {accuracy:.2%}")
        print(f"宏平均F1: {macro_f1:.4f}")
        print()
        print("各意图指标:")
        for intent, metrics in sorted(intent_metrics.items()):
            if metrics["tp"] + metrics["fn"] > 0:  # 只显示有样本的
                print(f"  {intent:20s} P:{metrics['precision']:.2%}  R:{metrics['recall']:.2%}  F1:{metrics['f1']:.4f}  (TP:{metrics['tp']}/FP:{metrics['fp']}/FN:{metrics['fn']})")

        print()
        print("错误案例:")
        for d in details:
            if not d["correct"]:
                print(f"  ❌ '{d['query']}' -> 预期:{d['expected']}, 预测:{d['predicted']} (conf:{d['confidence']:.2f})")

    return result


if __name__ == "__main__":
    evaluate_intent_classification()
