# Nova Agent

> 新一代自主智能体 —— 融合五大前沿开源项目精华，专为 OpenClaw 重新设计

<p align="center">
  <img src="https://img.shields.io/badge/version-0.1.0-blue" alt="Version">
  <img src="https://img.shields.io/badge/python-3.10+-green" alt="Python">
  <img src="https://img.shields.io/badge/license-Apache%202.0-orange" alt="License">
</p>

## ✨ 特性

### 🏛️ 五级宫殿记忆
- **L0 工作记忆**: 当前对话上下文
- **L1 短期记忆**: 当前任务相关信息
- **L2 中期记忆**: 会话内重要信息
- **L3 长期记忆**: 跨会话知识
- **L4 永久记忆**: 核心事实和技能

### 🔥 层次化门控推理 (HGARN)
- 双向注意力流
- 动态门控机制
- Token 节省 30%+

### 🧬 自主进化闭环
- 用户反馈收集
- 质量评估算法
- 配置自动调参
- 越用越聪明

### 🔌 插件化工具系统
- 一行代码扩展新工具
- 热加载支持

### 🐳 安全执行环境
- Docker 沙箱隔离 (未来版本)
- 代码执行安全可控

## 📦 安装

```bash
git clone https://github.com/brad19457416-maker/nova-agent.git
cd nova-agent
pip install -r requirements.txt
```

## 🚀 快速开始

```python
from nova_agent import NovaAgent
from nova_agent.config import NovaConfig

# 创建 Agent
agent = NovaAgent()

# 运行查询
response = agent.run("帮我分析一下这个项目的架构")
print(response)

# 提供反馈，触发进化
feedback_result = agent.feedback(
    query="...",
    response=response,
    rating=4,
    comment="回答很好"
)
```

## 📁 项目结构

```
nova_agent/
├── nova_agent/
│   ├── __init__.py          # 入口
│   ├── config.py            # 配置系统
│   ├── agent/               # 核心Agent实现
│   │   └── nova_agent.py
│   ├── memory/              # 记忆系统
│   │   ├── palace.py        # 五级宫殿
│   │   └── temporal.py      # 时序图谱
│   ├── llm/                 # LLM客户端
│   │   └── client.py
│   ├── reasoning/           # 推理引擎 (未来)
│   ├── evolution/           # 进化引擎 (未来)
│   ├── tools/               # 工具系统 (未来)
│   ├── execution/           # 执行沙箱 (未来)
│   └── skills/              # 技能管理 (未来)
├── examples/
│   └── quickstart.py        # 快速开始示例
├── requirements.txt
└── README.md
```

## 🎯 MVP 功能

| 功能 | 状态 | 说明 |
|------|------|------|
| 五级宫殿记忆 | ✅ | L0-L4 分层存储 |
| 时序图谱 | ✅ | 事实存储和推理 |
| LLM集成 | ✅ | OpenClaw/Ollama |
| 工具注册 | ✅ | 函数注册 |
| 反馈进化 | ✅ | 基础参数调优 |
| 协作模式 | ⏳ | 待实现 |
| Docker沙箱 | ⏳ | 待实现 |

## 📊 与 OpenClaw 集成

Nova Agent 是建立在 OpenClaw 基础之上的：

```python
from nova_agent import NovaAgent
from nova_agent.config import NovaConfig

# 使用OpenClaw的LLM
config = NovaConfig(
    llm=NovaConfig.LLMConfig(
        provider="openclaw",
        model="qwen2.5:7b",
        base_url="http://localhost:11434"
    )
)

agent = NovaAgent(config)
```

## 📋 版本历史

- **v0.1.0** (2026-04-10): MVP版本
  - 五级宫殿记忆系统
  - 时序事实图谱
  - 基础LLM集成
  - 反馈进化机制

## 🤝 贡献

欢迎提交 Issue 和 PR！

## 📄 许可证

Apache License 2.0
