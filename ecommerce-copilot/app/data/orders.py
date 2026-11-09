"""
订单模拟数据 - 生成50+订单
"""
from __future__ import annotations

import random
from datetime import datetime, timedelta
from typing import List
from ..models.order import Order, OrderItem, OrderStatus, LogisticsInfo
from .products import generate_products

_orders_cache: List[Order] = []

# 用户ID列表
_USER_IDS = [f"user_{i:03d}" for i in range(1, 21)]

# 物流公司
_CARRIERS = ["顺丰速运", "京东物流", "中通快递", "圆通速递", "韵达快递", "申通快递", "极兔速递"]

# 收货地址
_ADDRESSES = [
    {"province": "北京市", "city": "北京市", "district": "朝阳区", "detail": "建国路88号SOHO现代城A座1001", "receiver": "张三", "phone": "138****1234"},
    {"province": "上海市", "city": "上海市", "district": "浦东新区", "detail": "陆家嘴环路1000号恒生银行大厦20楼", "receiver": "李四", "phone": "139****5678"},
    {"province": "广东省", "city": "深圳市", "district": "南山区", "detail": "科技园南区深南大道9996号松日鼎盛大厦15层", "receiver": "王五", "phone": "137****9012"},
    {"province": "浙江省", "city": "杭州市", "district": "西湖区", "detail": "文三路478号华星时代广场C座502", "receiver": "赵六", "phone": "136****3456"},
    {"province": "江苏省", "city": "南京市", "district": "鼓楼区", "detail": "中山路18号德基广场2期2501", "receiver": "钱七", "phone": "135****7890"},
    {"province": "四川省", "city": "成都市", "district": "锦江区", "detail": "春熙路东段1号IFS国际金融中心3号楼22层", "receiver": "孙八", "phone": "134****2345"},
    {"province": "湖北省", "city": "武汉市", "district": "江汉区", "detail": "建设大道568号新世界国贸大厦1座30楼", "receiver": "周九", "phone": "133****6789"},
    {"province": "陕西省", "city": "西安市", "district": "雁塔区", "detail": "高新路2号西安软件园秦风阁B101", "receiver": "吴十", "phone": "132****0123"},
]

# 支付方式
_PAYMENT_METHODS = ["微信支付", "支付宝", "银行卡", "花呗", "京东白条"]


def generate_orders(seed: int = 123) -> List[Order]:
    """生成50+订单"""
    global _orders_cache
    if _orders_cache:
        return _orders_cache

    random.seed(seed)
    products = generate_products()
    orders = []
    order_counter = 1

    # 为每个用户生成2-5个订单
    for user_id in _USER_IDS:
        num_orders = random.randint(2, 5)
        for _ in range(num_orders):
            order_id = f"ORD2024{order_counter:05d}"
            order_counter += 1

            # 随机选择2-4个商品
            num_items = random.randint(1, 4)
            selected_products = random.sample(products, min(num_items, len(products)))

            items = []
            total_amount = 0
            for prod in selected_products:
                qty = random.randint(1, 3)
                subtotal = round(prod.price * qty, 2)
                total_amount += subtotal
                items.append(OrderItem(
                    sku_id=prod.sku_id,
                    product_name=prod.name,
                    quantity=qty,
                    unit_price=prod.price,
                    subtotal=subtotal,
                    image_url=f"https://example.com/images/{prod.sku_id}_1.jpg",
                    attributes={"颜色": prod.attributes.get("颜色", "默认"), "尺码": prod.attributes.get("尺码", "均码")},
                ))

            # 计算优惠和运费
            discount_amount = round(total_amount * random.uniform(0, 0.2), 2)
            shipping_fee = 0 if total_amount > 99 else round(random.uniform(5, 15), 2)
            actual_payment = round(total_amount - discount_amount + shipping_fee, 2)

            # 随机订单状态
            status_weights = [0.05, 0.1, 0.15, 0.25, 0.3, 0.1, 0.03, 0.02]
            statuses = list(OrderStatus)
            status = random.choices(statuses, weights=status_weights[:len(statuses)], k=1)[0]

            # 生成时间线
            create_time = datetime.now() - timedelta(days=random.randint(1, 90))
            payment_time = None
            shipping_time = None
            delivery_time = None
            complete_time = None
            cancel_reason = None
            logistics = None

            if status in [OrderStatus.PAID, OrderStatus.SHIPPED, OrderStatus.DELIVERED, OrderStatus.COMPLETED, OrderStatus.REFUNDING, OrderStatus.REFUNDED]:
                payment_time = create_time + timedelta(hours=random.randint(1, 24))
            if status in [OrderStatus.SHIPPED, OrderStatus.DELIVERED, OrderStatus.COMPLETED]:
                shipping_time = payment_time + timedelta(hours=random.randint(6, 48))
                # 生成物流信息
                logistics = _generate_logistics(shipping_time, status)
            if status in [OrderStatus.DELIVERED, OrderStatus.COMPLETED]:
                delivery_time = shipping_time + timedelta(days=random.randint(1, 5))
            if status == OrderStatus.COMPLETED:
                complete_time = delivery_time + timedelta(days=random.randint(3, 15))
            if status == OrderStatus.CANCELLED:
                cancel_reason = random.choice(["不想要了", "拍错了", "价格太贵", "等待时间太长"])

            order = Order(
                order_id=order_id,
                user_id=user_id,
                status=status,
                items=items,
                total_amount=round(total_amount, 2),
                discount_amount=discount_amount,
                shipping_fee=shipping_fee,
                actual_payment=actual_payment,
                shipping_address=random.choice(_ADDRESSES),
                payment_method=random.choice(_PAYMENT_METHODS) if payment_time else "",
                payment_time=payment_time,
                shipping_time=shipping_time,
                delivery_time=delivery_time,
                create_time=create_time,
                complete_time=complete_time,
                cancel_reason=cancel_reason,
                logistics=logistics,
                remark=random.choice(["", "请尽快发货", "送货前电话联系", "放在快递柜"]) if random.random() < 0.3 else None,
            )
            orders.append(order)

    _orders_cache = orders
    return orders


def _generate_logistics(shipping_time: datetime, status: OrderStatus) -> LogisticsInfo:
    """生成物流信息"""
    carrier = random.choice(_CARRIERS)
    tracking_number = f"{carrier[:2]}{random.randint(1000000000, 9999999999)}"

    updates = [
        {"time": shipping_time.isoformat(), "location": "仓库已出库", "status": "已发货"},
        {"time": (shipping_time + timedelta(hours=6)).isoformat(), "location": "转运中心", "status": "运输中"},
    ]

    current_location = "运输途中"
    logistics_status = "in_transit"

    if status in [OrderStatus.DELIVERED, OrderStatus.COMPLETED]:
        updates.append({"time": (shipping_time + timedelta(days=2)).isoformat(), "location": "目的地城市", "status": "派送中"})
        updates.append({"time": (shipping_time + timedelta(days=2, hours=8)).isoformat(), "location": "已签收", "status": "已签收"})
        current_location = "已签收"
        logistics_status = "delivered"
    elif status == OrderStatus.SHIPPED:
        updates.append({"time": (shipping_time + timedelta(days=1)).isoformat(), "location": "途中城市", "status": "运输中"})
        current_location = "运输途中"
        logistics_status = "in_transit"

    estimated_delivery = shipping_time + timedelta(days=random.randint(2, 5))

    return LogisticsInfo(
        tracking_number=tracking_number,
        carrier=carrier,
        status=logistics_status,
        current_location=current_location,
        estimated_delivery=estimated_delivery,
        updates=updates,
    )


def get_all_orders() -> List[Order]:
    """获取所有订单"""
    return generate_orders()


if __name__ == "__main__":
    orders = generate_orders()
    print(f"生成订单数量: {len(orders)}")
    print(f"状态分布:")
    from collections import Counter
    statuses = Counter(o.status.value for o in orders)
    for s, count in statuses.items():
        print(f"  {s}: {count}")
