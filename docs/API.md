# Nova Agent API 文档

## 核心模块

### nova_agent

包入口，导出主要类和函数。

```python
from nova_agent import ConfigManager, __version__
```

#### `__version__`

当前版本号。

```python
print(nova_agent.__version__)  # "0.3.0"
```

---

## nova_agent.config

配置管理系统。

### ConfigManager

统一配置管理器，支持YAML/JSON配置和环境变量覆盖。

```python
from nova_agent.config import ConfigManager

config = ConfigManager("./config")
```

#### 构造函数

```python
ConfigManager(config_dir: Optional[str] = None)
```

**参数**:
- `config_dir`: 配置目录路径，默认`"./config"`

#### 方法

##### get

获取配置值，支持点号路径。

```python
get(key: str, default: Any = None) -> Any
```

**示例**:
```python
# 获取工作流最大迭代次数
max_iter = config.get("workflow.max_iterations", 5)

# 获取LLM模型
model = config.get("llm.model", "qwen2.5:7b")
```

##### get_section

获取整个配置节。

```python
get_section(section: str) -> Dict[str, Any]
```

**示例**:
```python
llm_config = config.get_section("llm")
# {'llm': {'type': 'ollama', 'model': 'qwen2.5:7b'}}
```

##### set

设置配置值。

```python
set(key: str, value: Any) -> None
```

**示例**:
```python
config.set("workflow.max_iterations", 10)
```

##### save

保存配置到文件。

```python
save(section: str) -> None
```

**示例**:
```python
config.save("workflow")
```

---

## nova_agent.llm

LLM客户端模块。

### create_llm_client

创建LLM客户端工厂函数。

```python
from nova_agent.llm import create_llm_client

llm = create_llm_client(config: Dict[str, Any])
```

**参数**:
- `config`: LLM配置字典
  - `type`: 客户端类型 (`"ollama"`, `"openclaw"`, `"mock"`)
  - `model`: 模型名称
  - `temperature`: 温度参数
  - `max_tokens`: 最大token数
  - `ollama`: Ollama特定配置
  - `openclaw`: OpenClaw特定配置

**返回**: `LLMClient`实例

**示例**:
```python
# Ollama
ollama_llm = create_llm_client({
    "type": "ollama",
    "model": "qwen2.5:7b",
    "ollama": {"base_url": "http://localhost:11434"}
})

# OpenClaw
openclaw_llm = create_llm_client({
    "type": "openclaw",
    "model": "kimi-k2.5",
    "openclaw": {"base_url": "http://localhost:8080"}
})

# Mock
mock_llm = create_llm_client({"type": "mock"})
```

### LLMClient

LLM客户端基类。

#### generate

生成文本。

```python
async generate(prompt: str, **kwargs) -> str
```

**参数**:
- `prompt`: 提示词
- `**kwargs`: 额外参数（temperature, max_tokens等）

**返回**: 生成的文本

**示例**:
```python
response = await llm.generate("Hello, world!")
print(response)
```

#### generate_stream

流式生成文本。

```python
async generate_stream(prompt: str, **kwargs) -> AsyncIterator[str]
```

**示例**:
```python
async for chunk in llm.generate_stream("讲个故事"):
    print(chunk, end="", flush=True)
```

---

## nova_agent.workflow

工作流引擎模块。

### WorkflowEngine

工作流引擎，执行配置定义的工作流。

```python
from nova_agent.workflow import WorkflowEngine

engine = WorkflowEngine(
    config=config,
    skills=skills,
    llm_client=llm,
    storage=storage,
    antipattern_checker=checker
)
```

#### 构造函数

```python
WorkflowEngine(
    config: ConfigManager,
    skills: SkillLoader,
    llm_client: Optional[LLMClient] = None,
    storage: Optional[SQLiteStore] = None,
    antipattern_checker: Optional[AntipatternChecker] = None
)
```

#### 方法

##### run

运行工作流。

```python
async run(workflow_name: str, context: Dict[str, Any]) -> WorkflowResult
```

**参数**:
- `workflow_name`: 工作流名称
- `context`: 执行上下文

**返回**: `WorkflowResult`对象

**示例**:
```python
result = await engine.run("research", {"task": "调研Python异步"})
print(result.status)  # WorkflowStatus.COMPLETED
print(result.final_output)
```

### WorkflowResult

工作流执行结果。

**属性**:
- `workflow_name`: 工作流名称
- `status`: 执行状态 (`WorkflowStatus`)
- `phases`: 阶段结果列表
- `final_output`: 最终输出
- `total_duration_ms`: 总执行时间（毫秒）
- `metadata`: 元数据字典

### WorkflowStatus

工作流状态枚举。

```python
from nova_agent.workflow import WorkflowStatus

WorkflowStatus.PENDING      # 等待中
WorkflowStatus.RUNNING      # 运行中
WorkflowStatus.COMPLETED    # 已完成
WorkflowStatus.FAILED       # 失败
WorkflowStatus.CANCELLED    # 已取消
```

---

## nova_agent.skills

技能系统模块。

### SkillLoader

技能加载器。

```python
from nova_agent.skills import SkillLoader

skills = SkillLoader(config)
```

#### 方法

##### load

加载技能。

```python
load(skill_name: str) -> Skill
```

### AntipatternChecker

反模式检查器。

```python
from nova_agent.skills import AntipatternChecker

checker = AntipatternChecker(config, storage)
```

#### 方法

##### check

检查反模式。

```python
check(content: str, context: Dict[str, Any]) -> List[AntipatternWarning]
```

---

## nova_agent.tools

工具系统模块。

### ToolRegistry

工具注册表。

```python
from nova_agent.tools import ToolRegistry

tools = ToolRegistry()
```

#### 方法

##### execute

执行工具。

```python
async execute(tool_name: str, **kwargs) -> ToolResult
```

**参数**:
- `tool_name`: 工具名称
- `**kwargs`: 工具参数

**返回**: `ToolResult`对象

**示例**:
```python
result = await tools.execute("web_search", query="Python教程")
if result.success:
    print(result.data)
```

### ToolResult

工具执行结果。

**属性**:
- `success`: 是否成功
- `data`: 返回数据
- `error`: 错误信息（如果失败）

---

## nova_agent.storage

存储系统模块。

### SQLiteStore

SQLite存储实现。

```python
from nova_agent.storage import SQLiteStore

storage = SQLiteStore("./data/nova.db")
```

#### 构造函数

```python
SQLiteStore(db_path: str)
```

#### 方法

##### save_execution

保存执行记录。

```python
save_execution(record: Dict[str, Any]) -> str
```

##### get_execution

获取执行记录。

```python
get_execution(execution_id: str) -> Optional[Dict[str, Any]]
```

##### list_executions

列出执行记录。

```python
list_executions(
    workflow_name: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 100
) -> List[Dict[str, Any]]
```

---

## nova_agent.collaboration

协作系统模块。

### LeadSubCollaboration

Lead/Sub协作模式。

```python
from nova_agent.collaboration import LeadSubCollaboration

collab = LeadSubCollaboration(
    llm_client=llm,
    max_subs=4
)
```

#### 方法

##### execute

执行协作任务。

```python
async execute(task: str, context: Dict[str, Any]) -> CollaborationResult
```

### SwarmCollaboration

Swarm协作模式。

```python
from nova_agent.collaboration import SwarmCollaboration

swarm = SwarmCollaboration(
    llm_client=llm,
    agent_count=5
)
```

---

## nova_agent.main

CLI模块。

### NovaAgentCLI

命令行接口类。

```python
from nova_agent.main import NovaAgentCLI

cli = NovaAgentCLI(config_dir="./config", db_path="./data/nova.db")
```

#### 方法

##### run_workflow

运行工作流。

```python
async run_workflow(workflow_name: str, task: str) -> Dict[str, Any]
```

##### run_skill

运行技能。

```python
async run_skill(skill_name: str, task: str) -> Dict[str, Any]
```

##### run_collab

运行协作。

```python
async run_collab(task: str, max_subs: int = 4) -> Dict[str, Any]
```

##### run_tool

运行工具。

```python
async run_tool(tool_name: str, **kwargs) -> Dict[str, Any]
```

##### get_stats

获取统计信息。

```python
get_stats() -> Dict[str, Any]
```

---

## 类型提示

完整类型提示支持：

```python
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from nova_agent.config import ConfigManager
    from nova_agent.llm import LLMClient
    from nova_agent.workflow import WorkflowEngine, WorkflowResult
    from nova_agent.skills import SkillLoader, AntipatternChecker
    from nova_agent.tools import ToolRegistry, ToolResult
    from nova_agent.storage import SQLiteStore
```

---

## 示例

### 完整工作流示例

```python
import asyncio
from nova_agent import ConfigManager
from nova_agent.llm import create_llm_client
from nova_agent.workflow import WorkflowEngine
from nova_agent.skills import SkillLoader, AntipatternChecker
from nova_agent.storage import SQLiteStore

async def main():
    # 初始化组件
    config = ConfigManager("./config")
    storage = SQLiteStore("./data/nova.db")
    skills = SkillLoader(config)
    checker = AntipatternChecker(config, storage)
    llm = create_llm_client(config.get_section("llm").get("llm", {}))
    
    # 创建工作流引擎
    engine = WorkflowEngine(
        config=config,
        skills=skills,
        llm_client=llm,
        storage=storage,
        antipattern_checker=checker
    )
    
    # 运行工作流
    result = await engine.run(
        "research",
        {"task": "调研Python异步编程最佳实践"}
    )
    
    # 处理结果
    print(f"状态: {result.status.value}")
    print(f"耗时: {result.total_duration_ms}ms")
    print(f"输出: {result.final_output}")
    
    # 检查反模式警告
    if result.metadata.get("antipattern_warnings"):
        for warning in result.metadata["antipattern_warnings"]:
            print(f"警告: {warning['name']} - {warning['message']}")

if __name__ == "__main__":
    asyncio.run(main())
```

---

## 错误处理

所有异步方法可能抛出以下异常：

- `ConfigError`: 配置错误
- `WorkflowError`: 工作流执行错误
- `ToolError`: 工具执行错误
- `LLMError`: LLM调用错误
- `StorageError`: 存储错误

**示例**:
```python
from nova_agent.exceptions import ConfigError, WorkflowError

try:
    result = await engine.run("research", {"task": "..."})
except ConfigError as e:
    print(f"配置错误: {e}")
except WorkflowError as e:
    print(f"工作流错误: {e}")
```

---

*文档版本: 0.3.0*
