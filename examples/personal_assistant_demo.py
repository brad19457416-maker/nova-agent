"""
个人助手演示
展示Nova Agent的通用助手场景
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio

from nova_agent import NovaAgent
from nova_agent.config import NovaConfig, MemoryConfig
from nova_agent.llm.client import SimpleMockLLMClient
from nova_agent.assistant.personal_assistant import PersonalAssistant


async def demo():
    """演示个人助手功能"""
    
    print("="*60)
    print("👤 Nova Agent - 个人助手演示")
    print("="*60)
    print()
    
    # 初始化
    print("🚀 初始化个人助手...")
    
    config = NovaConfig(
        name="Assistant",
        debug=False,
        memory=MemoryConfig(storage_path="/tmp/nova_assistant_demo")
    )
    
    agent = NovaAgent(config)
    agent.llm = SimpleMockLLMClient()
    
    assistant = PersonalAssistant(agent)
    assistant.set_user_name("高畋")
    
    print("✅ 初始化完成!")
    print()
    
    # 测试各种场景
    test_cases = [
        {
            "query": "搜索 Python异步编程",
            "desc": "搜索场景"
        },
        {
            "query": "帮我算一下 15 * 23 + 100",
            "desc": "计算场景"
        },
        {
            "query": "添加日程：明天下午3点开会",
            "desc": "日程添加"
        },
        {
            "query": "查看今天的日程",
            "desc": "日程查询"
        },
        {
            "query": "你好，请介绍一下你自己",
            "desc": "通用对话"
        }
    ]
    
    for i, test in enumerate(test_cases, 1):
        print(f"【测试 {i}】{test['desc']}")
        print(f"👤 用户: {test['query']}")
        
        try:
            response = await assistant.process(test['query'])
            print(f"🤖 助手: {response}")
        except Exception as e:
            print(f"❌ 错误: {e}")
        
        print()
    
    # 显示统计
    print("="*60)
    print("📊 助手统计")
    print("="*60)
    
    stats = assistant.get_stats()
    print(f"用户: {stats['context']['user_name']}")
    print(f"最近意图: {stats['context']['recent_intents']}")
    print(f"工具使用: {stats['tools']}")
    print()
    
    print("="*60)
    print("✅ 个人助手演示完成!")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(demo())
