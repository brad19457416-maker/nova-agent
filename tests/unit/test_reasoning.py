"""
推理引擎单元测试
"""

from nova_agent.reasoning.bidirectional_attn import BidirectionalAttentionFlow
from nova_agent.reasoning.confidence_routing import ConfidenceRouter
from nova_agent.reasoning.gated_residual import GatedResidualAggregator
from nova_agent.reasoning.hgarn_engine import HGARNEngine
from nova_agent.reasoning.wta import WTASelection


class TestGatedResidualAggregator:
    """测试门控残差聚合器"""

    def test_aggregator_creation(self):
        """测试聚合器创建"""
        aggregator = GatedResidualAggregator()
        assert aggregator is not None

    def test_simple_aggregation(self):
        """测试简单聚合"""
        aggregator = GatedResidualAggregator()

        # 模拟子任务结果
        subtask_results = [
            {"content": "结果1", "result": "详细结果1", "confidence": 0.8},
            {"content": "结果2", "result": "详细结果2", "confidence": 0.9},
        ]

        context = {"task": "测试任务"}
        result = aggregator.aggregate(subtask_results, level=1, context=context)
        assert result is not None


class TestConfidenceRouter:
    """测试置信度路由器"""

    def test_router_creation(self):
        """测试路由器创建"""
        router = ConfidenceRouter(min_gate=0.15, cumulative_threshold=2.5)
        assert router is not None
        assert router.min_gate == 0.15

    def test_should_continue(self):
        """测试是否继续推理"""
        router = ConfidenceRouter(min_gate=0.15, cumulative_threshold=2.5)

        # 累积增益足够高，应该停止
        assert router.should_continue(0.5, 3.0) is False

        # 累积增益不够，应该继续
        assert router.should_continue(0.5, 1.0) is True

        # 当前增益太小，应该停止
        assert router.should_continue(0.1, 1.0) is False

    def test_filter_by_confidence(self):
        """测试按置信度过滤"""
        router = ConfidenceRouter(min_gate=0.5)

        blocks = [
            {"id": 1, "confidence": 0.9},
            {"id": 2, "confidence": 0.3},
            {"id": 3, "confidence": 0.8},
        ]

        filtered = router.filter_by_confidence(blocks, min_confidence=0.5)
        assert len(filtered) == 2
        assert all(b["confidence"] >= 0.5 for b in filtered)


class TestBidirectionalAttentionFlow:
    """测试双向注意力流"""

    def test_attention_flow_creation(self):
        """测试注意力流创建"""
        flow = BidirectionalAttentionFlow(enabled=True, reverse_threshold=0.3)
        assert flow is not None
        assert flow.enabled is True
        assert flow.reverse_threshold == 0.3

    def test_is_enabled(self):
        """测试启用状态"""
        flow_enabled = BidirectionalAttentionFlow(enabled=True)
        flow_disabled = BidirectionalAttentionFlow(enabled=False)

        assert flow_enabled.is_enabled() is True
        assert flow_disabled.is_enabled() is False


class TestWTASelection:
    """测试赢者通吃选择"""

    def test_wta_creation(self):
        """测试WTA创建"""
        wta = WTASelection(max_activate=7)
        assert wta is not None
        assert wta.max_activate == 7

    def test_select_with_query(self):
        """测试使用查询选择"""
        wta = WTASelection(max_activate=3)

        items = [
            {"id": 1, "similarity": 0.5},
            {"id": 2, "similarity": 0.9},
            {"id": 3, "similarity": 0.3},
            {"id": 4, "similarity": 0.8},
            {"id": 5, "similarity": 0.7},
        ]

        selected = wta.select(items, query="测试查询")
        assert len(selected) <= 3
        # 最高分应该被选中
        assert items[1] in selected  # similarity 0.9

    def test_select_no_similarity(self):
        """测试没有similarity字段的情况"""
        wta = WTASelection(max_activate=2)

        items = [
            {"id": 1, "gain": 0.5},
            {"id": 2, "gain": 0.9},
            {"id": 3, "gain": 0.3},
        ]

        selected = wta.select(items, query="测试")
        assert len(selected) <= 2


class TestHGARNEngine:
    """测试HGARN推理引擎"""

    def test_engine_creation(self):
        """测试引擎创建"""
        engine = HGARNEngine(block_size=8, max_blocks_per_level=2, max_levels=3)
        assert engine is not None
        assert engine.block_size == 8

    def test_engine_components(self):
        """测试引擎组件"""
        engine = HGARNEngine()

        assert engine.gated_aggregator is not None
        assert engine.bidirectional_attn is not None
        assert engine.confidence_router is not None
        assert engine.wta is not None
