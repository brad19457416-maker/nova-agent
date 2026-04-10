"""
Lead/Sub协作实现

主从协作模式：
- Lead负责分解任务、分配任务、汇总结果
- Sub负责执行具体子任务

使用示例:
    collab = LeadSubCollaboration(llm_client)
    
    result = await collab.execute(
        task="实现用户认证系统",
        config={"max_subs": 3}
    )
"""

import asyncio
from typing import Dict, List, Any, Optional
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
import uuid
import logging

from .roles import Agent, AgentRole, AgentState, Task

logger = logging.getLogger(__name__)


@dataclass
class LeadSubResult:
    """Lead/Sub执行结果"""
    task: str
    subtasks_count: int
    sub_results: List[Dict]
    final_result: Any
    duration_ms: float
    metadata: Dict = field(default_factory=dict)


class LeadSubCollaboration:
    """
    Lead/Sub协作实现
    
    工作流程:
    1. Lead分解任务
    2. 创建Sub Agents
    3. 并行执行子任务
    4. Lead汇总结果
    """
    
    def __init__(self, llm_client, max_subs: int = 5):
        self.llm = llm_client
        self.max_subs = max_subs
        self.agents: Dict[str, Agent] = {}
        self.tasks: Dict[str, Task] = {}
    
    async def execute(self, task: str, config: Dict = None) -> LeadSubResult:
        """
        执行Lead/Sub协作
        
        Args:
            task: 主任务描述
            config: 配置
                - max_subs: 最大Sub数量
                - parallel: 是否并行执行
                - aggregation_strategy: 汇总策略
        
        Returns:
            LeadSubResult: 执行结果
        """
        start_time = datetime.now()
        config = config or {}
        max_subs = config.get("max_subs", self.max_subs)
        parallel = config.get("parallel", True)
        
        logger.info(f"Lead/Sub协作开始: {task}")
        
        # 1. Leader分解任务
        subtasks = await self._decompose_task(task, max_subs)
        
        # 2. 创建Sub Agents
        subs = await self._create_sub_agents(subtasks)
        
        # 3. 执行子任务
        if parallel:
            sub_results = await self._execute_parallel(subs)
        else:
            sub_results = await self._execute_sequential(subs)
        
        # 4. Leader汇总
        final_result = await self._synthesize_results(task, sub_results, config)
        
        duration_ms = (datetime.now() - start_time).total_seconds() * 1000
        
        logger.info(f"Lead/Sub协作完成: {task} ({duration_ms:.0f}ms)")
        
        return LeadSubResult(
            task=task,
            subtasks_count=len(subtasks),
            sub_results=sub_results,
            final_result=final_result,
            duration_ms=duration_ms,
            metadata={
                "strategy": "parallel" if parallel else "sequential",
                "successful_subs": len([r for r in sub_results if not r.get("error")])
            }
        )
    
    async def _decompose_task(self, task: str, max_subs: int) -> List[str]:
        """
        Leader分解任务
        
        简化实现：根据任务类型返回预设的子任务模板
        """
        # 模拟任务分解
        # 实际应该调用LLM进行智能分解
        
        # 根据关键词判断任务类型
        if "代码" in task or "实现" in task or "开发" in task:
            return [
                "分析需求",
                "设计接口",
                "实现核心功能",
                "编写测试"
            ][:max_subs]
        
        elif "调研" in task or "研究" in task:
            return [
                "收集背景信息",
                "查找相关资料",
                "分析对比",
                "形成结论"
            ][:max_subs]
        
        elif "写作" in task or "写" in task:
            return [
                "规划大纲",
                "撰写初稿",
                "修订完善",
                "润色定稿"
            ][:max_subs]
        
        else:
            # 默认分解
            return [
                "理解任务",
                "分析需求",
                "制定方案",
                "执行实现"
            ][:max_subs]
    
    async def _create_sub_agents(self, subtasks: List[str]) -> List[Agent]:
        """创建Sub Agents"""
        agents = []
        
        for i, subtask in enumerate(subtasks):
            agent_id = f"sub_{i}"
            agent = Agent(
                id=agent_id,
                role=AgentRole.SUB,
                state=AgentState.IDLE,
                context={"task": subtask, "index": i}
            )
            agents.append(agent)
            self.agents[agent_id] = agent
            
            # 创建任务
            task_id = f"task_{i}"
            self.tasks[task_id] = Task(
                id=task_id,
                description=subtask,
                assigned_to=agent_id
            )
        
        logger.info(f"Created {len(agents)} sub agents")
        return agents
    
    async def _execute_parallel(self, subs: List[Agent]) -> List[Dict]:
        """并行执行子任务"""
        results = await asyncio.gather(*[
            self._execute_sub(agent) for agent in subs
        ])
        return results
    
    async def _execute_sequential(self, subs: List[Agent]) -> List[Dict]:
        """串行执行子任务"""
        results = []
        for agent in subs:
            result = await self._execute_sub(agent)
            results.append(result)
        return results
    
    async def _execute_sub(self, agent: Agent) -> Dict:
        """执行子任务"""
        agent.state = AgentState.WORKING
        
        try:
            task = agent.context.get("task", "")
            
            # 简化实现：直接返回模拟结果
            # 实际应该调用LLM执行任务
            result = await self._simulate_subtask(task, agent.id)
            
            agent.state = AgentState.COMPLETED
            agent.result = result
            
            return {
                "agent_id": agent.id,
                "task": task,
                "result": result,
                "status": "completed"
            }
            
        except Exception as e:
            agent.state = AgentState.FAILED
            agent.error = str(e)
            
            logger.error(f"Sub agent failed: {agent.id} - {e}")
            
            return {
                "agent_id": agent.id,
                "task": agent.context.get("task", ""),
                "error": str(e),
                "status": "failed"
            }
    
    async def _simulate_subtask(self, task: str, agent_id: str) -> str:
        """模拟子任务执行"""
        # 模拟执行时间
        await asyncio.sleep(0.01)
        
        # 根据任务类型返回模拟结果
        if "分析" in task:
            return f"[{agent_id}] 分析完成：..."
        elif "设计" in task:
            return f"[{agent_id}] 设计方案：..."
        elif "实现" in task:
            return f"[{agent_id}] 代码实现：..."
        else:
            return f"[{agent_id}] 任务完成：{task}"
    
    async def _synthesize_results(
        self, 
        original_task: str, 
        sub_results: List[Dict],
        config: Dict
    ) -> str:
        """
        Leader汇总结果
        
        简化实现：合并所有子结果
        """
        strategy = config.get("aggregation_strategy", "concatenate")
        
        if strategy == "concatenate":
            # 简单拼接
            parts = []
            for r in sub_results:
                if "result" in r:
                    parts.append(f"## {r['task']}\n{r['result']}")
            
            return f"# 任务完成：{original_task}\n\n" + "\n\n".join(parts)
        
        elif strategy == "summary":
            # 生成摘要
            return f"任务 '{original_task}' 已完成。共执行 {len(sub_results)} 个子任务。"
        
        else:
            # 默认返回结果列表
            return {
                "task": original_task,
                "sub_results": sub_results
            }