"""
Inkcore 工具集成

为 NC 提供技法查询和章节分析能力

使用方法:
    from nova_agent.tools.inkcore import InkcoreTool
    
    tool = InkcoreTool(base_url="http://localhost:8000")
    
    # 搜索技法
    techniques = await tool.search_techniques(scene_type="战斗")
    
    # 分析章节
    analysis = await tool.analyze_chapter(chapter_text)
"""

import aiohttp
from typing import Dict, List, Any, Optional
import logging

from .base import BaseTool, ToolResult

logger = logging.getLogger(__name__)


class InkcoreTool(BaseTool):
    """
    Inkcore 集成工具
    
    连接 Inkcore NC API 服务
    """
    
    name = "inkcore"
    description = "Inkcore小说技法分析服务"
    parameters = {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["search", "analyze", "style", "categories"],
                "description": "操作类型"
            },
            "query": {"type": "string", "description": "搜索查询"},
            "scene_type": {"type": "string", "description": "场景类型"},
            "category": {"type": "string", "description": "技法类别"},
            "chapter_text": {"type": "string", "description": "章节文本"},
            "novel_name": {"type": "string", "description": "小说名称"},
            "min_confidence": {"type": "number", "default": 0.6},
            "limit": {"type": "integer", "default": 10}
        },
        "required": ["action"]
    }
    
    def __init__(self, config: Dict = None):
        super().__init__(config)
        self.base_url = config.get("base_url", "http://localhost:8000") if config else "http://localhost:8000"
        self.session = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """获取session"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def execute(self, action: str, **kwargs) -> ToolResult:
        """执行Inkcore操作"""
        try:
            if action == "search":
                return await self._search(kwargs)
            elif action == "analyze":
                return await self._analyze(kwargs)
            elif action == "style":
                return await self._get_style(kwargs)
            elif action == "categories":
                return await self._get_categories()
            else:
                return ToolResult(
                    success=False,
                    data=None,
                    error=f"Unknown action: {action}"
                )
        except Exception as e:
            logger.error(f"Inkcore tool failed: {e}")
            return ToolResult(
                success=False,
                data=None,
                error=str(e)
            )
    
    async def _search(self, params: Dict) -> ToolResult:
        """搜索技法"""
        session = await self._get_session()
        
        payload = {
            "query": params.get("query"),
            "scene_type": params.get("scene_type"),
            "category": params.get("category"),
            "min_confidence": params.get("min_confidence", 0.6),
            "limit": params.get("limit", 10)
        }
        
        async with session.post(
            f"{self.base_url}/api/v1/search",
            json=payload,
            timeout=aiohttp.ClientTimeout(total=30)
        ) as resp:
            if resp.status == 200:
                data = await resp.json()
                return ToolResult(
                    success=True,
                    data=data,
                    metadata={"count": len(data)}
                )
            else:
                text = await resp.text()
                return ToolResult(
                    success=False,
                    data=None,
                    error=f"Search failed: {resp.status} - {text}"
                )
    
    async def _analyze(self, params: Dict) -> ToolResult:
        """分析章节"""
        session = await self._get_session()
        
        chapter_text = params.get("chapter_text", "")
        if not chapter_text:
            return ToolResult(
                success=False,
                data=None,
                error="chapter_text is required"
            )
        
        async with session.post(
            f"{self.base_url}/api/v1/analyze",
            json={"chapter_text": chapter_text},
            timeout=aiohttp.ClientTimeout(total=60)
        ) as resp:
            if resp.status == 200:
                data = await resp.json()
                return ToolResult(
                    success=True,
                    data=data,
                    metadata={
                        "techniques_count": data.get("techniques_count", 0),
                        "quality_score": data.get("quality_score", 0)
                    }
                )
            else:
                text = await resp.text()
                return ToolResult(
                    success=False,
                    data=None,
                    error=f"Analyze failed: {resp.status} - {text}"
                )
    
    async def _get_style(self, params: Dict) -> ToolResult:
        """获取风格画像"""
        session = await self._get_session()
        
        novel_name = params.get("novel_name", "default")
        
        async with session.get(
            f"{self.base_url}/api/v1/style/{novel_name}",
            timeout=aiohttp.ClientTimeout(total=30)
        ) as resp:
            if resp.status == 200:
                data = await resp.json()
                return ToolResult(
                    success=True,
                    data=data
                )
            else:
                text = await resp.text()
                return ToolResult(
                    success=False,
                    data=None,
                    error=f"Get style failed: {resp.status} - {text}"
                )
    
    async def _get_categories(self) -> ToolResult:
        """获取技法类别"""
        session = await self._get_session()
        
        async with session.get(
            f"{self.base_url}/api/v1/categories",
            timeout=aiohttp.ClientTimeout(total=30)
        ) as resp:
            if resp.status == 200:
                data = await resp.json()
                return ToolResult(
                    success=True,
                    data=data,
                    metadata={"count": len(data)}
                )
            else:
                text = await resp.text()
                return ToolResult(
                    success=False,
                    data=None,
                    error=f"Get categories failed: {resp.status} - {text}"
                )
    
    async def close(self):
        """关闭连接"""
        if self.session and not self.session.closed:
            await self.session.close()


class MockInkcoreTool(BaseTool):
    """模拟 Inkcore 工具（用于测试）"""
    
    name = "inkcore_mock"
    description = "模拟Inkcore服务（测试用）"
    
    async def execute(self, action: str, **kwargs) -> ToolResult:
        """模拟执行"""
        logger.info(f"[MockInkcore] {action}: {kwargs}")
        
        if action == "search":
            return ToolResult(
                success=True,
                data=[
                    {"name": "危机开场", "category": "plot", "confidence": 0.85},
                    {"name": "对话推进", "category": "dialogue", "confidence": 0.80}
                ]
            )
        elif action == "analyze":
            return ToolResult(
                success=True,
                data={
                    "techniques_count": 5,
                    "quality_score": 0.75,
                    "techniques": [
                        {"name": "危机开场", "confidence": 0.85},
                        {"name": "内心独白", "confidence": 0.80}
                    ]
                }
            )
        else:
            return ToolResult(
                success=True,
                data={"message": f"Mock {action} response"}
            )