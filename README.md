# Nova Agent

新一代自主智能体 —— 融合五大前沿开源项目精华，专为 OpenClaw 重新设计从零开始。

---

## 🆚 Nova Agent vs 原生 OpenClaw Agent

| 特性 | 原生 OpenClaw Agent | Nova Agent |
|------|---------------------|------------|
| **长期记忆** | 简单内存存储 | 🏛️ 五级宫殿记忆结构 + 时序事实图谱 |
| **推理架构** | 单轮直接推理 | 🔥 HGARN 层次化双向注意力流 + 动态门控 |
| **自主进化** | 无 | 🧬 完整闭环：评估 → 优化 → 沉淀 → 增强 |
| **协作模式** | 单智能体 / 固定子代理 | 四种模式：直接回答 / Lead/Sub / Swarm / Agency |
| **工具扩展 | 内置工具 | 🔌 完全插件化，热加载，易于第三方扩展 |
| **执行安全** | 直接执行 | 🐳 Docker 沙箱隔离，安全可控 |
| **技能管理** | 静态加载 | 🎯 可组合技能 + 渐进学习 + 自适应遗忘 |
| **配置优化** | 静态配置 | 📈 自主进化自动调参，越用越懂你 |

## 🌟 核心特性

| 特性 | 说明 |
|------|------|
| **🏛️ 五级宫殿记忆** | MemPalace 宫殿式结构化存储 + 时序事实图谱（Graphiti 理念），支持 OpenViking 兼容层级结构 |
| **🔥 层次化门控推理** | HGARN 独创双向注意力流 + 累积增益早停 + JSON 压缩门控，Token 节省 30%+ |
| **🧬 自主进化闭环** | Hermes 风格自我进化：用户反馈 → 质量评估 → 配置进化 → 技能学习，越用越聪明 |
| **👥 四种协作模式 | 适应不同场景：<br>1. **单智能体直接回答** - 简单问题<br>2. **Lead/Sub 主/子分层并行** - 复杂任务分解 (DeerFlow)<br>3. **Swarm 群体平行推演** - 决策预测探索 (MiroFish)<br>4. **Agency 用户参与协作** - 大型项目开发 (OpenAI Agency) |
| **🔌 插件化工具系统** | Hermes 风格可插拔设计，一行代码扩展新工具 |
| **🐳 沙箱执行环境** | DeerFlow 风格 Docker 隔离，代码执行安全可重现 |
| **🎯 可组合技能** | SuperPowers 风格技能封装 + AAAK 压缩节省 Token + 自适应技能遗忘 |
| **⚡ 动态并发控制** | 动态调整并发数 + 优先级调度 + 指数退避，资源利用更高效 |

## 🏛️ 架构概览

```
nova-agent/
 ├── nova_agent/
 │   ├── agent/                 # 核心 Agent 实现
 │   ├── memory/                # 记忆系统（宫殿+时序图谱）
 │   ├── reasoning/             # HGARN 推理引擎
 │   ├── evolution/             # 自我进化引擎
 │   ├── tools/                 # 插件化工具系统
 │   ├── execution/             # 执行沙箱
 │   ├── skills/                # 技能管理与学习
 │   ├── collaboration/         # 四种协作模式
 │   ├── concurrency/           # 动态并发控制
 │   ├── llm/                   # LLM 客户端抽象
 │   └── config.py             # 配置系统
 ├── examples/
 │   ├── quickstart.py          # 快速开始示例
 │   └── agency_project.py     # Agency 用户协作示例
 └── README.md
```

## 🎯 设计理念

- **Built for OpenClaw** —— 原生支持 OpenClaw，开箱即用
- **Any Model, Fully Local** —— 借鉴 Hermes，支持任何 LLM，完全本地运行
- **Structured Long-term Memory** —— 宫殿记忆 + 时序图谱，解决幻觉问题
- **Stateful Self-evolution** —— 越用越聪明，持续进化
- **Four Collaboration Modes** —— 适应从简单到复杂的所有场景
- **Secure Isolated Execution** —— Docker 沙箱保障安全

## 📦 安装

```bash
git clone https://github.com/brad19457416-maker/nova-agent.git
cd nova-agent
pip install -r requirements.txt
```

## 🚀 快速开始（OpenClaw 环境）

```python
from nova_agent import NovaAgent

# 默认配置，使用 OpenClaw LLM 客户端
agent = NovaAgent()

# 运行查询
response = agent.run("帮我分析一下这个项目的架构，并给出改进建议")
print(response)

# 提供反馈，触发自主进化
feedback_result = agent.feedback(
    query="你的问题",
    response=response,
    rating=4,  # 1-5 分
    comment="整体不错，结果很好"
)
print(feedback_result["evolution_report"])
```

## 💡 Nova Agent 如何帮助 OpenClaw 用户

Nova Agent 是**建立在 OpenClaw 基础之上的**，它：

1. **增强而不是替代** —— Nova Agent 充分利用 OpenClaw 的基础设施（工具调用、消息路由、权限管理等）
2. **专注于 Agent 架构创新** —— 在记忆、推理、进化、协作这些层面提供完整的高级实现
3. **原生集成 OpenClaw LLM 客户端** —— 直接使用你已配置的 LLM，无需额外配置
4. **完全兼容 OpenClaw Skill 生态** —— 可以直接使用现有的 OpenClaw Skill

**对于 OpenClaw 用户来说：**
- 如果你只需要简单问答/工具调用：用原生 OpenClaw 就够了
- 如果你需要处理**复杂长期任务**、**自主学习**、**多智能体协作**：Nova Agent 给你更强的能力

## 🔗 参考项目

本项目融合了以下优秀项目的设计思想：

- [NousResearch/Hermes](https://github.com/NousResearch/Hermes) —— 自我进化
- [milla-jovovich/mempalace](https://github.com/milla-jovovich/mempalace) —— 宫殿记忆
- [666ghj/MiroFish](https://github.com/666ghj/MiroFish) —— 群体智能推演
- [bytedance/DeerFlow](https://github.com/bytedance/DeerFlow) —— 主/子架构 + 沙箱
- [bytedance/OpenViking](https://github.com/bytedance/OpenViking) —— 层级上下文数据库
- [OpenAI/Agency](https://github.com/openai/agency) —— Human-in-the-loop 协作
- [obra/superpowers](https://github.com/obra/superpowers) —— 可组合技能

## 📄 许可证

Apache 2.0
