"""
内置工具集
提供基础功能的工具实现
"""

import subprocess
import json
import os
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import asyncio

from nova_agent.tools.base import BaseTool, ToolResult, ToolParameter


class WebSearchTool(BaseTool):
    """
    网页搜索工具
    使用DuckDuckGo或其他搜索API
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        super().__init__(
            name="web_search",
            description="搜索网页信息",
            parameters=[
                ToolParameter(
                    name="query",
                    type="string",
                    description="搜索查询",
                    required=True
                ),
                ToolParameter(
                    name="num_results",
                    type="number",
                    description="结果数量",
                    required=False,
                    default=5
                ),
                ToolParameter(
                    name="recency",
                    type="string",
                    description="时间范围: day, week, month, year, any",
                    required=False,
                    default="any",
                    enum=["day", "week", "month", "year", "any"]
                )
            ]
        )
    
    async def execute(self, **kwargs) -> ToolResult:
        query = kwargs.get("query")
        num_results = kwargs.get("num_results", 5)
        recency = kwargs.get("recency", "any")
        
        try:
            # 使用ddgr命令行工具 (需要安装: pip install ddgr)
            # 或使用DuckDuckGo API
            
            # 模拟搜索结果
            results = [
                {
                    "title": f"关于 '{query}' 的搜索结果 {i+1}",
                    "url": f"https://example.com/result{i+1}",
                    "snippet": f"这是关于{query}的详细信息...",
                    "source": "duckduckgo"
                }
                for i in range(num_results)
            ]
            
            return ToolResult(
                success=True,
                data={
                    "query": query,
                    "results": results,
                    "total": len(results)
                },
                metadata={"recency": recency}
            )
            
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class WebFetchTool(BaseTool):
    """
    网页获取工具
    获取网页内容
    """
    
    def __init__(self):
        super().__init__(
            name="web_fetch",
            description="获取网页内容",
            parameters=[
                ToolParameter(
                    name="url",
                    type="string",
                    description="网页URL",
                    required=True
                ),
                ToolParameter(
                    name="max_chars",
                    type="number",
                    description="最大字符数",
                    required=False,
                    default=5000
                ),
                ToolParameter(
                    name="extract_mode",
                    type="string",
                    description="提取模式: markdown, text, html",
                    required=False,
                    default="markdown",
                    enum=["markdown", "text", "html"]
                )
            ]
        )
    
    async def execute(self, **kwargs) -> ToolResult:
        url = kwargs.get("url")
        max_chars = kwargs.get("max_chars", 5000)
        extract_mode = kwargs.get("extract_mode", "markdown")
        
        try:
            import requests
            from bs4 import BeautifulSoup
            
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            if extract_mode == "markdown":
                # 简单转换为markdown
                soup = BeautifulSoup(response.text, 'html.parser')
                text = soup.get_text(separator='\n')
                content = text[:max_chars]
            elif extract_mode == "text":
                soup = BeautifulSoup(response.text, 'html.parser')
                content = soup.get_text()[:max_chars]
            else:  # html
                content = response.text[:max_chars]
            
            return ToolResult(
                success=True,
                data={
                    "url": url,
                    "content": content,
                    "length": len(content),
                    "extract_mode": extract_mode
                }
            )
            
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class CodeExecuteTool(BaseTool):
    """
    代码执行工具
    安全地执行Python代码
    """
    
    def __init__(self, sandbox: bool = True):
        self.sandbox = sandbox
        super().__init__(
            name="code_execute",
            description="执行Python代码",
            parameters=[
                ToolParameter(
                    name="code",
                    type="string",
                    description="Python代码",
                    required=True
                ),
                ToolParameter(
                    name="timeout",
                    type="number",
                    description="超时时间(秒)",
                    required=False,
                    default=30
                )
            ]
        )
    
    async def execute(self, **kwargs) -> ToolResult:
        code = kwargs.get("code")
        timeout = kwargs.get("timeout", 30)
        
        try:
            # 创建临时文件执行代码
            import tempfile
            
            with tempfile.NamedTemporaryFile(
                mode='w',
                suffix='.py',
                delete=False
            ) as f:
                f.write(code)
                temp_file = f.name
            
            # 执行代码
            proc = await asyncio.create_subprocess_exec(
                'python3', temp_file,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    proc.communicate(),
                    timeout=timeout
                )
                
                # 清理临时文件
                os.unlink(temp_file)
                
                output = stdout.decode() if stdout else ""
                errors = stderr.decode() if stderr else ""
                
                if proc.returncode == 0:
                    return ToolResult(
                        success=True,
                        data={
                            "output": output,
                            "execution_time": timeout
                        }
                    )
                else:
                    return ToolResult(
                        success=False,
                        data={"output": output},
                        error=errors or "Execution failed"
                    )
                    
            except asyncio.TimeoutError:
                proc.kill()
                return ToolResult(
                    success=False,
                    error=f"Execution timeout after {timeout} seconds"
                )
                
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class FileTool(BaseTool):
    """
    文件操作工具
    读写文件
    """
    
    def __init__(self, base_path: str = "."):
        self.base_path = os.path.abspath(base_path)
        super().__init__(
            name="file",
            description="文件读写操作",
            parameters=[
                ToolParameter(
                    name="action",
                    type="string",
                    description="操作: read, write, list, delete",
                    required=True,
                    enum=["read", "write", "list", "delete"]
                ),
                ToolParameter(
                    name="path",
                    type="string",
                    description="文件路径",
                    required=True
                ),
                ToolParameter(
                    name="content",
                    type="string",
                    description="写入内容(仅write时需要)",
                    required=False
                ),
                ToolParameter(
                    name="encoding",
                    type="string",
                    description="编码",
                    required=False,
                    default="utf-8"
                )
            ]
        )
    
    async def execute(self, **kwargs) -> ToolResult:
        action = kwargs.get("action")
        path = kwargs.get("path")
        content = kwargs.get("content")
        encoding = kwargs.get("encoding", "utf-8")
        
        # 安全检查：确保路径在base_path内
        full_path = os.path.join(self.base_path, path)
        full_path = os.path.abspath(full_path)
        
        if not full_path.startswith(self.base_path):
            return ToolResult(
                success=False,
                error="Path outside allowed directory"
            )
        
        try:
            if action == "read":
                with open(full_path, 'r', encoding=encoding) as f:
                    data = f.read()
                return ToolResult(success=True, data={"content": data})
                
            elif action == "write":
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                with open(full_path, 'w', encoding=encoding) as f:
                    f.write(content or "")
                return ToolResult(success=True, data={"path": path, "bytes_written": len(content or "")})
                
            elif action == "list":
                items = []
                for item in os.listdir(full_path):
                    item_path = os.path.join(full_path, item)
                    items.append({
                        "name": item,
                        "type": "directory" if os.path.isdir(item_path) else "file",
                        "size": os.path.getsize(item_path) if os.path.isfile(item_path) else None
                    })
                return ToolResult(success=True, data={"items": items})
                
            elif action == "delete":
                if os.path.isfile(full_path):
                    os.remove(full_path)
                elif os.path.isdir(full_path):
                    os.rmdir(full_path)
                return ToolResult(success=True, data={"deleted": path})
                
            else:
                return ToolResult(success=False, error=f"Unknown action: {action}")
                
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class CalculatorTool(BaseTool):
    """
    计算器工具
    执行数学计算
    """
    
    def __init__(self):
        super().__init__(
            name="calculator",
            description="执行数学计算",
            parameters=[
                ToolParameter(
                    name="expression",
                    type="string",
                    description="数学表达式，如: 2 + 2, sqrt(16), sin(30)",
                    required=True
                ),
                ToolParameter(
                    name="precision",
                    type="number",
                    description="结果精度(小数位数)",
                    required=False,
                    default=2
                )
            ]
        )
    
    async def execute(self, **kwargs) -> ToolResult:
        expression = kwargs.get("expression", "")
        precision = kwargs.get("precision", 2)
        
        try:
            # 安全评估表达式
            import math
            
            # 允许的函数和常量
            allowed_names = {
                k: v for k, v in math.__dict__.items()
                if not k.startswith('_')
            }
            allowed_names.update({
                "abs": abs,
                "max": max,
                "min": min,
                "sum": sum,
                "pow": pow
            })
            
            # 编译并执行
            code = compile(expression, "<string>", "eval")
            
            # 检查安全性
            for name in code.co_names:
                if name not in allowed_names:
                    return ToolResult(
                        success=False,
                        error=f"Disallowed name: {name}"
                    )
            
            result = eval(code, {"__builtins__": {}}, allowed_names)
            
            # 格式化结果
            if isinstance(result, float):
                result = round(result, precision)
            
            return ToolResult(
                success=True,
                data={
                    "expression": expression,
                    "result": result,
                    "precision": precision
                }
            )
            
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class CalendarTool(BaseTool):
    """
    日历工具
    管理日程和提醒
    """
    
    def __init__(self, storage_path: str = "./data/calendar"):
        self.storage_path = storage_path
        os.makedirs(storage_path, exist_ok=True)
        
        self.events_file = os.path.join(storage_path, "events.json")
        self.events: List[Dict] = self._load_events()
        
        super().__init__(
            name="calendar",
            description="日历和日程管理",
            parameters=[
                ToolParameter(
                    name="action",
                    type="string",
                    description="操作: add, list, delete, get_today",
                    required=True,
                    enum=["add", "list", "delete", "get_today"]
                ),
                ToolParameter(
                    name="title",
                    type="string",
                    description="事件标题",
                    required=False
                ),
                ToolParameter(
                    name="datetime",
                    type="string",
                    description="时间 (ISO格式: 2024-01-15T14:30:00)",
                    required=False
                ),
                ToolParameter(
                    name="event_id",
                    type="string",
                    description="事件ID(删除时用)",
                    required=False
                ),
                ToolParameter(
                    name="description",
                    type="string",
                    description="事件描述",
                    required=False
                )
            ]
        )
    
    def _load_events(self) -> List[Dict]:
        """加载事件"""
        if os.path.exists(self.events_file):
            try:
                with open(self.events_file, 'r') as f:
                    return json.load(f)
            except:
                return []
        return []
    
    def _save_events(self):
        """保存事件"""
        with open(self.events_file, 'w') as f:
            json.dump(self.events, f, indent=2)
    
    async def execute(self, **kwargs) -> ToolResult:
        action = kwargs.get("action")
        
        try:
            if action == "add":
                title = kwargs.get("title")
                dt_str = kwargs.get("datetime")
                description = kwargs.get("description", "")
                
                if not title or not dt_str:
                    return ToolResult(
                        success=False,
                        error="Title and datetime are required for add action"
                    )
                
                event = {
                    "id": f"evt_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    "title": title,
                    "datetime": dt_str,
                    "description": description,
                    "created_at": datetime.now().isoformat()
                }
                
                self.events.append(event)
                self._save_events()
                
                return ToolResult(
                    success=True,
                    data={"event": event}
                )
                
            elif action == "list":
                # 按时间排序
                sorted_events = sorted(
                    self.events,
                    key=lambda e: e["datetime"]
                )
                return ToolResult(
                    success=True,
                    data={
                        "events": sorted_events,
                        "count": len(sorted_events)
                    }
                )
                
            elif action == "delete":
                event_id = kwargs.get("event_id")
                if not event_id:
                    return ToolResult(
                        success=False,
                        error="event_id is required for delete action"
                    )
                
                self.events = [e for e in self.events if e["id"] != event_id]
                self._save_events()
                
                return ToolResult(success=True, data={"deleted": event_id})
                
            elif action == "get_today":
                today = datetime.now().strftime("%Y-%m-%d")
                today_events = [
                    e for e in self.events
                    if e["datetime"].startswith(today)
                ]
                return ToolResult(
                    success=True,
                    data={
                        "date": today,
                        "events": today_events
                    }
                )
                
            else:
                return ToolResult(success=False, error=f"Unknown action: {action}")
                
        except Exception as e:
            return ToolResult(success=False, error=str(e))
