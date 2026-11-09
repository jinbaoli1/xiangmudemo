"""
Commerce Copilot - FastAPI 入口

提供：
- SSE流式对话接口
- REST API（商品、订单、售后、政策等）
- 健康检查
- 数据统计
"""
from __future__ import annotations

import asyncio
import json
import uuid
import time
from typing import List, Optional, Dict, Any

from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel, Field

# 内部模块导入
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from .models.conversation import IntentType
from .models.product import ProductSearchParams, ProductCategory
from .services.product_service import ProductService
from .services.order_service import OrderService
from .services.inventory_service import InventoryService
from .services.after_sale_rule_service import AfterSaleRuleService
from .graph import run_conversation, run_conversation_stream
from .mock_llm import get_mock_llm


# ============ 应用初始化 ============

app = FastAPI(
    title="Commerce Copilot API",
    description="电商服务智能体 API - 基于 LangGraph + FastAPI + 混合检索",
    version="1.0.0",
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============ 启动事件 ============

@app.on_event("startup")
async def startup_event():
    """应用启动时初始化服务"""
    print("=" * 60)
    print("Commerce Copilot 启动中...")
    print("=" * 60)

    # 初始化各服务（构建索引）
    print("初始化商品服务...")
    product_service = ProductService.get_instance()
    print(f"  ✓ {product_service.product_count} 个商品")

    print("初始化订单服务...")
    order_service = OrderService.get_instance()
    print(f"  ✓ {order_service.order_count} 个订单")

    print("初始化库存服务...")
    InventoryService.get_instance()
    print(f"  ✓ 完成")

    print("初始化售后规则服务...")
    rule_service = AfterSaleRuleService.get_instance()
    print(f"  ✓ {rule_service.rule_count} 条规则")

    print("初始化MockLLM...")
    get_mock_llm()
    print(f"  ✓ 完成")

    print("=" * 60)
    print("Commerce Copilot 启动完成！")
    print("=" * 60)


# ============ 请求模型 ============

class ChatRequest(BaseModel):
    """对话请求"""
    message: str = Field(..., min_length=1, max_length=2000, description="用户消息")
    conversation_id: str = Field(..., description="对话ID")
    idempotency_key: Optional[str] = Field(None, description="幂等键")


class ChatResponse(BaseModel):
    """对话响应"""
    response: str = Field(..., description="回复文本")
    conversation_id: str = Field(..., description="对话ID")
    trace_id: str = Field(..., description="追踪ID")
    intent: str = Field(default="", description="识别的意图")
    intent_confidence: float = Field(default=0.0, description="意图置信度")
    tools_used: List[str] = Field(default_factory=list, description="使用的工具")
    sources: List[Dict[str, Any]] = Field(default_factory=list, description="引用来源")
    needs_human: bool = Field(default=False, description="是否需要人工")
    handoff_reason: str = Field(default="", description="转人工原因")
    processing_time_ms: float = Field(default=0.0, description="处理耗时")


# ============ SSE 流式对话接口 ============

@app.post("/api/chat/stream")
async def chat_stream(
    request: ChatRequest,
    x_user_id: str = Header(..., alias="X-User-Id", description="用户ID"),
    x_trace_id: Optional[str] = Header(None, alias="X-Trace-Id", description="追踪ID"),
):
    """
    SSE流式对话接口

    逐节点返回状态更新，最终返回完整响应
    """
    if not x_user_id:
        raise HTTPException(status_code=401, detail="用户ID不能为空")

    async def event_generator():
        """SSE事件生成器"""
        loop = asyncio.get_event_loop()

        # 在线程池中执行图遍历（避免阻塞事件循环）
        def run_graph():
            results = []
            for event in run_conversation_stream(
                user_id=x_user_id,
                message=request.message,
                conversation_id=request.conversation_id,
            ):
                results.append(event)
            return results

        events = await loop.run_in_executor(None, run_graph)

        # 逐个发送事件
        for i, event in enumerate(events):
            # 模拟流式延迟（增强体验）
            if i > 0:
                await asyncio.sleep(0.05)

            event_type = event.get("type", "node_update")

            if event_type == "node_update":
                node_name = event.get("node", "")
                state = event.get("state", {})

                # 发送节点开始事件
                yield f"event: node_start\ndata: {json.dumps({'node': node_name, 'trace_id': event.get('trace_id')}, ensure_ascii=False)}\n\n"

                # 如果有响应文本，分段发送
                response_text = state.get("response_text", "")
                if response_text:
                    # 按字符流式输出
                    chunk_size = 20
                    for j in range(0, len(response_text), chunk_size):
                        chunk = response_text[j:j + chunk_size]
                        yield f"event: message_chunk\ndata: {json.dumps({'content': chunk, 'node': node_name}, ensure_ascii=False)}\n\n"
                        await asyncio.sleep(0.02)

                # 发送节点完成事件
                yield f"event: node_end\ndata: {json.dumps({'node': node_name, 'state': state}, ensure_ascii=False)}\n\n"

            elif event_type == "complete":
                yield f"event: complete\ndata: {json.dumps(event, ensure_ascii=False)}\n\n"

        # 结束标记
        yield "event: done\ndata: [DONE]\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# ============ 非流式对话接口 ============

@app.post("/api/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    x_user_id: str = Header(..., alias="X-User-Id"),
    x_trace_id: Optional[str] = Header(None, alias="X-Trace-Id"),
):
    """非流式对话接口"""
    if not x_user_id:
        raise HTTPException(status_code=401, detail="用户ID不能为空")

    loop = asyncio.get_event_loop()

    def run_sync():
        return run_conversation(
            user_id=x_user_id,
            message=request.message,
            conversation_id=request.conversation_id,
        )

    state = await loop.run_in_executor(None, run_sync)

    return ChatResponse(
        response=state.response_text,
        conversation_id=state.conversation_id,
        trace_id=state.trace_id,
        intent=state.intent.value if state.intent else "",
        intent_confidence=state.intent_confidence,
        tools_used=state.tools_used,
        sources=state.response_sources,
        needs_human=state.needs_human,
        handoff_reason=state.handoff_reason,
        processing_time_ms=state.processing_time_ms,
    )


# ============ 商品 API ============

@app.get("/api/products")
async def search_products(
    q: str = "",
    category: Optional[str] = None,
    brand: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    page: int = 1,
    page_size: int = 10,
    sort_by: str = "relevance",
    in_stock_only: bool = False,
):
    """商品搜索接口"""
    product_service = ProductService.get_instance()

    category_enum = None
    if category:
        try:
            category_enum = ProductCategory(category)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"无效的分类: {category}")

    params = ProductSearchParams(
        query=q,
        category=category_enum,
        brand=brand,
        min_price=min_price,
        max_price=max_price,
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        in_stock_only=in_stock_only,
    )

    result = product_service.search_products(params)
    return {
        "code": 0,
        "data": {
            "products": [p.model_dump() for p in result.products],
            "total": result.total,
            "page": result.page,
            "page_size": result.page_size,
            "search_time_ms": result.search_time_ms,
        },
    }


@app.get("/api/products/{sku_id}")
async def get_product(sku_id: str):
    """获取商品详情"""
    product_service = ProductService.get_instance()
    product = product_service.get_product_by_sku(sku_id)

    if not product:
        raise HTTPException(status_code=404, detail="商品不存在")

    return {"code": 0, "data": product.model_dump()}


@app.get("/api/products/hot")
async def get_hot_products(category: Optional[str] = None, limit: int = 10):
    """获取热门商品"""
    product_service = ProductService.get_instance()

    category_enum = None
    if category:
        try:
            category_enum = ProductCategory(category)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"无效的分类: {category}")

    products = product_service.get_hot_products(category=category_enum, limit=limit)
    return {
        "code": 0,
        "data": [p.model_dump() for p in products],
    }


# ============ 订单 API ============

@app.get("/api/orders")
async def get_orders(
    x_user_id: str = Header(..., alias="X-User-Id"),
    status: Optional[str] = None,
    page: int = 1,
    page_size: int = 10,
):
    """获取用户订单列表"""
    order_service = OrderService.get_instance()

    orders, total = order_service.get_user_orders(
        user_id=x_user_id,
        status=status,
        page=page,
        page_size=page_size,
    )

    return {
        "code": 0,
        "data": {
            "orders": [o.model_dump() for o in orders],
            "total": total,
            "page": page,
            "page_size": page_size,
        },
    }


@app.get("/api/orders/{order_id}")
async def get_order_detail(
    order_id: str,
    x_user_id: str = Header(..., alias="X-User-Id"),
):
    """获取订单详情（带鉴权）"""
    order_service = OrderService.get_instance()

    order, error = order_service.get_order_by_id(order_id, x_user_id)
    if error:
        raise HTTPException(status_code=403 if "无权" in error else 404, detail=error)

    return {"code": 0, "data": order.model_dump()}


@app.get("/api/orders/{order_id}/logistics")
async def get_order_logistics(
    order_id: str,
    x_user_id: str = Header(..., alias="X-User-Id"),
):
    """获取订单物流信息"""
    order_service = OrderService.get_instance()

    logistics, error = order_service.get_logistics(order_id, x_user_id)
    if error:
        raise HTTPException(status_code=404, detail=error)

    return {"code": 0, "data": logistics.model_dump()}


@app.get("/api/orders/statistics")
async def get_order_statistics(
    x_user_id: str = Header(..., alias="X-User-Id"),
):
    """获取订单统计"""
    order_service = OrderService.get_instance()
    stats = order_service.get_order_statistics(x_user_id)
    return {"code": 0, "data": stats}


# ============ 售后 API ============

@app.post("/api/after-sale/evaluate")
async def evaluate_after_sale(
    request: Dict[str, Any],
    x_user_id: str = Header(..., alias="X-User-Id"),
):
    """售后资格评估"""
    from .tools.evaluate_after_sale import evaluate_after_sale_tool

    order_id = request.get("order_id")
    if not order_id:
        raise HTTPException(status_code=400, detail="订单号不能为空")

    result = evaluate_after_sale_tool(
        user_id=x_user_id,
        order_id=order_id,
        after_sale_type=request.get("after_sale_type"),
        sku_id=request.get("sku_id"),
        reason=request.get("reason", ""),
        user_intent=request.get("user_intent", ""),
    )

    return {"code": 0 if result.get("success") else 1, "data": result}


@app.post("/api/after-sale/draft")
async def create_after_sale_draft(
    request: Dict[str, Any],
    x_user_id: str = Header(..., alias="X-User-Id"),
):
    """创建售后草稿"""
    from .tools.create_after_sale_draft import create_after_sale_draft_tool

    order_id = request.get("order_id")
    after_sale_type = request.get("after_sale_type")

    if not order_id or not after_sale_type:
        raise HTTPException(status_code=400, detail="订单号和售后类型不能为空")

    result = create_after_sale_draft_tool(
        user_id=x_user_id,
        order_id=order_id,
        after_sale_type=after_sale_type,
        sku_id=request.get("sku_id"),
        reason=request.get("reason", ""),
        description=request.get("description", ""),
        evidence_images=request.get("evidence_images"),
        idempotency_key=request.get("idempotency_key"),
    )

    return {"code": 0 if result.get("success") else 1, "data": result}


@app.post("/api/after-sale/confirm")
async def confirm_after_sale(
    request: Dict[str, Any],
    x_user_id: str = Header(..., alias="X-User-Id"),
):
    """确认提交售后申请"""
    from .tools.confirm_after_sale import confirm_after_sale_tool

    application_id = request.get("application_id")
    if not application_id:
        raise HTTPException(status_code=400, detail="申请ID不能为空")

    result = confirm_after_sale_tool(
        user_id=x_user_id,
        application_id=application_id,
        confirm=request.get("confirm", True),
    )

    return {"code": 0 if result.get("success") else 1, "data": result}


# ============ 政策 API ============

@app.get("/api/policy/search")
async def search_policy(q: str, top_k: int = 3):
    """政策搜索"""
    from .tools.policy_rag import policy_rag_tool

    result = policy_rag_tool(query=q, top_k=top_k)
    return {"code": 0 if result.get("success") else 1, "data": result}


# ============ 系统 API ============

@app.get("/api/health")
async def health_check():
    """健康检查"""
    product_service = ProductService.get_instance()
    order_service = OrderService.get_instance()
    rule_service = AfterSaleRuleService.get_instance()

    return {
        "status": "healthy",
        "timestamp": time.time(),
        "services": {
            "product_service": {
                "status": "ok",
                "product_count": product_service.product_count,
            },
            "order_service": {
                "status": "ok",
                "order_count": order_service.order_count,
            },
            "after_sale_rule_service": {
                "status": "ok",
                "rule_count": rule_service.rule_count,
            },
        },
    }


@app.get("/api/stats")
async def get_stats():
    """系统统计信息"""
    product_service = ProductService.get_instance()
    order_service = OrderService.get_instance()
    rule_service = AfterSaleRuleService.get_instance()

    # 统计商品分类
    from collections import Counter
    from .data.products import get_all_products
    products = get_all_products()
    category_stats = dict(Counter(p.category.value for p in products if p.is_on_sale))

    return {
        "code": 0,
        "data": {
            "products": {
                "total": product_service.product_count,
                "by_category": category_stats,
                "brands_count": len(product_service.get_all_brands()),
            },
            "orders": {
                "total": order_service.order_count,
            },
            "after_sale_rules": {
                "total": rule_service.rule_count,
            },
            "intents": [e.value for e in IntentType],
        },
    }


# ============ 根路径 ============

@app.get("/")
async def root():
    """根路径"""
    return {
        "name": "Commerce Copilot API",
        "version": "1.0.0",
        "description": "电商服务智能体 API",
        "docs": "/docs",
        "endpoints": {
            "chat_stream": "POST /api/chat/stream (SSE)",
            "chat": "POST /api/chat",
            "products": "GET /api/products",
            "orders": "GET /api/orders",
            "policy_search": "GET /api/policy/search",
            "health": "GET /api/health",
            "stats": "GET /api/stats",
        },
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)
