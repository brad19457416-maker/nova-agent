"""
记忆系统单元测试
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from nova_agent.memory.palace import MemoryPalace
from nova_agent.memory.temporal_graph import TemporalFactGraph, Fact


class TestMemoryPalace:
    """测试记忆宫殿"""

    def setup_method(self):
        """每个测试前创建临时目录"""
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """每个测试后清理"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_palace_creation(self):
        """测试记忆宫殿创建"""
        palace = MemoryPalace(data_dir=self.temp_dir, vector_backend="memory")
        assert palace is not None
        assert isinstance(palace.data_dir, Path)
        assert str(palace.data_dir) == self.temp_dir

    def test_add_memory(self):
        """测试添加记忆"""
        palace = MemoryPalace(data_dir=self.temp_dir, vector_backend="memory")

        # 添加记忆
        memory_id = palace.add_memory(
            wing="narrative",
            room="plot",
            hall="events",
            content="测试内容",
            compressed=False
        )

        assert memory_id is not None
        assert isinstance(memory_id, str)

    def test_retrieve_from_palace(self):
        """测试从宫殿检索"""
        palace = MemoryPalace(data_dir=self.temp_dir, vector_backend="memory")

        # 添加记忆
        palace.add_memory(
            wing="narrative",
            room="plot",
            hall="events",
            content="测试内容关于人工智能",
            compressed=False
        )

        # 使用检索器检索
        results = palace.retriever.retrieve(
            query="人工智能",
            wing="narrative",
            room="plot"
        )

        assert isinstance(results, list)


class TestTemporalFactGraph:
    """测试时序事实图谱"""

    def test_graph_creation(self):
        """测试图谱创建"""
        graph = TemporalFactGraph()
        assert graph is not None
        assert len(graph.facts) == 0

    def test_add_fact(self):
        """测试添加事实"""
        graph = TemporalFactGraph()
        fact = graph.add_fact(
            subject="许乐",
            predicate="身份",
            object_="帝国皇子",
            confidence=0.9,
            source="第一章"
        )

        assert fact is not None
        assert fact.subject == "许乐"
        assert fact.predicate == "身份"
        assert fact.object_ == "帝国皇子"
        assert fact.confidence == 0.9
        assert fact.fact_id is not None

    def test_get_current_facts(self):
        """测试获取当前事实"""
        graph = TemporalFactGraph()

        # 添加多个事实
        graph.add_fact("许乐", "身份", "机修师", confidence=0.8)
        graph.add_fact("许乐", "能力", "格斗", confidence=0.9)

        # 获取关于许乐的所有事实
        facts = graph.get_current_facts("许乐")
        assert len(facts) == 2

    def test_get_facts_by_predicate(self):
        """测试按谓词获取事实"""
        graph = TemporalFactGraph()

        graph.add_fact("许乐", "身份", "机修师")
        graph.add_fact("施清海", "身份", "特工")
        graph.add_fact("许乐", "能力", "格斗")

        # 获取所有身份相关事实
        identity_facts = graph.get_current_facts("许乐", predicate="身份")
        assert len(identity_facts) == 1
        assert identity_facts[0].object_ == "机修师"

    def test_fact_validity(self):
        """测试事实有效性"""
        graph = TemporalFactGraph()

        # 添加事实
        fact = graph.add_fact(
            "许乐",
            "位置",
            "钟楼街",
            start_time="2024-01-01T00:00:00"
        )

        # 检查有效性
        assert fact.is_valid_at("2024-06-01T00:00:00") is True

    def test_fact_replacement(self):
        """测试事实替换（相同subject+predicate）"""
        graph = TemporalFactGraph()

        # 添加第一个事实
        fact1 = graph.add_fact("许乐", "位置", "钟楼街", start_time="2024-01-01")

        # 添加第二个事实（会自动关闭第一个）
        fact2 = graph.add_fact("许乐", "位置", "首都", start_time="2024-06-01")

        # 第一个事实应该被关闭
        assert fact1.end_time is not None
        # 第二个事实应该有效
        assert fact2.end_time is None

    def test_query_by_time(self):
        """测试按时间查询"""
        graph = TemporalFactGraph()

        # 添加带时间的事实
        graph.add_fact("许乐", "位置", "钟楼街", start_time="2024-01-01T00:00:00")
        graph.add_fact("许乐", "位置", "首都", start_time="2024-06-01T00:00:00")

        # 查询特定时间点的事实
        facts_at_time = graph.query_by_time("许乐", "2024-03-01T00:00:00")
        assert len(facts_at_time) == 1
        assert facts_at_time[0].object_ == "钟楼街"

    def test_get_timeline(self):
        """测试获取时间线"""
        graph = TemporalFactGraph()

        # 添加带时间的事实
        graph.add_fact("许乐", "位置", "钟楼街", start_time="2024-01-01")
        graph.add_fact("许乐", "位置", "首都", start_time="2024-06-01")

        # 获取许乐位置的时间线
        timeline = graph.get_timeline("许乐", "位置")
        assert len(timeline) == 2
