# Nova Agent CI/CD 配置详细指南

本文档详细说明如何配置 GitHub Actions 所需的 Secrets。

---

## 目录
1. [PyPI Token 配置](#pypi-token-配置)
2. [Codecov Token 配置](#codecov-token-配置)
3. [验证配置](#验证配置)
4. [发布新版本](#发布新版本)

---

## PyPI Token 配置

### 步骤 1：注册/登录 PyPI

访问 https://pypi.org/

如果已有账号直接登录，没有则注册。

### 步骤 2：进入 Account Settings

点击右上角用户名 → **Account settings**

### 步骤 3：创建 API Token

1. 左侧菜单选择 **API tokens**
2. 点击 **Add API token** 按钮

### 步骤 4：填写 Token 信息

| 字段 | 填写内容 |
|------|----------|
| **Token name** | `github-actions` 或 `nova-agent-ci` |
| **Scope** | 选择 **Entire account** (如果这是你的第一个项目) 或 **Project: nova-agent** |

### 步骤 5：复制 Token

⚠️ **重要**: Token 只显示一次，务必复制保存！

格式类似：`pypi-AgEIcHlwaS5vcmcCJ...`

---

## GitHub Secrets 配置

### 步骤 1：进入仓库 Settings

访问：`https://github.com/brad19457416-maker/nova-agent/settings`

### 步骤 2：进入 Secrets 页面

左侧菜单 → **Secrets and variables** → **Actions**

或直接访问：`https://github.com/brad19457416-maker/nova-agent/settings/secrets/actions`

### 步骤 3：添加 PYPI_API_TOKEN

1. 点击绿色按钮 **New repository secret**
2. 填写信息：
   - **Name**: `PYPI_API_TOKEN`
   - **Secret**: 粘贴刚才复制的 PyPI Token
3. 点击 **Add secret**

### 步骤 4：（可选）添加 CODECOV_TOKEN

如果你想上传测试覆盖率到 Codecov：

1. 访问 https://about.codecov.io/
2. 用 GitHub 账号登录
3. 添加你的仓库
4. 复制 Token
5. 在 GitHub Secrets 中添加：
   - **Name**: `CODECOV_TOKEN`
   - **Secret**: 粘贴 Codecov Token

---

## 验证配置

### 方法 1：查看 Secrets 列表

在 `https://github.com/brad19457416-maker/nova-agent/settings/secrets/actions` 应该能看到：

| Name | Updated |
|------|---------|
| PYPI_API_TOKEN | Just now |

### 方法 2：测试 CI 工作流

推送任意提交到 main 分支，查看 Actions 是否正常运行：

```bash
git add .
git commit -m "Test CI workflow"
git push origin main
```

然后访问：`https://github.com/brad19457416-maker/nova-agent/actions`

应该能看到 CI 工作流正在运行。

---

## 发布新版本

### 首次发布前检查清单

- [ ] PyPI Token 已配置
- [ ] 版本号已更新 (`setup.py` 和 `nova_agent/__init__.py`)
- [ ] 所有测试通过
- [ ] 代码已推送到 main

### 发布步骤

#### 1. 更新版本号

编辑 `setup.py`:
```python
version="0.1.0",  # 改为新版本，如 "0.1.1"
```

编辑 `nova_agent/__init__.py`:
```python
__version__ = "0.1.1"
```

#### 2. 提交更改

```bash
git add setup.py nova_agent/__init__.py
git commit -m "Bump version to 0.1.1"
git push origin main
```

#### 3. 创建并推送 Tag

```bash
# 创建 tag
git tag v0.1.1

# 推送 tag 到远程 (这会触发 release 工作流)
git push origin v0.1.1
```

#### 4. 查看发布进度

访问：`https://github.com/brad19457416-maker/nova-agent/actions`

应该能看到 `Release` 工作流正在运行。

#### 5. 验证发布

- **GitHub Release**: 访问 `https://github.com/brad19457416-maker/nova-agent/releases`
- **PyPI**: 访问 `https://pypi.org/project/nova-agent/`

---

## 常见问题

### Q: PyPI Token 泄露了怎么办？

1. 立即到 PyPI 删除该 Token
2. 在 GitHub 删除旧的 Secret
3. 创建新的 Token 并重新配置

### Q: 发布失败了怎么办？

查看 Actions 日志：`https://github.com/brad19457416-maker/nova-agent/actions`

常见原因：
- Token 配置错误 → 检查 Secret 名称是否为 `PYPI_API_TOKEN`
- 版本号已存在 → PyPI 不允许重复版本，需要更新版本号
- 测试失败 → 修复测试后重新推送

### Q: 如何测试发布流程而不真正发布？

方法 1: 使用 TestPyPI
- 修改 `.github/workflows/release.yml`
- 将 `twine upload dist/*` 改为 `twine upload --repository testpypi dist/*`
- 需要额外配置 TestPyPI 的 Token

方法 2: 手动触发
- 创建 release 分支测试
- 完成后删除测试 tag 和 release

---

## 下一步

配置完成后：
1. ✅ CI 会在每次 PR 时自动运行测试
2. ✅ 代码推送到 main 会自动检查
3. ✅ 推送 tag 会自动发布到 PyPI

现在你可以：
- 继续完善代码
- 添加更多测试
- 完善文档
- 发布第一个正式版本！

