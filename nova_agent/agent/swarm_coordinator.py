"""
Swarm Coordinator - 群体智能平行推演协调器

MiroFish 启发的群体智能推演：
- 创建 N 个独立智能体
- 每个智能体独立推理，得出结论
- 统计共识与分歧，生成综合报告
- 适合探索性决策、预测类问题
"""

import logging
from concurrent.futures import ThreadPoolExecutor
from typing import Any

logger = logging.getLogger(__name__)


class SwarmCoordinator:
    """
    Swarm Coordinator - 群体智能平行推演

    工作流程：
    1. 接收用户问题/预测需求
    2. 提取种子信息，构建问题背景
    3. 创建 N 个独立智能体，每个独立推演
    4. 收集所有推演结果
    5. 分析共识和分歧，生成综合报告
    """

    def __init__(self, config: dict[str, Any]):
        self.config = config
        self.num_agents = config.get("num_agents", 5)
        self.enable_diversity = config.get("enable_diversity", True)

    def create_swarm_agents(
        self, query: str, context: dict[str, Any], memory_palace, plugin_manager
    ) -> list[dict]:
        """创建群体中的每个智能体，注入不同视角"""
        agents = []

        # 如果开启多样性，给每个智能体不同的角色/视角
        if self.enable_diversity:
            perspectives = self._generate_diverse_perspectives(query)
        else:
            perspectives = [None] * self.num_agents

        for i, perspective in enumerate(perspectives):
            agent_config = self.config.copy()
            if perspective:
                agent_config["perspective"] = perspective

            agents.append(
                {
                    "index": i,
                    "perspective": perspective,
                    "config": agent_config,
                    "memory_palace": memory_palace,
                    "plugin_manager": plugin_manager,
                }
            )

        return agents

    def _generate_diverse_perspectives(self, query: str) -> list[str]:
        """为群体生成多样化视角，促进独立思考"""
        # 典型的多视角
        base_perspectives = [
            "你是乐观主义者，倾向于看到机会和可能性",
            "你是悲观主义者，倾向于看到风险和问题",
            "你是务实主义者，关注可行性和实际执行",
            "你是创新主义者，喜欢寻找非常规方案",
            "你是批评家，从质疑角度审视每个假设",
            "你是决策者，关注如何行动和决策",
            "你是分析师，关注数据和逻辑推理",
            "你是创造者，关注新的可能性和组合",
        ]

        # 返回足够数量，不超过我们需要的
        return base_perspectives[: self.num_agents]

    def run_parallel_deduction(self, swarm_agents: list[dict], query: str) -> list[dict]:
        """并行运行所有智能体的推演"""
        results = []

        with ThreadPoolExecutor(max_workers=len(swarm_agents)) as executor:
            futures = []

            for agent_info in swarm_agents:
                future = executor.submit(self._run_single_agent, agent_info, query)
                futures.append((agent_info["index"], future))

            for idx, future in futures:
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    logger.error(f"Swarm agent {idx} failed: {e}")
                    results.append({"agent_index": idx, "success": False, "error": str(e)})

        # 按索引排序
        results.sort(key=lambda x: x.get("agent_index", 0))
        return results

    def _run_single_agent(self, agent_info: dict, query: str) -> dict:
        """单个智能体独立推演"""
        from ..reasoning.hgarn_engine import HGARNEngine

        perspective = agent_info.get("perspective")
        memory_palace = agent_info["memory_palace"]
        config = agent_info["config"]

        # 独立推理引擎
        engine = HGARNEngine(
            block_size=config.get("block_size", 4),
            max_blocks_per_level=1,
            max_levels=config.get("max_levels", 2),
        )

        # 构建上下文，注入视角
        context = {"query": query}
        if perspective:
            context["perspective"] = perspective

            # 检索相关记忆
        relevant_memories = memory_palace.retrieve(query)
        context["relevant_memories"] = relevant_memories

        # 推理
        result = engine.solve(context)

        return {
            "agent_index": agent_info["index"],
            "perspective": perspective,
            "success": result.success,
            "conclusion": result.final_response,
            "confidence": result.confidence if hasattr(result, "confidence") else None,
        }

    def analyze_consensus(self, results: list[dict]) -> dict[str, Any]:
        """分析结果中的共识和分歧"""
        # 统计成功推演的智能体
        successful = [r for r in results if r["success"]]

        if not successful:
            return {
                "all_failed": True,
                "consensus_level": 0,
                "conclusions": [],
                "report": "所有智能体推演失败，无法生成结论",
            }

        # 这里使用 LLM 分析共识和分歧
        # 在实际聚合中完成
        return {
            "total_agents": len(results),
            "successful_agents": len(successful),
            "results": successful,
        }

    def generate_report(self, analysis: dict[str, Any], query: str) -> str:
        """生成最终综合报告"""
        from ..reasoning.hgarn_engine import HGARNEngine

        engine = HGARNEngine()

        # 让 HGARN 聚合生成综合报告
        context = {
            "query": query,
            "swarm_results": analysis["results"],
            "task": "综合多个智能体的独立推演，分析共识和分歧，给出最终结论",
        }

        result = engine.solve(context)
        return result.final_response

    def run(
        self, query: str, context: dict[str, Any], memory_palace, plugin_manager
    ) -> dict[str, Any]:
        """完整运行群体推演"""
        logger.info(f"SwarmCoordinator starting with {self.num_agents} agents")

        # 1. 创建群体智能体
        swarm_agents = self.create_swarm_agents(query, context, memory_palace, plugin_manager)

        # 2. 并行推演
        results = self.run_parallel_deduction(swarm_agents, query)

        # 3. 分析共识
        analysis = self.analyze_consensus(results)

        # 4. 生成报告
        final_report = self.generate_report(analysis, query)

        return {
            "success": any(r["success"] for r in results),
            "query": query,
            "num_agents": self.num_agents,
            "successful": sum(1 for r in results if r["success"]),
            "individual_results": results,
            "consensus_analysis": analysis,
            "final_report": final_report,
        }
