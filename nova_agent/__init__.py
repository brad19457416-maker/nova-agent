"""
Nova Agent v0.3.0

通用自主智能体框架 + 深度研究专家

示例:
    >>> from nova_agent import ConfigManager
    >>> config = ConfigManager("./config")
    >>> print(config.get("llm.model"))

主要模块:
    - config: 配置管理
    - workflow: 工作流引擎
    - llm: LLM客户端
    - skills: 技能系统
    - tools: 工具系统
    - storage: 存储系统
    - collaboration: 协作系统

更多信息:
    - 使用指南: https://github.com/brad19457416-maker/nova-agent/blob/master/USAGE.md
    - API文档: https://github.com/brad19457416-maker/nova-agent/blob/master/docs/API.md
"""

__version__ = "0.3.0"

# 导出主要类
from nova_agent.config import ConfigManager

__all__ = [
    "__version__",
    "ConfigManager",
]