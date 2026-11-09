"""历史告警相似度检索器"""
import math
from typing import List, Dict, Any
from collections import Counter
from datetime import datetime


def _alert_tokenize(alert: Dict[str, Any]) -> List[str]:
    """告警文本分词"""
    text_parts = [
        alert.get("alert_name", ""),
        alert.get("summary", ""),
        alert.get("description", ""),
        alert.get("metric_name", ""),
        alert.get("service", ""),
        alert.get("host", ""),
        " ".join(alert.get("tags", [])),
    ]
    text = " ".join(text_parts).lower()
    # 简单分词
    import re
    words = re.findall(r'[a-zA-Z][a-zA-Z0-9_+\-]+', text)
    chars = re.findall(r'[\u4e00-\u9fff]', text)
    numbers = re.findall(r'\d+', text)
    return words + chars + numbers


def _cosine_similarity(vec1: Dict[str, float], vec2: Dict[str, float]) -> float:
    """余弦相似度"""
    common = set(vec1.keys()) & set(vec2.keys())
    dot = sum(vec1[k] * vec2[k] for k in common)
    norm1 = math.sqrt(sum(v * v for v in vec1.values()))
    norm2 = math.sqrt(sum(v * v for v in vec2.values()))
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return dot / (norm1 * norm2)


class AlertRetriever:
    """历史告警相似度匹配器"""

    def __init__(self, historical_alerts: List[Dict[str, Any]]):
        self.alerts = historical_alerts
        self._build_index()

    def _build_index(self):
        """构建TF向量索引"""
        self.tf_vectors = []
        for alert in self.alerts:
            tokens = _alert_tokenize(alert)
            freq = Counter(tokens)
            total = max(len(tokens), 1)
            tf = {word: count / total for word, count in freq.items()}
            self.tf_vectors.append(tf)

        # 构建倒排索引加速
        self.inverted_index: Dict[str, List[int]] = {}
        for i, tf in enumerate(self.tf_vectors):
            for word in tf:
                if word not in self.inverted_index:
                    self.inverted_index[word] = []
                self.inverted_index[word].append(i)

    def find_similar(
        self,
        alert: Dict[str, Any],
        top_k: int = 5,
        service: str = None,
        min_score: float = 0.1,
        only_resolved: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        查找相似历史告警
        :param alert: 当前告警
        :param top_k: 返回数量
        :param service: 服务过滤
        :param min_score: 最小相似度
        :param only_resolved: 只返回已解决的
        :return: 相似告警列表
        """
        query_tokens = _alert_tokenize(alert)
        if not query_tokens:
            return []

        freq = Counter(query_tokens)
        total = max(len(query_tokens), 1)
        query_tf = {word: count / total for word, count in freq.items()}

        # 通过倒排索引找候选
        candidate_indices = set()
        for word in query_tf:
            if word in self.inverted_index:
                candidate_indices.update(self.inverted_index[word])

        scored = []
        for idx in candidate_indices:
            hist_alert = self.alerts[idx]

            # 服务过滤
            if service and hist_alert.get("service") != service:
                continue

            # 只看已解决的
            if only_resolved and hist_alert.get("status") != "resolved":
                continue

            sim = _cosine_similarity(query_tf, self.tf_vectors[idx])

            # 同指标加分
            if hist_alert.get("metric_name") == alert.get("metric_name"):
                sim = min(1.0, sim + 0.15)

            # 同服务加分
            if hist_alert.get("service") == alert.get("service"):
                sim = min(1.0, sim + 0.1)

            # 同主机加分
            if hist_alert.get("host") == alert.get("host"):
                sim = min(1.0, sim + 0.05)

            if sim >= min_score:
                scored.append((idx, sim))

        scored.sort(key=lambda x: x[1], reverse=True)

        results = []
        for idx, score in scored[:top_k]:
            alert_copy = self.alerts[idx].copy()
            alert_copy["similarity_score"] = round(score, 4)
            results.append(alert_copy)

        return results

    def find_by_fingerprint(self, fingerprint: str) -> List[Dict[str, Any]]:
        """按指纹查找相同告警"""
        return [a for a in self.alerts if a.get("fingerprint") == fingerprint]

    def get_alert_frequency(self, metric_name: str, service: str = None, days: int = 30) -> Dict[str, Any]:
        """统计某告警的历史频率"""
        import datetime as dt
        now = datetime.now()
        cutoff = now - dt.timedelta(days=days)

        matched = []
        for alert in self.alerts:
            if alert.get("metric_name") != metric_name:
                continue
            if service and alert.get("service") != service:
                continue
            try:
                starts_at = datetime.fromisoformat(alert["starts_at"])
                if starts_at >= cutoff:
                    matched.append(alert)
            except (ValueError, KeyError):
                continue

        return {
            "metric_name": metric_name,
            "service": service or "all",
            "total_count": len(matched),
            "days": days,
            "average_duration_minutes": round(
                sum(a.get("extra", {}).get("duration_minutes", 0) for a in matched) / max(len(matched), 1),
                1,
            ),
            "severity_distribution": dict(Counter(a.get("severity") for a in matched)),
        }
