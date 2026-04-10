"""
NovaAgent - 主入口类

整合所有模块，提供统一的用户接口。
"""

import logging
import os
from typing import Any, Dict, List, Optional

from ..concurrency.dynamic_controller import DynamicConcurrencyController
from ..config import Config
from ..evolution.evaluator import Evaluator
from ..evolution.monitoring import EvolutionMonitor
from ..evolution.optimizer import StrategyOptimizer
from ..evolution.skill_learn import SkillLearner
from ..evolution.user_model import UserModel
from ..execution.sandbox_base import Sandbox
from ..llm.client_base import LLMClient
from ..llm.openclaw_client import OpenClawClient
from ..memory.palace import MemoryPalace
from ..memory.temporal_graph import TemporalFactGraph
from ..reasoning.hgarn_engine import HGARNEngine
from ..tools.plugin_manager import PluginManager

logger = logging.getLogger(__name__)


class NovaAgent:
    """
    Nova Agent - 新一代自主智能体

    特性：
    - 五级宫殿记忆 + 时序事实图谱
    - 层次化门控注意力残差推理 (HGARN)
    - 自主进化闭环：评估 → 优化 → 沉淀 → 增强
    - 四种协作模式满足不同场景：
      1. 单智能体直接回答 - 简单问题
      2. Lead/Sub 主/子分层并行 - 复杂任务分解
      3. Swarm 群体平行推演 - 决策预测探索
      4. Agency 用户参与协作 - 大型项目开发，用户随时介入 (OpenAI Agency 启发)
    - 插件化工具系统，易于扩展
    - Docker 沙箱执行，安全隔离
    - OpenViking 格式兼容
    - 配置自主进化，根据反馈自动调整参数
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None, config_path: Optional[str] = None):
        """
        初始化 Nova Agent

        Args:
            config: 配置字典，覆盖默认配置
            config_path: 从文件加载配置，优先级高于字典
        """
        # 加载配置
        if config_path and os.path.exists(config_path):
            self.config = Config.load(config_path)
        else:
            self.config = Config.default()

        if config:
            self.config.update(config)

        # 初始化记忆系统
        self.memory_palace = MemoryPalace(
            data_dir=self.config.memory_data_dir, vector_backend=self.config.vector_backend
        )
        self.temporal_graph = TemporalFactGraph()

        # 初始化推理引擎（使用配置参数）
        self.reasoning_engine = HGARNEngine(
            block_size=self.config.block_size,
            max_blocks_per_level=self.config.max_blocks_per_level,
            max_levels=self.config.max_levels,
            enable_recursive_decomposition=self.config.enable_recursive_decomposition,
            max_recursion_depth=self.config.max_recursion_depth,
            cumulative_gain_threshold=self.config.cumulative_gain_threshold,
            enable_vector_prefilter=self.config.enable_vector_prefilter,
            vector_similarity_threshold=self.config.vector_similarity_threshold,
            min_gate_for_continue=self.config.min_gate_for_continue,
        )

        # 初始化 LLM 客户端
        self.llm_client = self._init_llm_client()
        # 注入到推理引擎
        self.reasoning_engine.set_llm_client(self.llm_client)

        # 初始化进化系统（完整闭环）
        self.evaluator = Evaluator()
        self.strategy_optimizer = StrategyOptimizer()
        self.skill_learner = SkillLearner(self.memory_palace)
        self.user_model = UserModel()
        self.evolution_monitor = EvolutionMonitor()

        # 并发控制器
        if self.config.enable_dynamic_concurrency:
            self.concurrency_controller = DynamicConcurrencyController(
                min_concurrency=self.config.min_concurrency,
                max_concurrency=self.config.max_concurrency,
                backoff_base=self.config.exponential_backoff_base,
            )

        # 初始化工具系统
        self.plugin_manager = PluginManager()
        self.plugin_manager.load_builtin_plugins()

        # 初始化执行沙箱
        self.sandbox = self._init_sandbox()

        # 统计
        self.total_runs = 0

        # 加载已保存的配置（如果存在）
        self._load_saved_config()

        logger.info(
            f"NovaAgent initialized successfully: "
            f"max_levels={self.config.max_levels}, "
            f"evolution={'enabled' if self.config.evolution_enabled else 'disabled'}"
        )

    def _init_llm_client(self) -> LLMClient:
        """根据配置初始化 LLM 客户端"""
        if self.config.llm_provider == "openclaw":
            return OpenClawClient(self.config.llm_config)
        else:
            raise ValueError(f"Unknown LLM provider: {self.config.llm_provider}")

    def _init_sandbox(self) -> Sandbox:
        """根据配置初始化沙箱"""
        if self.config.sandbox_type == "docker":
            from ..execution.docker_sandbox import DockerSandbox

            return DockerSandbox(self.config.sandbox_config)
        elif self.config.sandbox_type == "local":
            from ..execution.local_sandbox import LocalSandbox

            return LocalSandbox(self.config.sandbox_config)
        else:
            raise ValueError(f"Unknown sandbox type: {self.config.sandbox_type}")

    def _load_saved_config(self):
        """加载已保存的进化配置"""
        config_path = os.path.join(self.config.memory_data_dir, "config_evolved.json")
        if os.path.exists(config_path) and self.config.auto_optimize_config:
            evolved_config = Config.load(config_path)
            # 只覆盖进化相关参数
            self.config.max_levels = evolved_config.max_levels
            self.config.cumulative_gain_threshold = evolved_config.cumulative_gain_threshold
            self.config.lateral_inhibition_base_strength = (
                evolved_config.lateral_inhibition_base_strength
            )
            logger.info("Loaded evolved configuration from previous runs")

    def _save_evolved_config(self):
        """保存进化后的配置"""
        if not self.config.evolution_enabled:
            return
        config_path = os.path.join(self.config.memory_data_dir, "config_evolved.json")
        self.config.save(config_path)

    def run(self, query: str, **kwargs) -> str:
        """
        运行用户查询

        Args:
            query: 用户问题/请求
            **kwargs: 额外参数，覆盖配置

        Returns:
            最终响应文本
        """
        self.total_runs += 1

        # 1. 记忆检索：从宫殿记忆检索相关上下文
        relevant_memories = self.memory_palace.retrieve(
            query, hierarchical_filter=True, contradiction_check=True
        )

        # 2. 时序图谱检索相关事实
        relevant_facts = self.temporal_graph.search_relevant(query)

        # 3. 构建上下文，注入推理引擎
        context = self._build_context(query, relevant_memories, relevant_facts)
        # 注入 LLM 客户端
        context["llm_client"] = self.llm_client

        # 4. HGARN 层次化推理
        result = self.reasoning_engine.solve(context, **kwargs)

        # 5. 如果需要工具调用，执行工具
        if result.needs_tools:
            tool_results = self._execute_tools(result.tool_calls)
            result = self.reasoning_engine.solve_with_tools(context, tool_results, **kwargs)

        # 6. 记录交互用于后续进化
        interaction_record = self._record_interaction(query, result)

        # 7. 记录进化监控
        self.evolution_monitor.record_evaluation(
            task_type=self._classify_task(query),
            success=result.success,
            confidence=result.confidence,
        )

        # 8. 返回最终结果
        return result.final_response

    def _classify_task(self, query: str) -> str:
        """简单任务分类用于监控"""
        query_lower = query.lower()
        if any(w in query_lower for w in ["code", "写代码", "编程", "debug"]):
            return "coding"
        elif any(w in query_lower for w in ["write", "写", "文章", "报告"]):
            return "writing"
        elif any(w in query_lower for w in ["search", "find", "搜索", "查找"]):
            return "search"
        elif any(w in query_lower for w in ["analyze", "分析"]):
            return "analysis"
        else:
            return "general"

    def _build_context(self, query: str, memories: List, facts: List) -> Dict:
        """构建推理上下文"""
        context = {
            "query": query,
            "memories": memories,
            "facts": facts,
            "timestamp": self._get_timestamp(),
            "config": self.config.to_dict(),
        }
        return context

    def _execute_tools(self, tool_calls: List[Dict]) -> List[Dict]:
        """执行工具调用"""
        results = []
        for call in tool_calls:
            plugin = self.plugin_manager.get_plugin(call["plugin_name"])
            if plugin:
                result = plugin.execute(call["parameters"], sandbox=self.sandbox)
                results.append(
                    {
                        "plugin_name": call["plugin_name"],
                        "result": result,
                        "success": result.success,
                    }
                )
            else:
                results.append(
                    {
                        "plugin_name": call["plugin_name"],
                        "error": f"Plugin not found: {call['plugin_name']}",
                        "success": False,
                    }
                )
        return results

    def _record_interaction(self, query: str, result) -> Dict:
        """记录交互用于进化"""
        record = {
            "query": query,
            "result": result.final_response,
            "success": result.success,
            "confidence": result.confidence,
            "timestamp": self._get_timestamp(),
            "tools_used": result.tools_used if hasattr(result, "tools_used") else [],
            "num_blocks": result.num_blocks,
            "num_levels": result.num_levels,
        }

        # 存储到记忆宫殿
        self.memory_palace.add_interaction(record)

        # 更新用户模型
        self.user_model.record_interaction(query, result.final_response, None)

        return record

    def feedback(self, query: str, response: str, rating: int, comment: str = "") -> Dict:
        """
        用户反馈，触发自主进化

        Args:
            query: 原始查询
            response: Agent 响应
            rating: 评分 1-5
            comment: 可选评论

        Returns:
            进化结果，包含变更
        """
        # 评估质量
        evaluation = self.evaluator.evaluate(
            query=query, response=response, rating=rating, comment=comment
        )

        # 如果评分足够高，沉淀为技能
        if (
            evaluation.should_learn
            and evaluation.quality_score >= self.config.min_quality_for_learning
        ):
            skill_id = self.skill_learner.learn_from_example(query, response, evaluation)
            logger.info(f"Learned new skill: {skill_id}")

        # 自主进化配置参数
        changes = {}
        if self.config.evolution_enabled and self.config.auto_optimize_config:
            original_config = self.config.to_dict()
            changes = self.config.apply_evolution(evaluation.quality_score)
            if changes:
                # 保存进化后的配置
                self._save_evolved_config()
                logger.info(f"Configuration evolved: {len(changes)} parameters changed")

        # 更新用户画像
        self.user_model.record_interaction(query, response, rating)

        # 记录进化步骤
        before_rate = self.evolution_monitor.get_success_rate()
        after_rate = self.evolution_monitor.get_success_rate()
        num_skills = len(self.skill_learner.list_learned_skills())
        self.evolution_monitor.record_evolution_step(
            before_rate,
            after_rate,
            1 if evaluation.should_learn else 0,
            f"Feedback rating {rating}",
        )

        logger.info(f"Feedback processed: rating={rating}, changes={len(changes)}")

        return {
            "success": True,
            "evaluation": evaluation,
            "configuration_changes": changes,
            "skill_learned": evaluation.should_learn,
            "evolution_report": self.evolution_monitor.generate_report(),
        }

    def get_config(self) -> Dict[str, Any]:
        """获取当前配置"""
        return self.config.to_dict()

    def update_config(self, changes: Dict[str, Any]) -> None:
        """手动更新配置"""
        self.config.update(changes)
        self._save_evolved_config()
        logger.info(f"Manual config update: {list(changes.keys())}")

    def save_config(self, path: str) -> None:
        """保存配置到文件"""
        self.config.save(path)

    def load_plugin(self, plugin_path: str) -> bool:
        """加载外部插件"""
        return self.plugin_manager.load_plugin_from_path(plugin_path)

    def get_memory_status(self) -> Dict[str, Any]:
        """获取记忆系统状态"""
        return {
            "palace_stats": self.memory_palace.get_stats(),
            "graph_stats": self.temporal_graph.get_stats(),
            "evolution_stats": self.evolution_monitor.get_stats(),
            "user_model_stats": self.user_model.get_stats(),
            "current_config": self.get_config(),
        }

    def get_evolution_report(self) -> str:
        """生成进化报告"""
        return self.evolution_monitor.generate_report()

    def _get_timestamp(self) -> str:
        """获取当前时间戳"""
        from datetime import datetime

        return datetime.utcnow().isoformat()
