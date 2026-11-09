"""
政策文档数据 - 包含退货政策、配送政策、支付政策等
"""
from __future__ import annotations

from datetime import datetime
from typing import List
from ..models.policy import PolicyDocument, PolicyChunk


def get_policy_documents() -> List[PolicyDocument]:
    """获取所有政策文档"""
    now = datetime.now()
    docs = [
        PolicyDocument(
            doc_id="POL_001",
            title="七天无理由退货政策",
            category="after_sale",
            content="""
# 七天无理由退货政策

## 一、政策概述
本平台承诺自商品签收之日起7天内，符合条件的商品可申请无理由退货退款。

## 二、适用范围
1. 除特殊商品外，所有在售商品均支持七天无理由退货
2. 特殊商品包括：定制类商品、鲜活易腐商品、数字化商品、贴身用品等

## 三、申请条件
1. 商品完好，不影响二次销售
2. 商品包装、配件、吊牌等完整
3. 在签收后7天内提交申请

## 四、退货运费
1. 因个人原因退货，运费由买家承担
2. 因质量问题退货，运费由平台承担
3. 购买运费险的订单，按保险条款理赔

## 五、退款说明
1. 退款金额按实付金额计算
2. 优惠券、积分等不予退还
3. 退款到账时间：1-7个工作日

## 六、特殊说明
- 套装商品需整体退货，不可部分退货
- 赠品需一并退回，否则按赠品价格扣款
- 如商品已使用或损坏，将影响退款金额
            """.strip(),
            version="2.0",
            effective_date=now,
            is_active=True,
            tags=["退货", "无理由", "7天", "售后"],
            priority=10,
        ),
        PolicyDocument(
            doc_id="POL_002",
            title="质量问题退换货政策",
            category="after_sale",
            content="""
# 质量问题退换货政策

## 一、政策概述
因商品质量问题导致的退换货，平台承担往返运费，并优先处理。

## 二、质量问题认定
1. 商品存在功能故障或缺陷
2. 商品与描述严重不符
3. 商品收到时已损坏
4. 商品为假冒伪劣产品

## 三、申请时限
1. 签收后30天内可申请质量问题退货
2. 签收后15天内可申请质量问题换货
3. 保修期内可申请维修服务

## 四、申请流程
1. 提交售后申请，选择质量问题原因
2. 上传商品问题照片或视频凭证
3. 客服审核（通常24小时内）
4. 审核通过后安排退货或换货
5. 收到退回商品后发出新品或退款

## 五、运费承担
1. 质量问题退货运费由平台承担
2. 用户先行垫付运费，退款时一并返还
3. 运费险理赔金额与实际运费差额由平台补足

## 六、注意事项
- 请保留商品原包装以便退换
- 人为损坏不在保修范围内
- 不可抗力造成的损坏不予保修
            """.strip(),
            version="1.5",
            effective_date=now,
            is_active=True,
            tags=["质量问题", "换货", "退货", "保修"],
            priority=9,
        ),
        PolicyDocument(
            doc_id="POL_003",
            title="配送与物流政策",
            category="delivery",
            content="""
# 配送与物流政策

## 一、配送范围
1. 中国大陆地区全部支持配送
2. 港澳台及海外地区暂不支持
3. 偏远地区可能延长配送时间

## 二、配送时效
1. 普通快递：3-5个工作日
2. 顺丰速运：1-2个工作日
3. 同城配送：当日达（限部分城市）
4. 预售商品：按页面标注时间发货

## 三、发货时间
1. 工作日16:00前付款，当日发货
2. 16:00后付款，次日发货
3. 周末及节假日顺延

## 四、运费标准
1. 订单满99元包邮
2. 未满99元收取10元运费
3. 偏远地区加收5-15元
4. 特殊商品运费单独计算

## 五、物流跟踪
1. 发货后可在订单详情中查看物流信息
2. 物流信息可能有6-12小时延迟
3. 如超过5天未收到，请联系客服

## 六、签收说明
1. 请当面验货，确认无误后签收
2. 如发现破损，可拒收并联系客服
3. 代收点签收视为本人签收
            """.strip(),
            version="1.2",
            effective_date=now,
            is_active=True,
            tags=["配送", "物流", "运费", "发货", "快递"],
            priority=8,
        ),
        PolicyDocument(
            doc_id="POL_004",
            title="支付与退款政策",
            category="payment",
            content="""
# 支付与退款政策

## 一、支持的支付方式
1. 微信支付
2. 支付宝
3. 银行卡支付
4. 花呗分期
5. 平台余额

## 二、支付安全
1. 所有支付均通过加密通道传输
2. 平台不保存用户银行卡信息
3. 支持指纹支付和面容支付

## 三、退款政策
1. 退款原路退回至支付账户
2. 退款到账时间：
   - 微信/支付宝：1-3个工作日
   - 银行卡：3-7个工作日
   - 花呗：1-10个工作日
3. 退款金额为实付金额，不含优惠券

## 四、部分退款
1. 订单支持部分商品退款
2. 部分退款后订单金额仍满包邮条件的，不扣运费
3. 部分退款后不满包邮条件的，按比例扣除运费

## 五、退款失败处理
1. 如退款失败，请检查账户状态
2. 银行卡过期或注销的，请联系客服处理
3. 退款失败后会重新发起
            """.strip(),
            version="1.3",
            effective_date=now,
            is_active=True,
            tags=["支付", "退款", "微信", "支付宝", "银行卡"],
            priority=7,
        ),
        PolicyDocument(
            doc_id="POL_005",
            title="会员与积分政策",
            category="membership",
            content="""
# 会员与积分政策

## 一、会员等级
1. 普通会员：注册即可成为
2. 白银会员：累计消费满500元
3. 黄金会员：累计消费满2000元
4. 铂金会员：累计消费满5000元
5. 钻石会员：累计消费满10000元

## 二、会员权益
1. 普通会员：生日礼包、积分翻倍日
2. 白银会员：9.5折优惠、优先客服
3. 黄金会员：9折优惠、免费退换货、专属客服
4. 铂金会员：8.5折优惠、极速售后、专属顾问
5. 钻石会员：8折优惠、专属特权、VIP通道

## 三、积分获取
1. 消费1元积1分
2. 评价晒单奖励50积分
3. 每日签到奖励5-20积分
4. 邀请好友奖励100积分

## 四、积分使用
1. 100积分抵扣1元
2. 单笔订单最高抵扣50%
3. 积分可兑换优惠券
4. 积分可兑换实物礼品

## 五、积分有效期
1. 积分有效期为获得之日起12个月
2. 过期积分自动清零
3. 会员等级按近12个月消费计算
            """.strip(),
            version="2.1",
            effective_date=now,
            is_active=True,
            tags=["会员", "积分", "VIP", "等级", "权益"],
            priority=6,
        ),
        PolicyDocument(
            doc_id="POL_006",
            title="发票开具政策",
            category="invoice",
            content="""
# 发票开具政策

## 一、发票类型
1. 增值税普通电子发票
2. 增值税专用发票（需企业资质）

## 二、申请方式
1. 下单时勾选需要发票
2. 订单完成后在订单详情中申请
3. 联系客服申请补开发票

## 三、发票内容
1. 默认开具商品明细
2. 可选择开具大类（如办公用品、礼品等）
3. 发票金额为实付金额

## 四、开具时间
1. 电子发票：订单完成后1-3个工作日
2. 纸质发票：申请后5-7个工作日寄出
3. 专用发票：申请后7-10个工作日

## 五、注意事项
1. 订单发生退款的，需退回已开发票
2. 发票抬头不可修改，请仔细核对
3. 跨年度发票不可重开
            """.strip(),
            version="1.0",
            effective_date=now,
            is_active=True,
            tags=["发票", "电子发票", "增值税", "报销"],
            priority=5,
        ),
        PolicyDocument(
            doc_id="POL_007",
            title="隐私保护政策",
            category="privacy",
            content="""
# 隐私保护政策

## 一、信息收集
1. 注册信息：手机号、昵称
2. 订单信息：收货地址、联系人、电话
3. 支付信息：支付方式、交易记录
4. 设备信息：设备型号、操作系统

## 二、信息使用
1. 用于完成订单配送和售后服务
2. 用于发送订单状态通知
3. 用于优化服务和用户体验
4. 用于安全风控和反欺诈

## 三、信息保护
1. 采用加密技术存储敏感信息
2. 严格的内部权限管理
3. 定期安全审计和漏洞扫描
4. 不向第三方出售用户信息

## 四、信息共享
1. 仅在必要时与合作伙伴共享
2. 合作伙伴需签署保密协议
3. 法律要求时配合提供信息

## 五、用户权利
1. 可查看和修改个人信息
2. 可注销账户删除个人信息
3. 可撤回授权同意
4. 可投诉和举报隐私问题
            """.strip(),
            version="1.0",
            effective_date=now,
            is_active=True,
            tags=["隐私", "个人信息", "数据保护", "安全"],
            priority=4,
        ),
    ]
    return docs


def get_policy_chunks() -> List[PolicyChunk]:
    """获取政策文档切片（用于检索）"""
    docs = get_policy_documents()
    chunks = []
    chunk_index = 0

    for doc in docs:
        # 按二级标题切片
        lines = doc.content.split("\n")
        current_section = ""
        current_content = []
        section_path = doc.title

        for line in lines:
            line = line.strip()
            if line.startswith("## "):
                # 保存上一段
                if current_content:
                    chunk_id = f"CHUNK_{chunk_index:04d}"
                    chunks.append(PolicyChunk(
                        chunk_id=chunk_id,
                        doc_id=doc.doc_id,
                        doc_title=doc.title,
                        content="\n".join(current_content),
                        chunk_index=chunk_index,
                        section_path=f"{doc.title} > {current_section}",
                        tags=doc.tags,
                        metadata={"version": doc.version, "category": doc.category},
                    ))
                    chunk_index += 1
                current_section = line.replace("## ", "")
                current_content = [line]
            elif line.startswith("# "):
                if current_content:
                    chunk_id = f"CHUNK_{chunk_index:04d}"
                    chunks.append(PolicyChunk(
                        chunk_id=chunk_id,
                        doc_id=doc.doc_id,
                        doc_title=doc.title,
                        content="\n".join(current_content),
                        chunk_index=chunk_index,
                        section_path=section_path,
                        tags=doc.tags,
                        metadata={"version": doc.version, "category": doc.category},
                    ))
                    chunk_index += 1
                current_section = line.replace("# ", "")
                current_content = [line]
            elif line:
                current_content.append(line)

        # 保存最后一段
        if current_content:
            chunk_id = f"CHUNK_{chunk_index:04d}"
            chunks.append(PolicyChunk(
                chunk_id=chunk_id,
                doc_id=doc.doc_id,
                doc_title=doc.title,
                content="\n".join(current_content),
                chunk_index=chunk_index,
                section_path=f"{doc.title} > {current_section}" if current_section else doc.title,
                tags=doc.tags,
                metadata={"version": doc.version, "category": doc.category},
            ))
            chunk_index += 1

    return chunks
