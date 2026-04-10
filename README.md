# Nova Agent

新一代自主智能体 —— 融合五大前沿开源项目精华，重新设计从零开始。

## 🌟 核心特性

| 特性 | 说明 |
|------|------|
| **🏛️ 五级宫殿记忆** | 融合 MemPalace + 我们时序事实图谱，最强长期记忆 |
| **🔥 层次化门控推理** | HGARN 独创双向注意力流 + 动态门控 + 置信度路由 |
| **🧬 自主进化闭环** | Hermes 风格自我进化 —— 评估 → 优化 → 沉淀 → 增强 |
| **👥 双模式协作** | 支持主/子分层调度 (DeerFlow) + 群体平行推演 (MiroFish) |
| **🔌 插件化工具系统** | Hermes 风格可插拔设计，易于扩展 |
| **🐳 沙箱执行环境** | DeerFlow 风格 Docker 隔离，安全可重现 |
| **🎯 可组合技能** | SuperPowers 风格技能封装 + 渐进加载 |

## 🏛️ 架构概览

```
 nova-agent/
  ├── agent/                 # 核心 Agent 实现
  ├── memory/                # 记忆系统（宫殿+图谱）
  ├── reasoning/             # 核心推理引擎
  ├── evolution/             # 自我进化引擎
  ├── tools/                 # 插件化工具系统
  ├── execution/             # 执行沙箱
  ├── skills/                # 技能管理
  ├── collaboration/         # 多智能体协作
  └── concurrency/           # 并发控制
```

## 🎯 设计理念

- **Any Model, Any Platform, Fully Local** —— 借鉴 Hermes
- **Memory Palace for Structured Long-term Memory** —— 借鉴 MemPalace
- **Stateful Self-evolution** —— 越用越聪明
- **Two Collaboration Modes** —— 分层分解 vs 群体推演
- **Secure Isolated Execution** —— Docker 沙箱保障安全

## 📦 安装

```bash
git clone https://github.com/your-name/nova-agent.git
cd nova-agent
pip install -r requirements.txt
```

## 🚀 快速开始

```python
from nova_agent import NovaAgent

agent = NovaAgent()
response = agent.run("你的问题")
print(response)
```

## 🔗 参考项目

本项目融合了以下优秀项目的设计思想：

- [NousResearch/Hermes](https://github.com/NousResearch/Hermes) —— 自我进化
- [milla-jovovich/mempalace](https://github.com/milla-jovovich/mempalace) —— 宫殿记忆
- [666ghj/MiroFish](https://github.com/666ghj/MiroFish) —— 群体智能推演
- [bytedance/DeerFlow](https://github.com/bytedance/DeerFlow) —— 主/子架构 + 沙箱
- [obra/superpowers](https://github.com/obra/superpowers) —— 可组合技能

## 📄 许可证

Apache 2.0
