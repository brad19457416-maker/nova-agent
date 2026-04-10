"""
Web工具
"""

import aiohttp
from typing import Dict, Any, List
from urllib.parse import urlparse
import logging

from .base import BaseTool, ToolResult

logger = logging.getLogger(__name__)


class WebSearchTool(BaseTool):
    """
    Web搜索工具
    
    使用DuckDuckGo进行搜索
    """
    
    name = "web_search"
    description = "搜索网页信息"
    parameters = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "搜索关键词"
            },
            "num_results": {
                "type": "integer",
                "description": "结果数量",
                "default": 5
            }
        },
        "required": ["query"]
    }
    
    def __init__(self, config: Dict = None):
        super().__init__(config)
        self.session = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """获取session"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def execute(self, query: str, num_results: int = 5, **kwargs) -> ToolResult:
        """执行搜索"""
        try:
            # 使用DuckDuckGo API
            session = await self._get_session()
            
            url = "https://html.duckduckgo.com/html/"
            params = {"q": query}
            
            async with session.post(url, data=params) as resp:
                if resp.status == 200:
                    html = await resp.text()
                    results = self._parse_results(html, num_results)
                    
                    return ToolResult(
                        success=True,
                        data=results,
                        metadata={"query": query, "count": len(results)}
                    )
                else:
                    return ToolResult(
                        success=False,
                        data=None,
                        error=f"Search failed: {resp.status}"
                    )
        except Exception as e:
            logger.error(f"Web search failed: {e}")
            return ToolResult(
                success=False,
                data=None,
                error=str(e)
            )
    
    def _parse_results(self, html: str, num: int) -> List[Dict]:
        """解析搜索结果"""
        from bs4 import BeautifulSoup
        
        try:
            soup = BeautifulSoup(html, 'html.parser')
            results = []
            
            for result in soup.select('.result')[:num]:
                title_elem = result.select_one('.result__title')
                snippet_elem = result.select_one('.result__snippet')
                url_elem = result.select_one('.result__url')
                
                if title_elem:
                    results.append({
                        "title": title_elem.get_text(strip=True),
                        "snippet": snippet_elem.get_text(strip=True) if snippet_elem else "",
                        "url": url_elem.get_text(strip=True) if url_elem else ""
                    })
            
            return results
        except Exception as e:
            logger.error(f"Parse failed: {e}")
            return []


class WebFetchTool(BaseTool):
    """
    Web抓取工具
    
    抓取网页内容并提取文本
    """
    
    name = "web_fetch"
    description = "抓取网页内容"
    parameters = {
        "type": "object",
        "properties": {
            "url": {
                "type": "string",
                "description": "网页URL"
            },
            "extract_text": {
                "type": "boolean",
                "description": "是否提取纯文本",
                "default": True
            }
        },
        "required": ["url"]
    }
    
    def __init__(self, config: Dict = None):
        super().__init__(config)
        self.session = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """获取session"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def execute(self, url: str, extract_text: bool = True, **kwargs) -> ToolResult:
        """执行抓取"""
        try:
            session = await self._get_session()
            
            async with session.get(
                url,
                timeout=aiohttp.ClientTimeout(total=30),
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                }
            ) as resp:
                if resp.status == 200:
                    html = await resp.text()
                    
                    if extract_text:
                        text = self._extract_text(html)
                    else:
                        text = html
                    
                    return ToolResult(
                        success=True,
                        data={
                            "url": url,
                            "title": self._extract_title(html),
                            "text": text,
                            "length": len(text)
                        },
                        metadata={"status": resp.status}
                    )
                else:
                    return ToolResult(
                        success=False,
                        data=None,
                        error=f"Fetch failed: {resp.status}"
                    )
        except Exception as e:
            logger.error(f"Web fetch failed: {e}")
            return ToolResult(
                success=False,
                data=None,
                error=str(e)
            )
    
    def _extract_title(self, html: str) -> str:
        """提取标题"""
        from bs4 import BeautifulSoup
        try:
            soup = BeautifulSoup(html, 'html.parser')
            title = soup.find('title')
            return title.get_text(strip=True) if title else ""
        except:
            return ""
    
    def _extract_text(self, html: str) -> str:
        """提取纯文本"""
        from bs4 import BeautifulSoup
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # 移除脚本和样式
            for script in soup(["script", "style"]):
                script.decompose()
            
            # 获取文本
            text = soup.get_text()
            
            # 清理
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = '\n'.join(chunk for chunk in chunks if chunk)
            
            return text[:10000]  # 限制长度
        except Exception as e:
            logger.error(f"Extract text failed: {e}")
            return ""


class MockSearchTool(BaseTool):
    """模拟搜索工具（用于测试）"""
    
    name = "mock_search"
    description = "模拟Web搜索"
    
    async def execute(self, query: str, **kwargs) -> ToolResult:
        """模拟执行"""
        logger.info(f"[MockSearch] {query}")
        
        return ToolResult(
            success=True,
            data=[
                {"title": f"结果1: {query}", "snippet": "这是搜索结果1...", "url": "https://example.com/1"},
                {"title": f"结果2: {query}", "snippet": "这是搜索结果2...", "url": "https://example.com/2"},
                {"title": f"结果3: {query}", "snippet": "这是搜索结果3...", "url": "https://example.com/3"}
            ],
            metadata={"query": query, "mock": True}
        )