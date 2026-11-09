"""药品模拟数据 - 500+药品."""
import random

# 药品分类和基础信息
MEDICATION_CATEGORIES = [
    # 抗生素类
    {"category": "青霉素类抗生素", "prefixes": ["青霉素", "氨苄", "阿莫", "哌拉", "美洛"],
     "suffixes": ["西林", "西林钠", "西林钾"],
     "indication": "用于敏感菌引起的呼吸道、泌尿道、皮肤软组织等感染",
     "side_effects": "过敏反应、皮疹、恶心、腹泻",
     "contraindications": "对青霉素类药物过敏者禁用",
     "interactions": "与丙磺舒合用可延长半衰期",
     "pregnancy_warning": True, "controlled": False},
    {"category": "头孢菌素类", "prefixes": ["头孢", "头孢呋", "头孢克", "头孢地", "头孢吡", "头孢他", "头孢曲", "头孢哌"],
     "suffixes": ["肟", "酯", "辛", "尼", "啶", "酮", "松", "钠"],
     "indication": "用于敏感菌所致的呼吸道、泌尿道、胆道等感染",
     "side_effects": "皮疹、瘙痒、恶心、腹泻、静脉炎",
     "contraindications": "对头孢菌素类过敏者禁用",
     "interactions": "与氨基糖苷类合用有协同抗菌作用",
     "pregnancy_warning": False, "controlled": False},
    {"category": "喹诺酮类抗生素", "prefixes": ["左氧氟", "环丙", "莫西", "诺氟", "氧氟", "培氟"],
     "suffixes": ["沙星", "沙星片", "沙星胶囊"],
     "indication": "用于敏感菌引起的呼吸道、泌尿道、消化道感染",
     "side_effects": "胃肠道反应、头晕、皮疹、肌腱炎",
     "contraindications": "18岁以下患者禁用、孕妇禁用",
     "interactions": "与含金属离子药物合用减少吸收",
     "pregnancy_warning": True, "controlled": False},
    {"category": "大环内酯类", "prefixes": ["阿奇", "罗红", "克拉", "红", "乙酰螺旋"],
     "suffixes": ["霉素", "霉素片", "霉素胶囊"],
     "indication": "用于支原体、衣原体及敏感菌感染",
     "side_effects": "胃肠道反应、肝功能异常、皮疹",
     "contraindications": "对大环内酯类过敏者禁用",
     "interactions": "可抑制茶碱代谢，增加茶碱血药浓度",
     "pregnancy_warning": False, "controlled": False},
    # 心血管药物
    {"category": "ACEI类降压药", "prefixes": ["卡托", "依那", "贝那", "赖诺", "雷米", "培哚"],
     "suffixes": ["普利", "普利片"],
     "indication": "用于高血压、心力衰竭、心肌梗死后",
     "side_effects": "干咳、低血压、皮疹、血钾升高",
     "contraindications": "双侧肾动脉狭窄、高钾血症、妊娠",
     "interactions": "与利尿剂合用增强降压效果",
     "pregnancy_warning": True, "controlled": False},
    {"category": "ARB类降压药", "prefixes": ["氯沙", "缬沙", "厄贝", "替米", "奥美", "坎地"],
     "suffixes": ["坦", "坦片", "沙坦胶囊"],
     "indication": "用于高血压、心力衰竭、糖尿病肾病",
     "side_effects": "头晕、低血压、血钾升高",
     "contraindications": "双侧肾动脉狭窄、高钾血症、妊娠",
     "interactions": "与利尿剂合用增强降压效果",
     "pregnancy_warning": True, "controlled": False},
    {"category": "钙通道阻滞剂", "prefixes": ["硝苯", "氨氯", "左旋氨氯", "非洛", "拉西", "尼莫"],
     "suffixes": ["地平", "地平片", "地平缓释片"],
     "indication": "用于高血压、冠心病心绞痛",
     "side_effects": "头痛、面部潮红、下肢水肿、心悸",
     "contraindications": "严重低血压、心源性休克",
     "interactions": "与β受体阻滞剂合用可能增加心动过缓风险",
     "pregnancy_warning": False, "controlled": False},
    {"category": "β受体阻滞剂", "prefixes": ["美托", "比索", "阿替", "普萘", "卡维", "拉贝"],
     "suffixes": ["洛尔", "洛尔片"],
     "indication": "用于高血压、心绞痛、心律失常、心力衰竭",
     "side_effects": "心动过缓、乏力、支气管痉挛、血糖异常",
     "contraindications": "严重心动过缓、支气管哮喘、二度以上房室传导阻滞",
     "interactions": "与钙通道阻滞剂合用增加心动过缓风险",
     "pregnancy_warning": False, "controlled": False},
    {"category": "利尿剂", "prefixes": ["呋塞", "氢氯噻", "螺内", "吲达帕", "托拉塞", "布美他"],
     "suffixes": ["米", "嗪", "酯", "胺", "尼"],
     "indication": "用于水肿、高血压、心力衰竭",
     "side_effects": "电解质紊乱、脱水、尿酸升高",
     "contraindications": "无尿、严重电解质紊乱",
     "interactions": "与氨基糖苷类合用增加耳毒性",
     "pregnancy_warning": False, "controlled": False},
    {"category": "降脂药(他汀类)", "prefixes": ["阿托伐", "瑞舒伐", "辛伐", "普伐", "氟伐", "匹伐"],
     "suffixes": ["他汀", "他汀片", "他汀钙片"],
     "indication": "用于高胆固醇血症、冠心病二级预防",
     "side_effects": "肝功能异常、肌肉疼痛、胃肠道反应",
     "contraindications": "活动性肝病、严重肾功能不全",
     "interactions": "与贝特类合用增加肌病风险",
     "pregnancy_warning": True, "controlled": False},
    {"category": "抗血小板药", "prefixes": ["阿司匹", "氯吡", "替格瑞", "双嘧达"],
     "suffixes": ["林", "雷", "洛", "莫"],
     "indication": "用于心脑血管疾病的预防和治疗",
     "side_effects": "出血、胃肠道刺激、皮疹",
     "contraindications": "活动性出血、严重肝功能不全",
     "interactions": "与抗凝药合用增加出血风险",
     "pregnancy_warning": False, "controlled": False},
    # 消化系统药物
    {"category": "质子泵抑制剂", "prefixes": ["奥美拉", "兰索拉", "泮托拉", "雷贝拉", "埃索美拉"],
     "suffixes": ["唑", "唑肠溶胶囊", "唑肠溶片"],
     "indication": "用于胃溃疡、十二指肠溃疡、胃食管反流病",
     "side_effects": "头痛、腹泻、恶心、腹胀",
     "contraindications": "对本品过敏者禁用",
     "interactions": "可影响氯吡格雷的活化",
     "pregnancy_warning": False, "controlled": False},
    {"category": "H2受体拮抗剂", "prefixes": ["西咪替", "雷尼替", "法莫替", "尼扎替"],
     "suffixes": ["丁", "丁片", "丁胶囊"],
     "indication": "用于胃溃疡、十二指肠溃疡、胃食管反流病",
     "side_effects": "头痛、头晕、腹泻、男性乳房发育（西咪替丁）",
     "contraindications": "对本品过敏者禁用",
     "interactions": "西咪替丁可抑制肝药酶，影响多种药物代谢",
     "pregnancy_warning": False, "controlled": False},
    {"category": "胃黏膜保护剂", "prefixes": ["铝碳酸", "硫糖", "枸橼酸铋", "胶体果胶"],
     "suffixes": ["镁", "铝", "钾", "铋"],
     "indication": "用于胃炎、胃溃疡、十二指肠溃疡",
     "side_effects": "便秘、腹泻、黑便（铋剂）",
     "contraindications": "严重肾功能不全者禁用铋剂",
     "interactions": "可影响其他药物的吸收",
     "pregnancy_warning": False, "controlled": False},
    {"category": "促胃动力药", "prefixes": ["多潘立", "莫沙必", "伊托必", "甲氧氯普"],
     "suffixes": ["酮", "利", "胺"],
     "indication": "用于消化不良、腹胀、恶心、呕吐",
     "side_effects": "头晕、腹泻、锥体外系反应（甲氧氯普胺）",
     "contraindications": "胃肠道出血、肠梗阻",
     "interactions": "与抗胆碱药合用作用减弱",
     "pregnancy_warning": False, "controlled": False},
    {"category": "止泻药", "prefixes": ["蒙脱石", "洛哌丁", "地衣芽孢", "双歧三联"],
     "suffixes": ["散", "胺", "杆菌", "活菌"],
     "indication": "用于急慢性腹泻",
     "side_effects": "便秘、腹胀",
     "contraindications": "肠梗阻、便秘患者慎用",
     "interactions": "蒙脱石可影响其他药物吸收",
     "pregnancy_warning": False, "controlled": False},
    {"category": "泻药", "prefixes": ["乳果", "聚乙二醇", "番泻", "酚酞", "麻仁"],
     "suffixes": ["糖", "散", "叶", "丸"],
     "indication": "用于便秘",
     "side_effects": "腹泻、腹痛、腹胀、电解质紊乱",
     "contraindications": "肠梗阻、腹痛原因不明者",
     "interactions": "长期使用可导致电解质紊乱",
     "pregnancy_warning": False, "controlled": False},
    # 呼吸系统药物
    {"category": "支气管扩张剂", "prefixes": ["沙丁胺", "特布他", "异丙托溴", "噻托溴", "布地奈"],
     "suffixes": ["醇", "铵", "德"],
     "indication": "用于支气管哮喘、慢性阻塞性肺疾病",
     "side_effects": "心悸、手抖、头痛、口干",
     "contraindications": "对本品过敏者禁用",
     "interactions": "与β受体阻滞剂合用作用减弱",
     "pregnancy_warning": False, "controlled": False},
    {"category": "吸入糖皮质激素", "prefixes": ["布地奈", "氟替卡", "倍氯米", "糠酸莫米"],
     "suffixes": ["德", "松", "松吸入剂"],
     "indication": "用于支气管哮喘的长期控制",
     "side_effects": "口腔念珠菌感染、声音嘶哑、咽喉不适",
     "contraindications": "对本品过敏者禁用",
     "interactions": "与长效β2受体激动剂合用有协同作用",
     "pregnancy_warning": False, "controlled": False},
    {"category": "止咳化痰药", "prefixes": ["氨溴", "乙酰半胱", "羧甲司", "右美沙", "喷托维"],
     "suffixes": ["索", "氨酸", "坦", "芬", "林"],
     "indication": "用于咳嗽、咳痰不易咳出",
     "side_effects": "恶心、呕吐、腹泻、头晕",
     "contraindications": "对本品过敏者禁用",
     "interactions": "应避免与中枢性镇咳药同时使用",
     "pregnancy_warning": False, "controlled": False},
    # 内分泌药物
    {"category": "口服降糖药", "prefixes": ["二甲双", "格列本", "格列齐", "格列吡", "格列美", "阿卡波", "伏格列波", "瑞格列", "那格列", "吡格列", "罗格列", "西格列", "沙格列", "维格列"],
     "suffixes": ["胍", "脲", "特", "嗪", "脲", "糖", "奈", "酮", "汀"],
     "indication": "用于2型糖尿病的血糖控制",
     "side_effects": "低血糖、胃肠道反应、体重增加",
     "contraindications": "1型糖尿病、糖尿病酮症酸中毒、严重肝肾功能不全",
     "interactions": "与其他降糖药合用增加低血糖风险",
     "pregnancy_warning": True, "controlled": False},
    {"category": "胰岛素", "prefixes": ["普通胰岛", "门冬胰岛", "赖脯胰岛", "甘精胰岛", "地特胰岛", "预混胰岛", "低精蛋白胰岛"],
     "suffixes": ["素", "素注射液", "素笔芯"],
     "indication": "用于1型糖尿病和2型糖尿病的血糖控制",
     "side_effects": "低血糖、注射部位反应、体重增加",
     "contraindications": "低血糖发作时禁用",
     "interactions": "与其他降糖药合用增强降糖效果",
     "pregnancy_warning": False, "controlled": False},
    {"category": "甲状腺药物", "prefixes": ["左甲状腺", "甲巯咪", "丙硫氧嘧", "甲状腺"],
     "suffixes": ["素钠", "唑", "啶", "片"],
     "indication": "用于甲状腺功能亢进或减退的治疗",
     "side_effects": "心悸、手抖、体重变化、肝功能异常（甲巯咪唑）",
     "contraindications": "对本品过敏者禁用",
     "interactions": "左甲状腺素与多种药物有相互作用",
     "pregnancy_warning": False, "controlled": False},
    # 神经系统药物
    {"category": "非甾体抗炎药", "prefixes": ["布洛", "阿司匹", "对乙酰氨基", "吲哚美", "双氯芬", "美洛昔", "塞来昔", "依托考"],
     "suffixes": ["芬", "林", "酚", "辛", "酸", "康", "布", "昔"],
     "indication": "用于发热、头痛、关节痛、牙痛等轻中度疼痛",
     "side_effects": "胃肠道刺激、肾功能损害、出血风险",
     "contraindications": "活动性消化性溃疡、严重肝肾功能不全",
     "interactions": "与抗凝药合用增加出血风险",
     "pregnancy_warning": True, "controlled": False},
    {"category": "抗癫痫药", "prefixes": ["苯妥英", "卡马西", "丙戊酸", "苯巴比", "地西泮", "左乙拉西", "托吡", "拉莫三"],
     "suffixes": ["钠", "平", "镁", "妥", "坦", "酯", "嗪"],
     "indication": "用于各种类型癫痫的治疗",
     "side_effects": "头晕、嗜睡、肝功能异常、皮疹",
     "contraindications": "严重肝功能不全、对本品过敏",
     "interactions": "多种药物可影响抗癫痫药的血药浓度",
     "pregnancy_warning": True, "controlled": True},
    {"category": "抗抑郁药", "prefixes": ["氟西", "帕罗西", "舍曲", "氟伏沙", "西酞普", "艾司西酞普", "文拉法", "度洛西", "米氮", "阿米替", "丙米", "氯米帕"],
     "suffixes": ["汀", "明", "兰", "平", "林", "明"],
     "indication": "用于抑郁症、焦虑症等精神疾病的治疗",
     "side_effects": "恶心、头痛、失眠、性功能障碍",
     "contraindications": "对本品过敏者禁用，禁止与MAOI合用",
     "interactions": "与单胺氧化酶抑制剂合用可引起5-HT综合征",
     "pregnancy_warning": True, "controlled": True},
    {"category": "镇静催眠药", "prefixes": ["地西", "艾司唑", "阿普唑", "氯硝西", "佐匹克", "右佐匹克", "唑吡", "扎来普"],
     "suffixes": ["泮", "仑", "隆", "坦", "隆"],
     "indication": "用于失眠、焦虑、癫痫等",
     "side_effects": "嗜睡、头晕、乏力、依赖性",
     "contraindications": "严重呼吸功能不全、重症肌无力",
     "interactions": "与酒精及其他中枢抑制剂合用增强抑制作用",
     "pregnancy_warning": True, "controlled": True},
    # 抗过敏药
    {"category": "抗组胺药", "prefixes": ["氯雷他", "西替利", "左西替利", "地氯雷他", "依巴斯", "咪唑斯", "氯苯那", "苯海拉", "赛庚"],
     "suffixes": ["定", "嗪", "汀", "啶", "明", "啶"],
     "indication": "用于过敏性鼻炎、荨麻疹、过敏性皮炎等",
     "side_effects": "嗜睡、头晕、口干（第一代较明显）",
     "contraindications": "对本品过敏者禁用",
     "interactions": "与中枢抑制剂合用增加嗜睡",
     "pregnancy_warning": False, "controlled": False},
    # 维生素及营养药
    {"category": "维生素类", "prefixes": ["维生素A", "维生素B1", "维生素B2", "维生素B6", "维生素B12", "维生素C", "维生素D", "维生素E", "维生素K", "叶酸", "烟酰胺", "泛酸", "生物素"],
     "suffixes": ["片", "胶囊", "注射液"],
     "indication": "用于维生素缺乏症的预防和治疗",
     "side_effects": "过量服用可能引起中毒（脂溶性维生素）",
     "contraindications": "对本品过敏者禁用",
     "interactions": "维生素C可增加铁的吸收",
     "pregnancy_warning": False, "controlled": False},
    {"category": "矿物质补充剂", "prefixes": ["碳酸钙", "葡萄糖酸钙", "乳酸钙", "枸橼酸钙", "硫酸亚铁", "富马酸亚铁", "琥珀酸亚铁", "葡萄糖酸锌", "甘草锌"],
     "suffixes": ["片", "颗粒", "口服液"],
     "indication": "用于钙、铁、锌等矿物质缺乏的预防和治疗",
     "side_effects": "便秘、胃肠道不适",
     "contraindications": "高钙血症、高尿酸血症",
     "interactions": "钙剂可影响四环素类和喹诺酮类的吸收",
     "pregnancy_warning": False, "controlled": False},
    # 皮肤科外用药
    {"category": "外用糖皮质激素", "prefixes": ["氢化可的", "地塞米", "曲安奈", "糠酸莫米", "卤米", "丙酸氯倍他", "丁酸氢化可的"],
     "suffixes": ["松乳膏", "松软膏", "德乳膏", "松凝胶"],
     "indication": "用于湿疹、皮炎、银屑病等炎症性皮肤病",
     "side_effects": "皮肤萎缩、毛细血管扩张、色素沉着",
     "contraindications": "真菌性皮肤病、病毒性皮肤病",
     "interactions": "外用吸收少，全身相互作用少见",
     "pregnancy_warning": False, "controlled": False},
    {"category": "外用抗菌药", "prefixes": ["莫匹罗", "夫西地", "红霉素", "克林霉", "环丙沙"],
     "suffixes": ["星软膏", "酸乳膏", "素软膏", "素凝胶"],
     "indication": "用于皮肤细菌感染",
     "side_effects": "局部刺激、瘙痒、干燥",
     "contraindications": "对本品过敏者禁用",
     "interactions": "外用吸收少，全身相互作用少见",
     "pregnancy_warning": False, "controlled": False},
    {"category": "外用抗真菌药", "prefixes": ["特比萘", "咪康", "酮康", "克霉", "联苯苄", "布替萘", "阿莫罗"],
     "suffixes": ["芬乳膏", "唑软膏", "唑乳膏", "芬凝胶"],
     "indication": "用于手足癣、体股癣、甲癣等真菌感染",
     "side_effects": "局部刺激、瘙痒、灼热感",
     "contraindications": "对本品过敏者禁用",
     "interactions": "外用吸收少，全身相互作用少见",
     "pregnancy_warning": False, "controlled": False},
    # 眼科用药
    {"category": "眼科用药", "prefixes": ["左氧氟沙", "妥布霉", "氯霉", "红霉", "色甘酸", "吡嘧司特", "布林佐", "噻吗洛", "毛果芸香", "玻璃酸", "羧甲基纤维素"],
     "suffixes": ["星滴眼液", "素眼膏", "钠滴眼液", "尔滴眼液", "碱滴眼液", "钠滴眼液"],
     "indication": "用于眼部感染、青光眼、干眼症等",
     "side_effects": "眼部刺激、视物模糊、结膜充血",
     "contraindications": "对本品过敏者禁用",
     "interactions": "局部用药全身吸收少",
     "pregnancy_warning": False, "controlled": False},
    # 耳鼻喉科用药
    {"category": "鼻用药物", "prefixes": ["布地奈", "糠酸莫米", "丙酸氟替卡", "盐酸羟甲", "盐酸赛洛", "生理海", "生理性海"],
     "suffixes": ["德鼻喷雾剂", "松鼻喷剂", "唑啉滴鼻液", "唑林鼻喷剂", "水鼻腔喷雾"],
     "indication": "用于过敏性鼻炎、急慢性鼻炎、鼻窦炎",
     "side_effects": "鼻腔干燥、刺激感、鼻出血",
     "contraindications": "对本品过敏者禁用",
     "interactions": "局部用药全身吸收少",
     "pregnancy_warning": False, "controlled": False},
    # 中成药
    {"category": "感冒类中成药", "prefixes": ["感冒清", "板蓝根", "银翘", "双黄连", "连花清", "藿香正", "小柴胡", "清开灵", "苦甘", "祖卡木"],
     "suffixes": ["颗粒", "胶囊", "片", "口服液"],
     "indication": "用于感冒引起的发热、头痛、鼻塞、流涕等症状",
     "side_effects": "偶见胃肠道不适、皮疹",
     "contraindications": "对本品过敏者禁用，孕妇慎用",
     "interactions": "与西药合用时注意成分重复",
     "pregnancy_warning": True, "controlled": False},
    {"category": "止咳化痰类中成药", "prefixes": ["川贝枇杷", "急支", "肺力咳", "橘红", "蛇胆川贝", "复方甘草", "养阴清肺", "通宣理", "杏苏止", "止嗽"],
     "suffixes": ["糖浆", "口服液", "颗粒", "丸"],
     "indication": "用于咳嗽、咳痰",
     "side_effects": "偶见恶心、头晕",
     "contraindications": "对本品过敏者禁用",
     "interactions": "与西药止咳药合用需注意剂量",
     "pregnancy_warning": False, "controlled": False},
    {"category": "胃肠类中成药", "prefixes": ["保和", "香砂养胃", "附子理中", "参苓白术", "补脾益肠", "四神", "麻仁", "通便", "藿香正", "香连"],
     "suffixes": ["丸", "胶囊", "颗粒", "片"],
     "indication": "用于消化不良、腹胀、腹泻、便秘等",
     "side_effects": "偶见胃肠道不适",
     "contraindications": "对本品过敏者禁用",
     "interactions": "与西药合用需间隔1-2小时",
     "pregnancy_warning": False, "controlled": False},
    {"category": "活血化瘀类中成药", "prefixes": ["丹参", "川芎", "红花", "血塞通", "血栓通", "银杏叶", "步长脑心通", "通心络", "复方丹参", "速效救心"],
     "suffixes": ["片", "胶囊", "滴丸", "注射液"],
     "indication": "用于心脑血管疾病、瘀血阻滞证",
     "side_effects": "偶见胃肠道不适、出血倾向",
     "contraindications": "有出血倾向者、孕妇禁用",
     "interactions": "与抗凝药合用增加出血风险",
     "pregnancy_warning": True, "controlled": False},
    {"category": "补益类中成药", "prefixes": ["六味地黄", "金匮肾气", "补中益气", "归脾", "人参健脾", "阿胶", "逍遥", "知柏地黄", "杞菊地黄", "麦味地黄"],
     "suffixes": ["丸", "颗粒", "胶囊", "口服液"],
     "indication": "用于各种虚证的调理",
     "side_effects": "偶见胃肠道不适",
     "contraindications": "感冒发热期间不宜服用",
     "interactions": "与其他药物合用时注意配伍",
     "pregnancy_warning": False, "controlled": False},
]


def generate_medications():
    """生成500+药品数据."""
    medications = []
    med_id = 1
    random.seed(42)

    for cat_info in MEDICATION_CATEGORIES:
        category = cat_info["category"]
        for prefix in cat_info["prefixes"]:
            for suffix in cat_info["suffixes"]:
                name = prefix + suffix
                # 计算剂量信息
                dosage_forms = ["口服", "外用", "注射", "滴眼", "滴鼻"]
                if "外用" in category or "乳膏" in suffix or "软膏" in suffix:
                    form = "外用"
                elif "滴眼液" in suffix:
                    form = "滴眼"
                elif "滴鼻" in suffix or "鼻喷雾" in suffix:
                    form = "滴鼻"
                elif "注射液" in suffix:
                    form = "注射"
                else:
                    form = "口服"

                # 剂量描述
                if form == "口服":
                    if "片" in suffix or "胶囊" in suffix:
                        dosage = f"每次1-2{('片' if '片' in suffix else '粒')}，每日{random.choice(['1次', '2次', '3次'])}"
                    elif "颗粒" in suffix or "散" in suffix:
                        dosage = f"每次1袋，每日{random.choice(['2次', '3次'])}，开水冲服"
                    elif "口服液" in suffix or "糖浆" in suffix:
                        dosage = f"每次10ml，每日{random.choice(['2次', '3次'])}"
                    elif "丸" in suffix:
                        dosage = f"每次{random.choice(['6g', '8丸', '1丸'])}，每日{random.choice(['2次', '3次'])}"
                    else:
                        dosage = f"遵医嘱服用"
                elif form == "外用":
                    dosage = "取适量涂于患处，每日2-3次"
                elif form == "滴眼":
                    dosage = "每次1-2滴，每日3-4次"
                elif form == "滴鼻":
                    dosage = "每次1-2喷，每日2-3次"
                else:
                    dosage = "遵医嘱使用"

                medications.append({
                    "id": med_id,
                    "name": name,
                    "generic_name": name,
                    "category": category,
                    "indication": cat_info["indication"],
                    "dosage": dosage,
                    "side_effects": cat_info["side_effects"],
                    "contraindications": cat_info["contraindications"],
                    "interactions": cat_info["interactions"],
                    "pregnancy_warning": cat_info["pregnancy_warning"],
                    "controlled": cat_info["controlled"],
                })
                med_id += 1

                # 限制数量，避免太多
                if med_id > 550:
                    break
            if med_id > 550:
                break
        if med_id > 550:
            break

    return medications
