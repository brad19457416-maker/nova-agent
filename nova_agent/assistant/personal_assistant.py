"""
个人助理 - 通用助手场景实现
"""

import re
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import json

from nova_agent.agent.nova_agent import NovaAgent
from nova_agent.tools.registry import ToolRegistry
from nova_agent.tools.builtin import (
    WebSearchTool, WebFetchTool, CodeExecuteTool,
    FileTool, CalculatorTool, CalendarTool
)


@dataclass
class ConversationContext:
    """对话上下文"""
    user_name: str = "用户"
    preferences: Dict[str, Any] = field(default_factory=dict)
    recent_intents: List[str] = field(default_factory=list)


@dataclass
class Intent:
    """意图识别结果"""
    name: str
    confidence: float
    entities: Dict[str, Any] = field(default_factory=dict)
    slots: Dict[str, str] = field(default_factory=dict)


class IntentRecognizer:
    """
    意图识别器
    识别用户意图并提取关键信息
    """
    
    # 意图模式
    INTENT_PATTERNS = {
        "search": [
            r"搜索|查找|找|search|find|look up",
            r"(.*)是什么",
            r"(.*)怎么样",
            r"(.*)好吗",
        ],
        "web_fetch": [
            r"获取|抓取|打开|访问|fetch|get",
            r"看看.*网页",
        ],
        "code": [
            r"写.*代码|编程|code|program",
            r"执行.*计算",
            r"帮我算",
        ],
        "calendar_add": [
            r"添加.*日程|新建.*提醒|设置.*提醒",
            r"(.*号|.*点).*(提醒|会议|日程)",
        ],
        "calendar_list": [
            r"查看.*日程|今天.*安排|有什么.*安排",
            r"我的.*日程",
        ],
        "file_read": [
            r"读取|查看.*文件|打开.*文件|读.*文件",
        ],
        "file_write": [
            r"保存|写入|创建.*文件",
        ],
        "weather": [
            r"天气|温度|气候",
        ],
        "general": [
            r".*"
        ]
    }
    
    def recognize(self, query: str) -> Intent:
        """
        识别意图
        
        Args:
            query: 用户查询
            
        Returns:
            Intent对象
        """
        query = query.strip()
        
        # 匹配意图
        for intent_name, patterns in self.INTENT_PATTERNS.items():
            for pattern in patterns:
                match = re.search(pattern, query.lower())
                if match:
                    # 提取实体
                    entities = self._extract_entities(query, intent_name, match)
                    
                    return Intent(
                        name=intent_name,
                        confidence=0.8,
                        entities=entities,
                        slots={"original": query}
                    )
        
        # 默认通用意图
        return Intent(
            name="general",
            confidence=0.5,
            slots={"original": query}
        )
    
    def _extract_entities(
        self,
        query: str,
        intent: str,
        match: re.Match
    ) -> Dict[str, Any]:
        """提取实体"""
        entities = {}
        
        # 提取时间
        time_patterns = [
            (r"(\d+)号", "day"),
            (r"(\d+)点", "hour"),
            (r"(\d+)分", "minute"),
            (r"今天", "today"),
            (r"明天", "tomorrow"),
            (r"后天", "day_after_tomorrow"),
        ]
        
        for pattern, key in time_patterns:
            if re.search(pattern, query):
                entities[key] = True
        
        # 提取数字
        numbers = re.findall(r"\d+", query)
        if numbers:
            entities["numbers"] = [int(n) for n in numbers]
        
        # URL
        urls = re.findall(r"https?://[^\s]+", query)
        if urls:
            entities["url"] = urls[0]
        
        return entities


class PersonalAssistant:
    """
    个人助理
    
    功能:
    - 意图识别
    - 工具自动选择
    - 对话管理
    - 个性化服务
    """
    
    def __init__(self, agent: NovaAgent):
        self.agent = agent
        self.intent_recognizer = IntentRecognizer()
        self.tool_registry = ToolRegistry()
        self.context = ConversationContext()
        
        # 注册内置工具
        self._register_builtin_tools()
    
    def _register_builtin_tools(self):
        """注册内置工具"""
        self.tool_registry.register(WebSearchTool())
        self.tool_registry.register(WebFetchTool())
        self.tool_registry.register(CodeExecuteTool())
        self.tool_registry.register(FileTool(base_path="./data/files"))
        self.tool_registry.register(CalculatorTool())
        self.tool_registry.register(CalendarTool())
    
    async def process(self, query: str) -> str:
        """
        处理用户查询
        
        Args:
            query: 用户查询
            
        Returns:
            响应内容
        """
        # 1. 意图识别
        intent = self.intent_recognizer.recognize(query)
        
        # 更新上下文
        self.context.recent_intents.append(intent.name)
        if len(self.context.recent_intents) > 10:
            self.context.recent_intents = self.context.recent_intents[-10:]
        
        # 2. 根据意图处理
        if intent.name == "search":
            return await self._handle_search(query, intent)
        
        elif intent.name == "web_fetch":
            return await self._handle_web_fetch(query, intent)
        
        elif intent.name == "code":
            return await self._handle_code(query, intent)
        
        elif intent.name == "calendar_add":
            return await self._handle_calendar_add(query, intent)
        
        elif intent.name == "calendar_list":
            return await self._handle_calendar_list(query, intent)
        
        elif intent.name == "file_read":
            return await self._handle_file_read(query, intent)
        
        elif intent.name == "file_write":
            return await self._handle_file_write(query, intent)
        
        else:
            # 3. 使用通用Agent处理
            return await self._handle_general(query)
    
    async def _handle_search(self, query: str, intent: Intent) -> str:
        """处理搜索"""
        # 提取搜索关键词
        keywords = query
        for prefix in ["搜索", "查找", "找"]:
            keywords = keywords.replace(prefix, "")
        keywords = keywords.strip()
        
        if not keywords:
            keywords = intent.entities.get("query", query)
        
        result = await self.tool_registry.execute(
            "web_search",
            {"query": keywords, "num_results": 5}
        )
        
        if result.success:
            results = result.data.get("results", [])
            output = f"搜索结果 ({keywords}):\n\n"
            for i, r in enumerate(results, 1):
                output += f"{i}. {r.get('title', '无标题')}\n"
                output += f"   {r.get('snippet', '')[:100]}...\n\n"
            return output
        else:
            return f"搜索失败: {result.error}"
    
    async def _handle_web_fetch(self, query: str, intent: Intent) -> str:
        """处理网页获取"""
        url = intent.entities.get("url")
        
        if not url:
            # 尝试从查询中提取
            urls = re.findall(r"https?://[^\s]+", query)
            url = urls[0] if urls else None
        
        if not url:
            return "请提供要访问的URL"
        
        result = await self.tool_registry.execute(
            "web_fetch",
            {"url": url, "max_chars": 3000}
        )
        
        if result.success:
            return f"网页内容:\n\n{result.data.get('content', '')[:2000]}"
        else:
            return f"获取失败: {result.error}"
    
    async def _handle_code(self, query: str, intent: Intent) -> str:
        """处理代码执行"""
        # 提取代码或计算表达式
        code = query
        for prefix in ["写代码", "编程", "计算", "帮我算"]:
            code = code.replace(prefix, "")
        code = code.strip()
        
        if not code:
            return "请提供要执行的代码或计算表达式"
        
        # 判断是计算还是代码
        if re.match(r"^[\d\s\+\-\*/\.\(\)]+$", code):
            # 简单计算
            result = await self.tool_registry.execute(
                "calculator",
                {"expression": code}
            )
        else:
            # 代码执行
            result = await self.tool_registry.execute(
                "code_execute",
                {"code": code}
            )
        
        if result.success:
            output = result.data.get("output", "")
            return f"执行结果:\n{output}"
        else:
            return f"执行失败: {result.error}"
    
    async def _handle_calendar_add(self, query: str, intent: Intent) -> str:
        """处理添加日程"""
        # 提取标题和时间
        title = intent.slots.get("original", query)
        
        # 简化：使用当前时间 + 1小时
        dt = datetime.now() + timedelta(hours=1)
        datetime_str = dt.strftime("%Y-%m-%dT%H:%M:%S")
        
        result = await self.tool_registry.execute(
            "calendar",
            {
                "action": "add",
                "title": title,
                "datetime": datetime_str,
                "description": "通过语音助手添加"
            }
        )
        
        if result.success:
            return f"日程已添加: {title}\n时间: {datetime_str}"
        else:
            return f"添加失败: {result.error}"
    
    async def _handle_calendar_list(self, query: str, intent: Intent) -> str:
        """处理查看日程"""
        result = await self.tool_registry.execute(
            "calendar",
            {"action": "get_today"}
        )
        
        if result.success:
            events = result.data.get("events", [])
            if not events:
                return "今天没有日程安排"
            
            output = "今天的日程:\n"
            for e in events:
                dt = datetime.fromisoformat(e["datetime"])
                output += f"- {dt.strftime('%H:%M')} {e['title']}\n"
            return output
        else:
            return f"查询失败: {result.error}"
    
    async def _handle_file_read(self, query: str, intent: Intent) -> str:
        """处理读取文件"""
        # 提取文件名
        match = re.search(r"读取.*?文件[：:](.+)|读取(.+)\.txt", query)
        filename = ""
        if match:
            filename = match.group(1) or match.group(2)
        
        if not filename:
            return "请指定要读取的文件名"
        
        result = await self.tool_registry.execute(
            "file",
            {"action": "read", "path": filename}
        )
        
        if result.success:
            return f"文件内容:\n{result.data.get('content', '')[:1000]}"
        else:
            return f"读取失败: {result.error}"
    
    async def _handle_file_write(self, query: str, intent: Intent) -> str:
        """处理写入文件"""
        return "文件写入功能需要指定文件名和内容"
    
    async def _handle_general(self, query: str) -> str:
        """处理通用查询"""
        # 使用Nova Agent处理
        return self.agent.run(query)
    
    def set_user_name(self, name: str):
        """设置用户名"""
        self.context.user_name = name
    
    def set_preference(self, key: str, value: Any):
        """设置偏好"""
        self.context.preferences[key] = value
    
    def get_stats(self) -> Dict:
        """获取助手统计"""
        return {
            "context": {
                "user_name": self.context.user_name,
                "recent_intents": self.context.recent_intents[-5:]
            },
            "tools": self.tool_registry.get_usage_stats()
        }
