#!/usr/bin/env python3
"""
Nova Agent 部署验证测试
"""

import sys
sys.path.insert(0, '/root/.openclaw/workspace/nova-agent')

from nova_agent import NovaAgent
from nova_agent.config import Config

print("=" * 70)
print("Nova Agent 部署验证测试")
print("=" * 70)

# 测试 1: 默认配置初始化
print("\n[测试 1] 默认配置初始化...")
try:
    config = Config.default()
    print(f"  ✓ 配置创建成功")
    print(f"    - 记忆目录: {config.memory_data_dir}")
    print(f"    - 向量后端: {config.vector_backend}")
    print(f"    - 最大推理层级: {config.max_levels}")
    print(f"    - 块大小: {config.block_size}")
except Exception as e:
    print(f"  ✗ 失败: {e}")

# 测试 2: Agent 初始化
print("\n[测试 2] Agent 初始化...")
try:
    agent = NovaAgent()
    print(f"  ✓ Agent 创建成功")
    print(f"    - 记忆宫殿: {type(agent.memory_palace).__name__}")
    print(f"    - 时序图谱: {type(agent.temporal_graph).__name__}")
    print(f"    - 推理引擎: {type(agent.reasoning_engine).__name__}")
    print(f"    - LLM客户端: {type(agent.llm_client).__name__}")
except Exception as e:
    print(f"  ✗ 失败: {e}")
    import traceback
    traceback.print_exc()

# 测试 3: 配置模式
print("\n[测试 3] 配置模式...")
try:
    conservative_config = Config.conservative()
    efficient_config = Config.efficient()
    print(f"  ✓ 保守配置: max_levels={conservative_config.max_levels}")
    print(f"  ✓ 高效配置: max_levels={efficient_config.max_levels}")
except Exception as e:
    print(f"  ✗ 失败: {e}")

# 测试 4: 进化配置调整
print("\n[测试 4] 配置进化调整...")
try:
    config = Config.default()
    changes = config.apply_evolution(quality_score=0.2)
    print(f"  ✓ 低质量反馈调整成功")
    print(f"    变更: {changes}")
    
    config2 = Config.default()
    changes2 = config2.apply_evolution(quality_score=0.95)
    print(f"  ✓ 高质量反馈调整成功")
    print(f"    变更: {changes2}")
except Exception as e:
    print(f"  ✗ 失败: {e}")
    import traceback
    traceback.print_exc()

# 测试 5: 保存和加载配置
print("\n[测试 5] 配置持久化...")
try:
    import tempfile
    import os
    
    config = Config.default()
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        temp_path = f.name
    
    config.save(temp_path)
    loaded_config = Config.load(temp_path)
    
    assert config.max_levels == loaded_config.max_levels
    print(f"  ✓ 配置保存/加载成功")
    
    os.unlink(temp_path)
except Exception as e:
    print(f"  ✗ 失败: {e}")

print("\n" + "=" * 70)
print("验证完成")
print("=" * 70)
