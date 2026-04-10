"""
Nova Agent 核心实现
"""

import time
import uuid
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime

from nova_agent.config import NovaConfig
from nova_agent.llm.client import LLMClient, OpenClawLLMClient, LLMMessage
from nova_agent.memory.palace import MemoryPalace
from nova_agent.memory.temporal import TemporalGraph, FactType


class NovaAgent:
    """
    Nova Agent - 新一代自主智能体
    
    核心特性:
    - 五级宫殿记忆系统
    - 时序事实图谱
    - 工具调用能力
    - 反馈进化机制
    """
    
    def __init__(self, config: Optional[NovaConfig] = None):
        """初始化Agent"""
        self.config = config or NovaConfig.from_env()
        self.agent_id = str(uuid.uuid4())[:8]
        self.name = self.config.name
        
        # 初始化LLM客户端
        if self.config.llm.provider == "openclaw":
            self.llm = OpenClawLLMClient(
                model=self.config.llm.model,
                base_url=self.config.llm.base_url,
                api_key=self.config.llm.api_key,
                timeout=self.config.llm.timeout
            )
        else:
            # 可以扩展其他LLM提供商
            self.llm = OpenClawLLMClient(
                model=self.config.llm.model,
                base_url=self.config.llm.base_url
            )
        
        # 初始化记忆系统
        self.memory = MemoryPalace(
            storage_path=self.config.memory.storage_path,
            max_entries_per_level=self.config.memory.max_entries_per_level
        )
        
        # 初始化时序图谱
        self.temporal_graph = TemporalGraph(
            storage_path=self.config.memory.storage_path
        )
        
        # 工具注册
        self.tools: Dict[str, Callable] = {}
        
        # 会话状态
        self.session_id = str(uuid.uuid4())[:8]
        self.interaction_count = 0
        self.feedback_history: List[Dict] = []
        
        if self.config.debug:
            print(f"🚀 Nova Agent '{self.name}' ({self.agent_id}) 初始化完成")
    
    def run(self, query: str, context: Optional[str] = None) -> str:
        """
        运行Agent处理查询
        
        Args:
            query: 用户查询
            context: 额外上下文
        
        Returns:
            Agent响应
        """
        start_time = time.time()
        self.interaction_count += 1
        
        # 1. 存储用户查询到工作记忆
        self.memory.store(
            content=f"用户: {query}",
            level=0,  # 工作记忆
            importance=0.8,
            tags=["user_query", f"session_{self.session_id}"]
        )
        
        # 2. 检索相关记忆
        relevant_memories = self.memory.recall(query, top_k=5)
        memory_context = self._format_memories(relevant_memories)
        
        # 3. 构建提示
        system_prompt = self._build_system_prompt()
        
        messages = [
            LLMMessage(role="system", content=system_prompt),
        ]
        
        # 添加上下文
        full_context = self.memory.get_context(max_entries=5)
        if full_context:
            messages.append(LLMMessage(
                role="system", 
                content=f"相关背景:\n{full_context}"
            ))
        
        if memory_context:
            messages.append(LLMMessage(
                role="system",
                content=f"相关记忆:\n{memory_context}"
            ))
        
        if context:
            messages.append(LLMMessage(
                role="system",
                content=f"额外上下文:\n{context}"
            ))
        
        messages.append(LLMMessage(role="user", content=query))
        
        # 4. 调用LLM
        try:
            response = self.llm.chat(
                messages,
                temperature=self.config.llm.temperature,
                max_tokens=self.config.llm.max_tokens
            )
            
            result = response.content
            
            # 5. 存储响应到工作记忆
            self.memory.store(
                content=f"助手: {result[:500]}...",  # 只存前500字符
                level=0,
                importance=0.6,
                tags=["assistant_response", f"session_{self.session_id}"]
            )
            
            # 6. 提取事实存入时序图谱
            self._extract_facts(query, result)
            
            elapsed = time.time() - start_time
            if self.config.debug:
                print(f"✅ 响应生成完成，耗时 {elapsed:.2f}s")
            
            return result
            
        except Exception as e:
            error_msg = f"处理查询时出错: {str(e)}"
            if self.config.debug:
                print(f"❌ {error_msg}")
            return error_msg
    
    def feedback(self, query: str, response: str, rating: int, comment: str = "") -> Dict:
        """
        接收用户反馈，触发进化
        
        Args:
            query: 原始查询
            response: 原始响应
            rating: 评分 1-5
            comment: 评论
        
        Returns:
            进化报告
        """
        feedback_entry = {
            "id": str(uuid.uuid4())[:8],
            "timestamp": datetime.now().isoformat(),
            "query": query,
            "response": response,
            "rating": rating,
            "comment": comment
        }
        
        self.feedback_history.append(feedback_entry)
        
        # 存储到长期记忆
        self.memory.store(
            content=f"反馈: {comment}" if comment else f"评分: {rating}/5",
            level=2,  # 中期记忆
            importance=rating / 5.0,
            tags=["feedback", f"rating_{rating}"]
        )
        
        # 进化报告
        report = {
            "feedback_id": feedback_entry["id"],
            "rating": rating,
            "total_feedback": len(self.feedback_history),
            "avg_rating": sum(f["rating"] for f in self.feedback_history) / len(self.feedback_history),
            "evolution_triggered": len(self.feedback_history) >= self.config.evolution.feedback_threshold,
            "evolution_report": None
        }
        
        # 触发进化
        if report["evolution_triggered"] and self.config.evolution.enabled:
            report["evolution_report"] = self._evolve()
        
        return report
    
    def register_tool(self, name: str, func: Callable, description: str = "") -> None:
        """注册工具"""
        self.tools[name] = {
            "func": func,
            "description": description
        }
        
        # 存储到永久记忆
        self.memory.store(
            content=f"工具: {name} - {description}",
            level=4,  # 永久记忆
            importance=0.9,
            tags=["tool", name]
        )
    
    def get_stats(self) -> Dict:
        """获取Agent统计信息"""
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "session_id": self.session_id,
            "interactions": self.interaction_count,
            "memory": self.memory.stats(),
            "temporal_graph": self.temporal_graph.stats(),
            "tools": list(self.tools.keys()),
            "feedback_count": len(self.feedback_history)
        }
    
    def _build_system_prompt(self) -> str:
        """构建系统提示"""
        return f"""你是 {self.name}，一个智能助手。

核心能力:
1. 利用长期记忆提供连贯的对话体验
2. 基于事实进行推理和回答
3. 持续学习和改进

当前状态:
- 会话ID: {self.session_id}
- 交互次数: {self.interaction_count}

请提供有帮助、准确且自然的回答。"""
    
    def _format_memories(self, memories: List[Any]) -> str:
        """格式化记忆为文本"""
        if not memories:
            return ""
        
        lines = []
        for mem in memories:
            level_name = ["工作", "短期", "中期", "长期", "永久"][mem.level]
            lines.append(f"[{level_name}记忆] {mem.content[:100]}...")
        
        return "\n".join(lines)
    
    def _extract_facts(self, query: str, response: str) -> None:
        """从对话中提取事实存入图谱"""
        # MVP版本：简单提取关键实体和事件
        # 实际应用中可以使用LLM进行更复杂的提取
        
        # 示例：存储这次交互作为一个事件
        self.temporal_graph.add_fact(
            content=f"交互 #{self.interaction_count}: {query[:50]}...",
            fact_type=FactType.EVENT,
            entities=["用户", "助手"],
            source="conversation"
        )
    
    def _evolve(self) -> Dict:
        """
        执行自我进化
        MVP版本：简单的参数调整
        """
        if not self.feedback_history:
            return {"status": "no_feedback"}
        
        # 计算平均评分
        avg_rating = sum(f["rating"] for f in self.feedback_history) / len(self.feedback_history)
        
        # 根据评分调整参数
        evolution_actions = []
        
        if avg_rating < 3.0:
            # 评分较低，增加温度以获得更多样性
            self.config.llm.temperature = min(1.0, self.config.llm.temperature + 0.1)
            evolution_actions.append("增加temperature以获得更丰富的回答")
        elif avg_rating > 4.5:
            # 评分很高，降低温度以保持稳定
            self.config.llm.temperature = max(0.1, self.config.llm.temperature - 0.05)
            evolution_actions.append("降低temperature以保持回答质量")
        
        # 清空反馈历史（实际应用中可以保留更多历史）
        self.feedback_history = []
        
        return {
            "status": "evolved",
            "avg_rating": avg_rating,
            "actions": evolution_actions,
            "new_temperature": self.config.llm.temperature
        }
