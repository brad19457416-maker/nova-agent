# Changelog

所有重要的变更都会记录在这个文件中。

格式基于 [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)，
并且本项目遵循 [Semantic Versioning](https://semver.org/lang/zh-CN/)。

## [0.3.0] - 2026-04-10

### 🎉 新特性

- **配置驱动架构**: 支持YAML/JSON配置和环境变量覆盖
- **工作流引擎**: 阶段式执行，支持调研/写作/代码三种内置工作流
- **LLM客户端**: 支持Ollama、OpenClaw和Mock三种后端
- **工具系统**: 内置web搜索、网页抓取、代码执行、墨芯分析等工具
- **协作系统**: 支持Lead/Sub和Swarm两种协作模式
- **API服务**: FastAPI实现的HTTP API
- **反模式检查**: 自动检测工作流中的常见问题
- **SQLite存储**: 执行历史持久化

### 🏗️ 架构变更

- 完全移除v0.1.x旧架构 (~8,000行代码)
- 统一使用v0.3.x新架构 (~3,900行代码)
- 代码量减少66%，架构更清晰

### 📁 文件变更

- 新增: `USAGE.md` - 详细使用指南
- 新增: `docs/API.md` - API文档
- 更新: `README.md` - 全面重写，反映新架构
- 删除: 大量v0.1.x相关的冗余文档

### 🐛 修复

- 修复版本号不一致问题
- 移除`sys.path.insert`代码异味
- 统一导入路径 (`nova_agent.v0_3` → `nova_agent`)

### 📝 文档

- 添加完整的使用指南
- 添加API参考文档
- 添加代码示例
- 更新README

---

## [0.1.1] - 2026-04-10

### 🐛 修复

- 修复代码质量问题 (Ruff 363个错误 → 0个)
- 修复类型检查问题
- 修复API不匹配问题

### ✅ 测试

- 添加35个单元测试
- 配置测试覆盖率达到94%
- 添加CI/CD配置

### 📦 构建

- 添加GitHub Actions工作流
- 添加PyPI自动发布
- 添加代码质量检查

---

## [0.1.0] - 2026-04-09

### 🎉 初始版本

- 五级宫殿记忆系统
- HGARN层次化门控推理
- 自主进化闭环
- 插件化工具系统
- Docker沙箱执行环境

---

[0.3.0]: https://github.com/brad19457416-maker/nova-agent/releases/tag/v0.3.0
[0.1.1]: https://github.com/brad19457416-maker/nova-agent/releases/tag/v0.1.1
[0.1.0]: https://github.com/brad19457416-maker/nova-agent/releases/tag/v0.1.0
