"""检索层测试"""
import pytest
from app.retrieval.knowledge_retriever import KnowledgeRetriever, BM25Okapi, TfidfRetriever, _tokenize
from app.retrieval.alert_retriever import AlertRetriever, _cosine_similarity


class TestTokenization:
    """分词测试"""

    def test_tokenize_english(self):
        tokens = _tokenize("CPU usage is high")
        assert "cpu" in tokens
        assert "usage" in tokens
        assert "high" in tokens

    def test_tokenize_chinese(self):
        tokens = _tokenize("CPU使用率过高")
        assert "cpu" in tokens
        # 中文字符应该被分词
        assert len(tokens) > 1

    def test_tokenize_empty(self):
        tokens = _tokenize("")
        assert tokens == []

    def test_tokenize_mixed(self):
        tokens = _tokenize("MySQL慢查询优化慢查询")
        assert "mysql" in tokens


class TestBM25:
    """BM25测试"""

    def test_basic_search(self):
        corpus = [
            ["cpu", "使用率", "过高"],
            ["内存", "溢出", "错误"],
            ["数据库", "连接", "池", "耗尽"],
        ]
        bm25 = BM25Okapi(corpus)
        scores = bm25.get_scores(["cpu", "过高"])
        assert len(scores) == 3
        assert scores[0] > scores[1]
        assert scores[0] > scores[2]

    def test_empty_query(self):
        corpus = [["hello", "world"]]
        bm25 = BM25Okapi(corpus)
        scores = bm25.get_scores([])
        assert scores == [0.0]


class TestTfidfRetriever:
    """TF-IDF测试"""

    def test_basic_search(self):
        corpus = [
            ["cpu", "使用率", "过高", "系统"],
            ["内存", "溢出", "错误", "系统"],
            ["数据库", "连接", "池", "耗尽"],
        ]
        tfidf = TfidfRetriever(corpus)
        scores = tfidf.get_scores(["cpu", "过高"])
        assert len(scores) == 3
        assert scores[0] > 0

    def test_cosine_similarity(self):
        v1 = {"a": 1.0, "b": 2.0}
        v2 = {"a": 1.0, "b": 2.0}
        sim = _cosine_similarity(v1, v2)
        assert abs(sim - 1.0) < 0.001

    def test_cosine_orthogonal(self):
        v1 = {"a": 1.0}
        v2 = {"b": 1.0}
        sim = _cosine_similarity(v1, v2)
        assert sim == 0.0


class TestKnowledgeRetriever:
    """知识库检索器测试"""

    def test_search_returns_results(self, init_test_data):
        from app.services.knowledge_service import get_knowledge_service
        ks = get_knowledge_service()
        results = ks.search_knowledge("CPU使用率过高", top_k=5)
        assert len(results) > 0
        assert "retrieval_score" in results[0]

    def test_search_top_k(self, init_test_data):
        from app.services.knowledge_service import get_knowledge_service
        ks = get_knowledge_service()
        results = ks.search_knowledge("内存", top_k=3)
        assert len(results) <= 3

    def test_search_by_tags(self, init_test_data):
        from app.services.knowledge_service import get_knowledge_service
        ks = get_knowledge_service()
        results = ks.search_knowledge_by_tags(["CPU", "性能"], top_k=5)
        assert isinstance(results, list)

    def test_knowledge_stats(self, init_test_data):
        from app.services.knowledge_service import get_knowledge_service
        ks = get_knowledge_service()
        stats = ks.get_knowledge_stats()
        assert stats["total_entries"] >= 50
        assert "category_distribution" in stats


class TestAlertRetriever:
    """告警检索器测试"""

    def test_find_similar(self, init_test_data, sample_alert):
        from app.services.knowledge_service import get_knowledge_service
        ks = get_knowledge_service()
        similar = ks.find_similar_alerts(sample_alert, top_k=5, service="order-service")
        assert isinstance(similar, list)
        if similar:
            assert "similarity_score" in similar[0]

    def test_alert_frequency(self, init_test_data):
        from app.services.knowledge_service import get_knowledge_service
        ks = get_knowledge_service()
        freq = ks.get_alert_frequency("cpu_usage", service="order-service")
        assert "total_count" in freq
        assert "average_duration_minutes" in freq

    def test_historical_stats(self, init_test_data):
        from app.services.knowledge_service import get_knowledge_service
        ks = get_knowledge_service()
        stats = ks.get_historical_alert_stats()
        assert stats["total_alerts"] >= 200
        assert "severity_distribution" in stats
        assert "status_distribution" in stats
