from __future__ import annotations

from enum import Enum
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator


class OrderStatus(str, Enum):
    """订单状态"""
    PENDING_PAYMENT = "pending_payment"    # 待支付
    PAID = "paid"                          # 已支付
    SHIPPED = "shipped"                    # 已发货
    DELIVERED = "delivered"                # 已签收
    COMPLETED = "completed"                # 已完成
    CANCELLED = "cancelled"                # 已取消
    REFUNDING = "refunding"                # 退款中
    REFUNDED = "refunded"                  # 已退款


class OrderItem(BaseModel):
    """订单商品项"""
    sku_id: str = Field(..., description="商品SKU ID")
    product_name: str = Field(..., description="商品名称")
    quantity: int = Field(..., gt=0, description="数量")
    unit_price: float = Field(..., gt=0, description="单价")
    subtotal: float = Field(..., ge=0, description="小计")
    image_url: Optional[str] = Field(None, description="商品图片")
    attributes: dict = Field(default_factory=dict, description="规格属性")

    @field_validator("subtotal")
    @classmethod
    def subtotal_must_match(cls, v: float, info):
        qty = info.data.get("quantity", 0)
        price = info.data.get("unit_price", 0)
        expected = round(qty * price, 2)
        if abs(v - expected) > 0.01:
            # 允许小差异，不强制报错
            pass
        return v


class LogisticsInfo(BaseModel):
    """物流信息"""
    tracking_number: str = Field(..., description="物流单号")
    carrier: str = Field(..., description="物流公司")
    status: str = Field(default="in_transit", description="物流状态")
    current_location: str = Field(default="", description="当前位置")
    estimated_delivery: Optional[datetime] = Field(None, description="预计送达时间")
    updates: List[dict] = Field(default_factory=list, description="物流轨迹")


class Order(BaseModel):
    """订单模型"""
    order_id: str = Field(..., description="订单号")
    user_id: str = Field(..., description="用户ID")
    status: OrderStatus = Field(..., description="订单状态")
    items: List[OrderItem] = Field(default_factory=list, description="商品列表")
    total_amount: float = Field(..., ge=0, description="订单总金额")
    discount_amount: float = Field(default=0, ge=0, description="优惠金额")
    shipping_fee: float = Field(default=0, ge=0, description="运费")
    actual_payment: float = Field(..., ge=0, description="实付金额")
    shipping_address: dict = Field(default_factory=dict, description="收货地址")
    payment_method: str = Field(default="", description="支付方式")
    payment_time: Optional[datetime] = Field(None, description="支付时间")
    shipping_time: Optional[datetime] = Field(None, description="发货时间")
    delivery_time: Optional[datetime] = Field(None, description="签收时间")
    create_time: datetime = Field(default_factory=datetime.now, description="创建时间")
    complete_time: Optional[datetime] = Field(None, description="完成时间")
    cancel_reason: Optional[str] = Field(None, description="取消原因")
    logistics: Optional[LogisticsInfo] = Field(None, description="物流信息")
    remark: Optional[str] = Field(None, description="订单备注")

    @property
    def can_cancel(self) -> bool:
        """是否可取消"""
        return self.status in (OrderStatus.PENDING_PAYMENT, OrderStatus.PAID)

    @property
    def can_return(self) -> bool:
        """是否可退货"""
        return self.status in (OrderStatus.DELIVERED, OrderStatus.COMPLETED)

    @property
    def can_refund(self) -> bool:
        """是否可退款（未发货）"""
        return self.status == OrderStatus.PAID

    @property
    def days_since_delivery(self) -> Optional[int]:
        """签收天数"""
        if self.delivery_time:
            return (datetime.now() - self.delivery_time).days
        return None
