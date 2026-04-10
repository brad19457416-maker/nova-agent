# Nova Agent 使用指南

## 目录

- [快速开始](#快速开始)
- [CLI使用](#cli使用)
- [Python API](#python-api)
- [工作流](#工作流)
- [配置](#配置)
- [工具](#工具)
- [协作](#协作)
- [故障排除](#故障排除)

---

## 快速开始

### 安装

```bash
git clone https://github.com/brad19457416-maker/nova-agent.git
cd nova-agent
pip install -e ".[dev]"
```

### 首次运行

```bash
# 创建必要目录
mkdir -p config/default data

# 复制默认配置
cp -r config/default config/myconfig

# 测试安装
python -m nova_agent.main stats
```

---

## CLI使用

### 基本命令

```bash
# 查看帮助
python -m nova_agent.main --help

# 查看统计
python -m nova_agent.main stats

# 列出资源
python -m nova_agent.main list
```

### 工作流命令

```bash
# 调研工作流
python -m nova_agent.main workflow research "调研Python异步编程最佳实践"

# 写作工作流
python -m nova_agent.main workflow writing "写一篇关于AI的科普文章"

# 代码工作流
python -m nova_agent.main workflow code "实现一个带缓存的HTTP客户端"
```

### 技能命令

```bash
# 运行技能
python -m nova_agent.main skill research_skill "分析这个项目的依赖"
```

### 协作命令

```bash
# Lead/Sub协作
python -m nova_agent.main collab "设计一个用户认证系统" --max-subs 3
```

### 工具命令

```bash
# 搜索工具
python -m nova_agent.main tool web_search --query "Python教程"

# 网页抓取
python -m nova_agent.main tool web_fetch --url "https://example.com"

# 代码执行
python -m nova_agent.main tool code_execute --code "print('Hello')"
```

### 配置命令

```bash
# 配置Ollama
python -m nova_agent.main config --llm ollama --model qwen2.5:7b

# 配置OpenClaw
python -m nova_agent.main config --llm openclaw --model kimi-k2.5
```

---

## Python API

### 基础使用

```python
import asyncio
from nova_agent import ConfigManager
from nova_agent.workflow import WorkflowEngine
from nova_agent.llm import create_llm_client
from nova_agent.skills import SkillLoader

async def main():
    # 加载配置
    config = ConfigManager("./config")
    
    # 创建组件
    llm = create_llm_client({"type": "mock"})
    skills = SkillLoader(config)
    
    # 创建工作流引擎
    engine = WorkflowEngine(
        config=config,
        skills=skills,
        llm_client=llm
    )
    
    # 运行工作流
    result = await engine.run(
        "research",
        {"task": "调研Python异步编程"}
    )
    
    print(f"状态: {result.status.value}")
    print(f"耗时: {result.total_duration_ms}ms")
    print(f"输出: {result.final_output}")

asyncio.run(main())
```

### 配置管理

```python
from nova_agent.config import ConfigManager

# 初始化
config = ConfigManager("./config")

# 获取配置（支持点号路径）
max_iter = config.get("workflow.max_iterations", 5)

# 设置配置
config.set("workflow.max_iterations", 10)

# 保存配置
config.save("workflow")

# 环境变量覆盖
# NOVA_WORKFLOW_MAX_ITERATIONS=10
```

### LLM客户端

```python
from nova_agent.llm import create_llm_client

# Ollama
ollama_llm = create_llm_client({
    "type": "ollama",
    "model": "qwen2.5:7b",
    "ollama": {
        "base_url": "http://localhost:11434"
    }
})

# OpenClaw
openclaw_llm = create_llm_client({
    "type": "openclaw",
    "model": "kimi-k2.5",
    "openclaw": {
        "base_url": "http://localhost:8080"
    }
})

# Mock（测试用）
mock_llm = create_llm_client({"type": "mock"})

# 使用
response = await llm.generate("Hello, world!")
```

### 工具使用

```python
from nova_agent.tools import ToolRegistry

tools = ToolRegistry()

# 执行工具
result = await tools.execute("web_search", query="Python教程")

if result.success:
    print(result.data)
else:
    print(f"错误: {result.error}")
```

---

## 工作流

### 内置工作流

#### 1. 调研工作流 (research)

7阶段深度调研：

1. **query_analysis** - 查询分析
2. **search** - 信息搜索
3. **evaluation** - 结果评估
4. **extraction** - 信息提取
5. **synthesis** - 信息综合
6. **fact_check** - 事实核查
7. **report** - 报告生成

#### 2. 写作工作流 (writing)

6阶段内容创作：

1. **topic_analysis** - 主题分析
2. **outline** - 大纲生成
3. **draft** - 初稿撰写
4. **review** - 内容审查
5. **revise** - 修订完善
6. **polish** - 润色定稿

#### 3. 代码工作流 (code)

6阶段代码生成：

1. **requirement** - 需求分析
2. **design** - 架构设计
3. **implement** - 代码实现
4. **test** - 测试生成
5. **review** - 代码审查
6. **document** - 文档生成

### 自定义工作流

```yaml
# config/default/workflow.yaml
workflows:
  my_workflow:
    name: 我的工作流
    description: 自定义工作流
    phases:
      - id: phase1
        name: 第一阶段
        handler: MyHandler
        max_iterations: 3
        condition:
          type: confidence
          min_confidence: 0.7
```

---

## 配置

### 配置文件结构

```
config/
├── default/           # 默认配置
│   ├── workflow.yaml
│   ├── skill.yaml
│   ├── antipatterns.yaml
│   ├── llm.yaml
│   ├── tools.yaml
│   └── storage.yaml
└── prod/             # 生产环境配置
    └── llm.yaml      # 覆盖默认配置
```

### 环境变量

所有配置都可以通过环境变量覆盖：

```bash
# 格式: NOVA_<SECTION>_<KEY>
export NOVA_WORKFLOW_MAX_ITERATIONS=10
export NOVA_LLM_MODEL=gpt-4
export NOVA_STORAGE_DB_PATH=/path/to/db.sqlite
```

### 配置示例

#### LLM配置

```yaml
# config/default/llm.yaml
llm:
  type: ollama
  model: qwen2.5:7b
  temperature: 0.7
  max_tokens: 2000
  
  ollama:
    base_url: http://localhost:11434
    timeout: 30
```

#### 工具配置

```yaml
# config/default/tools.yaml
tools:
  web_search:
    enabled: true
    max_results: 10
    timeout: 30
  
  code_execute:
    enabled: true
    timeout: 60
    max_memory_mb: 512
```

---

## 工具

### 可用工具

| 工具名 | 功能 | 参数 |
|--------|------|------|
| web_search | 网页搜索 | query, max_results |
| web_fetch | 网页抓取 | url, selector |
| code_execute | 代码执行 | code, timeout |
| file_read | 文件读取 | path |
| file_write | 文件写入 | path, content |
| inkcore | 墨芯分析 | text, analysis_type |

### 工具示例

```python
# 网页搜索
result = await tools.execute("web_search", 
    query="Python教程",
    max_results=5
)

# 网页抓取
result = await tools.execute("web_fetch",
    url="https://example.com",
    selector="article"
)

# 代码执行
result = await tools.execute("code_execute",
    code="print(sum(range(100)))",
    timeout=30
)
```

---

## 协作

### Lead/Sub协作

```python
from nova_agent.collaboration import LeadSubCollaboration

collab = LeadSubCollaboration(
    llm_client=llm,
    max_subs=4
)

result = await collab.execute(
    task="设计一个用户系统",
    context={"requirements": [...]}
)

print(result.final_result)
```

### Swarm协作

```python
from nova_agent.collaboration import SwarmCollaboration

swarm = SwarmCollaboration(
    llm_client=llm,
    agent_count=5
)

result = await swarm.execute(
    task="头脑风暴新功能",
    context={}
)
```

---

## 故障排除

### 常见问题

#### 1. 配置目录不存在

```
Error: Config dir not found: ./config/default
```

**解决**:
```bash
mkdir -p config/default
# 创建必要的配置文件
```

#### 2. LLM连接失败

```
Error: Cannot connect to Ollama
```

**解决**:
```bash
# 检查Ollama服务
curl http://localhost:11434/api/tags

# 或切换到Mock模式
export NOVA_LLM_TYPE=mock
```

#### 3. 缺少依赖

```
ModuleNotFoundError: No module named 'aiohttp'
```

**解决**:
```bash
pip install aiohttp
# 或安装全部依赖
pip install -e ".[dev]"
```

#### 4. 数据库权限

```
Error: unable to open database file
```

**解决**:
```bash
mkdir -p data
chmod 755 data
```

### 调试模式

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

---

## 更多资源

- [详细设计文档](V0.3.0-DETAILED-SPEC.md)
- [API文档](docs/API.md) (待完善)
- [示例代码](examples/)
