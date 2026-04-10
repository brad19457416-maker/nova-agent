# Nova Agent v0.1.1 推送指南

## 快速推送

### 方法 1: 使用脚本 (推荐)

```bash
# 1. 设置 GitHub Token
export GH_TOKEN=ghp_xxxxxxxxxxxx

# 2. 运行推送脚本
bash push_release.sh
```

### 方法 2: 手动推送

```bash
cd /root/.openclaw/workspace/nova-agent

# 1. 使用 token 设置远程 URL
git remote set-url origin "https://YOUR_TOKEN@github.com/brad19457416-maker/nova-agent.git"

# 2. 推送主分支
git push origin master

# 3. 创建 tag
git tag v0.1.1

# 4. 推送 tag (这会触发 release 工作流)
git push origin v0.1.1

# 5. 恢复远程 URL (安全考虑)
git remote set-url origin "https://github.com/brad19457416-maker/nova-agent.git"
```

---

## 获取 GitHub Token

1. 访问 https://github.com/settings/tokens
2. 点击 **Generate new token (classic)**
3. 填写 Note: `nova-agent-release`
4. 选择过期时间 (建议 30 天)
5. 勾选权限:
   - [x] **repo** (完整仓库访问)
6. 点击 **Generate token**
7. **立即复制 token** (只显示一次!)

---

## 验证推送

推送后访问:

- **CI 状态**: https://github.com/brad19457416-maker/nova-agent/actions
- **Releases**: https://github.com/brad19457416-maker/nova-agent/releases
- **PyPI**: https://pypi.org/project/nova-agent/ (发布后)

---

## 本地手动执行命令

如果以上方法都不行，你可以在本地执行:

```bash
# 克隆仓库
git clone https://github.com/brad19457416-maker/nova-agent.git
cd nova-agent

# 版本已更新到 0.1.1，直接推送
git push origin master
git tag v0.1.1
git push origin v0.1.1
```

