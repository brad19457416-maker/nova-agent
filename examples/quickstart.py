"""
Nova Agent 快速开始示例
"""

import os
import sys

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from nova_agent import NovaAgent
from nova_agent.config import NovaConfig


def main():
    """快速开始示例"""
    
    # 方式1: 使用默认配置
    # agent = NovaAgent()
    
    # 方式2: 自定义配置
    config = NovaConfig(
        name="Nova",
        llm=NovaConfig.LLMConfig(
            model="qwen2.5:7b",
            base_url="http://localhost:11434",
            temperature=0.7
        ),
        memory=NovaConfig.MemoryConfig(
            storage_path="./data/nova_memory",
            max_entries_per_level=100
        ),
        debug=True
    )
    
    # 创建Agent
    print("="*50)
    print("🚀 初始化 Nova Agent...")
    print("="*50)
    agent = NovaAgent(config)
    
    # 注册自定义工具
    def get_time():
        """获取当前时间"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    agent.register_tool(
        "get_time",
        get_time,
        "获取当前时间"
    )
    
    print("\n" + "="*50)
    print("💬 开始对话...")
    print("="*50)
    
    # 对话1: 简单问答
    print("\n👤 用户: 你好，请介绍一下你自己")
    response = agent.run("你好，请介绍一下你自己")
    print(f"🤖 助手: {response}")
    
    # 对话2: 带上下文
    print("\n👤 用户: 我之前问你什么了？")
    response = agent.run("我之前问你什么了？")
    print(f"🤖 助手: {response}")
    
    # 对话3: 复杂任务
    print("\n👤 用户: 请用3个要点总结一下我们今天的对话")
    response = agent.run("请用3个要点总结一下我们今天的对话")
    print(f"🤖 助手: {response}")
    
    # 显示统计信息
    print("\n" + "="*50)
    print("📊 Agent 统计信息")
    print("="*50)
    stats = agent.get_stats()
    print(f"Agent名称: {stats['name']}")
    print(f"Agent ID: {stats['agent_id']}")
    print(f"交互次数: {stats['interactions']}")
    print(f"记忆统计: {stats['memory']}")
    print(f"时序图谱: {stats['temporal_graph']}")
    print(f"已注册工具: {stats['tools']}")
    
    # 模拟反馈
    print("\n" + "="*50)
    print("💡 反馈进化示例")
    print("="*50)
    
    feedback_result = agent.feedback(
        query="请用3个要点总结一下我们今天的对话",
        response=response,
        rating=4,
        comment="回答得很好，但可以更简洁"
    )
    
    print(f"反馈ID: {feedback_result['feedback_id']}")
    print(f"评分: {feedback_result['rating']}/5")
    print(f"总反馈数: {feedback_result['total_feedback']}")
    if feedback_result.get('evolution_report'):
        print(f"进化报告: {feedback_result['evolution_report']}")
    
    print("\n" + "="*50)
    print("✅ 快速开始示例完成!")
    print("="*50)


if __name__ == "__main__":
    main()
