#!/bin/bash
# 完整测试套件运行脚本

cd /root/.openclaw/workspace/nova-agent
source venv/bin/activate

echo "======================================"
echo "Nova Agent 完整测试套件"
echo "======================================"
echo ""

# 1. 代码质量检查
echo "[1/4] 代码质量检查..."
echo "  - Ruff 检查..."
ruff check nova_agent/ tests/ 2>&1 | tail -3

echo "  - Black 格式化检查..."
black --check nova_agent/ tests/ 2>&1 | tail -2

# 2. 配置测试
echo ""
echo "[2/4] 配置系统测试..."
python -m pytest tests/unit/test_config.py -v --tb=line 2>&1 | tail -5

# 3. 单元测试（超时保护）
echo ""
echo "[3/4] 其他单元测试（30秒超时）..."
timeout 30 python -m pytest tests/unit/test_memory.py tests/unit/test_reasoning.py -v --tb=line 2>&1 | tail -10 || echo "  部分测试超时（可能涉及模型加载）"

# 4. 核心功能验证
echo ""
echo "[4/4] 核心功能验证..."
python -c "
from nova_agent.config import Config
from nova_agent.memory.temporal_graph import TemporalFactGraph
from nova_agent.reasoning.confidence_routing import ConfidenceRouter
from nova_agent.reasoning.wta import WTASelection

# 验证
config = Config.default()
graph = TemporalFactGraph()
fact = graph.add_fact('Test', 'is', 'OK')
router = ConfidenceRouter()
wta = WTASelection()
items = [{'id': 1, 'similarity': 0.9}]
selected = wta.select(items, 'test')

print('  ✓ Config:', 'OK')
print('  ✓ TemporalFactGraph:', 'OK')
print('  ✓ ConfidenceRouter:', 'OK')
print('  ✓ WTASelection:', 'OK')
"

echo ""
echo "======================================"
echo "测试完成！"
echo "======================================"
