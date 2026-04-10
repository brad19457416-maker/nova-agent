"""
反模式系统

明确告知AI不要做什么，比告诉它要做什么更有效

使用示例:
    checker = AntipatternChecker(config_manager)
    
    # 检查内容
    warnings = checker.check(content, "research")
    
    # 从反馈学习
    checker.learn_from_feedback({
        "type": "negative_pattern",
        "issue": "对话太平淡",
        "category": "writing"
    })
"""

from typing import Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum
import re
import logging

logger = logging.getLogger(__name__)


class Severity(Enum):
    CRITICAL = "critical"  # 必须避免
    MAJOR = "major"        # 应该避免
    MINOR = "minor"        # 建议避免


@dataclass
class Antipattern:
    """反模式定义"""
    id: str
    name: str
    description: str
    category: str
    severity: Severity = Severity.MAJOR
    keywords: List[str] = field(default_factory=list)
    patterns: List[str] = field(default_factory=list)
    remediation: str = ""


class AntipatternChecker:
    """
    反模式检查器
    
    功能:
    - 加载反模式库
    - 文本内容检查
    - 反馈学习扩展
    """
    
    CATEGORIES = ["general", "research", "writing", "code", "design"]
    
    def __init__(self, config_manager, storage=None):
        self.config = config_manager
        self.storage = storage
        self.antipatterns: Dict[str, List[Antipattern]] = {
            cat: [] for cat in self.CATEGORIES
        }
        self._load_antipatterns()
    
    def _load_antipatterns(self):
        """加载反模式库"""
        antipatterns_config = self.config.get_section("antipatterns")
        
        for category, patterns in antipatterns_config.items():
            if category not in self.CATEGORIES:
                continue
            
            for pattern_data in patterns:
                antipattern = Antipattern(
                    id=pattern_data.get("id", ""),
                    name=pattern_data.get("name", ""),
                    description=pattern_data.get("description", ""),
                    category=category,
                    severity=Severity(pattern_data.get("severity", "major")),
                    keywords=pattern_data.get("keywords", []),
                    patterns=pattern_data.get("patterns", []),
                    remediation=pattern_data.get("remediation", "")
                )
                self.antipatterns[category].append(antipattern)
        
        # 从存储加载用户添加的反模式
        if self.storage:
            try:
                stored = self.storage.get_antipatterns()
                for ap in stored:
                    antipattern = Antipattern(
                        id=ap.get("id", ""),
                        name=ap.get("name", ""),
                        description=ap.get("description", ""),
                        category=ap.get("category", "general"),
                        severity=Severity(ap.get("severity", "major")),
                        keywords=ap.get("keywords", []),
                        remediation=ap.get("remediation", "")
                    )
                    if antipattern.category in self.CATEGORIES:
                        self.antipatterns[antipattern.category].append(antipattern)
            except Exception as e:
                logger.warning(f"Failed to load antipatterns from storage: {e}")
        
        total = sum(len(v) for v in self.antipatterns.values())
        logger.info(f"Loaded {total} antipatterns")
    
    def check(self, content: str, category: str = "general") -> List[Dict]:
        """
        检查内容是否包含反模式
        
        Args:
            content: 待检查内容
            category: 类别（general/research/writing/code）
        
        Returns:
            匹配的反模式列表
        """
        if not content:
            return []
        
        matches = []
        
        # 检查指定类别
        for ap in self.antipatterns.get(category, []):
            if self._matches(content, ap):
                matches.append({
                    "id": ap.id,
                    "name": ap.name,
                    "description": ap.description,
                    "severity": ap.severity.value,
                    "remediation": ap.remediation,
                    "category": category
                })
        
        # 也检查通用反模式
        for ap in self.antipatterns.get("general", []):
            if self._matches(content, ap):
                matches.append({
                    "id": ap.id,
                    "name": ap.name,
                    "description": ap.description,
                    "severity": ap.severity.value,
                    "category": "general"
                })
        
        # 去重
        seen = set()
        unique_matches = []
        for m in matches:
            if m["id"] not in seen:
                seen.add(m["id"])
                unique_matches.append(m)
        
        # 按严重程度排序
        severity_order = {"critical": 0, "major": 1, "minor": 2}
        unique_matches.sort(key=lambda x: severity_order.get(x["severity"], 3))
        
        return unique_matches
    
    def _matches(self, content: str, antipattern: Antipattern) -> bool:
        """检查内容是否匹配反模式"""
        content_lower = content.lower()
        
        # 关键词匹配
        for keyword in antipattern.keywords:
            if keyword.lower() in content_lower:
                return True
        
        # 正则模式匹配
        for pattern in antipattern.patterns:
            try:
                if re.search(pattern, content, re.IGNORECASE):
                    return True
            except re.error:
                pass
        
        return False
    
    def get_warning_level(self, matches: List[Dict]) -> str:
        """根据匹配结果获取警告级别"""
        if not matches:
            return "none"
        
        severity_scores = {
            "critical": 3,
            "major": 2,
            "minor": 1
        }
        
        total_score = sum(
            severity_scores.get(m.get("severity", "major"), 2)
            for m in matches
        )
        
        if total_score >= 5:
            return "high"
        elif total_score >= 2:
            return "medium"
        else:
            return "low"
    
    def learn_from_feedback(self, feedback: Dict):
        """
        从反馈学习，添加新的反模式
        
        Args:
            feedback: 反馈数据
                {
                    "type": "negative_pattern",
                    "content": "生成的内容...",
                    "issue": "问题描述",
                    "category": "writing"
                }
        """
        if feedback.get("type") != "negative_pattern":
            return
        
        issue = feedback.get("issue", "")
        category = feedback.get("category", "general")
        
        if not issue or category not in self.CATEGORIES:
            return
        
        # 简单关键词提取
        keywords = issue.split()[:5]
        
        # 创建新反模式
        new_ap = Antipattern(
            id=f"learned_{len(self.antipatterns[category])}",
            name=issue[:50],
            description=issue,
            category=category,
            severity=Severity.MAJOR,
            keywords=keywords,
            remediation="从用户反馈中学习"
        )
        
        self.antipatterns[category].append(new_ap)
        
        # 持久化存储
        if self.storage:
            try:
                self.storage.save_antipattern(
                    new_ap.name,
                    new_ap.description,
                    new_ap.category,
                    new_ap.severity.value,
                    new_ap.keywords
                )
                logger.info(f"Learned new antipattern: {new_ap.name}")
            except Exception as e:
                logger.error(f"Failed to save antipattern: {e}")
    
    def get_all_for_category(self, category: str) -> List[Dict]:
        """获取指定类别的所有反模式"""
        if category not in self.CATEGORIES:
            return []
        
        return [
            {
                "id": ap.id,
                "name": ap.name,
                "description": ap.description,
                "severity": ap.severity.value,
                "remediation": ap.remediation
            }
            for ap in self.antipatterns[category]
        ]
    
    def get_prompt_context(self, category: str = "general") -> str:
        """
        获取反模式提示上下文
        
        用于在LLM调用时注入反模式约束
        """
        antipatterns = self.antipatterns.get(category, []) + self.antipatterns.get("general", [])
        
        if not antipatterns:
            return ""
        
        lines = ["\n\n# 反模式（必须避免）\n"]
        
        # 按严重程度分组
        critical = [ap for ap in antipatterns if ap.severity == Severity.CRITICAL]
        major = [ap for ap in antipatterns if ap.severity == Severity.MAJOR]
        
        if critical:
            lines.append("## 严重问题（必须避免）\n")
            for ap in critical:
                lines.append(f"- **{ap.name}**: {ap.description}")
                if ap.keywords:
                    lines.append(f"  关键词: {', '.join(ap.keywords)}")
        
        if major:
            lines.append("\n## 主要问题（建议避免）\n")
            for ap in major:
                lines.append(f"- **{ap.name}**: {ap.description}")
        
        return "\n".join(lines)
