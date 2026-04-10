#!/bin/bash
# Nova Agent v0.1.1 发布推送脚本
# 使用方法: 设置 GH_TOKEN 环境变量后运行

echo "Nova Agent v0.1.1 发布推送"
echo "============================"

# 检查 token
if [ -z "$GH_TOKEN" ]; then
    echo "错误: 请设置 GH_TOKEN 环境变量"
    echo "获取方法:"
    echo "1. 访问 https://github.com/settings/tokens"
    echo "2. 创建 Personal Access Token (需要 repo 权限)"
    echo "3. export GH_TOKEN=your_token_here"
    exit 1
fi

cd /root/.openclaw/workspace/nova-agent

# 设置远程 URL 使用 token
git remote set-url origin "https://$GH_TOKEN@github.com/brad19457416-maker/nova-agent.git"

# 推送主分支
echo "推送 main 分支..."
git push origin master

# 创建并推送 tag
echo "创建 tag v0.1.1..."
git tag v0.1.1

echo "推送 tag..."
git push origin v0.1.1

# 恢复远程 URL (移除 token)
git remote set-url origin "https://github.com/brad19457416-maker/nova-agent.git"

echo ""
echo "✅ 推送完成!"
echo ""
echo "查看 CI 状态:"
echo "https://github.com/brad19457416-maker/nova-agent/actions"
echo ""
echo "查看 Release:"
echo "https://github.com/brad19457416-maker/nova-agent/releases"
