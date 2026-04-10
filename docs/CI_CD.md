# CI/CD 配置说明

Nova Agent 使用 GitHub Actions 实现持续集成和持续部署。

---

## 工作流概览

### 1. CI 工作流 (.github/workflows/ci.yml)

**触发条件:**
- Push 到 `main` 或 `develop` 分支
- Pull Request 到 `main` 或 `develop` 分支

**执行的任务:**

#### 测试任务 (test)
- 在 Python 3.9, 3.10, 3.11, 3.12 上运行
- 安装依赖
- 运行完整测试套件
- 生成覆盖率报告
- 上传覆盖率到 Codecov

#### 代码检查任务 (lint)
- **Black**: 代码格式化检查
- **Ruff**: 代码风格和质量检查
- **MyPy**: 类型检查

#### 构建任务 (build)
- 构建 Python 包
- 验证包完整性
- 上传构建产物

---

### 2. 发布工作流 (.github/workflows/release.yml)

**触发条件:**
- Push tag 以 `v` 开头 (例如 `v0.1.0`)

**执行的任务:**
1. 构建 Python 包
2. 发布到 PyPI (需要 `PYPI_API_TOKEN` secret)
3. 创建 GitHub Release

---

## 本地开发命令

使用 Makefile 简化常见任务:

```bash
# 安装开发依赖
make install-dev

# 运行测试
make test

# 运行测试并生成覆盖率报告
make test-cov

# 格式化代码
make format

# 检查代码风格
make lint

# 类型检查
make type-check

# 构建包
make build

# 清理构建文件
make clean
```

---

## 代码质量工具配置

### Black (代码格式化)
```toml
[tool.black]
line-length = 100
target-version = ['py39', 'py310', 'py311', 'py312']
```

### Ruff (代码检查)
```toml
[tool.ruff]
line-length = 100
target-version = "py39"
select = ["E", "F", "I", "N", "W", "UP", "B", "C4", "SIM"]
```

### MyPy (类型检查)
```toml
[tool.mypy]
python_version = "3.9"
warn_return_any = true
warn_unused_configs = true
```

---

## 发布新版本

1. 更新版本号 (`setup.py` 和 `nova_agent/__init__.py`)
2. 更新 `CHANGELOG.md`
3. 创建 tag:
   ```bash
   git tag v0.1.1
   git push origin v0.1.1
   ```
4. GitHub Actions 会自动发布到 PyPI

---

## 必需的 Secrets

在 GitHub 仓库设置中添加:

- `PYPI_API_TOKEN`: PyPI API Token (用于发布)
- `CODECOV_TOKEN`: Codecov Token (可选，用于覆盖率上传)

---

## 状态徽章

添加到 README.md:

```markdown
[![CI](https://github.com/brad19457416-maker/nova-agent/actions/workflows/ci.yml/badge.svg)](https://github.com/brad19457416-maker/nova-agent/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/brad19457416-maker/nova-agent/branch/main/graph/badge.svg)](https://codecov.io/gh/brad19457416-maker/nova-agent)
[![PyPI version](https://badge.fury.io/py/nova-agent.svg)](https://badge.fury.io/py/nova-agent)
```

