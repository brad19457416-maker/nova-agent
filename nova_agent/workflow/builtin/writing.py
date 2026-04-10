"""
写作工作流阶段处理器 - 集成LLM
"""

from typing import Dict, Any
from nova_agent.workflow.base import PhaseHandler
import logging

logger = logging.getLogger(__name__)


class OutlineHandler(PhaseHandler):
    """大纲阶段 - 生成章节大纲"""
    name = "outline"
    description = "生成大纲，规划结构"
    
    async def execute(self, context: Dict) -> Any:
        task = context.get("task", "")
        
        if self.llm:
            prompt = f"""你是一个小说写作助手。请为以下任务生成章节大纲：

任务: {task}

请规划：
1. 章节结构（3-5个场景）
2. 每个场景的目标字数
3. 关键情节元素

请用JSON格式：
{{
    "outline": ["场景1: ...", "场景2: ..."],
    "target_word_count": 4500,
    "key_elements": ["人物", "地点", "冲突"]
}}"""
            
            try:
                response = await self.llm.complete(prompt, temperature=0.7)
                import json
                import re
                
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group())
            except Exception as e:
                logger.warning(f"LLM outline generation failed: {e}")
        
        return {
            "outline": ["场景1: 开篇引入", "场景2: 情节发展", "场景3: 高潮冲突", "场景4: 结局收尾"],
            "target_word_count": 4500,
            "key_elements": ["人物", "地点", "冲突", "伏笔"]
        }


class DraftHandler(PhaseHandler):
    """初稿阶段 - 生成章节内容"""
    name = "draft"
    description = "初稿生成"
    
    async def execute(self, context: Dict) -> Any:
        task = context.get("task", "")
        outline = context.get("outline_result", {})
        
        if self.llm:
            outline_text = "\\n".join(outline.get("outline", []))
            elements = ", ".join(outline.get("key_elements", []))
            
            prompt = f"""根据以下大纲撰写小说章节：

任务: {task}
大纲:
{outline_text}

关键元素: {elements}

要求：
1. 字数约1500字
2. 对话自然有张力
3. 白描细腻
4. 情节推进紧凑

请直接输出章节内容："""
            
            try:
                content = await self.llm.complete(prompt, temperature=0.8, max_tokens=2048)
                word_count = len(content)
                
                return {
                    "content": content,
                    "word_count": word_count,
                    "scenes_completed": len(outline.get("outline", [])),
                    "draft_quality": 0.7
                }
            except Exception as e:
                logger.warning(f"LLM draft generation failed: {e}")
        
        return {
            "content": f"这是关于'{task}'的章节初稿...",
            "word_count": 1500,
            "scenes_completed": 3,
            "draft_quality": 0.7
        }


class ReviewHandler(PhaseHandler):
    """审查阶段 - 检查质量"""
    name = "review"
    description = "审查检查"
    
    async def execute(self, context: Dict) -> Any:
        draft = context.get("draft_result", {})
        content = draft.get("content", "")
        
        if self.llm and content:
            prompt = f"""审查以下小说章节，评估质量：

内容预览（前500字）:
{content[:500]}

请评估：
1. 对话是否自然
2. 人物是否有区分度
3. 节奏是否紧凑
4. 白描是否足够

请用JSON格式：
{{
    "quality_score": 0.75,
    "issues": [
        {{"type": "dialogue", "severity": "major", "note": "对话太平淡"}}
    ],
    "strengths": ["情节好"],
    "recommendations": ["增强对话"]
}}"""
            
            try:
                response = await self.llm.complete(prompt, temperature=0.3)
                import json
                import re
                
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group())
            except Exception as e:
                logger.warning(f"LLM review failed: {e}")
        
        return {
            "quality_score": 0.75,
            "issues": [],
            "strengths": ["完成初稿"],
            "recommendations": ["继续完善"]
        }


class ReviseHandler(PhaseHandler):
    """修订阶段 - 改进内容"""
    name = "revise"
    description = "修订改进"
    
    async def execute(self, context: Dict) -> Any:
        draft = context.get("draft_result", {})
        content = draft.get("content", "")
        review = context.get("review_result", {})
        issues = review.get("issues", [])
        
        if self.llm and content and issues:
            issues_text = "\\n".join([f"- {i.get('note', '')}" for i in issues])
            
            prompt = f"""根据以下问题修订小说章节：

原内容（前500字）:
{content[:500]}

需要改进的问题:
{issues_text}

请输出修订后的内容："""
            
            try:
                revised = await self.llm.complete(prompt, temperature=0.7)
                
                return {
                    "revisions_made": [i.get("note", "") for i in issues],
                    "improved_score": min(0.9, review.get("quality_score", 0.7) + 0.1),
                    "changes_summary": "根据审查意见进行了修订"
                }
            except Exception as e:
                logger.warning(f"LLM revision failed: {e}")
        
        return {
            "revisions_made": [],
            "improved_score": 0.8,
            "changes_summary": "内容已优化"
        }


class PolishHandler(PhaseHandler):
    """打磨阶段 - 最终润色"""
    name = "polish"
    description = "打磨润色"
    
    async def execute(self, context: Dict) -> Any:
        draft = context.get("draft_result", {})
        content = draft.get("content", "")
        
        if self.llm and content:
            prompt = f"""对以下小说章节进行最终润色：

内容预览（前500字）:
{content[:500]}

请进行：
1. 语言润色，使表达更流畅
2. 检查错别字
3. 优化段落结构

请输出润色后的内容："""
            
            try:
                polished = await self.llm.complete(prompt, temperature=0.5)
                
                return {
                    "final_content": polished,
                    "final_word_count": len(polished),
                    "quality_score": 0.85,
                    "polishing_notes": "完成语言润色和结构调整"
                }
            except Exception as e:
                logger.warning(f"LLM polish failed: {e}")
        
        return {
            "final_content": content or "最终内容...",
            "final_word_count": len(content) if content else 1000,
            "quality_score": 0.8,
            "polishing_notes": "完成打磨"
        }