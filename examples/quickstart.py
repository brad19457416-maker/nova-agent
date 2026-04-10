"""
Nova Agent Quickstart

快速开始示例
"""

from nova_agent import NovaAgent
from nova_agent.config import Config

# 创建 Agent，使用默认配置
agent = NovaAgent()

# 运行查询
response = agent.run("帮我分析一下 Nova Agent 架构的主要优势")
print(response)

# 如果有反馈，可以提供评分帮助 Agent 进化
# agent.feedback("帮我分析一下 Nova Agent 架构的主要优势", response, rating=5)
