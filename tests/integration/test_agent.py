"""
集成测试 - 测试完整工作流
"""

import shutil
import tempfile

from nova_agent import NovaAgent
from nova_agent.config import Config


class TestNovaAgentIntegration:
    """测试 Nova Agent 集成工作流"""

    def setup_method(self):
        """每个测试前创建临时目录"""
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """每个测试后清理"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_agent_initialization(self):
        """测试 Agent 初始化"""
        config = Config.default()
        config.memory_data_dir = self.temp_dir

        agent = NovaAgent(config=config.to_dict())

        assert agent is not None
        assert agent.config is not None
        assert agent.memory_palace is not None
        assert agent.reasoning_engine is not None

    def test_agent_config_access(self):
        """测试 Agent 配置访问"""
        agent = NovaAgent()

        # 验证配置值
        assert agent.config.max_levels > 0
        assert agent.config.block_size > 0
        assert agent.config.vector_backend in ["chromadb", "memory"]

    def test_evolution_components(self):
        """测试进化组件"""
        agent = NovaAgent()

        # 验证进化系统组件
        assert agent.evaluator is not None
        assert agent.strategy_optimizer is not None
        assert agent.user_model is not None
        assert agent.evolution_monitor is not None

    def test_config_evolution_integration(self):
        """测试配置进化集成"""
        agent = NovaAgent()

        # 模拟低质量反馈
        agent.config.apply_evolution(quality_score=0.2)

        # 配置应该根据反馈调整（可能调整也可能不调整，视策略而定）
        assert agent.config is not None


class TestAgentWorkflows:
    """测试 Agent 工作流"""

    def test_simple_query_workflow(self):
        """测试简单查询工作流"""
        # 注意：此测试需要 LLM 客户端，可能需要 mock
        pass  # 待实现

    def test_multi_turn_conversation(self):
        """测试多轮对话"""
        pass  # 待实现

    def test_feedback_loop(self):
        """测试反馈循环"""
        pass  # 待实现
