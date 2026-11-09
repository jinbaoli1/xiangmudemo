"""
检索层单元测试
"""
import pytest
from app.retrieval.bm25_retriever import BM25Retriever
from app.retrieval.tfidf_retriever import TFIDFRetriever
from app.retrieval.hybrid_search import HybridSearcher, RRFCombiner, SimpleReranker
from app.retrieval.base import RetrievalResult


class TestBM25Retriever:
    """BM25检索器测试"""

    def test_bm25_basic_search(self):
        """测试BM25基本检索"""
        items = [
            {"id": 1, "text": "无线蓝牙耳机 高音质 降噪"},
            {"id": 2, "text": "有线耳机 入耳式 运动"},
            {"id": 3, "text": "智能手机 拍照 长续航"},
        ]
        retriever = BM25Retriever(
            items=items,
            text_extractor=lambda x: x["text"],
        )

        results = retriever.search("无线耳机", top_k=2)
        assert len(results) > 0
        assert results[0].item["id"] == 1

    def test_bm25_empty_query(self):
        """测试空查询"""
        items = [{"id": 1, "text": "测试"}]
        retriever = BM25Retriever(items=items, text_extractor=lambda x: x["text"])
        results = retriever.search("", top_k=10)
        assert len(results) == 0

    def test_bm25_empty_corpus(self):
        """测试空语料库"""
        retriever = BM25Retriever(text_extractor=lambda x: str(x))
        assert retriever.is_built is False
        results = retriever.search("test")
        assert len(results) == 0


class TestTFIDFRetriever:
    """TF-IDF检索器测试"""

    def test_tfidf_basic_search(self):
        """测试TF-IDF基本检索"""
        items = [
            {"id": 1, "text": "无线蓝牙耳机 高音质 主动降噪"},
            {"id": 2, "text": "有线耳机 入耳式 运动跑步"},
            {"id": 3, "text": "智能手机 拍照 长续航"},
        ]
        retriever = TFIDFRetriever(
            items=items,
            text_extractor=lambda x: x["text"],
        )

        results = retriever.search("无线耳机", top_k=2)
        assert len(results) > 0

    def test_tfidf_built_status(self):
        """测试构建状态"""
        retriever = TFIDFRetriever(text_extractor=lambda x: str(x))
        assert retriever.is_built is False

        retriever.build_index([{"text": "test"}])
        assert retriever.is_built is True


class TestRRFCombiner:
    """RRF融合测试"""

    def test_rrf_combine(self):
        """测试RRF融合"""
        combiner = RRFCombiner(k=60)

        list1 = [
            RetrievalResult(item={"id": "A"}, score=1.0, rank=1),
            RetrievalResult(item={"id": "B"}, score=0.8, rank=2),
            RetrievalResult(item={"id": "C"}, score=0.5, rank=3),
        ]
        list2 = [
            RetrievalResult(item={"id": "B"}, score=0.9, rank=1),
            RetrievalResult(item={"id": "A"}, score=0.7, rank=2),
            RetrievalResult(item={"id": "D"}, score=0.6, rank=3),
        ]

        combined = combiner.combine([list1, list2], top_k=10)
        assert len(combined) == 4  # A, B, C, D

    def test_rrf_empty_input(self):
        """测试空输入"""
        combiner = RRFCombiner()
        results = combiner.combine([], top_k=10)
        assert len(results) == 0


class TestSimpleReranker:
    """简易Reranker测试"""

    def test_rerank_basic(self):
        """测试基本重排"""
        reranker = SimpleReranker(
            title_extractor=lambda x: x["title"],
            tag_extractor=lambda x: x.get("tags", []),
            popularity_extractor=lambda x: x.get("sales", 0),
            rating_extractor=lambda x: x.get("rating", 5.0),
        )

        results = [
            RetrievalResult(
                item={"title": "无线蓝牙耳机", "tags": ["热销"], "sales": 1000, "rating": 4.8},
                score=0.8,
                rank=1,
            ),
            RetrievalResult(
                item={"title": "有线耳机", "tags": ["新品"], "sales": 500, "rating": 4.5},
                score=0.6,
                rank=2,
            ),
        ]

        reranked = reranker.rerank(results, query="无线耳机", top_k=10)
        assert len(reranked) == 2
        assert reranked[0].rank == 1
        # 标题匹配的应该排在前面
        assert "蓝牙" in reranked[0].item["title"] or "无线" in reranked[0].item["title"]


class TestHybridSearcher:
    """混合检索器测试"""

    def test_hybrid_search_basic(self):
        """测试混合检索基本功能"""
        items = [
            {"id": 1, "title": "无线蓝牙耳机", "desc": "高音质主动降噪", "tags": ["热销"], "sales": 5000, "rating": 4.8},
            {"id": 2, "title": "有线入耳式耳机", "desc": "运动跑步专用", "tags": ["新品"], "sales": 2000, "rating": 4.5},
            {"id": 3, "title": "智能手机", "desc": "拍照手机长续航", "tags": ["爆款"], "sales": 10000, "rating": 4.9},
        ]

        searcher = HybridSearcher(
            items=items,
            text_extractor=lambda x: f"{x['title']} {x['desc']}",
            title_extractor=lambda x: x["title"],
            tag_extractor=lambda x: x["tags"],
            popularity_extractor=lambda x: float(x["sales"]),
            rating_extractor=lambda x: x["rating"],
        )

        results = searcher.search("无线耳机", top_k=3)
        assert len(results) > 0
        assert searcher.is_built is True
        assert searcher.item_count == 3

    def test_hybrid_search_with_filter(self):
        """测试带过滤的检索"""
        items = [
            {"id": 1, "title": "无线蓝牙耳机 高音质降噪", "tags": ["热销"], "price": 299, "sales": 5000, "rating": 4.8},
            {"id": 2, "title": "有线入耳式耳机 运动跑步", "tags": ["新品"], "price": 89, "sales": 2000, "rating": 4.5},
            {"id": 3, "title": "智能手机 拍照手机 长续航", "tags": ["爆款"], "price": 3999, "sales": 10000, "rating": 4.9},
            {"id": 4, "title": "笔记本电脑 轻薄办公本", "tags": ["热销"], "price": 5999, "sales": 8000, "rating": 4.7},
            {"id": 5, "title": "智能手表 健康监测", "tags": ["新品"], "price": 1299, "sales": 3000, "rating": 4.6},
        ]

        searcher = HybridSearcher(
            items=items,
            text_extractor=lambda x: x["title"],
            title_extractor=lambda x: x["title"],
            tag_extractor=lambda x: x["tags"],
            popularity_extractor=lambda x: float(x["sales"]),
            rating_extractor=lambda x: x["rating"],
        )

        # 过滤价格大于1000的
        results = searcher.search(
            "智能",
            top_k=10,
            filter_fn=lambda x: x["price"] > 1000,
        )
        assert len(results) >= 1
        # 所有结果价格都应大于1000
        for r in results:
            assert r.item["price"] > 1000
