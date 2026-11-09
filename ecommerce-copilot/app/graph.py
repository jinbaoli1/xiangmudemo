"""
Commerce Copilot 状态机 - 自包含实现（LangGraph 风格）

采用状态机模式，包含以下节点：
authenticate → classify_intent → extract_slots → 路由到6条业务链路 → END

6条业务链路：
1. 商品导购 (product_shopping)
2. 订单查询 (order_query)
3. 售后预审 (after_sale)
4. 政策QA (policy_qa)
5. 闲聊 (chitchat)
6. 人工接管 (human_handoff)

设计上参考 LangGraph 的 StateGraph 模式：
- 节点是普通函数，接收状态返回状态更新
- 边连接节点
- 条件边根据状态路由到不同节点
- invoke() 执行完整流程
- stream() 流式输出每个节点
"""
from __future__ import annotations

import time
import uuid
from typing import Dict, Any, List, Optional, Callable, TypedDict

from .models.conversation import (
    ConversationState, IntentType, UserContext, ExtractedSlots,
    ConversationMessage, RoleType,
)
from .models.after_sale import AfterSaleType
from .mock_llm import get_mock_llm
from .tools.search_products import search_products_tool
from .tools.get_order import get_order_tool
from .tools.get_logistics import get_logistics_tool
from .tools.evaluate_after_sale import evaluate_after_sale_tool
from .tools.create_after_sale_draft import create_after_sale_draft_tool
from .tools.confirm_after_sale import confirm_after_sale_tool
from .tools.policy_rag import policy_rag_tool


# ============ 节点函数 ============

def node_authenticate(state: ConversationState) -> Dict[str, Any]:
    """身份验证节点 - 从header注入user_id，构建用户上下文"""
    return {
        "current_node": "authenticate",
    }


def node_classify_intent(state: ConversationState) -> Dict[str, Any]:
    """意图分类节点"""
    llm = get_mock_llm()
    intent, confidence, ranking = llm.classify_intent(state.user_message)

    return {
        "intent": intent,
        "intent_confidence": confidence,
        "intent_ranking": ranking,
        "current_node": "classify_intent",
        "tools_used": state.tools_used + ["intent_classifier"],
    }


def node_extract_slots(state: ConversationState) -> Dict[str, Any]:
    """槽位提取节点"""
    llm = get_mock_llm()
    slots = llm.extract_slots(state.user_message, state.intent)

    return {
        "slots": slots,
        "current_node": "extract_slots",
    }


def node_product_shopping(state: ConversationState) -> Dict[str, Any]:
    """商品导购链路"""
    slots = state.slots
    query = state.user_message

    search_params = {
        "query": slots.product_name or query,
        "category": slots.category,
        "brand": slots.brand,
        "min_price": slots.min_price,
        "max_price": slots.max_price,
        "page_size": 5,
    }

    result = search_products_tool(**{k: v for k, v in search_params.items() if v is not None})

    llm = get_mock_llm()
    response_text = llm.generate_product_response(result, query)

    sources = []
    for p in result.get("products", []):
        sources.append({
            "type": "product",
            "sku_id": p["sku_id"],
            "name": p["name"],
            "price": p["price"],
        })

    return {
        "tool_results": {**state.tool_results, "search_products": result},
        "tools_used": state.tools_used + ["search_products"],
        "response_text": response_text,
        "response_sources": sources,
        "response_data": {"products": result.get("products", []), "total": result.get("total", 0)},
        "current_node": "product_shopping",
    }


def node_order_query(state: ConversationState) -> Dict[str, Any]:
    """订单查询链路"""
    user_id = state.user_context.user_id
    slots = state.slots
    query = state.user_message

    if slots.order_id:
        result = get_order_tool(user_id=user_id, order_id=slots.order_id)
        tool_name = "get_order"
    else:
        result = get_order_tool(user_id=user_id, page_size=5)
        tool_name = "get_order_list"

    logistics_result = None
    if slots.order_id and any(kw in query for kw in ["物流", "快递", "到哪", "发货", "配送"]):
        logistics_result = get_logistics_tool(user_id=user_id, order_id=slots.order_id)

    llm = get_mock_llm()
    if logistics_result and logistics_result.get("success"):
        response_text = llm.generate_logistics_response(logistics_result)
    else:
        response_text = llm.generate_order_response(result, query)

    sources = [{"type": "order", "order_id": o["order_id"], "status": o["status"]}
               for o in result.get("orders", [])]

    tool_results = {**state.tool_results, tool_name: result}
    tools_used = state.tools_used + [tool_name]
    if logistics_result:
        tool_results["get_logistics"] = logistics_result
        tools_used.append("get_logistics")

    return {
        "tool_results": tool_results,
        "tools_used": tools_used,
        "response_text": response_text,
        "response_sources": sources,
        "response_data": {"orders": result.get("orders", []), "total": result.get("total", 0)},
        "current_node": "order_query",
    }


def node_after_sale(state: ConversationState) -> Dict[str, Any]:
    """售后预审链路（状态机式）"""
    user_id = state.user_context.user_id
    slots = state.slots
    query = state.user_message
    llm = get_mock_llm()

    current_step = state.after_sale_step
    tool_results = dict(state.tool_results)
    tools_used = list(state.tools_used)
    response_text = ""
    needs_human = False
    handoff_reason = ""
    handoff_package = {}
    draft_id = state.after_sale_draft_id

    if not current_step or current_step == "evaluate":
        if not slots.order_id:
            response_text = (
                "好的，我来帮您处理售后申请。\n\n"
                "请问您的订单号是什么？您可以在「我的订单」中查看订单号，"
                "格式为 ORD 开头的一串数字。"
            )
            return {
                "response_text": response_text,
                "after_sale_step": "waiting_order_id",
                "current_node": "after_sale",
                "tools_used": tools_used,
                "tool_results": tool_results,
            }

        eval_result = evaluate_after_sale_tool(
            user_id=user_id,
            order_id=slots.order_id,
            after_sale_type=slots.after_sale_type,
            reason=slots.return_reason or "",
            is_vip=state.user_context.is_vip,
            user_intent=query,
        )

        tool_results["evaluate_after_sale"] = eval_result
        tools_used.append("evaluate_after_sale")

        if not eval_result.get("eligible"):
            response_text = llm.generate_after_sale_response(eval_result, step="evaluate")
            return {
                "tool_results": tool_results,
                "tools_used": tools_used,
                "response_text": response_text,
                "after_sale_step": "completed",
                "current_node": "after_sale",
            }

        response_text = llm.generate_after_sale_response(eval_result, step="evaluate")

        if eval_result.get("auto_approve") and eval_result.get("risk_level") == "low":
            as_type = eval_result.get("after_sale_type", "return")
            draft_result = create_after_sale_draft_tool(
                user_id=user_id,
                order_id=slots.order_id,
                after_sale_type=as_type,
                reason=slots.return_reason or "七天无理由退货",
            )
            tool_results["create_after_sale_draft"] = draft_result
            tools_used.append("create_after_sale_draft")

            if draft_result.get("success"):
                draft_id = draft_result["application"]["application_id"]
                confirm_result = confirm_after_sale_tool(
                    user_id=user_id,
                    application_id=draft_id,
                    confirm=True,
                )
                tool_results["confirm_after_sale"] = confirm_result
                tools_used.append("confirm_after_sale")
                response_text = llm.generate_after_sale_response(confirm_result, step="confirm")

                if confirm_result.get("needs_human"):
                    needs_human = True
                    handoff_reason = confirm_result.get("handoff_reason", "")
                    handoff_package = confirm_result.get("handoff_package", {})

            current_step = "completed"
        else:
            current_step = "evaluated"

    elif current_step == "evaluated":
        confirm_words = ["确认", "好的", "是的", "对", "申请", "提交", "要", "办"]
        cancel_words = ["不", "算了", "取消", "不要", "再考虑"]
        user_msg_lower = query.lower()

        if any(w in user_msg_lower for w in cancel_words):
            response_text = "好的，售后申请已取消。如果后续需要，随时告诉我哦~"
            current_step = "cancelled"
        elif any(w in user_msg_lower for w in confirm_words):
            eval_result = tool_results.get("evaluate_after_sale", {})
            as_type = eval_result.get("after_sale_type", "return")
            draft_result = create_after_sale_draft_tool(
                user_id=user_id,
                order_id=slots.order_id,
                after_sale_type=as_type,
                reason=slots.return_reason or "七天无理由退货",
                description=query,
            )
            tool_results["create_after_sale_draft"] = draft_result
            tools_used.append("create_after_sale_draft")

            if draft_result.get("success"):
                draft_id = draft_result["application"]["application_id"]
                response_text = llm.generate_after_sale_response(draft_result, step="draft")
                current_step = "draft_created"
            else:
                response_text = f"创建草稿失败：{draft_result.get('error', '未知错误')}"
                current_step = "error"
        else:
            eval_result = tool_results.get("evaluate_after_sale", {})
            response_text = llm.generate_after_sale_response(eval_result, step="evaluate")

    elif current_step == "draft_created":
        confirm_words = ["确认", "好的", "是的", "对", "提交", "没问题", "正确"]
        cancel_words = ["不", "算了", "取消", "不对", "错了", "修改"]
        user_msg_lower = query.lower()

        if any(w in user_msg_lower for w in cancel_words):
            if draft_id:
                confirm_result = confirm_after_sale_tool(user_id=user_id, application_id=draft_id, confirm=False)
                tool_results["confirm_after_sale"] = confirm_result
                tools_used.append("confirm_after_sale")
                response_text = llm.generate_after_sale_response(confirm_result, step="confirm")
            else:
                response_text = "好的，已取消申请。"
            current_step = "cancelled"
        elif any(w in user_msg_lower for w in confirm_words):
            if draft_id:
                confirm_result = confirm_after_sale_tool(user_id=user_id, application_id=draft_id, confirm=True)
                tool_results["confirm_after_sale"] = confirm_result
                tools_used.append("confirm_after_sale")
                response_text = llm.generate_after_sale_response(confirm_result, step="confirm")
                if confirm_result.get("needs_human"):
                    needs_human = True
                    handoff_reason = confirm_result.get("handoff_reason", "")
                    handoff_package = confirm_result.get("handoff_package", {})
                current_step = "completed"
            else:
                response_text = "抱歉，找不到对应的售后申请，请重新发起。"
                current_step = "error"
        else:
            draft_result = tool_results.get("create_after_sale_draft", {})
            response_text = llm.generate_after_sale_response(draft_result, step="draft")

    elif current_step == "waiting_order_id":
        import re
        order_match = re.search(r'ORD[0-9]{5,}', query.upper())
        if order_match:
            slots.order_id = order_match.group()
            eval_result = evaluate_after_sale_tool(
                user_id=user_id,
                order_id=slots.order_id,
                after_sale_type=slots.after_sale_type,
                is_vip=state.user_context.is_vip,
                user_intent=query,
            )
            tool_results["evaluate_after_sale"] = eval_result
            tools_used.append("evaluate_after_sale")
            response_text = llm.generate_after_sale_response(eval_result, step="evaluate")
            current_step = "evaluated" if eval_result.get("eligible") else "completed"
        else:
            response_text = "我没有识别到订单号，请提供正确的订单号（格式如ORD202401001）。"

    return {
        "tool_results": tool_results,
        "tools_used": tools_used,
        "response_text": response_text,
        "after_sale_step": current_step,
        "after_sale_draft_id": draft_id,
        "needs_human": needs_human,
        "handoff_reason": handoff_reason,
        "handoff_package": handoff_package,
        "current_node": "after_sale",
        "slots": slots,
    }


def node_policy_qa(state: ConversationState) -> Dict[str, Any]:
    """政策QA链路"""
    query = state.user_message
    result = policy_rag_tool(query=query, top_k=3, return_sources=True)

    llm = get_mock_llm()
    response_text = llm.generate_policy_response(result, query)

    sources = [
        {"type": "policy", "doc_id": s.get("doc_id"), "doc_title": s.get("doc_title"),
         "section_path": s.get("section_path"), "relevance_score": s.get("relevance_score")}
        for s in result.get("sources", [])
    ]

    return {
        "tool_results": {**state.tool_results, "policy_rag": result},
        "tools_used": state.tools_used + ["policy_rag"],
        "response_text": response_text,
        "response_sources": sources,
        "response_data": {"chunks": result.get("chunks", []), "confidence": result.get("confidence", 0)},
        "current_node": "policy_qa",
    }


def node_chitchat(state: ConversationState) -> Dict[str, Any]:
    """闲聊链路"""
    llm = get_mock_llm()
    response_text = llm.generate_chitchat_response(state.user_message)

    return {
        "response_text": response_text,
        "current_node": "chitchat",
        "tools_used": state.tools_used + ["chitchat"],
    }


def node_human_handoff(state: ConversationState) -> Dict[str, Any]:
    """人工接管链路 - 生成接管包"""
    user_id = state.user_context.user_id

    handoff_package = {
        "user_id": user_id,
        "user_level": state.user_context.user_level,
        "is_vip": state.user_context.is_vip,
        "risk_level": state.user_context.risk_level,
        "intent": state.intent.value if state.intent else "unknown",
        "intent_confidence": state.intent_confidence,
        "user_message": state.user_message,
        "conversation_id": state.conversation_id,
        "trace_id": state.trace_id,
        "tools_used": state.tools_used,
        "handoff_reason": state.handoff_reason or "用户主动要求人工",
        "risk_tags": [],
    }

    if state.handoff_package:
        handoff_package.update(state.handoff_package)

    llm = get_mock_llm()
    reason = state.handoff_reason or "您要求人工客服"
    response_text = llm.generate_handoff_response(handoff_package, reason)

    return {
        "needs_human": True,
        "handoff_reason": state.handoff_reason or "用户主动要求人工",
        "handoff_package": handoff_package,
        "response_text": response_text,
        "current_node": "human_handoff",
        "tools_used": state.tools_used + ["human_handoff"],
    }


def node_unknown(state: ConversationState) -> Dict[str, Any]:
    """未知意图处理"""
    llm = get_mock_llm()
    response_text = llm.generate_unknown_response(state.user_message)

    return {
        "response_text": response_text,
        "current_node": "unknown",
        "tools_used": state.tools_used + ["unknown_handler"],
    }


# ============ 路由函数 ============

def route_by_intent(state: ConversationState) -> str:
    """根据意图路由到对应业务链路"""
    intent = state.intent

    # 售后流程进行中，继续走售后链路
    if state.after_sale_step and state.after_sale_step not in ("", "completed", "cancelled", "error"):
        return "after_sale"

    if intent == IntentType.HUMAN_HANDOFF:
        return "human_handoff"

    route_map = {
        IntentType.PRODUCT_SHOPPING: "product_shopping",
        IntentType.ORDER_QUERY: "order_query",
        IntentType.AFTER_SALE: "after_sale",
        IntentType.POLICY_QA: "policy_qa",
        IntentType.CHITCHAT: "chitchat",
        IntentType.UNKNOWN: "unknown",
    }

    return route_map.get(intent, "unknown")


# ============ 状态图实现 ============

class CopilotStateGraph:
    """
    Commerce Copilot 状态图（自包含实现，LangGraph 风格）

    节点函数签名: (state: ConversationState) -> Dict[str, Any]
    返回的字典会被合并到状态中（字段级别更新）
    """

    def __init__(self, state_schema):
        self._state_schema = state_schema
        self._nodes: Dict[str, Callable] = {}
        self._edges: Dict[str, str] = {}
        self._conditional_edges: Dict[str, Callable] = {}
        self._entry_point: Optional[str] = None
        self._end_nodes: set = set()

    def add_node(self, name: str, node_fn: Callable):
        """添加节点"""
        self._nodes[name] = node_fn

    def set_entry_point(self, name: str):
        """设置入口节点"""
        self._entry_point = name

    def set_finish_point(self, name: str):
        """设置终点节点"""
        self._end_nodes.add(name)

    def add_edge(self, from_node: str, to_node: str):
        """添加边"""
        self._edges[from_node] = to_node

    def add_conditional_edges(self, from_node: str, condition_fn: Callable, branches: Dict[str, str]):
        """添加条件边"""
        def router(state):
            route = condition_fn(state)
            return branches.get(route, list(branches.values())[0] if branches else None)
        self._conditional_edges[from_node] = router

    def compile(self) -> "CopilotStateGraph":
        """编译图（验证并返回自身）"""
        if not self._entry_point:
            raise ValueError("必须设置入口节点")
        return self

    def invoke(self, initial_state: ConversationState) -> ConversationState:
        """执行完整流程，返回最终状态"""
        state = initial_state
        current_node = self._entry_point

        visited = set()
        max_steps = 50  # 防止无限循环
        steps = 0

        while current_node and steps < max_steps:
            if current_node in visited and current_node not in ("after_sale",):
                # 防止循环（售后节点允许重复访问，因为是多步的）
                break
            visited.add(current_node)

            # 执行节点
            node_fn = self._nodes.get(current_node)
            if not node_fn:
                raise ValueError(f"节点不存在: {current_node}")

            # 获取状态更新
            updates = node_fn(state)

            # 合并更新到状态
            state = self._merge_state(state, updates)
            state.current_node = updates.get("current_node", current_node)

            # 如果是终点节点，执行完就结束
            if current_node in self._end_nodes:
                break

            # 确定下一个节点
            if current_node in self._conditional_edges:
                # 条件路由
                next_node = self._conditional_edges[current_node](state)
            elif current_node in self._edges:
                next_node = self._edges[current_node]
            else:
                # 没有出边，结束
                break

            current_node = next_node
            steps += 1

        return state

    def stream(self, initial_state: ConversationState):
        """流式执行，逐个产出节点结果"""
        state = initial_state
        current_node = self._entry_point

        visited = set()
        max_steps = 50
        steps = 0

        while current_node and steps < max_steps:
            if current_node in visited and current_node not in ("after_sale",):
                break
            visited.add(current_node)

            node_fn = self._nodes.get(current_node)
            if not node_fn:
                raise ValueError(f"节点不存在: {current_node}")

            updates = node_fn(state)
            state = self._merge_state(state, updates)
            state.current_node = updates.get("current_node", current_node)

            # 产出当前节点结果
            yield current_node, state

            # 如果是终点节点，执行完就结束
            if current_node in self._end_nodes:
                break

            # 下一个节点
            if current_node in self._conditional_edges:
                next_node = self._conditional_edges[current_node](state)
            elif current_node in self._edges:
                next_node = self._edges[current_node]
            else:
                break

            current_node = next_node
            steps += 1

    @staticmethod
    def _merge_state(state: ConversationState, updates: Dict[str, Any]) -> ConversationState:
        """将更新合并到状态中"""
        # 使用 Pydantic 的 model_copy + update
        update_dict = {}
        for key, value in updates.items():
            if hasattr(state, key):
                if isinstance(value, dict) and isinstance(getattr(state, key), dict):
                    # 合并字典
                    merged = dict(getattr(state, key))
                    merged.update(value)
                    update_dict[key] = merged
                else:
                    # 其他类型（包括list）直接替换
                    # 节点函数负责返回完整的列表值
                    update_dict[key] = value

        if update_dict:
            state = state.model_copy(update=update_dict)

        return state


# ============ 构建状态图 ============

_graph_instance = None


def build_graph() -> CopilotStateGraph:
    """构建状态图"""
    graph = CopilotStateGraph(ConversationState)

    # 添加节点
    graph.add_node("authenticate", node_authenticate)
    graph.add_node("classify_intent", node_classify_intent)
    graph.add_node("extract_slots", node_extract_slots)
    graph.add_node("product_shopping", node_product_shopping)
    graph.add_node("order_query", node_order_query)
    graph.add_node("after_sale", node_after_sale)
    graph.add_node("policy_qa", node_policy_qa)
    graph.add_node("chitchat", node_chitchat)
    graph.add_node("human_handoff", node_human_handoff)
    graph.add_node("unknown", node_unknown)

    # 设置入口
    graph.set_entry_point("authenticate")

    # 主流程边
    graph.add_edge("authenticate", "classify_intent")
    graph.add_edge("classify_intent", "extract_slots")

    # 条件路由
    graph.add_conditional_edges(
        "extract_slots",
        route_by_intent,
        {
            "product_shopping": "product_shopping",
            "order_query": "order_query",
            "after_sale": "after_sale",
            "policy_qa": "policy_qa",
            "chitchat": "chitchat",
            "human_handoff": "human_handoff",
            "unknown": "unknown",
        },
    )

    # 业务链路结束后到达终点
    graph.set_finish_point("product_shopping")
    graph.set_finish_point("order_query")
    graph.set_finish_point("after_sale")
    graph.set_finish_point("policy_qa")
    graph.set_finish_point("chitchat")
    graph.set_finish_point("human_handoff")
    graph.set_finish_point("unknown")

    return graph.compile()


def get_graph() -> CopilotStateGraph:
    """获取编译后的状态图（单例）"""
    global _graph_instance
    if _graph_instance is None:
        _graph_instance = build_graph()
    return _graph_instance


# ============ 执行入口 ============

def run_conversation(
    user_id: str,
    message: str,
    conversation_id: str,
    message_history: List[ConversationMessage] = None,
    is_vip: bool = False,
) -> ConversationState:
    """执行一轮对话"""
    start_time = time.perf_counter()
    trace_id = str(uuid.uuid4())

    user_context = UserContext(
        user_id=user_id,
        nickname=f"用户{user_id[-3:]}",
        user_level="vip" if is_vip else "normal",
        is_vip=is_vip,
        risk_level="low",
    )

    initial_state = ConversationState(
        conversation_id=conversation_id,
        trace_id=trace_id,
        user_context=user_context,
        user_message=message,
        message_history=message_history or [],
    )

    graph = get_graph()
    final_state = graph.invoke(initial_state)
    final_state.processing_time_ms = (time.perf_counter() - start_time) * 1000

    return final_state


def run_conversation_stream(
    user_id: str,
    message: str,
    conversation_id: str,
    message_history: List[ConversationMessage] = None,
    is_vip: bool = False,
):
    """流式执行对话（SSE用）"""
    start_time = time.perf_counter()
    trace_id = str(uuid.uuid4())

    user_context = UserContext(
        user_id=user_id,
        nickname=f"用户{user_id[-3:]}",
        user_level="vip" if is_vip else "normal",
        is_vip=is_vip,
        risk_level="low",
    )

    initial_state = ConversationState(
        conversation_id=conversation_id,
        trace_id=trace_id,
        user_context=user_context,
        user_message=message,
        message_history=message_history or [],
    )

    graph = get_graph()

    for node_name, state in graph.stream(initial_state):
        elapsed = (time.perf_counter() - start_time) * 1000
        yield {
            "type": "node_update",
            "node": node_name,
            "trace_id": trace_id,
            "elapsed_ms": round(elapsed, 2),
            "state": _extract_public_state(state),
        }

    yield {
        "type": "complete",
        "trace_id": trace_id,
        "total_time_ms": round((time.perf_counter() - start_time) * 1000, 2),
    }


def _extract_public_state(state: ConversationState) -> Dict[str, Any]:
    """从状态中提取可公开的信息"""
    return {
        "current_node": state.current_node,
        "intent": state.intent.value if state.intent else None,
        "intent_confidence": state.intent_confidence,
        "response_text": state.response_text,
        "needs_human": state.needs_human,
        "tools_used": state.tools_used,
    }
