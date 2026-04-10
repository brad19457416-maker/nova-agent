# Nova Agent v0.3.0

> 新一代自主智能体框架 + 深度研究专家

<p align="center">
  <img src="https://img.shields.io/badge/version-0.3.0-blue" alt="Version">
  <img src="https://img.shields.io/badge/python-3.9+-green" alt="Python">
  <img src="https://img.shields.io/badge/license-Apache%202.0-orange" alt="License">
</p>

## ✨ 核心特性

### 1. 配置驱动架构
- **YAML配置**: 工作流、技能、反模式全部声明式配置
- **环境变量覆盖**: `NOVA_WORKFLOW_MAX_ITERATIONS=10`
- **多环境支持**: dev/prod/test 无缝切换

### 2. 工作流引擎
- **阶段式执行**: 7阶段调研 / 6阶段写作 / 6阶段代码
- **条件分支**: 基于置信度的智能阶段跳过
- **反模式检查**: 自动检测常见问题
- **执行历史**: SQLite持久化存储

### 3. LLM客户端
支持多种LLM后端:

| 类型 | 描述 | 连接方式 |
|------|------|----------|
| OllamaLLM | 本地Ollama | `http://localhost:11434` |
| OpenClawLLM | OpenClaw Gateway | `http://localhost:8080` |
| MockLLM | 模拟测试 | 无需连接 |

### 4. 工具系统
- **web_search**: DuckDuckGo搜索
- **web_fetch**: 网页内容抓取
- **code_execute**: 安全Python代码执行
- **inkcore**: 墨芯小说技法分析

### 5. 协作系统
- **Lead/Sub**: 主从协作模式
- **Swarm**: 多Agent共识

---

## 📦 安装

```bash
git clone https://github.com/brad19457416-maker/nova-agent.git
cd nova-agent
pip install -e ".[dev]"
```

### 依赖要求
- Python >= 3.9
- 可选: `aiohttp` (用于LLM客户端)
- 可选: `fastapi` + `uvicorn` (用于API服务)
- 可选: `beautifulsoup4` (用于web工具)

---

## 🚀 快速开始

### CLI使用

```bash
# 运行调研工作流
python -m nova_agent.main workflow research "调研Python异步编程"

# 运行写作工作流
python -m nova_agent.main workflow writing "写一章科幻小说"

# 运行代码工作流
python -m nova_agent.main workflow code "实现一个HTTP客户端"

# 查看统计
python -m nova_agent.main stats

# 配置LLM
python -m nova_agent.main config --llm ollama --model qwen2.5:7b
```

### API服务

```bash
# 启动服务
python -m nova_agent.server
# 或
uvicorn nova_agent.server:app --host 0.0.0.0 --port 8080
```

API端点:
- `GET /health` - 健康检查
- `GET /stats` - 统计信息
- `POST /workflow/run` - 运行工作流
- `POST /skill/run` - 运行技能
- `POST /collab/run` - 运行协作

### Python API

```python
from nova_agent import ConfigManager
from nova_agent.workflow import WorkflowEngine
from nova_agent.llm import create_llm_client

# 加载配置
config = ConfigManager("./config")

# 创建LLM客户端
llm = create_llm_client({"type": "ollama", "model": "qwen2.5:7b"})

# 运行工作流
engine = WorkflowEngine(config, skills, llm)
result = await engine.run("research", {"task": "调研Python异步编程"})
```

---

## 📁 项目结构

```
nova_agent/
├── __init__.py           # 包入口
├── config.py             # 配置管理
├── main.py               # CLI入口
├── server.py             # API服务
├── collaboration/        # 协作系统
│   ├── lead_sub.py      # Lead/Sub协作
│   ├── swarm.py         # Swarm协作
│   └── roles.py         # 角色定义
├── llm/                  # LLM客户端
│   └── client.py        # Ollama/OpenClaw/Mock
├── skills/               # 技能系统
│   ├── loader.py        # 技能加载器
│   └── antipatterns.py  # 反模式检查
├── storage/              # 存储系统
│   └── sqlite_store.py  # SQLite存储
├── tools/                # 工具系统
│   ├── base.py          # 工具基类
│   ├── web.py           # Web工具
│   ├── code.py          # 代码执行
│   ├── files.py         # 文件操作
│   └── inkcore.py       # 墨芯集成
└── workflow/             # 工作流引擎
    ├── engine.py        # 工作流引擎
    ├── base.py          # 阶段处理器基类
    └── builtin/         # 内置工作流
        ├── research.py  # 调研工作流
        ├── writing.py   # 写作工作流
        └── code.py      # 代码工作流

config/default/           # 默认配置
├── workflow.yaml        # 工作流配置
├── skill.yaml           # 技能配置
├── antipatterns.yaml    # 反模式配置
├── llm.yaml             # LLM配置
├── tools.yaml           # 工具配置
└── storage.yaml         # 存储配置
```

---

## ⚙️ 配置

### 配置优先级
1. 环境变量 (`NOVA_WORKFLOW_MAX_ITERATIONS=10`)
2. 运行时配置 (`config.set()`)
3. 配置文件 (`config/default/*.yaml`)
4. 默认值

### 工作流配置示例

```yaml
# config/default/workflow.yaml
workflows:
  research:
    name: 深度调研
    description: 7阶段调研工作流
    phases:
      - id: query_analysis
        name: 查询分析
        handler: QueryAnalysisHandler
        max_iterations: 3
      - id: search
        name: 信息搜索
        handler: SearchHandler
        max_iterations: 5
      # ... 更多阶段
```

### LLM配置示例

```yaml
# config/default/llm.yaml
llm:
  type: ollama
  model: qwen2.5:7b
  ollama:
    base_url: http://localhost:11434
```

---

## 📊 状态

| 组件 | 状态 | 说明 |
|------|------|------|
| 配置系统 | ✅ 稳定 | YAML/JSON + 环境变量 |
| 工作流引擎 | ✅ 稳定 | 阶段式执行 |
| LLM客户端 | ✅ 稳定 | Ollama/OpenClaw/Mock |
| 工具系统 | ✅ 稳定 | Web/代码/文件 |
| 协作系统 | 🚧 Beta | Lead/Sub/Swarm |
| API服务 | 🚧 Beta | FastAPI实现 |

---

## 📚 文档

- [V0.3.0 详细设计](V0.3.0-DETAILED-SPEC.md)
- [V0.3.0 发布说明](V0.3.0-RELEASE-NOTES.md)
- [实现计划](V0.3.0-IMPLEMENTATION-PLAN.md)
- [路线图](ROADMAP.md)
- [贡献指南](CONTRIBUTING.md)

---

## 🤝 贡献

欢迎提交 Issue 和 PR！

1. Fork 仓库
2. 创建分支 (`git checkout -b feature/xxx`)
3. 提交更改 (`git commit -am 'feat: xxx'`)
4. 推送分支 (`git push origin feature/xxx`)
5. 创建 Pull Request

---

## 📄 许可证

Apache License 2.0

---

<p align="center">
  Nova Agent - 让AI代理变得简单
</p>
