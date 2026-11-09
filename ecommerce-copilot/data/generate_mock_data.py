"""
模拟数据生成脚本
生成 200+ 商品、50+ 订单
运行: python generate_mock_data.py
"""
import json
import random
from datetime import datetime, timedelta
from pathlib import Path

# 确保在 data 目录下
DATA_DIR = Path(__file__).parent

# 商品分类
CATEGORIES = {
    "手机数码": ["Apple", "华为", "小米", "OPPO", "vivo", "三星", "荣耀", "一加"],
    "电脑办公": ["联想", "戴尔", "惠普", "华硕", "华为", "Apple", "小米", "宏碁"],
    "家用电器": ["美的", "海尔", "格力", "小米", "西门子", "博世", "松下", "飞利浦"],
    "服饰鞋包": ["Nike", "Adidas", "Uniqlo", "Zara", "李宁", "安踏", "太平鸟", "波司登"],
    "美妆个护": ["雅诗兰黛", "兰蔻", "欧莱雅", "SK-II", "资生堂", "完美日记", "花西子", "自然堂"],
    "食品生鲜": ["三只松鼠", "良品铺子", "百草味", "蒙牛", "伊利", "统一", "康师傅", "旺旺"],
    "母婴用品": ["帮宝适", "花王", "好奇", "贝亲", "好孩子", "飞鹤", "惠氏", "美赞臣"],
    "家居家装": ["宜家", "无印良品", "网易严选", "源氏木语", "全友", "顾家", "林氏木业", "索菲亚"],
    "运动户外": ["Nike", "Adidas", "迪卡侬", "北面", "探路者", "骆驼", "安踏", "李宁"],
    "图书音像": ["中信出版社", "人民文学", "机械工业", "商务印书馆", "三联书店", "后浪", "磨铁", "果麦"],
}

# 商品名称模板
PRODUCT_TEMPLATES = {
    "手机数码": [
        ("{brand} {series} 智能手机 128GB", "最新款旗舰手机，搭载{series}处理器，超清拍照系统，长续航", "旗舰,5G,拍照手机"),
        ("{brand} 无线蓝牙耳机 降噪版", "主动降噪，超长续航，高保真音质，舒适佩戴", "蓝牙耳机,降噪,无线"),
        ("{brand} 平板电脑 128GB WiFi版", "高清屏幕，强劲性能，轻薄便携，适合学习办公", "平板,大屏,学习办公"),
        ("{brand} 智能手表 运动版", "心率监测，GPS定位，50米防水，运动模式丰富", "智能手表,运动,健康监测"),
        ("{brand} 移动电源 20000mAh", "大容量，快充支持，双向快充，便携安全", "充电宝,快充,大容量"),
    ],
    "电脑办公": [
        ("{brand} 笔记本电脑 14英寸 i5/16G/512G", "轻薄本，高性能处理器，固态硬盘，长续航", "轻薄本,商务办公,高性能"),
        ("{brand} 台式电脑主机 i7/32G/1T", "游戏台式机，高端显卡，大容量存储，流畅运行", "台式机,游戏,高性能"),
        ("{brand} 27英寸 4K显示器", "4K超清，IPS面板，护眼技术，多接口", "显示器,4K,设计办公"),
        ("{brand} 机械键盘 青轴/红轴", "全键无冲，RGB背光，人体工学设计，耐用", "机械键盘,游戏,办公"),
        ("{brand} 无线鼠标 静音版", "人体工学设计，静音按键，长续航，精准定位", "无线鼠标,静音,人体工学"),
    ],
    "家用电器": [
        ("{brand} 对开门冰箱 500L", "大容量，风冷无霜，变频节能，智能温控", "冰箱,大容量,变频"),
        ("{brand} 滚筒洗衣机 10kg", "大容量，变频电机，多种洗涤程序，静音设计", "洗衣机,滚筒,大容量"),
        ("{brand} 1.5匹 变频空调", "冷暖两用，一级能效，智能控制，静音运行", "空调,变频,节能"),
        ("{brand} 扫地机器人 激光导航", "智能规划路线，自动回充，APP远程控制", "扫地机器人,智能,激光导航"),
        ("{brand} 微波炉 23L 智能款", "大容量，多档火力，智能菜单，易清洁", "微波炉,智能,大容量"),
    ],
    "服饰鞋包": [
        ("{brand} 男士运动休闲鞋", "透气网面，缓震鞋底，时尚百搭，舒适耐穿", "运动鞋,透气,缓震"),
        ("{brand} 女士羽绒服 中长款", "90%白鸭绒，保暖防风，修身显瘦，时尚设计", "羽绒服,保暖,修身"),
        ("{brand} 男士休闲夹克 春秋款", "简约设计，舒适面料，多口袋，百搭款式", "夹克,休闲,春秋"),
        ("{brand} 经典双肩背包 20L", "防水面料，多隔层设计，舒适背负，大容量", "双肩包,防水,大容量"),
        ("{brand} 女士真皮手提包", "头层牛皮，精致做工，百搭款式，多色可选", "手提包,真皮,时尚"),
    ],
    "美妆个护": [
        ("{brand} 小棕瓶精华 50ml", "修护精华，抗衰老，提亮肤色，保湿滋润", "精华液,修护,抗衰老"),
        ("{brand} 口红 哑光系列", "持久显色，滋润不拔干，多色可选，时尚包装", "口红,哑光,持久"),
        ("{brand} 面膜 补水保湿 20片装", "深层补水，提亮肤色，温和不刺激，适合各种肤质", "面膜,补水,保湿"),
        ("{brand} 电动牙刷 声波震动", "声波震动，多档模式，智能定时，长续航", "电动牙刷,声波,智能"),
        ("{brand} 洗发水 去屑控油 500ml", "深层清洁，去屑控油，柔顺发丝，清香怡人", "洗发水,去屑,控油"),
    ],
    "食品生鲜": [
        ("{brand} 每日坚果 30包 混合装", "8种坚果果干，每日一包，营养均衡，新鲜烘焙", "坚果,零食,营养"),
        ("{brand} 纯牛奶 250ml*24盒", "100%纯牛奶，高钙营养，新鲜奶源，健康早餐", "牛奶,高钙,早餐"),
        ("{brand} 猪肉脯 原味 200g", "精选猪肉，传统工艺，香甜可口，独立包装", "肉脯,零食,休闲"),
        ("{brand} 方便面 红烧牛肉 5连包", "经典口味，面饼劲道，汤浓味美，方便快捷", "方便面,速食,经典"),
        ("{brand} 普洱茶饼 357g 熟茶", "云南古树茶，陈香浓郁，口感醇厚，收藏佳品", "普洱茶,熟茶,茶叶"),
    ],
    "母婴用品": [
        ("{brand} 纸尿裤 L码 100片", "超薄透气，瞬吸干爽，柔软亲肤，防漏设计", "纸尿裤,透气,干爽"),
        ("{brand} 婴儿奶粉 3段 800g", "接近母乳配方，DHA+ARA，促进脑部发育", "奶粉,婴儿,营养"),
        ("{brand} 婴儿推车 轻便折叠款", "轻便折叠，双向推行，避震设计，安全可靠", "婴儿推车,轻便,折叠"),
        ("{brand} 宝宝辅食机 蒸煮搅拌一体", "蒸煮搅拌二合一，食品级材质，易清洗", "辅食机,蒸煮,婴儿"),
        ("{brand} 儿童安全座椅 9个月-12岁", "ISOFIX接口，多档调节，侧面防护，安全舒适", "安全座椅,儿童,安全"),
    ],
    "家居家装": [
        ("{brand} 实木餐桌 1.4米 4人位", "进口实木，环保板材，简约设计，稳固耐用", "餐桌,实木,简约"),
        ("{brand} 记忆棉床垫 1.8米 软硬适中", "记忆棉材质，人体工学设计，透气舒适，护脊", "床垫,记忆棉,舒适"),
        ("{brand} LED台灯 护眼学习灯", "无频闪，无蓝光危害，多档调光，USB充电", "台灯,护眼,学习"),
        ("{brand} 床上四件套 纯棉 1.8米床", "100%纯棉，亲肤透气，时尚印花，多色可选", "四件套,纯棉,床上用品"),
        ("{brand} 收纳箱 特大号 3个装", "大容量，加厚材质，可叠加，防潮防尘", "收纳箱,大容量,整理"),
    ],
    "运动户外": [
        ("{brand} 跑步鞋 缓震透气款", "缓震中底，透气网面，轻量设计，适合跑步", "跑步鞋,缓震,透气"),
        ("{brand} 冲锋衣 男女同款 三合一", "防水防风，抓绒内胆，可拆卸，四季可穿", "冲锋衣,防水,户外"),
        ("{brand} 瑜伽垫 加厚防滑 10mm", "加厚防滑，环保材质，回弹性好，附送绑带", "瑜伽垫,防滑,加厚"),
        ("{brand} 户外帐篷 3-4人 全自动", "自动速开，防水防晒，轻便携带，适合露营", "帐篷,户外,露营"),
        ("{brand} 运动水壶 1000ml 保温款", "大容量，双层保温，食品级材质，运动便携", "水壶,保温,运动"),
    ],
    "图书音像": [
        ("{brand} 畅销小说 精装版", "畅销作家代表作，情节精彩，值得收藏，精装装帧", "小说,畅销,精装"),
        ("{brand} 编程入门到精通", "零基础入门，实例丰富，循序渐进，适合自学", "编程,技术,入门"),
        ("{brand} 历史知识读物 图文版", "图文并茂，通俗易懂，知识丰富，增长见识", "历史,读物,知识"),
        ("{brand} 儿童绘本 3-6岁 10册", "精美插画，故事有趣，启蒙教育，亲子共读", "绘本,儿童,启蒙"),
        ("{brand} 经济管理类畅销书", "管理学经典，案例丰富，实用干货，提升自我", "经管,畅销书,管理"),
    ],
}


def generate_products(count: int = 220) -> list:
    """生成模拟商品数据"""
    products = []
    product_id = 1

    for category, brands in CATEGORIES.items():
        templates = PRODUCT_TEMPLATES[category]
        # 每个分类生成约 count/10 个商品
        per_category = count // len(CATEGORIES) + 5

        for i in range(per_category):
            brand = random.choice(brands)
            tmpl_name, tmpl_desc, tmpl_tags = random.choice(templates)
            series_list = ["Pro", "Max", "Ultra", "SE", "Plus", "Lite", "Air"]
            series = random.choice(series_list)

            name = tmpl_name.format(brand=brand, series=series)
            description = tmpl_desc.format(brand=brand, series=series)
            # 基础价格区间按分类调整
            price_map = {
                "手机数码": (999, 8999),
                "电脑办公": (199, 12999),
                "家用电器": (299, 7999),
                "服饰鞋包": (99, 2599),
                "美妆个护": (49, 1599),
                "食品生鲜": (19, 499),
                "母婴用品": (39, 3999),
                "家居家装": (59, 5999),
                "运动户外": (79, 2999),
                "图书音像": (29, 299),
            }
            min_price, max_price = price_map[category]
            price = round(random.uniform(min_price, max_price), 2)
            original_price = round(price * random.uniform(1.1, 1.5), 2)

            specs = json.dumps({
                "品牌": brand,
                "系列": series,
                "颜色": random.choice(["黑色", "白色", "银色", "蓝色", "粉色", "灰色"]),
                "尺寸": random.choice(["S", "M", "L", "XL", "标准"]),
                "产地": random.choice(["中国大陆", "日本", "美国", "德国", "韩国"]),
            }, ensure_ascii=False)

            product = {
                "id": product_id,
                "name": name,
                "category": category,
                "brand": brand,
                "price": price,
                "original_price": original_price,
                "description": description,
                "specs": specs,
                "tags": tmpl_tags,
                "image_url": f"https://picsum.photos/seed/product{product_id}/400/400",
                "stock": random.randint(10, 5000),
                "sales": random.randint(0, 50000),
                "rating": round(random.uniform(3.5, 5.0), 1),
                "is_active": True,
            }
            products.append(product)
            product_id += 1

    return products[:count]


def generate_orders(count: int = 55) -> list:
    """生成模拟订单数据"""
    orders = []
    now = datetime.now()

    user_names = ["张三", "李四", "王五", "赵六", "钱七", "孙八", "周九", "吴十",
                  "郑十一", "王小明", "李小红", "刘芳", "陈强", "杨丽", "黄伟", "徐静"]

    status_list = ["pending", "paid", "shipped", "delivered", "completed", "cancelled", "refunded"]
    status_weights = [3, 5, 10, 15, 50, 5, 7]  # 权重分布

    provinces = ["北京市朝阳区", "上海市浦东新区", "广州市天河区", "深圳市南山区",
                 "杭州市西湖区", "成都市武侯区", "武汉市洪山区", "西安市雁塔区"]

    logistics_companies = ["顺丰速运", "京东物流", "中通快递", "圆通速递", "韵达快递", "申通快递"]

    for i in range(count):
        order_id = i + 1
        days_ago = random.randint(0, 30)
        created = now - timedelta(days=days_ago, hours=random.randint(0, 23), minutes=random.randint(0, 59))

        status = random.choices(status_list, weights=status_weights, k=1)[0]
        user_name = random.choice(user_names)
        user_id = f"user_{hash(user_name) % 1000:04d}"

        # 生成订单项
        num_items = random.randint(1, 4)
        items = []
        total_amount = 0.0
        for j in range(num_items):
            product_id = random.randint(1, 200)
            product_name = f"商品{product_id} - {random.choice(['旗舰款', '标准版', '豪华套装'])}"
            price = round(random.uniform(29, 3999), 2)
            quantity = random.randint(1, 3)
            subtotal = round(price * quantity, 2)
            total_amount += subtotal
            items.append({
                "product_id": product_id,
                "product_name": product_name,
                "product_image": f"https://picsum.photos/seed/product{product_id}/100/100",
                "specs": random.choice(["黑色 标准款", "白色 高配版", "蓝色 标准版"]),
                "price": price,
                "quantity": quantity,
                "subtotal": subtotal,
            })

        discount = round(total_amount * random.uniform(0, 0.15), 2)
        shipping_fee = 0.0 if total_amount > 99 else 8.0
        pay_amount = round(total_amount - discount + shipping_fee, 2)

        pay_time = None
        ship_time = None
        deliver_time = None
        logistics_company = None
        logistics_no = None

        if status in ["paid", "shipped", "delivered", "completed", "refunded", "refunding"]:
            pay_time = (created + timedelta(hours=random.randint(1, 24))).strftime("%Y-%m-%d %H:%M:%S")
        if status in ["shipped", "delivered", "completed", "refunded"]:
            ship_time = (created + timedelta(days=random.randint(1, 3))).strftime("%Y-%m-%d %H:%M:%S")
            logistics_company = random.choice(logistics_companies)
            logistics_no = f"SF{random.randint(100000000000, 999999999999)}"
        if status in ["delivered", "completed", "refunded"]:
            deliver_time = (created + timedelta(days=random.randint(3, 7))).strftime("%Y-%m-%d %H:%M:%S")

        order = {
            "id": order_id,
            "order_no": f"ORD{created.strftime('%Y%m%d')}{order_id:06d}",
            "user_id": user_id,
            "user_name": user_name,
            "status": status,
            "total_amount": round(total_amount, 2),
            "discount_amount": discount,
            "pay_amount": pay_amount,
            "shipping_fee": shipping_fee,
            "receiver_name": user_name,
            "receiver_phone": f"138{random.randint(10000000, 99999999)}",
            "receiver_address": random.choice(provinces) + f"某某街道{random.randint(1, 999)}号",
            "logistics_company": logistics_company,
            "logistics_no": logistics_no,
            "pay_time": pay_time,
            "ship_time": ship_time,
            "deliver_time": deliver_time,
            "remark": random.choice(["", "请尽快发货", "放快递柜", "工作日送达"]),
            "items": items,
        }
        orders.append(order)

    return orders


def main():
    """生成所有模拟数据"""
    print("正在生成商品数据...")
    products = generate_products(220)
    products_path = DATA_DIR / "products.json"
    with open(products_path, "w", encoding="utf-8") as f:
        json.dump(products, f, ensure_ascii=False, indent=2)
    print(f"  生成 {len(products)} 个商品 -> {products_path}")

    print("正在生成订单数据...")
    orders = generate_orders(55)
    orders_path = DATA_DIR / "orders.json"
    with open(orders_path, "w", encoding="utf-8") as f:
        json.dump(orders, f, ensure_ascii=False, indent=2)
    print(f"  生成 {len(orders)} 个订单 -> {orders_path}")

    print("\n模拟数据生成完成！")


if __name__ == "__main__":
    main()
