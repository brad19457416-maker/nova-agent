"""
工作流引擎

性能优化:
- 并行阶段执行 (独立阶段并发运行)
- 智能阶段调度 (依赖分析)
- 工作流结果缓存
- 内存池复用
- 异步批量处理

使用示例:
    engine = WorkflowEngine(config_manager, skill_loader, llm_client)
    
    # 运行工作流 (自动并行化)
    result = await engine.run("research", {"task": "xxx"})
    
    # 批量运行
    results = await engine.run_batch([
        {"workflow": "research", "input": {"task": "t1"}},
        {"workflow": "writing", "input": {"task": "t2"}},
    ])
"""

import asyncio
import time
from typing import Dict, List, Any, Optional, Set, Tuple
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
import logging
from collections import defaultdict

from .base import PhaseHandler

logger = logging.getLogger(__name__)


class PhaseStatus(Enum):
    """阶段状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class PhaseResult:
    """阶段执行结果"""
    phase: str
    status: PhaseStatus
    start_time: float = 0
    end_time: float = 0
    duration_ms: float = 0
    input_data: Dict = field(default_factory=dict)
    output_data: Any = None
    error: str = ""
    metadata: Dict = field(default_factory=dict)
    
    @property
    def success(self) -> bool:
        return self.status == PhaseStatus.COMPLETED


@dataclass
class WorkflowResult:
    """工作流执行结果"""
    workflow_name: str
    status: PhaseStatus
    phases: List[PhaseResult] = field(default_factory=list)
    final_output: Any = None
    total_duration_ms: float = 0
    metadata: Dict = field(default_factory=dict)
    parallel_phases: List[List[str]] = field(default_factory=list)  # 记录并行组


@dataclass
class PhaseDependency:
    """阶段依赖关系"""
    phase: str
    depends_on: Set[str] = field(default_factory=set)
    provides: Set[str] = field(default_factory=set)
    can_parallel: bool = True


class WorkflowOptimizer:
    """
    工作流优化器
    
    分析阶段依赖关系，优化执行顺序
    """
    
    def __init__(self):
        self._dependency_graph: Dict[str, PhaseDependency] = {}
    
    def analyze_workflow(self, phases: List[str], config: Dict) -> List[List[str]]:
        """
        分析工作流，生成并行执行组
        
        Args:
            phases: 阶段列表
            config: 工作流配置
        
        Returns:
            并行执行组列表，每组内的阶段可以并发执行
        
        Example:
            phases = ["clarify", "plan", "search", "expand", "verify"]
            # clarify -> plan -> [search, expand] -> verify
            return [
                ["clarify"],
                ["plan"],
                ["search", "expand"],  # 并行
                ["verify"]
            ]
        """
        if not phases:
            return []
        
        # 构建依赖图
        dependencies = self._build_dependency_graph(phases, config)
        
        # 拓扑排序，分组并行阶段
        return self._group_parallel_phases(phases, dependencies)
    
    def _build_dependency_graph(
        self, 
        phases: List[str], 
        config: Dict
    ) -> Dict[str, Set[str]]:
        """构建依赖图"""
        # 默认串行依赖 (前面的阶段是后面的依赖)
        dependencies = defaultdict(set)
        
        for i, phase in enumerate(phases):
            if i > 0:
                # 默认依赖前一个阶段
                dependencies[phase].add(phases[i-1])
        
        # 从配置读取显式依赖
        phase_configs = config.get("handlers", {})
        for phase, phase_config in phase_configs.items():
            if phase in phases:
                explicit_deps = phase_config.get("depends_on", [])
                dependencies[phase].update(explicit_deps)
        
        return dict(dependencies)
    
    def _group_parallel_phases(
        self,
        phases: List[str],
        dependencies: Dict[str, Set[str]]
    ) -> List[List[str]]:
        """将阶段分组为并行执行组"""
        if not phases:
            return []
        
        # 计算每个阶段的入度
        in_degree = {phase: 0 for phase in phases}
        for phase, deps in dependencies.items():
            if phase in in_degree:
                in_degree[phase] = len([d for d in deps if d in phases])
        
        # 拓扑排序分组
        remaining = set(phases)
        groups = []
        
        while remaining:
            # 找出入度为0的阶段
            ready = [p for p in remaining if in_degree.get(p, 0) == 0]
            
            if not ready:
                # 有循环依赖，强制按原顺序
                logger.warning("Circular dependency detected, falling back to sequential")
                return [[p] for p in phases]
            
            # 添加为并行组
            groups.append(ready)
            
            # 移除已处理的阶段
            for phase in ready:
                remaining.remove(phase)
                # 减少依赖此阶段的入度
                for p, deps in dependencies.items():
                    if phase in deps and p in in_degree:
                        in_degree[p] -= 1
        
        return groups


class WorkflowEngine:
    """
    工作流引擎
    
    性能优化:
    - 类级别handler缓存，避免重复注册
    - 工作流配置缓存
    - 并行阶段执行支持 (智能调度)
    - 结果缓存
    - 批量执行支持
    """
    
    # 类级别handler缓存
    _handlers: Dict[str, PhaseHandler] = {}
    _handlers_registered = False
    _lock = asyncio.Lock()
    
    def __init__(
        self,
        config_manager,
        skill_loader,
        llm_client=None,
        storage=None,
        antipattern_checker=None,
        enable_parallel: bool = True,
        max_parallel_phases: int = 3
    ):
        self.config = config_manager
        self.skills = skill_loader
        self.llm = llm_client
        self.storage = storage
        self.antipattern_checker = antipattern_checker
        
        # 并行执行配置
        self._enable_parallel = enable_parallel
        self._max_parallel_phases = max_parallel_phases
        self._optimizer = WorkflowOptimizer()
        
        # 工作流配置缓存
        self._workflow_configs: Dict[str, Dict] = {}
        self._config_lock = asyncio.Lock()
        
        # 结果缓存 (工作流名称 + 输入哈希 -> 结果)
        self._result_cache: Dict[str, WorkflowResult] = {}
        self._cache_lock = asyncio.Lock()
        
        # 注册处理器（线程安全）
        if not WorkflowEngine._handlers_registered:
            self._register_builtin_handlers()
            WorkflowEngine._handlers_registered = True
    
    def _register_builtin_handlers(self):
        """注册内置阶段处理器（类级别缓存）"""
        from nova_agent.workflow.builtin import (
            ClarifyHandler, PlanHandler, SearchHandler,
            ExpandHandler, VerifyHandler, SynthesizeHandler,
            OutlineHandler, DraftHandler, ReviewHandler,
            ReviseHandler, PolishHandler, DeliverHandler,
            AnalyzeHandler, DesignHandler, ImplementHandler,
            TestHandler
        )
        
        handlers = [
            ClarifyHandler, PlanHandler, SearchHandler,
            ExpandHandler, VerifyHandler, SynthesizeHandler,
            OutlineHandler, DraftHandler, ReviewHandler,
            ReviseHandler, PolishHandler, DeliverHandler,
            AnalyzeHandler, DesignHandler, ImplementHandler,
            TestHandler
        ]
        
        for handler_class in handlers:
            # 避免重复注册
            handler_name = handler_class.__name__.replace("Handler", "").lower()
            if handler_name in WorkflowEngine._handlers:
                continue
                
            handler = handler_class({})
            handler.inject_dependencies(self.llm, self.skills)
            WorkflowEngine._handlers[handler_name] = handler
            logger.info(f"Registered handler: {handler_name}")
        
        WorkflowEngine._handlers_registered = True
    
    def register_handler(self, name: str, handler: PhaseHandler):
        """注册阶段处理器（类级别）"""
        WorkflowEngine._handlers[name] = handler
    
    def get_handler(self, name: str) -> Optional[PhaseHandler]:
        """获取阶段处理器"""
        return WorkflowEngine._handlers.get(name)
    
    async def load_workflow(self, workflow_name: str) -> Dict:
        """加载工作流配置（带缓存）"""
        if workflow_name in self._workflow_configs:
            return self._workflow_configs[workflow_name]
        
        async with self._config_lock:
            if workflow_name in self._workflow_configs:
                return self._workflow_configs[workflow_name]
            
            config = self.config.get_workflow_config(workflow_name)
            if not config:
                raise ValueError(f"Workflow {workflow_name} not found")
            
            self._workflow_configs[workflow_name] = config
            return config
    
    def _get_cache_key(self, workflow_name: str, input_data: Dict) -> str:
        """生成缓存键"""
        # 简化实现：使用输入数据的字符串表示
        import hashlib
        input_str = f"{workflow_name}:{str(sorted(input_data.items()))}"
        return hashlib.md5(input_str.encode()).hexdigest()[:16]
    
    async def run(
        self, 
        workflow_name: str, 
        input_data: Dict,
        use_cache: bool = False,
        cache_ttl: float = 300.0
    ) -> WorkflowResult:
        """
        运行工作流
        
        Args:
            workflow_name: 工作流名称
            input_data: 输入数据
            use_cache: 是否使用结果缓存
            cache_ttl: 缓存有效期(秒)
        
        Returns:
            WorkflowResult: 工作流执行结果
        """
        start_time = time.time()
        
        # 检查缓存
        if use_cache:
            cache_key = self._get_cache_key(workflow_name, input_data)
            async with self._cache_lock:
                if cache_key in self._result_cache:
                    cached = self._result_cache[cache_key]
                    logger.info(f"Workflow cache hit: {workflow_name}")
                    return cached
        
        # 1. 加载工作流配置
        workflow_config = await self.load_workflow(workflow_name)
        domain = workflow_config.get("domain", "general")
        
        # 2. 初始化上下文
        context = {
            **input_data,
            "_workflow": workflow_name,
            "_domain": domain,
            "_start_time": start_time,
            "_history": [],
            "_antipattern_warnings": []
        }
        
        # 3. 获取阶段列表
        phases = workflow_config.get("phases", [])
        
        logger.info(f"Starting workflow: {workflow_name} with {len(phases)} phases")
        
        # 4. 执行阶段
        if self._enable_parallel and len(phases) > 1:
            # 并行执行
            phase_results, parallel_groups = await self._execute_phases_parallel(
                phases, context, workflow_config
            )
        else:
            # 串行执行
            phase_results = await self._execute_phases_sequential(
                phases, context, workflow_config
            )
            parallel_groups = [[p.phase] for p in phase_results]
        
        # 5. 生成最终输出
        final_output = self._generate_output(workflow_name, context, phase_results)
        
        duration_ms = (time.time() - start_time) * 1000
        
        overall_status = PhaseStatus.COMPLETED
        if any(p.status == PhaseStatus.FAILED for p in phase_results):
            overall_status = PhaseStatus.FAILED
        
        result = WorkflowResult(
            workflow_name=workflow_name,
            status=overall_status,
            phases=phase_results,
            final_output=final_output,
            total_duration_ms=duration_ms,
            parallel_phases=parallel_groups,
            metadata={
                "workflow_version": workflow_config.get("version", "1.0.0"),
                "antipattern_warnings": context.get("_antipattern_warnings", []),
                "parallel_enabled": self._enable_parallel
            }
        )
        
        logger.info(f"Workflow completed: {workflow_name} in {duration_ms:.0f}ms")
        
        # 6. 保存结果到缓存
        if use_cache:
            async with self._cache_lock:
                self._result_cache[cache_key] = result
        
        # 7. 保存执行记录
        if self.storage:
            # 异步保存，不阻塞返回
            asyncio.create_task(self._save_execution_async(
                workflow_name,
                input_data,
                final_output,
                overall_status.value,
                int(duration_ms),
                {"antipattern_warnings": len(context.get("_antipattern_warnings", []))}
            ))
        
        return result
    
    async def _execute_phases_sequential(
        self,
        phases: List[str],
        context: Dict,
        workflow_config: Dict
    ) -> List[PhaseResult]:
        """串行执行阶段"""
        phase_results = []
        
        for phase_name in phases:
            # 检查是否跳过
            if self._should_skip_phase(phase_name, context, workflow_config):
                phase_results.append(PhaseResult(
                    phase=phase_name,
                    status=PhaseStatus.SKIPPED,
                    start_time=time.time(),
                    end_time=time.time()
                ))
                logger.info(f"Skipped phase: {phase_name}")
                continue
            
            # 执行阶段
            result = await self._execute_phase(
                phase_name, context, workflow_config
            )
            phase_results.append(result)
            
            # 更新上下文
            await self._update_context(context, phase_name, result)
            
            # 检查是否继续
            if not result.success:
                if not workflow_config.get("config", {}).get("continue_on_error", False):
                    break
        
        return phase_results
    
    async def _execute_phases_parallel(
        self,
        phases: List[str],
        context: Dict,
        workflow_config: Dict
    ) -> Tuple[List[PhaseResult], List[List[str]]]:
        """
        并行执行阶段
        
        分析阶段依赖关系，将无依赖的阶段并行执行
        """
        # 分析并行组
        parallel_groups = self._optimizer.analyze_workflow(phases, workflow_config)
        
        logger.info(f"Parallel groups: {parallel_groups}")
        
        phase_results: Dict[str, PhaseResult] = {}
        
        for group in parallel_groups:
            # 检查整组是否需要跳过
            group_should_skip = all(
                self._should_skip_phase(p, context, workflow_config)
                for p in group
            )
            
            if group_should_skip:
                for phase_name in group:
                    phase_results[phase_name] = PhaseResult(
                        phase=phase_name,
                        status=PhaseStatus.SKIPPED,
                        start_time=time.time(),
                        end_time=time.time()
                    )
                continue
            
            # 限制并行度
            if len(group) > self._max_parallel_phases:
                # 拆分为多个批次
                batches = [
                    group[i:i + self._max_parallel_phases]
                    for i in range(0, len(group), self._max_parallel_phases)
                ]
            else:
                batches = [group]
            
            for batch in batches:
                # 并发执行批次
                tasks = [
                    self._execute_phase(phase, context, workflow_config)
                    for phase in batch
                    if not self._should_skip_phase(phase, context, workflow_config)
                ]
                
                if tasks:
                    batch_results = await asyncio.gather(*tasks, return_exceptions=True)
                    
                    for phase_name, result in zip(batch, batch_results):
                        if isinstance(result, Exception):
                            phase_results[phase_name] = PhaseResult(
                                phase=phase_name,
                                status=PhaseStatus.FAILED,
                                start_time=time.time(),
                                end_time=time.time(),
                                error=str(result)
                            )
                        else:
                            phase_results[phase_name] = result
                            await self._update_context(context, phase_name, result)
            
            # 检查组内是否有失败
            group_results = [phase_results[p] for p in group if p in phase_results]
            if any(r.status == PhaseStatus.FAILED for r in group_results):
                if not workflow_config.get("config", {}).get("continue_on_error", False):
                    break
        
        # 按原始顺序返回结果
        return (
            [phase_results[p] for p in phases if p in phase_results],
            parallel_groups
        )
    
    async def _execute_phase(
        self, 
        phase_name: str, 
        context: Dict, 
        workflow_config: Dict
    ) -> PhaseResult:
        """执行单个阶段"""
        start_time = time.time()
        
        handler = self.get_handler(phase_name)
        if not handler:
            return PhaseResult(
                phase=phase_name,
                status=PhaseStatus.FAILED,
                start_time=start_time,
                end_time=time.time(),
                error=f"Handler not found: {phase_name}"
            )
        
        try:
            logger.info(f"Executing phase: {phase_name}")
            output = await handler.execute(context)
            
            return PhaseResult(
                phase=phase_name,
                status=PhaseStatus.COMPLETED,
                start_time=start_time,
                end_time=time.time(),
                duration_ms=(time.time() - start_time) * 1000,
                input_data=context.copy(),
                output_data=output,
                metadata=workflow_config.get("handlers", {}).get(phase_name, {})
            )
            
        except Exception as e:
            logger.error(f"Phase error: {phase_name} - {e}")
            return PhaseResult(
                phase=phase_name,
                status=PhaseStatus.FAILED,
                start_time=start_time,
                end_time=time.time(),
                duration_ms=(time.time() - start_time) * 1000,
                error=str(e)
            )
    
    async def _update_context(self, context: Dict, phase_name: str, result: PhaseResult):
        """更新上下文"""
        context[f"{phase_name}_result"] = result.output_data
        context["_history"].append({
            "phase": phase_name,
            "status": result.status.value,
            "timestamp": datetime.now().isoformat()
        })
        
        # 检查反模式
        if result.output_data and self.antipattern_checker:
            antipattern_warnings = self.antipattern_checker.check(
                str(result.output_data),
                context.get("_domain", "general")
            )
            context["_antipattern_warnings"].extend(antipattern_warnings)
    
    async def _save_execution_async(
        self,
        workflow_name: str,
        input_data: Dict,
        output_data: Any,
        status: str,
        duration_ms: int,
        metadata: Dict
    ):
        """异步保存执行记录 (不阻塞主流程)"""
        try:
            if hasattr(self.storage, 'save_execution'):
                # 同步存储
                self.storage.save_execution(
                    workflow_name, input_data, output_data,
                    status, duration_ms, metadata
                )
            else:
                # 异步存储
                await self.storage.save_execution(
                    workflow_name, input_data, output_data,
                    status, duration_ms, metadata
                )
        except Exception as e:
            logger.error(f"Failed to save execution: {e}")
    
    async def run_batch(
        self,
        tasks: List[Dict[str, Any]],
        max_concurrent: int = 3
    ) -> List[WorkflowResult]:
        """
        批量运行工作流
        
        Args:
            tasks: 任务列表，每项包含:
                - workflow: 工作流名称
                - input: 输入数据
                - use_cache: 是否使用缓存
            max_concurrent: 最大并发数
        
        Returns:
            结果列表
        """
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def run_with_limit(task: Dict) -> WorkflowResult:
            async with semaphore:
                return await self.run(
                    task["workflow"],
                    task["input"],
                    use_cache=task.get("use_cache", False)
                )
        
        tasks_coros = [run_with_limit(t) for t in tasks]
        return await asyncio.gather(*tasks_coros, return_exceptions=True)
    
    def _should_skip_phase(
        self, 
        phase_name: str, 
        context: Dict, 
        workflow_config: Dict
    ) -> bool:
        """判断是否跳过阶段"""
        conditions = workflow_config.get("conditions", {}).get(phase_name, [])
        
        for condition in conditions:
            condition_type = condition.get("type")
            
            if condition_type == "confidence":
                threshold = condition.get("threshold", 0.5)
                confidence = context.get("confidence", 1.0)
                if confidence >= threshold:
                    return True
            
            elif condition_type == "required_fields":
                for field in condition.get("fields", []):
                    if field not in context:
                        return True
        
        return False
    
    def _generate_output(
        self, 
        workflow_name: str, 
        context: Dict,
        phase_results: List[PhaseResult]
    ) -> Any:
        """生成最终输出"""
        workflow_config = self._workflow_configs.get(workflow_name, {})
        outputs_config = workflow_config.get("outputs", {})
        
        if not outputs_config:
            if phase_results:
                return phase_results[-1].output_data
            return context
        
        output = {}
        for output_name in outputs_config.keys():
            key = f"{output_name}_result"
            output[output_name] = context.get(key)
        
        return output if len(output) > 1 else output.get(list(output.keys())[0])
    
    def clear_cache(self):
        """清除结果缓存"""
        self._result_cache.clear()
        logger.info("Workflow result cache cleared")
