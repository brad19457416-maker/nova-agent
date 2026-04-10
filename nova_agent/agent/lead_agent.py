"""
Lead Agent - 主协调 Agent

DeerFlow 启发的主/子分层协作架构：
- Lead Agent 负责任务分解、规划、结果聚合
- Sub Agent 各自执行子任务，独立上下文隔离
"""

from typing import Dict, Any, List, Optional
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

from ..reasoning.task_decomposition import TaskDecomposer
from .sub_agent import SubAgent
from ..concurrency.dynamic_controller import DynamicConcurrencyController

logger = logging.getLogger(__name__)


class LeadAgent:
    """
    Lead Agent - 主协调者
    
    负责：
    1. 接收用户完整任务
    2. 分解为多个子任务
    3. 动态生成 Sub Agent 并行执行
    4. 聚合所有子任务结果
    5. 生成最终输出
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.decomposer = TaskDecomposer()
        self.concurrency_controller = DynamicConcurrencyController(
            min_concurrency=config.get("min_concurrency", 1),
            max_concurrency=config.get("max_concurrency", 8)
        )
    
    def decompose_task(self, query: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """将完整任务分解为子任务"""
        return self.decomposer.decompose(query, context)
    
    def execute_parallel(self, sub_tasks: List[Dict[str, Any]], 
                       memory_palace, plugin_manager) -> List[Dict[str, Any]]:
        """并行执行多个子任务"""
        results = []
        current_concurrency = self.concurrency_controller.get_current_concurrency()
        
        with ThreadPoolExecutor(max_workers=current_concurrency) as executor:
            futures = []
            
            for task in sub_tasks:
                sub_agent = SubAgent(
                    task=task,
                    memory_palace=memory_palace,
                    plugin_manager=plugin_manager,
                    config=self.config
                )
                futures.append(executor.submit(sub_agent.execute))
            
            for future in as_completed(futures):
                try:
                    result = future.result()
                    results.append(result)
                    self.concurrency_controller.on_success()
                except Exception as e:
                    logger.error(f"SubAgent execution failed: {e}")
                    results.append({
                        "success": False,
                        "error": str(e)
                    })
                    self.concurrency_controller.on_failure()
        
        # 按原始任务顺序排序结果
        results.sort(key=lambda x: x.get("task_index", 0))
        return results
    
    def aggregate_results(self, sub_results: List[Dict[str, Any]], 
                         original_query: str, context: Dict[str, Any]) -> str:
        """聚合所有子任务结果生成最终回答"""
        # 使用 HGARN 聚合
        from ..reasoning.gated_residual import GatedResidualAggregator
        
        aggregator = GatedResidualAggregator()
        final_response = aggregator.aggregate(
            sub_results=sub_results,
            query=original_query,
            context=context
        )
        return final_response
    
    def run(self, query: str, context: Dict[str, Any], 
           memory_palace, plugin_manager) -> Dict[str, Any]:
        """完整运行主/子模式"""
        
        # 1. 分解任务
        logger.info(f"LeadAgent decomposing task: {query[:100]}...")
        sub_tasks = self.decompose_task(query, context)
        logger.info(f"Decomposed into {len(sub_tasks)} sub-tasks")
        
        # 2. 并行执行
        results = self.execute_parallel(sub_tasks, memory_palace, plugin_manager)
        
        # 3. 聚合结果
        final_response = self.aggregate_results(results, query, context)
        
        return {
            "success": all(r.get("success", False) for r in results),
            "sub_tasks": sub_tasks,
            "sub_results": results,
            "final_response": final_response
        }
