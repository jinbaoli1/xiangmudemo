"""药品服务."""
from __future__ import annotations

from typing import List, Optional, Set
from app.database import get_db
from app.models.schemas import Medication, MedicationSuggestion


class MedicationService:
    """药品服务类."""

    @staticmethod
    def list_all(category: Optional[str] = None, limit: int = 100) -> List[Medication]:
        """获取药品列表."""
        with get_db() as conn:
            cursor = conn.cursor()
            if category:
                cursor.execute(
                    "SELECT * FROM medications WHERE category = ? ORDER BY id LIMIT ?",
                    (category, limit)
                )
            else:
                cursor.execute("SELECT * FROM medications ORDER BY id LIMIT ?", (limit,))
            rows = cursor.fetchall()
            return [Medication(**dict(row)) for row in rows]

    @staticmethod
    def get_by_id(med_id: int) -> Optional[Medication]:
        """根据ID获取药品."""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM medications WHERE id = ?", (med_id,))
            row = cursor.fetchone()
            return Medication(**dict(row)) if row else None

    @staticmethod
    def get_by_name(name: str) -> Optional[Medication]:
        """根据名称获取药品."""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM medications WHERE name LIKE ? LIMIT 1", (f"%{name}%",))
            row = cursor.fetchone()
            return Medication(**dict(row)) if row else None

    @staticmethod
    def search(keyword: str, limit: int = 20) -> List[Medication]:
        """搜索药品."""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT * FROM medications
                WHERE name LIKE ? OR generic_name LIKE ? OR indication LIKE ? OR category LIKE ?
                ORDER BY id
                LIMIT ?
                """,
                (f"%{keyword}%", f"%{keyword}%", f"%{keyword}%", f"%{keyword}%", limit)
            )
            rows = cursor.fetchall()
            return [Medication(**dict(row)) for row in rows]

    @staticmethod
    def get_categories() -> List[str]:
        """获取药品分类列表."""
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT category FROM medications WHERE category IS NOT NULL")
            rows = cursor.fetchall()
            return [row["category"] for row in rows]

    @staticmethod
    def get_medications_for_disease(disease_name: str, limit: int = 5) -> List[MedicationSuggestion]:
        """根据疾病名称推荐药品."""
        # 基于疾病关键词匹配药品适应症
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT * FROM medications
                WHERE indication LIKE ?
                ORDER BY id
                LIMIT ?
                """,
                (f"%{disease_name}%", limit)
            )
            rows = cursor.fetchall()

            if rows:
                return [
                    MedicationSuggestion(
                        medication_name=row["name"],
                        generic_name=row["generic_name"],
                        category=row["category"] or "",
                        indication=row["indication"] or "",
                        dosage=row["dosage"] or "",
                        warnings=MedicationService._get_warnings(row),
                    )
                    for row in rows
                ]

            # 如果没有直接匹配，按疾病所属类别推荐
            return MedicationService._get_generic_medications(disease_name, limit)

    @staticmethod
    def _get_generic_medications(disease_name: str, limit: int) -> List[MedicationSuggestion]:
        """根据疾病类别获取通用推荐药品."""
        # 简化的疾病-药品类别映射
        disease_category_map = {
            "感冒": "感冒类中成药",
            "上呼吸道感染": "感冒类中成药",
            "咳嗽": "止咳化痰类中成药",
            "胃炎": "胃黏膜保护剂",
            "胃溃疡": "质子泵抑制剂",
            "高血压": "ACEI类降压药",
            "糖尿病": "口服降糖药",
            "感染": "头孢菌素类",
            "肺炎": "头孢菌素类",
            "疼痛": "非甾体抗炎药",
            "过敏": "抗组胺药",
            "失眠": "镇静催眠药",
            "焦虑": "抗抑郁药",
            "抑郁": "抗抑郁药",
            "湿疹": "外用糖皮质激素",
            "哮喘": "支气管扩张剂",
        }

        category = None
        for keyword, cat in disease_category_map.items():
            if keyword in disease_name:
                category = cat
                break

        if not category:
            return []

        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM medications WHERE category = ? LIMIT ?",
                (category, limit)
            )
            rows = cursor.fetchall()

            return [
                MedicationSuggestion(
                    medication_name=row["name"],
                    generic_name=row["generic_name"],
                    category=row["category"] or "",
                    indication=row["indication"] or "",
                    dosage=row["dosage"] or "",
                    warnings=MedicationService._get_warnings(row),
                )
                for row in rows
            ]

    @staticmethod
    def _get_warnings(row) -> List[str]:
        """从药品信息中提取警告信息."""
        warnings = []
        if row["pregnancy_warning"]:
            warnings.append("孕妇慎用或禁用")
        if row["controlled"]:
            warnings.append("管制药品，需凭处方使用")
        if row["contraindications"]:
            # 取前30个字作为警告
            contra = row["contraindications"]
            if len(contra) > 50:
                contra = contra[:50] + "..."
            warnings.append(f"禁忌症：{contra}")
        if row["interactions"]:
            inter = row["interactions"]
            if len(inter) > 50:
                inter = inter[:50] + "..."
            warnings.append(f"药物相互作用：{inter}")
        return warnings

    @staticmethod
    def check_drug_interactions(medication_names: List[str]) -> List[dict]:
        """检查药物相互作用."""
        if len(medication_names) < 2:
            return []

        medications = []
        for name in medication_names:
            med = MedicationService.get_by_name(name)
            if med:
                medications.append(med)

        interactions = []
        # 简单的相互作用检查规则
        dangerous_pairs = [
            (["头孢", "青霉素"], "酒精", "双硫仑样反应"),
            (["降压药", "降压"], "降压药", "低血压风险"),
            (["降糖药", "胰岛素"], "降糖药", "低血糖风险"),
            (["阿司匹林", "布洛芬"], "抗凝", "出血风险增加"),
        ]

        for i, med1 in enumerate(medications):
            for med2 in medications[i + 1:]:
                # 检查是否有相互作用
                interaction_level = "low"
                description = ""

                # 同类药物相互作用
                if med1.category == med2.category and "抗生素" in med1.category:
                    interaction_level = "medium"
                    description = f"{med1.name}与{med2.name}同属抗生素类，联用可能增加副作用风险"
                elif "降压" in med1.category and "降压" in med2.category:
                    interaction_level = "medium"
                    description = f"{med1.name}与{med2.name}均为降压药物，联用可能导致血压过低"
                elif "降糖" in med1.category and "降糖" in med2.category:
                    interaction_level = "medium"
                    description = f"{med1.name}与{med2.name}均为降糖药物，联用可能导致低血糖"
                elif "非甾体" in med1.category and "非甾体" in med2.category:
                    interaction_level = "high"
                    description = f"{med1.name}与{med2.name}均为非甾体抗炎药，联用会显著增加胃肠道和心血管不良反应风险，应避免联用"

                if description:
                    interactions.append({
                        "medication_1": med1.name,
                        "medication_2": med2.name,
                        "severity": interaction_level,
                        "description": description,
                    })

        return interactions

    @staticmethod
    def check_allergies(medication_names: List[str], allergies: str) -> List[dict]:
        """检查药物过敏."""
        if not allergies:
            return []

        allergy_list = [a.strip() for a in allergies.split(",") if a.strip()]
        results = []

        for med_name in medication_names:
            med = MedicationService.get_by_name(med_name)
            if not med:
                continue

            for allergy in allergy_list:
                # 简单匹配过敏成分
                if allergy in med.name or allergy in med.generic_name or allergy in med.category:
                    results.append({
                        "medication": med.name,
                        "allergen": allergy,
                        "severity": "high",
                        "description": f"{med.name}可能含有{allergy}相关成分，过敏者禁用",
                    })
                # 检查禁忌症中的过敏提示
                elif med.contraindications and allergy in med.contraindications:
                    results.append({
                        "medication": med.name,
                        "allergen": allergy,
                        "severity": "high",
                        "description": f"{med.name}禁忌症包含{allergy}过敏，禁用",
                    })

        return results

    @staticmethod
    def check_special_population(
        medication_names: List[str],
        pregnant: bool = False,
        elderly: bool = False,
        child: bool = False,
        liver_disease: bool = False,
        kidney_disease: bool = False,
    ) -> List[dict]:
        """检查特殊人群用药禁忌."""
        results = []

        for med_name in medication_names:
            med = MedicationService.get_by_name(med_name)
            if not med:
                continue

            # 孕妇
            if pregnant and med.pregnancy_warning:
                results.append({
                    "medication": med.name,
                    "population": "孕妇",
                    "severity": "high",
                    "description": f"{med.name}孕妇慎用或禁用，可能对胎儿有影响",
                })

            # 儿童
            if child and ("喹诺酮" in med.category or "四环素" in med.category):
                results.append({
                    "medication": med.name,
                    "population": "儿童",
                    "severity": "high",
                    "description": f"{med.name}18岁以下禁用，可能影响骨骼发育",
                })

            # 老年人
            if elderly and med.controlled:
                results.append({
                    "medication": med.name,
                    "population": "老年人",
                    "severity": "medium",
                    "description": f"{med.name}老年人应减量使用，注意监测不良反应",
                })

            # 肝肾功能不全
            if liver_disease and ("他汀" in med.name or "抗结核" in med.category):
                results.append({
                    "medication": med.name,
                    "population": "肝功能不全",
                    "severity": "high",
                    "description": f"{med.name}可能加重肝脏负担，肝功能不全者禁用或慎用",
                })

            if kidney_disease and ("氨基糖苷" in med.category or "造影" in med.name):
                results.append({
                    "medication": med.name,
                    "population": "肾功能不全",
                    "severity": "high",
                    "description": f"{med.name}可能有肾毒性，肾功能不全者禁用或调整剂量",
                })

        return results
