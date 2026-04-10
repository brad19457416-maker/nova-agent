#!/bin/bash
# Mypy 类型检查脚本

echo "Nova Agent 类型检查"
echo "===================="

cd /root/.openclaw/workspace/nova-agent
source venv/bin/activate

# 检查核心模块
echo ""
echo "检查核心模块..."

# 配置模块
echo "- config.py"
mypy nova_agent/config.py --python-version 3.12 --ignore-missing-imports --follow-imports=skip 2>&1 | grep -E "(error|warning|Success)" || echo "  ✓ 通过"

# 内存模块
echo "- memory/temporal_graph.py"
mypy nova_agent/memory/temporal_graph.py --python-version 3.12 --ignore-missing-imports --follow-imports=skip 2>&1 | grep -E "(error|warning|Success)" || echo "  ✓ 通过"

echo ""
echo "类型检查完成！"
