# 贡献指南

感谢你对 Nova Agent 的兴趣！以下是参与项目贡献的指南。

## 开发环境设置

```bash
# 克隆仓库
git clone https://github.com/brad19457416-maker/nova-agent.git
cd nova-agent

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装开发依赖
pip install -e ".[dev]"
```

## 代码风格

我们使用以下工具保持代码风格一致：

```bash
# 格式化代码
black nova_agent/ tests/

# 检查代码
ruff check nova_agent/ tests/

# 类型检查
mypy nova_agent/
```

## 测试

```bash
# 运行所有测试
pytest tests/ -v

# 带覆盖率报告
pytest tests/ --cov=nova_agent --cov-report=term

# 运行特定测试
pytest tests/unit/test_config.py -v
```

## 提交 PR

1. Fork 仓库并创建你的分支 (`git checkout -b feature/amazing-feature`)
2. 提交你的改动 (`git commit -m 'Add amazing feature'`)
3. 推送到分支 (`git push origin feature/amazing-feature`)
4. 创建 Pull Request

### PR 要求

- 所有测试必须通过
- 代码风格检查必须通过
- 新功能需要添加测试
- 更新相关文档

## 项目结构

```
nova_agent/
├── agent/          # 核心 Agent 实现
├── memory/         # 记忆系统
├── reasoning/      # HGARN 推理引擎
├── evolution/      # 自我进化引擎
├── tools/          # 插件化工具系统
├── execution/      # 执行沙箱
├── skills/         # 技能管理
├── collaboration/  # 协作模式
├── concurrency/    # 并发控制
├── llm/            # LLM 客户端
└── config.py       # 配置系统
```

## 报告 Bug

请使用 GitHub Issues 报告 Bug，包含：
- 问题描述
- 复现步骤
- 期望行为
- 实际行为
- 环境信息 (Python 版本、操作系统)

## 许可证

贡献即表示你同意你的代码将在 Apache 2.0 许可证下发布。
