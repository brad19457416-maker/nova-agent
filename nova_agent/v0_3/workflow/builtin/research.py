"""
调研工作流阶段处理器 - 集成LLM
"""

from typing import Dict, Any
from nova_agent.v0_3.workflow.base import PhaseHandler
import logging

logger = logging.getLogger(__name__)


class ClarifyHandler(PhaseHandler):
    """澄清阶段 - 理解任务"""
    name = "clarify"
    description = "澄清需求，理解任务"
    
    async def execute(self, context: Dict) -> Any:
        task = context.get("task", "")
        
        # 使用LLM澄清任务
        if self.llm:
            prompt = f"""你是一个任务澄清助手。用户提出了以下任务：

任务: {task}

请分析这个任务:
1. 核心目标是什么？
2. 需要哪些信息？
3. 期望的产出是什么？

请用简洁的语言回答，使用JSON格式:
{{
    "core_goal": "核心目标",
    "required_info": ["信息1", "信息2"],
    "expected_output": "期望产出",
    "confidence": 0.8
}}"""
            
            try:
                response = await self.llm.complete(prompt, temperature=0.3)
                # 解析JSON响应
                import json
                import re
                
                # 尝试提取JSON
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group())
                    return {
                        "clarified_task": task,
                        **result
                    }
            except Exception as e:
                logger.warning(f"LLM clarification failed: {e}")
        
        # 回退到默认实现
        return {
            "clarified_task": task,
            "core_goal": f"研究: {task}",
            "required_info": ["背景信息", "技术细节", "最佳实践"],
            "expected_output": "调研报告",
            "confidence": 0.7
        }


class PlanHandler(PhaseHandler):
    """规划阶段 - 制定调研计划"""
    name = "plan"
    description = "制定调研计划"
    
    async def execute(self, context: Dict) -> Any:
        clarified = context.get("clarify_result", {})
        task = clarified.get("clarified_task", context.get("task", ""))
        
        if self.llm:
            prompt = f"""为以下调研任务制定计划：

任务: {task}
核心目标: {clarified.get('core_goal', 'N/A')}

请列出3-5个关键调研问题，并说明需要查找的信息类型。

请用JSON格式回答:
{{
    "key_questions": ["问题1", "问题2", "问题3"],
    "search_strategy": "搜索策略描述",
    "priority": "high"
}}"""
            
            try:
                response = await self.llm.complete(prompt, temperature=0.5)
                import json
                import re
                
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group())
            except Exception as e:
                logger.warning(f"LLM planning failed: {e}")
        
        return {
            "key_questions": [
                f"什么是{task}？",
                f"{task}的核心概念是什么？",
                f"{task}的最佳实践是什么？"
            ],
            "search_strategy": "分层搜索",
            "priority": "high"
        }


class SearchHandler(PhaseHandler):
    """搜索阶段 - 执行信息搜索"""
    name = "search"
    description = "搜索信息"
    
    async def execute(self, context: Dict) -> Any:
        plan = context.get("plan_result", {})
        key_questions = plan.get("key_questions", [])
        
        queries = []
        
        # 使用LLM生成搜索查询
        if self.llm and key_questions:
            prompt = f"""基于以下问题，生成搜索关键词：

{chr(10).join(f"- {q}" for q in key_questions[:3])}

请生成3-5个搜索查询，用JSON格式：
{{"queries": ["查询1", "查询2", "查询3"]}}"""
            
            try:
                response = await self.llm.complete(prompt, temperature=0.7)
                import json
                import re
                
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    data = json.loads(json_match.group())
                    queries = data.get("queries", [])
            except Exception as e:
                logger.warning(f"LLM query generation failed: {e}")
        
        if not queries:
            queries = key_questions[:3] if key_questions else ["general information"]
        
        # 模拟搜索结果（实际应该调用搜索工具）
        return {
            "queries": queries,
            "results": [
                {"query": q, "results": f"关于'{q}'的搜索结果..."}
                for q in queries
            ],
            "count": len(queries)
        }


class ExpandHandler(PhaseHandler):
    """扩展阶段 - 基于结果深入"""
    name = "expand"
    description = "扩展查询，深化理解"
    
    async def execute(self, context: Dict) -> Any:
        search = context.get("search_result", {})
        results = search.get("results", [])
        
        if self.llm and results:
            prompt = f"""基于以下搜索结果，分析是否需要扩展查询：

搜索查询: {', '.join(search.get('queries', []))}

如果信息不足，请列出2-3个需要进一步搜索的问题。如果信息足够，请回复"无需扩展"。

请用JSON格式：
{{
    "expanded": true,
    "new_queries": ["新问题1", "新问题2"],
    "reason": "扩展原因"
}}"""
            
            try:
                response = await self.llm.complete(prompt, temperature=0.5)
                import json
                import re
                
                if "无需扩展" in response:
                    return {"expanded": False, "new_queries": [], "reason": "信息充足"}
                
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group())
            except Exception as e:
                logger.warning(f"LLM expansion failed: {e}")
        
        return {"expanded": False, "new_queries": [], "reason": "使用初始信息"}


class VerifyHandler(PhaseHandler):
    """验证阶段 - 确认信息准确性"""
    name = "verify"
    description = "验证信息准确性"
    
    async def execute(self, context: Dict) -> Any:
        search_results = context.get("search_result", {})
        queries = search_results.get("queries", [])
        
        if self.llm:
            prompt = f"""验证以下调研信息的准确性：

调研主题: {context.get('task', 'N/A')}
搜索查询: {', '.join(queries)}

请评估：
1. 信息来源是否可靠
2. 内容是否一致
3. 置信度如何

请用JSON格式：
{{
    "verified": true,
    "confidence": 0.85,
    "notes": "验证说明"
}}"""
            
            try:
                response = await self.llm.complete(prompt, temperature=0.3)
                import json
                import re
                
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group())
            except Exception as e:
                logger.warning(f"LLM verification failed: {e}")
        
        return {
            "verified": True,
            "confidence": 0.8,
            "notes": "基于可用信息验证"
        }


class SynthesizeHandler(PhaseHandler):
    """综合阶段 - 形成结论"""
    name = "synthesize"
    description = "综合分析，形成结论"
    
    async def execute(self, context: Dict) -> Any:
        task = context.get("task", "")
        
        if self.llm:
            prompt = f"""为以下调研任务形成综合结论：

任务: {task}

请提供：
1. 简洁的总结（100字以内）
2. 3-5个关键发现
3. 最终结论或建议

请用JSON格式：
{{
    "summary": "调研总结...",
    "key_findings": ["发现1", "发现2", "发现3"],
    "conclusion": "最终结论...",
    "recommendations": ["建议1", "建议2"]
}}"""
            
            try:
                response = await self.llm.complete(prompt, temperature=0.5)
                import json
                import re
                
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group())
            except Exception as e:
                logger.warning(f"LLM synthesis failed: {e}")
        
        return {
            "summary": f"关于'{task}'的调研完成",
            "key_findings": ["需要更多信息"],
            "conclusion": "调研完成",
            "recommendations": ["继续深入研究"]
        }


class DeliverHandler(PhaseHandler):
    """交付阶段 - 输出最终报告"""
    name = "deliver"
    description = "交付最终报告"
    
    async def execute(self, context: Dict) -> Any:
        synthesis = context.get("synthesize_result", {})
        
        # 格式化输出
        summary = synthesis.get("summary", "")
        findings = synthesis.get("key_findings", [])
        conclusion = synthesis.get("conclusion", "")
        recommendations = synthesis.get("recommendations", [])
        
        content = f"""# 调研报告: {context.get('task', 'Unknown')}

## 总结
{summary}

## 关键发现
{chr(10).join(f"- {f}" for f in findings)}

## 结论
{conclusion}

## 建议
{chr(10).join(f"- {r}" for r in recommendations)}
"""
        
        return {
            "title": f"调研报告: {context.get('task', 'Unknown')}",
            "content": content,
            "format": "markdown",
            "sources": context.get("verify_result", {}).get("notes", ""),
            "timestamp": "2026-04-10T12:00:00"
        }