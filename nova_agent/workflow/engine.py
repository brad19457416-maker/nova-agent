"""
工作流引擎

特性:
- 配置驱动
- 阶段式执行
- 条件分支
- 错误恢复
- 执行历史
- 反模式检查

使用示例:
    engine = WorkflowEngine(config_manager, skill_system, llm_client)
    
    # 运行工作流
    result = await engine.run("research", {"task": "xxx"})
    
    print(result.final_output)
"""

import asyncio
import time
from typing import Dict, List, Any, Optional, Callable
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
import logging

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


class WorkflowEngine:
    """
    工作流引擎
    
    性能优化:
    - 类级别handler缓存，避免重复注册
    - 工作流配置缓存
    - 并行阶段执行支持
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
        antipattern_checker=None
    ):
        self.config = config_manager
        self.skills = skill_loader
        self.llm = llm_client
        self.storage = storage
        self.antipattern_checker = antipattern_checker
        
        # 工作流配置缓存
        self._workflow_configs: Dict[str, Dict] = {}
        self._config_lock = asyncio.Lock()
        
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
    
    async def run(self, workflow_name: str, input_data: Dict) -> WorkflowResult:
        """运行工作流"""
        start_time = time.time()
        
        # 1. 加载工作流配置
        workflow_config = self.load_workflow(workflow_name)
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
        phase_results = []
        
        logger.info(f"Starting workflow: {workflow_name} with {len(phases)} phases")
        
        # 4. 执行每个阶段
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
                    domain
                )
                context["_antipattern_warnings"].extend(antipattern_warnings)
            
            # 检查是否继续
            if not result.success:
                logger.error(f"Phase failed: {phase_name} - {result.error}")
                if not workflow_config.get("config", {}).get("continue_on_error", False):
                    break
        
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
            metadata={
                "workflow_version": workflow_config.get("version", "1.0.0"),
                "antipattern_warnings": context["_antipattern_warnings"]
            }
        )
        
        logger.info(f"Workflow completed: {workflow_name} in {duration_ms:.0f}ms")
        
        # 6. 保存执行记录
        if self.storage:
            self.storage.save_execution(
                workflow_name,
                input_data,
                final_output,
                overall_status.value,
                int(duration_ms),
                {"antipattern_warnings": len(context["_antipattern_warnings"])}
            )
        
        return result
    
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
