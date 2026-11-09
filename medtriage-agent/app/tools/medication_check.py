"""用药安全检查工具."""
from __future__ import annotations

from typing import List, Dict, Any, Optional
from app.services.medication_service import MedicationService
from app.models.schemas import MedicationSuggestion


class MedicationCheckTool:
    """用药安全检查工具.

    功能：
    1. 根据疾病推荐药物
    2. 药物相互作用检查
    3. 过敏提示
    4. 特殊人群禁忌
    """

    name = "medication_check"
    description = "用药安全检查工具，包括药物推荐、相互作用检查、过敏提示、特殊人群禁忌"

    def __init__(self):
        self.medication_service = MedicationService()

    def recommend_medications(
        self,
        disease_name: str,
        limit: int = 5,
    ) -> Dict[str, Any]:
        """根据疾病推荐药物.

        Args:
            disease_name: 疾病名称
            limit: 返回数量

        Returns:
            药物推荐结果
        """
        suggestions = self.medication_service.get_medications_for_disease(disease_name, limit)

        return {
            "disease": disease_name,
            "medications": [
                {
                    "name": med.medication_name,
                    "generic_name": med.generic_name,
                    "category": med.category,
                    "indication": med.indication,
                    "dosage": med.dosage,
                    "warnings": med.warnings,
                }
                for med in suggestions
            ],
            "total_count": len(suggestions),
            "disclaimer": "以上药物推荐仅供参考，具体用药请遵医嘱。",
        }

    def check_interactions(self, medication_names: List[str]) -> Dict[str, Any]:
        """检查药物相互作用.

        Args:
            medication_names: 药物名称列表

        Returns:
            相互作用检查结果
        """
        interactions = self.medication_service.check_drug_interactions(medication_names)

        severity_count = {"high": 0, "medium": 0, "low": 0}
        for inter in interactions:
            severity_count[inter["severity"]] += 1

        return {
            "medications": medication_names,
            "interactions": interactions,
            "severity_summary": severity_count,
            "has_risk": len(interactions) > 0,
            "summary": (
                f"检测到{len(interactions)}个潜在药物相互作用，"
                f"其中高危{severity_count['high']}个，中危{severity_count['medium']}个，低危{severity_count['low']}个。"
                if interactions
                else "未检测到明显的药物相互作用。"
            ),
        }

    def check_allergies(
        self,
        medication_names: List[str],
        allergies: str,
    ) -> Dict[str, Any]:
        """检查药物过敏.

        Args:
            medication_names: 药物名称列表
            allergies: 过敏史（逗号分隔）

        Returns:
            过敏检查结果
        """
        allergy_results = self.medication_service.check_allergies(medication_names, allergies)

        return {
            "medications": medication_names,
            "allergies": allergies,
            "allergy_alerts": allergy_results,
            "has_allergy_risk": len(allergy_results) > 0,
            "summary": (
                f"检测到{len(allergy_results)}个过敏风险，建议避免使用相关药物。"
                if allergy_results
                else "未检测到明确的过敏风险。"
            ),
        }

    def check_special_population(
        self,
        medication_names: List[str],
        pregnant: bool = False,
        elderly: bool = False,
        child: bool = False,
        liver_disease: bool = False,
        kidney_disease: bool = False,
    ) -> Dict[str, Any]:
        """检查特殊人群用药禁忌.

        Args:
            medication_names: 药物名称列表
            pregnant: 是否孕妇
            elderly: 是否老年人
            child: 是否儿童
            liver_disease: 是否有肝病
            kidney_disease: 是否有肾病

        Returns:
            特殊人群用药检查结果
        """
        results = self.medication_service.check_special_population(
            medication_names,
            pregnant=pregnant,
            elderly=elderly,
            child=child,
            liver_disease=liver_disease,
            kidney_disease=kidney_disease,
        )

        population_flags = []
        if pregnant:
            population_flags.append("孕妇")
        if elderly:
            population_flags.append("老年人")
        if child:
            population_flags.append("儿童")
        if liver_disease:
            population_flags.append("肝功能不全")
        if kidney_disease:
            population_flags.append("肾功能不全")

        return {
            "medications": medication_names,
            "populations": population_flags,
            "warnings": results,
            "has_warnings": len(results) > 0,
            "summary": (
                f"针对{','.join(population_flags)}人群，"
                f"检测到{len(results)}项用药警示，请在医生指导下使用。"
                if results
                else f"针对{','.join(population_flags)}人群，未检测到明显用药禁忌，但仍建议遵医嘱使用。"
            ),
        }

    def comprehensive_check(
        self,
        medication_names: List[str],
        allergies: Optional[str] = None,
        pregnant: bool = False,
        elderly: bool = False,
        child: bool = False,
        liver_disease: bool = False,
        kidney_disease: bool = False,
    ) -> Dict[str, Any]:
        """综合用药安全检查.

        Args:
            medication_names: 药物名称列表
            allergies: 过敏史
            pregnant: 是否孕妇
            elderly: 是否老年人
            child: 是否儿童
            liver_disease: 是否有肝病
            kidney_disease: 是否有肾病

        Returns:
            综合检查结果
        """
        # 1. 药物相互作用
        interaction_result = self.check_interactions(medication_names)

        # 2. 过敏检查
        allergy_result = {"has_allergy_risk": False, "allergy_alerts": []}
        if allergies:
            allergy_result = self.check_allergies(medication_names, allergies)

        # 3. 特殊人群
        special_result = self.check_special_population(
            medication_names,
            pregnant=pregnant,
            elderly=elderly,
            child=child,
            liver_disease=liver_disease,
            kidney_disease=kidney_disease,
        )

        # 4. 综合风险评估
        total_high_risk = (
            sum(1 for i in interaction_result["interactions"] if i["severity"] == "high")
            + len(allergy_result.get("allergy_alerts", []))
            + sum(1 for w in special_result["warnings"] if w["severity"] == "high")
        )

        risk_level = "low"
        if total_high_risk > 0:
            risk_level = "high"
        elif (
            interaction_result["has_risk"]
            or allergy_result.get("has_allergy_risk")
            or special_result["has_warnings"]
        ):
            risk_level = "medium"

        return {
            "risk_level": risk_level,
            "interactions": interaction_result,
            "allergies": allergy_result,
            "special_population": special_result,
            "overall_summary": (
                "⚠️ 存在高风险用药问题，建议立即咨询医生或药师！"
                if risk_level == "high"
                else "存在一些用药注意事项，建议在医生指导下使用。"
                if risk_level == "medium"
                else "未发现明显用药风险，但仍建议遵医嘱用药。"
            ),
            "disclaimer": "本检查结果仅供参考，不能替代专业医疗建议。如有疑问，请咨询医生或药师。",
        }
