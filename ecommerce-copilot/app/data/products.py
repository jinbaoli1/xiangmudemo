"""
商品模拟数据 - 生成200+ SKU
覆盖10个分类，每个分类20+商品
"""
from __future__ import annotations

import random
from typing import List
from ..models.product import Product, ProductCategory

# 商品模板数据
_PRODUCT_TEMPLATES = {
    ProductCategory.ELECTRONICS: [
        {"name": "无线蓝牙耳机", "brands": ["苹果", "华为", "小米", "索尼", "Bose"],
         "descriptions": ["高品质音效，长续航，主动降噪", "入耳式设计，舒适佩戴", "低延迟游戏模式"]},
        {"name": "智能手机", "brands": ["苹果", "华为", "小米", "OPPO", "vivo", "三星"],
         "descriptions": ["旗舰级处理器，超清拍照", "大电池长续航，快充技术", "曲面屏设计，轻薄机身"]},
        {"name": "笔记本电脑", "brands": ["苹果", "联想", "华为", "戴尔", "惠普"],
         "descriptions": ["轻薄便携，商务办公首选", "高性能游戏本，独立显卡", "2K超清屏幕，创作利器"]},
        {"name": "平板电脑", "brands": ["苹果", "华为", "小米", "三星"],
         "descriptions": ["大屏娱乐，学习办公两不误", "支持手写笔，绘画笔记", "轻薄机身，持久续航"]},
        {"name": "智能手表", "brands": ["苹果", "华为", "小米", "三星", "Amazfit"],
         "descriptions": ["健康监测，运动追踪", "独立通话，消息提醒", "长续航，多种表盘"]},
        {"name": "无线充电器", "brands": ["小米", "华为", "绿联", "Anker", "倍思"],
         "descriptions": ["快充无线充电板", "立式无线充，边充边看", "车载无线充电器"]},
        {"name": "移动电源", "brands": ["小米", "Anker", "绿联", "品胜", "倍思"],
         "descriptions": ["大容量双向快充", "轻薄便携，自带线", "数显电量，多口输出"]},
        {"name": "蓝牙音箱", "brands": ["索尼", "JBL", "Bose", "小米", "华为"],
         "descriptions": ["便携防水，户外必备", "360度环绕立体声", "重低音，长续航"]},
    ],
    ProductCategory.CLOTHING: [
        {"name": "纯棉T恤", "brands": ["优衣库", "耐克", "阿迪达斯", "李宁", "安踏"],
         "descriptions": ["舒适透气，经典百搭", "纯棉材质，亲肤柔软", "多色可选，简约设计"]},
        {"name": "牛仔裤", "brands": ["李维斯", "Lee", "优衣库", "ZARA", "H&M"],
         "descriptions": ["经典直筒，修身显瘦", "弹力面料，舒适自在", "复古水洗，时尚百搭"]},
        {"name": "运动卫衣", "brands": ["耐克", "阿迪达斯", "李宁", "安踏", "彪马"],
         "descriptions": ["加绒保暖，秋冬必备", "宽松版型，舒适自在", "时尚印花，运动休闲"]},
        {"name": "羽绒服", "brands": ["波司登", "加拿大鹅", "北面", "哥伦比亚", "优衣库"],
         "descriptions": ["90%白鸭绒，超强保暖", "轻薄款，便携收纳", "长款过膝，极寒必备"]},
        {"name": "连衣裙", "brands": ["ZARA", "H&M", "优衣库", "ONLY", "Vero Moda"],
         "descriptions": ["优雅气质，通勤必备", "碎花设计，清新甜美", "修身显瘦，约会首选"]},
        {"name": "休闲运动鞋", "brands": ["耐克", "阿迪达斯", "李宁", "安踏", "New Balance"],
         "descriptions": ["缓震舒适，日常通勤", "复古百搭，时尚出街", "透气网面，轻便跑步"]},
    ],
    ProductCategory.HOME_APPLIANCES: [
        {"name": "空气炸锅", "brands": ["飞利浦", "九阳", "美的", "苏泊尔", "小熊"],
         "descriptions": ["无油健康，大容量", "智能触控，多功能菜单", "可视窗口，实时查看"]},
        {"name": "电饭煲", "brands": ["美的", "苏泊尔", "九阳", "松下", "象印"],
         "descriptions": ["IH电磁加热，柴火饭口感", "智能预约，多功能菜单", "小容量1-2人用"]},
        {"name": "扫地机器人", "brands": ["科沃斯", "石头", "小米", "追觅", "云鲸"],
         "descriptions": ["激光导航，智能规划", "扫拖一体，解放双手", "自动集尘，省心省力"]},
        {"name": "加湿器", "brands": ["小米", "美的", "飞利浦", "戴森", "亚都"],
         "descriptions": ["大容量，静音设计", "智能恒湿，除菌净化", "小型桌面，办公必备"]},
        {"name": "微波炉", "brands": ["美的", "格兰仕", "松下", "海尔", "三洋"],
         "descriptions": ["智能变频，均匀加热", "光波烧烤，一机多用", "小型迷你，租房必备"]},
        {"name": "电热水器", "brands": ["美的", "海尔", "A.O.史密斯", "万和", "万家乐"],
         "descriptions": ["储水式大容量", "即热式，恒温出水", "一级能效，安全防电墙"]},
    ],
    ProductCategory.BOOKS: [
        {"name": "小说", "brands": ["人民文学", "上海译文", "中信出版", "新经典", "磨铁"],
         "descriptions": ["畅销文学作品", "经典名著收藏版", "悬疑推理小说"]},
        {"name": "编程技术书", "brands": ["机械工业", "人民邮电", "电子工业", "O'Reilly", "图灵"],
         "descriptions": ["Python编程从入门到实践", "算法导论经典教材", "人工智能深度学习"]},
        {"name": "经济管理", "brands": ["中信出版", "机械工业", "湛庐文化", "读客", "后浪"],
         "descriptions": ["经济学原理入门", "企业管理经典", "投资理财指南"]},
        {"name": "历史读物", "brands": ["中华书局", "商务印书馆", "中信出版", "理想国", "后浪"],
         "descriptions": ["中国通史", "世界历史", "历史人物传记"]},
        {"name": "儿童绘本", "brands": ["信谊", "蒲蒲兰", "爱心树", "启发", "乐乐趣"],
         "descriptions": ["3-6岁启蒙绘本", "亲子共读经典", "立体书翻翻书"]},
    ],
    ProductCategory.FOOD: [
        {"name": "坚果礼盒", "brands": ["三只松鼠", "良品铺子", "百草味", "沃隆", "洽洽"],
         "descriptions": ["每日坚果混合装", "节日送礼礼盒", "健康零食大礼包"]},
        {"name": "速食面", "brands": ["康师傅", "统一", "白象", "今麦郎", "日清"],
         "descriptions": ["经典红烧牛肉味", "日式豚骨拉面", "非油炸更健康"]},
        {"name": "咖啡", "brands": ["雀巢", "星巴克", "三顿半", "瑞幸", "隅田川"],
         "descriptions": ["速溶黑咖啡粉", "挂耳咖啡现磨风味", "胶囊咖啡多口味"]},
        {"name": "牛奶", "brands": ["蒙牛", "伊利", "特仑苏", "金典", "德亚"],
         "descriptions": ["纯牛奶全脂高钙", "酸奶常温原味", "低脂高钙奶"]},
        {"name": "巧克力", "brands": ["德芙", "费列罗", "好时", "瑞士莲", "歌帝梵"],
         "descriptions": ["牛奶巧克力丝滑", "黑巧克力70%可可", "礼盒装送礼首选"]},
    ],
    ProductCategory.BEAUTY: [
        {"name": "精华液", "brands": ["兰蔻", "雅诗兰黛", "SK-II", "资生堂", "欧莱雅"],
         "descriptions": ["抗老精华视黄醇", "美白精华烟酰胺", "补水精华玻尿酸"]},
        {"name": "面膜", "brands": ["敷尔佳", "可复美", "蒂佳婷", "JMsolution", "自然堂"],
         "descriptions": ["补水面膜玻尿酸", "修护面膜舒缓", "美白提亮面膜"]},
        {"name": "口红", "brands": ["迪奥", "香奈儿", "MAC", "YSL", "花西子"],
         "descriptions": ["哑光雾面丝绒", "滋润保湿显白", "国风限量版"]},
        {"name": "防晒霜", "brands": ["安耐晒", "兰蔻", "雅漾", "理肤泉", "怡思丁"],
         "descriptions": ["清爽不油腻SPF50+", "物理防晒敏感肌", "面部专用隔离"]},
        {"name": "洁面乳", "brands": ["芙丽芳丝", "EltaMD", "珂润", "旁氏", "至本"],
         "descriptions": ["氨基酸温和洁面", "深层清洁控油", "敏感肌专用"]},
    ],
    ProductCategory.SPORTS: [
        {"name": "瑜伽垫", "brands": ["Keep", "奥义", "TPE", "青鸟", "悦步"],
         "descriptions": ["TPE环保材质防滑", "加厚15mm舒适", "便携折叠旅行款"]},
        {"name": "跑步鞋", "brands": ["耐克", "阿迪达斯", "亚瑟士", "索康尼", "布鲁克斯"],
         "descriptions": ["缓震跑鞋长距离", "竞速碳板鞋", "稳定支撑跑鞋"]},
        {"name": "哑铃", "brands": ["Keep", "迪卡侬", "斯诺德", "舒华", "乔山"],
         "descriptions": ["可调节重量哑铃", "包胶静音哑铃", "哑铃凳套装"]},
        {"name": "运动水壶", "brands": ["膳魔师", "象印", "Keep", "迪卡侬", "驼峰"],
         "descriptions": ["大容量运动水杯", "保温保冷不锈钢", "吸管式健身水壶"]},
        {"name": "健身手套", "brands": ["Keep", "迪卡侬", "李宁", "安踏", "Under Armour"],
         "descriptions": ["半指健身护腕", "防滑透气耐磨", "骑行运动手套"]},
    ],
    ProductCategory.TOYS: [
        {"name": "积木玩具", "brands": ["乐高", "小米", "邦宝", "启蒙", "奥迪双钻"],
         "descriptions": ["城市系列拼装", "科技组机械组", "儿童大颗粒积木"]},
        {"name": "毛绒玩具", "brands": ["迪士尼", "LINE FRIENDS", "Jellycat", "名创优品", "伶俐宝"],
         "descriptions": ["可爱公仔抱枕", "安抚玩偶婴儿", "仿真动物毛绒"]},
        {"name": "益智玩具", "brands": ["费雪", "伟易达", "澳贝", "Hape", "巧虎"],
         "descriptions": ["儿童早教益智", "拼图积木3-6岁", "逻辑思维训练"]},
        {"name": "遥控玩具", "brands": ["大疆", "小米", "司马", "伟力", "双鹰"],
         "descriptions": ["遥控汽车越野车", "无人机航拍", "遥控船水上玩具"]},
    ],
    ProductCategory.FURNITURE: [
        {"name": "办公椅", "brands": ["西昊", "网易严选", "赫曼米勒", "保友", "黑白调"],
         "descriptions": ["人体工学电脑椅", "电竞椅游戏座椅", "简约办公椅弓形"]},
        {"name": "书桌", "brands": ["宜家", "网易严选", "源氏木语", "原始原素", "林氏木业"],
         "descriptions": ["实木书桌简约", "升降桌站立办公", "电脑桌台式家用"]},
        {"name": "收纳柜", "brands": ["宜家", "无印良品", "爱丽思", "禧天龙", "也雅"],
         "descriptions": ["抽屉式收纳柜", "厨房置物架", "衣柜收纳分层"]},
        {"name": "沙发", "brands": ["宜家", "林氏木业", "全友", "顾家家居", "芝华仕"],
         "descriptions": ["布艺沙发小户型", "真皮沙发客厅", "功能沙发可躺"]},
    ],
    ProductCategory.STATIONERY: [
        {"name": "中性笔", "brands": ["晨光", "得力", "百乐", "斑马", "三菱"],
         "descriptions": ["按动中性笔0.5mm", "速干签字笔", "直液式走珠笔"]},
        {"name": "笔记本", "brands": ["晨光", "得力", "Moleskine", "无印良品", "国誉"],
         "descriptions": ["A5皮面商务笔记本", "线圈本活页本", "手账本礼盒装"]},
        {"name": "书包", "brands": ["晨光", "得力", "卡拉羊", "北极狐", "JanSport"],
         "descriptions": ["小学生书包减负", "双肩包电脑背包", "旅行包大容量"]},
        {"name": "文件收纳", "brands": ["得力", "晨光", "齐心", "广博", "真彩"],
         "descriptions": ["文件夹资料册", "文件架桌面收纳", "档案盒文件盒"]},
    ],
}

# 价格范围 (min, max)
_PRICE_RANGES = {
    ProductCategory.ELECTRONICS: (99, 9999),
    ProductCategory.CLOTHING: (39, 2999),
    ProductCategory.HOME_APPLIANCES: (59, 5999),
    ProductCategory.BOOKS: (19, 199),
    ProductCategory.FOOD: (9, 299),
    ProductCategory.BEAUTY: (29, 2999),
    ProductCategory.SPORTS: (29, 1999),
    ProductCategory.TOYS: (19, 1999),
    ProductCategory.FURNITURE: (99, 9999),
    ProductCategory.STATIONERY: (5, 299),
}

# 标签池
_TAG_POOLS = {
    ProductCategory.ELECTRONICS: ["新品", "热销", "爆款", "限时特惠", "官方正品", "全国联保", "顺丰包邮", "支持分期"],
    ProductCategory.CLOTHING: ["新品上市", "热销爆款", "限时折扣", "包邮", "多色可选", "纯棉", "加绒", "显瘦"],
    ProductCategory.HOME_APPLIANCES: ["正品保障", "全国联保", "上门安装", "以旧换新", "一级能效", "智能", "静音"],
    ProductCategory.BOOKS: ["正版包邮", "新书上架", "畅销榜", "精装版", "限量签名", "套装优惠"],
    ProductCategory.FOOD: ["新鲜日期", "包邮", "买二送一", "礼盒装", "进口", "健康零食", "节日特惠"],
    ProductCategory.BEAUTY: ["正品保障", "买一送一", "赠小样", "包邮", "敏感肌可用", "官方旗舰店", "限时特惠"],
    ProductCategory.SPORTS: ["运动必备", "专业级", "轻便舒适", "透气", "耐磨", "健身", "户外"],
    ProductCategory.TOYS: ["益智", "安全无毒", "3岁以上", "6岁以上", "生日礼物", "亲子互动", "动手能力"],
    ProductCategory.FURNITURE: ["包安装", "送货上门", "实木", "环保材质", "五年质保", "简约现代", "可定制"],
    ProductCategory.STATIONERY: ["学习必备", "办公文具", "学生用品", "实惠装", "盒装", "顺滑书写", "不断墨"],
}

_products_cache: List[Product] = []


def generate_products(seed: int = 42) -> List[Product]:
    """生成200+商品SKU"""
    global _products_cache
    if _products_cache:
        return _products_cache

    random.seed(seed)
    products = []
    sku_counter = 1

    for category, templates in _PRODUCT_TEMPLATES.items():
        price_min, price_max = _PRICE_RANGES[category]
        tags_pool = _TAG_POOLS[category]

        for template in templates:
            for brand in template["brands"]:
                # 每个品牌生成2-3个变体
                variants = random.randint(2, 3)
                for variant in range(variants):
                    desc = random.choice(template["descriptions"])
                    price = round(random.uniform(price_min, price_max), 2)
                    # 30%概率有原价
                    original_price = None
                    if random.random() < 0.3:
                        original_price = round(price * random.uniform(1.2, 2.0), 2)

                    # 生成标签
                    num_tags = random.randint(2, 5)
                    tags = random.sample(tags_pool, min(num_tags, len(tags_pool)))

                    # 生成属性
                    attributes = _generate_attributes(category, brand, template["name"])

                    sku_id = f"SKU{sku_counter:05d}"
                    product_name = f"{brand} {template['name']}"
                    if variant > 0:
                        product_name += f" {variant + 1}代" if random.random() < 0.5 else f" {'升级版' if variant == 1 else '旗舰版'}"

                    product = Product(
                        sku_id=sku_id,
                        name=product_name,
                        description=desc,
                        category=category,
                        price=price,
                        original_price=original_price,
                        brand=brand,
                        stock=random.randint(0, 500),
                        sales_volume=random.randint(10, 50000),
                        rating=round(random.uniform(3.5, 5.0), 1),
                        review_count=random.randint(5, 10000),
                        tags=tags,
                        images=[f"https://example.com/images/{sku_id}_1.jpg"],
                        attributes=attributes,
                        is_on_sale=random.random() > 0.05,  # 5%下架
                    )
                    products.append(product)
                    sku_counter += 1

    _products_cache = products
    return products


def _generate_attributes(category: ProductCategory, brand: str, name: str) -> dict:
    """生成商品属性"""
    attrs = {"品牌": brand}

    if category == ProductCategory.ELECTRONICS:
        attrs.update({
            "颜色": random.choice(["黑色", "白色", "银色", "蓝色", "粉色"]),
            "质保期": random.choice(["1年", "2年", "3年"]),
            "产地": random.choice(["中国大陆", "日本", "越南", "马来西亚"]),
        })
        if "耳机" in name:
            attrs.update({"续航时间": f"{random.randint(8, 40)}小时", "蓝牙版本": f"{random.choice(['5.0', '5.1', '5.2', '5.3'])}"})
        elif "手机" in name:
            attrs.update({"存储容量": random.choice(["128GB", "256GB", "512GB", "1TB"]), "屏幕尺寸": f'{random.choice(["6.1", "6.5", "6.7"])}英寸'})
    elif category == ProductCategory.CLOTHING:
        attrs.update({
            "尺码": random.choice(["S", "M", "L", "XL", "XXL"]),
            "颜色": random.choice(["黑色", "白色", "灰色", "蓝色", "红色"]),
            "材质": random.choice(["纯棉", "涤纶", "混纺", "羊毛"]),
        })
    elif category == ProductCategory.HOME_APPLIANCES:
        attrs.update({
            "容量": random.choice(["1L", "2L", "3L", "5L", "10L"]),
            "功率": f"{random.randint(100, 2000)}W",
            "质保期": random.choice(["1年", "2年", "3年"]),
        })
    elif category == ProductCategory.BOOKS:
        attrs.update({
            "作者": random.choice(["张三", "李四", "王五", "佚名"]),
            "出版社": brand,
            "页数": f"{random.randint(100, 800)}页",
            "出版日期": f"202{random.randint(0,3)}年",
        })
    elif category == ProductCategory.FOOD:
        attrs.update({
            "净含量": random.choice(["250g", "500g", "1kg", "2kg"]),
            "保质期": random.choice(["6个月", "12个月", "18个月"]),
            "产地": random.choice(["中国大陆", "日本", "韩国", "美国", "欧洲"]),
        })
    elif category == ProductCategory.BEAUTY:
        attrs.update({
            "规格": random.choice(["30ml", "50ml", "100ml", "150ml"]),
            "适用肤质": random.choice(["所有肤质", "干性", "油性", "混合性", "敏感肌"]),
            "产地": random.choice(["法国", "日本", "美国", "韩国", "中国"]),
        })
    else:
        attrs.update({
            "材质": random.choice(["塑料", "金属", "木质", "布料", "硅胶"]),
            "颜色": random.choice(["黑色", "白色", "灰色", "蓝色", "粉色"]),
        })

    return attrs


def get_all_products() -> List[Product]:
    """获取所有商品"""
    return generate_products()


if __name__ == "__main__":
    products = generate_products()
    print(f"生成商品数量: {len(products)}")
    print(f"分类分布:")
    from collections import Counter
    categories = Counter(p.category.value for p in products)
    for cat, count in categories.items():
        print(f"  {cat}: {count}")
