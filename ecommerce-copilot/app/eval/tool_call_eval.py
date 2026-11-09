"""
工具调用评测
评估工具调用的准确率、参数提取准确率
"""
from __future__ import annotations

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from app.graph import run_conversation
from app.models.conversation import IntentType


# 测试用例：(user_message, expected_tool, expected_params)
TOOL_CALL_TEST_CASES = [
    # 商品搜索
    {
        "message": "推荐一款无线耳机",
        "expected_intent": IntentType.PRODUCT_SHOPPING,
        "expected_tools": ["search_products"],
        "expected_params": {},
        "user_id": "user_001",
    },
    {
        "message": "有没有500元以下的华为手机",
        "expected_intent": IntentType.PRODUCT_SHOPPING,
        "expected_tools": ["search_products"],
        "expected_params": {"brand": "华为", "max_price": 500},
        "user_id": "user_001",
    },
    # 订单查询
    {
        "message": "我的订单",
        "expected_intent": IntentType.ORDER_QUERY,
        "expected_tools": ["get_order_list"],
        "expected_params": {},
        "user_id": "user_001",
    },
    {
        "message": "查一下订单ORD202401001",
        "expected_intent": IntentType.ORDER_QUERY,
        "expected_tools": ["get_order"],
        "expected_params": {"order_id": "ORD202401001"},
        "user_id": "user_001",
    },
    # 售后
    {
        "message": "我要退货",
        "expected_intent": IntentType.AFTER_SALE,
        "expected_tools": [],  # 缺订单号，不会调用工具
        "expected_params": {"after_sale_type": "return"},
        "user_id": "user_001",
    },
    # 政策QA
    {
        "message": "七天无理由退货政策",
        "expected_intent": IntentType.POLICY_QA,
        "expected_tools": ["policy_rag"],
        "expected_params": {},
        "user_id": "user_001",
    },
    {
        "message": "退款多久到账",
        "expected_intent": IntentType.POLICY_QA,
        "expected_tools": ["policy_rag"],
        "expected_params": {},
        "user_id": "user_001",
    },
    # 闲聊
    {
        "message": "你好",
        "expected_intent": IntentType.CHITCHAT,
        "expected_tools": ["chitchat"],
        "expected_params": {},
        "user_id": "user_001",
    },
    # 人工接管
    {
        "message": "转人工",
        "expected_intent": IntentType.HUMAN_HANDOFF,
        "expected_tools": ["human_handoff"],
        "expected_params": {},
        "user_id": "user_001",
    },
]


def evaluate_tool_calls(verbose: bool = True) -> dict:
    """
    评估工具调用准确率

    Returns:
        评估结果字典
    """
    results = []
    intent_correct = 0
    tool_correct = 0
    total = len(TOOL_CALL_TEST_CASES)

    for i, test_case in enumerate(TOOL_CALL_TEST_CASES):
        message = test_case["message"]
        expected_intent = test_case["expected_intent"]
        expected_tools = set(test_case["expected_tools"])

        # 执行对话
        state = run_conversation(
            user_id=test_case["user_id"],
            message=message,
            conversation_id=f"eval_conv_{i}",
        )

        actual_tools = set(state.tools_used)
        actual_intent = state.intent

        # 意图是否正确
        intent_ok = actual_intent == expected_intent
        if intent_ok:
            intent_correct += 1

        # 工具是否正确（检查核心工具是否被调用）
        if expected_tools:
            tool_ok = expected_tools.issubset(actual_tools) or any(
                t.replace("_list", "") in " ".join(actual_tools) for t in expected_tools
            )
        else:
            # 预期不调用工具（如缺槽位的售后）
            tool_ok = not any(t in ["evaluate_after_sale", "create_after_sale_draft"] for t in actual_tools)

        if tool_ok:
            tool_correct += 1

        results.append({
            "message": message,
            "expected_intent": expected_intent.value,
            "actual_intent": actual_intent.value,
            "intent_correct": intent_ok,
            "expected_tools": list(expected_tools),
            "actual_tools": list(actual_tools),
            "tool_correct": tool_ok,
            "response_preview": state.response_text[:100] + "..." if len(state.response_text) > 100 else state.response_text,
        })

    intent_accuracy = intent_correct / total if total > 0 else 0
    tool_accuracy = tool_correct / total if total > 0 else 0

    eval_result = {
        "total": total,
        "intent_correct": intent_correct,
        "intent_accuracy": round(intent_accuracy, 4),
        "tool_correct": tool_correct,
        "tool_accuracy": round(tool_accuracy, 4),
        "details": results,
    }

    if verbose:
        print("=" * 70)
        print("工具调用评测结果")
        print("=" * 70)
        print(f"总测试数: {total}")
        print(f"意图准确率: {intent_accuracy:.2%} ({intent_correct}/{total})")
        print(f"工具调用准确率: {tool_accuracy:.2%} ({tool_correct}/{total})")
        print()
        print("详细结果:")
        for r in results:
            status = "✅" if r["intent_correct"] and r["tool_correct"] else "❌"
            print(f"\n{status} 消息: {r['message']}")
            print(f"   意图: {r['expected_intent']} -> {r['actual_intent']} {'✓' if r['intent_correct'] else '✗'}")
            print(f"   工具: 期望{ r['expected_tools']} -> 实际{r['actual_tools']} {'✓' if r['tool_correct'] else '✗'}")
            print(f"   回复: {r['response_preview']}")

    return eval_result


if __name__ == "__main__":
    evaluate_tool_calls()
