"""Mock LLM - 基于规则模板模拟LLM，无需外部API."""
from __future__ import annotations

import re
import random
from typing import List, Dict, Any, Optional


class MockLLM:
    """模拟大语言模型.

    基于规则和模板生成回复，用于演示和测试。
    """

    def __init__(self, model_name: str = "mock-medical-llm"):
        self.model_name = model_name
        random.seed(42)

    def generate_triage_response(
        self,
        symptoms: List[str],
        is_critical: bool,
        departments: List[Dict[str, Any]],
    ) -> str:
        """生成分诊回复."""
        if is_critical:
            return (
                "⚠️ 根据您描述的症状，情况可能比较紧急，建议您立即前往医院急诊科就诊，"
                "或拨打急救电话。如果条件允许，请有人陪同前往。"
                "以下信息供参考，但请优先就医！\n\n"
            )

        response = ""

        if symptoms:
            response += f"根据您描述的症状（{'、'.join(symptoms[:5])}），我为您进行了初步分析：\n\n"
        else:
            response += "我需要更多信息来帮您判断。请问您能具体描述一下哪里不舒服吗？\n\n"
            return response

        if departments:
            response += "🏥 推荐就诊科室：\n"
            for i, dept in enumerate(departments[:3], 1):
                conf_pct = int(dept.get("confidence", 0) * 100)
                response += f"{i}. {dept.get('department_name', '')}（置信度 {conf_pct}%）\n"
            response += "\n"

        if len(symptoms) < 3:
            response += "为了更准确地判断，我想再了解一些情况：\n"
            follow_ups = [
                "症状持续多长时间了？",
                "有没有其他伴随症状？",
                "以前有没有出现过类似情况？",
                "最近有没有受凉、劳累或接触过病人？",
            ]
            for q in follow_ups[:2]:
                response += f"• {q}\n"

        return response

    def generate_diagnosis_response(
        self,
        symptoms: List[str],
        candidates: List[Dict[str, Any]],
    ) -> str:
        """生成诊断分析回复."""
        response = "📋 疾病初步分析：\n\n"
        response += f"根据您描述的症状（{'、'.join(symptoms[:5])}），以下是一些可能的疾病方向：\n\n"

        for i, cand in enumerate(candidates[:5], 1):
            prob_pct = int(cand.get("probability", 0) * 100)
            response += f"{i}. {cand.get('disease_name', '')}（可能性 {prob_pct}%）\n"
            if cand.get("description"):
                desc = cand["description"]
                if len(desc) > 80:
                    desc = desc[:80] + "..."
                response += f"   简介：{desc}\n"
            if cand.get("key_symptoms"):
                response += f"   常见症状：{'、'.join(cand['key_symptoms'][:3])}\n"
            response += "\n"

        response += (
            "⚠️ 提示：以上仅为基于症状的初步分析，不能替代专业医生诊断。"
            "建议您到医院相关科室就诊，进行进一步检查以明确诊断。\n"
        )

        return response

    def generate_medication_response(
        self,
        medications: List[Dict[str, Any]],
        risk_level: str = "low",
        warnings: List[str] = None,
    ) -> str:
        """生成用药建议回复."""
        response = "💊 用药建议：\n\n"

        if not medications:
            response += "暂未找到明确的药物推荐。建议您到医院就诊，由医生根据具体情况开具处方。\n"
            return response

        for i, med in enumerate(medications[:5], 1):
            response += f"{i}. {med.get('medication_name', med.get('name', ''))}\n"
            if med.get("category"):
                response += f"   类别：{med['category']}\n"
            if med.get("indication"):
                indication = med["indication"]
                if len(indication) > 60:
                    indication = indication[:60] + "..."
                response += f"   适应症：{indication}\n"
            if med.get("dosage"):
                response += f"   用法：{med['dosage']}\n"
            if med.get("warnings"):
                for w in med["warnings"][:2]:
                    response += f"   ⚠️ {w}\n"
            response += "\n"

        if risk_level == "high":
            response += "🚨 高风险提示：存在严重用药风险，请勿自行用药，请务必咨询医生或药师！\n"
        elif risk_level == "medium":
            response += "⚠️ 注意事项：存在一些用药注意事项，建议在医生指导下使用。\n"

        response += "\n📌 温馨提示：以上药物推荐仅供参考，具体用药请遵医嘱。"
        response += "用药前请仔细阅读药品说明书，如有不适请及时就医。\n"

        return response

    def generate_follow_up(
        self,
        stage: str,
        symptoms: List[str],
        context: Dict[str, Any] = None,
    ) -> List[str]:
        """生成追问问题."""
        questions = []

        if stage == "triage":
            if not symptoms:
                questions = [
                    "您能描述一下主要有哪些不舒服吗？",
                    "症状是从什么时候开始的？",
                ]
            elif len(symptoms) == 1:
                questions = [
                    "除了这个症状，还有没有其他不舒服？",
                    "症状持续多久了？是一阵阵的还是一直都有？",
                ]
            else:
                questions = [
                    "这些症状出现多久了？有没有加重或减轻的因素？",
                    "有没有去过其他医院检查或治疗过？",
                ]
        elif stage == "diagnosis":
            questions = [
                "您以前有没有得过什么疾病？",
                "有没有药物过敏史？",
                "近期有没有做过什么检查？",
            ]
        elif stage == "medication":
            questions = [
                "请问您是否有药物过敏史？",
                "您目前是否在服用其他药物？",
                "有没有肝肾功能方面的问题？",
            ]

        return questions

    def chat(self, message: str, history: List[Dict[str, str]] = None) -> str:
        """通用聊天回复（简化版）."""
        # 简单的规则回复
        greetings = ["你好", "您好", "hi", "hello", "在吗"]
        if any(g in message.lower() for g in greetings):
            return "您好！我是智能分诊助手，请问有什么可以帮您的？您可以描述一下您的症状。"

        thanks = ["谢谢", "感谢", "thanks", "thank you"]
        if any(t in message.lower() for t in thanks):
            return "不客气！希望对您有帮助。如果还有其他问题，随时可以问我。"

        bye = ["再见", "拜拜", "bye", "结束"]
        if any(b in message.lower() for b in bye):
            return "再见！祝您身体健康，生活愉快！如有需要随时回来咨询。"

        # 默认回复
        return "我理解您的问题了。为了更好地帮助您，请您详细描述一下症状，包括症状的部位、持续时间、严重程度等信息。"


# 全局实例
_mock_llm: Optional[MockLLM] = None


def get_mock_llm() -> MockLLM:
    """获取MockLLM单例."""
    global _mock_llm
    if _mock_llm is None:
        _mock_llm = MockLLM()
    return _mock_llm
