from __future__ import annotations

from enum import Enum
from datetime import datetime
from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field, field_validator


class IntentType(str, Enum):
    """意图类型"""
    PRODUCT_SHOPPING = "product_shopping"      # 商品导购
    ORDER_QUERY = "order_query"                # 订单查询
    AFTER_SALE = "after_sale"                  # 售后
    POLICY_QA = "policy_qa"                    # 政策QA
    CHITCHAT = "chitchat"                      # 闲聊
    HUMAN_HANDOFF = "human_handoff"            # 人工接管
    UNKNOWN = "unknown"                        # 未知


class RoleType(str, Enum):
    """消息角色"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"


class MessageContentType(str, Enum):
    """消息内容类型"""
    TEXT = "text"
    IMAGE = "image"
    CARD = "card"


class ConversationMessage(BaseModel):
    """对话消息"""
    message_id: str = Field(..., description="消息ID")
    role: RoleType = Field(..., description="角色")
    content: str = Field(..., description="消息内容")
    content_type: MessageContentType = Field(default=MessageContentType.TEXT, description="内容类型")
    timestamp: datetime = Field(default_factory=datetime.now, description="时间戳")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")
    tool_calls: List[Dict[str, Any]] = Field(default_factory=list, description="工具调用")
    tool_results: List[Dict[str, Any]] = Field(default_factory=list, description="工具结果")


class UserContext(BaseModel):
    """用户上下文"""
    user_id: str = Field(..., description="用户ID")
    nickname: str = Field(default="", description="昵称")
    user_level: str = Field(default="normal", description="用户等级")
    is_vip: bool = Field(default=False, description="是否VIP")
    risk_level: str = Field(default="low", description="风险等级")
    preferences: Dict[str, Any] = Field(default_factory=dict, description="用户偏好")
    device_info: Dict[str, Any] = Field(default_factory=dict, description="设备信息")


class ExtractedSlots(BaseModel):
    """提取的槽位信息"""
    product_name: Optional[str] = Field(None, description="商品名称")
    category: Optional[str] = Field(None, description="商品分类")
    brand: Optional[str] = Field(None, description="品牌")
    min_price: Optional[float] = Field(None, description="最低价格")
    max_price: Optional[float] = Field(None, description="最高价格")
    order_id: Optional[str] = Field(None, description="订单号")
    after_sale_type: Optional[str] = Field(None, description="售后类型")
    return_reason: Optional[str] = Field(None, description="退货原因")
    policy_topic: Optional[str] = Field(None, description="政策主题")
    raw_query: str = Field(default="", description="原始查询")
    confidence: Dict[str, float] = Field(default_factory=dict, description="各槽位置信度")
    missing_slots: List[str] = Field(default_factory=list, description="缺失的槽位")


class ConversationState(BaseModel):
    """对话状态（LangGraph状态）"""
    # 基础信息
    conversation_id: str = Field(..., description="对话ID")
    trace_id: str = Field(..., description="追踪ID")
    user_context: UserContext = Field(..., description="用户上下文")

    # 当前轮次信息
    user_message: str = Field(default="", description="用户消息")
    message_history: List[ConversationMessage] = Field(default_factory=list, description="消息历史")

    # 意图识别结果
    intent: IntentType = Field(default=IntentType.UNKNOWN, description="识别的意图")
    intent_confidence: float = Field(default=0.0, description="意图置信度")
    intent_ranking: List[Dict[str, Any]] = Field(default_factory=list, description="意图排序")

    # 槽位提取结果
    slots: ExtractedSlots = Field(default_factory=ExtractedSlots, description="提取的槽位")

    # 工具调用结果
    tool_results: Dict[str, Any] = Field(default_factory=dict, description="工具调用结果")
    tools_used: List[str] = Field(default_factory=list, description="已使用的工具列表")

    # 售后流程状态
    after_sale_step: str = Field(default="", description="售后当前步骤")
    after_sale_draft_id: Optional[str] = Field(None, description="售后草稿ID")

    # 响应生成
    response_text: str = Field(default="", description="生成的响应文本")
    response_data: Dict[str, Any] = Field(default_factory=dict, description="响应数据")
    response_sources: List[Dict[str, Any]] = Field(default_factory=list, description="引用来源")

    # 人工接管
    needs_human: bool = Field(default=False, description="是否需要人工")
    handoff_reason: str = Field(default="", description="转人工原因")
    handoff_package: Dict[str, Any] = Field(default_factory=dict, description="接管包")

    # 系统信息
    current_node: str = Field(default="start", description="当前节点")
    error: Optional[str] = Field(None, description="错误信息")
    total_tokens: int = Field(default=0, description="总token数")
    processing_time_ms: float = Field(default=0.0, description="处理耗时")
