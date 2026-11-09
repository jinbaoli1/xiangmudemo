"""医生模拟数据生成器 - 生成80+医生."""
import random

# 医生姓和名池
SURNAMES = ["王", "李", "张", "刘", "陈", "杨", "黄", "赵", "周", "吴",
            "徐", "孙", "胡", "朱", "高", "林", "何", "郭", "马", "罗",
            "梁", "宋", "郑", "谢", "韩", "唐", "冯", "于", "董", "萧"]
GIVEN_NAMES = ["伟", "芳", "娜", "敏", "静", "丽", "强", "磊", "军", "洋",
               "勇", "艳", "杰", "娟", "涛", "明", "超", "秀英", "霞", "平",
               "刚", "桂英", "建国", "建华", "志明", "淑芬", "文博", "雅琴", "玉梅", "劲松"]

TITLES = ["主任医师", "副主任医师", "主治医师", "住院医师"]


def generate_doctors(departments):
    """根据科室列表生成医生数据."""
    doctors = []
    doctor_id = 1
    random.seed(42)

    # 每个科室配置的医生数量和专长
    dept_specialties = {
        "心内科": ["冠心病介入", "心律失常", "心力衰竭", "高血压", "心脏康复"],
        "呼吸内科": ["肺部感染", "慢性阻塞性肺疾病", "哮喘", "肺癌", "间质性肺病"],
        "消化内科": ["胃肠疾病", "肝胆疾病", "胰腺疾病", "内镜诊疗", "炎症性肠病"],
        "神经内科": ["脑血管病", "癫痫", "帕金森", "头痛眩晕", "神经肌肉病"],
        "肾内科": ["肾小球疾病", "肾功能衰竭", "血液净化", "肾移植随访", "水电解质紊乱"],
        "内分泌科": ["糖尿病", "甲状腺疾病", "骨质疏松", "垂体肾上腺", "肥胖代谢"],
        "血液内科": ["白血病", "淋巴瘤", "贫血", "出凝血疾病", "造血干细胞移植"],
        "风湿免疫科": ["类风湿关节炎", "系统性红斑狼疮", "强直性脊柱炎", "干燥综合征", "血管炎"],
        "感染科": ["病毒性肝炎", "发热待查", "艾滋病", "结核病", "细菌真菌感染"],
        "普外科": ["胃肠外科", "肝胆外科", "甲状腺乳腺", "疝外科", "肛肠外科"],
        "骨科": ["脊柱外科", "关节外科", "创伤骨科", "运动医学", "骨肿瘤"],
        "神经外科": ["脑肿瘤", "脑血管病", "颅脑外伤", "脊柱脊髓", "功能神经外科"],
        "心胸外科": ["心脏外科", "普胸外科", "大血管外科", "微创胸外科", "心脏移植"],
        "泌尿外科": ["泌尿系结石", "前列腺疾病", "泌尿系肿瘤", "男科", "肾移植"],
        "妇产科": ["妇科肿瘤", "产科", "生殖内分泌", "计划生育", "妇科微创"],
        "儿科": ["新生儿", "小儿呼吸", "小儿消化", "小儿神经", "儿童保健"],
        "眼科": ["白内障", "青光眼", "眼底病", "角膜病", "眼视光"],
        "耳鼻喉科": ["耳科", "鼻科", "咽喉科", "头颈外科", "听力眩晕"],
        "口腔科": ["口腔内科", "口腔外科", "口腔修复", "口腔正畸", "儿童口腔"],
        "皮肤科": ["过敏性皮肤病", "银屑病", "痤疮", "皮肤肿瘤", "性病"],
        "急诊科": ["心肺复苏", "创伤急救", "中毒救治", "急危重症", "院前急救"],
        "重症医学科": ["呼吸支持", "循环支持", "多器官衰竭", "感染性休克", "营养支持"],
        "肿瘤科": ["化疗", "靶向治疗", "免疫治疗", "姑息治疗", "肿瘤介入"],
        "精神心理科": ["抑郁症", "焦虑症", "精神分裂症", "双相情感障碍", "睡眠障碍"],
        "中医科": ["中医内科", "中医外科", "针灸推拿", "中医妇科", "中医儿科"],
    }

    intro_templates = [
        "从事{specialty}临床工作{years}年，擅长{specialty}相关疾病的诊断与治疗，发表学术论文{pubs}篇。",
        "{title}，医学博士，{specialty}专业方向，曾在国内外知名医院进修，具有丰富的临床经验。",
        "擅长{specialty}疾病的诊治，尤其在{specialty}微创手术方面造诣深厚，年手术量超过500台。",
        "从事临床、教学、科研工作{years}余年，主持省部级课题{grants}项，对{specialty}有深入研究。",
        "{title}，硕士生导师，主要研究方向为{specialty}，在核心期刊发表论文{pubs}余篇。"
    ]

    for dept_idx, dept in enumerate(departments):
        dept_name = dept["name"]
        specialties = dept_specialties.get(dept_name, ["常见病诊治"])
        # 每个科室3-5个医生
        num_doctors = random.randint(3, 5)

        for i in range(num_doctors):
            surname = random.choice(SURNAMES)
            given_name = random.choice(GIVEN_NAMES)
            full_name = surname + given_name

            # 职称比例：主任20%，副主任30%，主治40%，住院10%
            r = random.random()
            if r < 0.2:
                title = TITLES[0]
                exp_base = 20
            elif r < 0.5:
                title = TITLES[1]
                exp_base = 15
            elif r < 0.9:
                title = TITLES[2]
                exp_base = 8
            else:
                title = TITLES[3]
                exp_base = 3

            experience = exp_base + random.randint(0, 10)
            specialty = specialties[i % len(specialties)]
            rating = round(4.0 + random.random() * 1.0, 1)
            consultation_count = random.randint(100, 5000)

            intro_template = random.choice(intro_templates)
            introduction = intro_template.format(
                specialty=specialty,
                years=experience,
                title=title,
                pubs=random.randint(5, 50),
                grants=random.randint(1, 5)
            )

            doctors.append({
                "id": doctor_id,
                "name": full_name,
                "department_id": dept_idx + 1,
                "title": title,
                "specialty": specialty,
                "experience_years": experience,
                "rating": rating,
                "consultation_count": consultation_count,
                "introduction": introduction,
            })
            doctor_id += 1

    return doctors
