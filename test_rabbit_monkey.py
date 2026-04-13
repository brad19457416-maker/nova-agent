#!/usr/bin/env python3
"""
测试优化后的童心绘：兔子和猴子的礼貌故事
"""

import sys
sys.path.insert(0, '/root/.openclaw/workspace/nova-agent')

from nova_agent import NovaAgent
from nova_agent.skills.children_book_generator import ChildrenBookGenerator

def main():
    print("=" * 60)
    print("童心绘（优化版）测试：兔子淘淘和猴子跳跳")
    print("主题：朋友相处，讲礼貌，行为规范")
    print("适合：3-6岁儿童")
    print("风格：水彩风")
    print("优化功能：市场学习 ✓ 质量评估 ✓ 即梦适配 ✓")
    print("=" * 60)
    print()
    
    # 初始化agent
    agent = NovaAgent()
    
    # 初始化生成器，启用全部优化
    generator = ChildrenBookGenerator(
        llm_client=agent.llm_client,
        image_backend="mock",
        prompt_platform="jimeng",  # 适配即梦
        enable_market_learning=True,  # 市场灵感学习
        enable_quality_check=True,    # 质量评估闭环
        max_regeneration_attempts=2,
        quality_threshold=70.0,
    )
    
    # 生成绘本
    pdf_path = generator.full_generate(
        topic="一只兔子和一只猴子是好朋友，一起玩耍，学习讲礼貌和行为规范",
        target_age=(3, 6),
        character_name=None,  # 让AI创作名字
        style="水彩风",
    )
    
    print()
    print("=" * 60)
    print(f"\n✅ 生成完成！")
    print(f"输出位置：{pdf_path}")
    print()

if __name__ == "__main__":
    main()
