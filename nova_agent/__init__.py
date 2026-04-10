"""
Nova Agent - 新一代自主智能体

融合五大前沿开源项目精华，重新设计从零开始。

- 🏛️ 五级宫殿记忆 + 时序事实图谱
- 🔥 层次化门控注意力残差推理（双向注意力流）
- 🧬 完整自主进化闭环
- 👥 双模式协作（主/子分层 + 群体平行推演）
- 🔌 插件化工具系统
- 🐳 Docker 沙箱执行环境
- 🎯 可组合技能渐进加载
"""

__version__ = "0.1.1"
__author__ = "Nova Agent Team"

from .agent.nova_agent import NovaAgent

__all__ = ["NovaAgent"]
