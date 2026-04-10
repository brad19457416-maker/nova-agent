"""
深度研究演示
展示Nova Agent如何解决调研策略死板、不会关联展开的问题
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from nova_agent import NovaAgent
from nova_agent.config import NovaConfig, MemoryConfig, LLMConfig
from nova_agent.llm.client import SimpleMockLLMClient


# 模拟搜索工具 - 演示用
async def mock_search_tool(query: str) -> list:
    """
    模拟搜索结果
    实际使用时替换为真实的搜索API (DuckDuckGo, Google, etc.)
    """
    # 根据查询返回模拟结果
    results = []
    
    if "AI" in query or "人工智能" in query:
        results = [
            {
                "content": "人工智能(AI)是计算机科学的一个分支，致力于创建能够执行通常需要人类智能的任务的系统。",
                "source": "百科",
                "confidence": 0.9,
                "entities": ["人工智能", "AI", "计算机科学"]
            },
            {
                "content": "2024年AI发展迅猛，大语言模型成为主流应用。",
                "source": "科技新闻",
                "confidence": 0.85,
                "entities": ["AI", "大语言模型", "2024"]
            }
        ]
    elif "大语言模型" in query or "LLM" in query:
        results = [
            {
                "content": "大语言模型(LLM)是基于Transformer架构的深度学习模型，能够理解和生成人类语言。",
                "source": "技术文档",
                "confidence": 0.92,
                "entities": ["大语言模型", "LLM", "Transformer"]
            },
            {
                "content": "GPT、Claude、Gemini是当前主流的大语言模型。",
                "source": "行业分析",
                "confidence": 0.88,
                "entities": ["GPT", "Claude", "Gemini", "LLM"]
            }
        ]
    elif "Transformer" in query:
        results = [
            {
                "content": "Transformer是2017年Google提出的神经网络架构，使用自注意力机制处理序列数据。",
                "source": "论文",
                "confidence": 0.95,
                "entities": ["Transformer", "注意力机制", "Google"]
            }
        ]
    else:
        results = [
            {
                "content": f"关于'{query}'的搜索结果...",
                "source": "搜索引擎",
                "confidence": 0.6,
                "entities": [query]
            }
        ]
    
    return results


async def demo_deep_research():
    """演示深度研究"""
    print("="*60)
    print("🔍 Nova Agent 深度研究演示")
    print("="*60)
    print()
    print("演示场景: 研究'人工智能'主题")
    print("对比: 传统搜索 vs 深度研究")
    print()
    
    # 初始化Agent
    config = NovaConfig(
        name="Researcher",
        debug=False,
        llm=LLMConfig(),
        memory=MemoryConfig(storage_path="/tmp/nova_research_demo")
    )
    
    agent = NovaAgent(config)
    # 使用mock LLM避免实际调用
    agent.llm = SimpleMockLLMClient()
    
    # 导入深度研究模块
    from nova_agent.research.deep_researcher import DeepResearcher, ResearchConfig
    
    # 创建深度研究员
    researcher = DeepResearcher(
        llm_client=agent.llm,
        search_tool=mock_search_tool,
        config=ResearchConfig(
            max_depth=3,
            max_queries_per_depth=3,
            cross_validation=True
        )
    )
    
    print("【传统搜索的问题】")
    print("- 只搜索一次: '人工智能'")
    print("- 得到结果就停止")
    print("- 不会深入挖掘相关概念")
    print("- 不会验证信息准确性")
    print()
    
    print("【深度研究的过程】")
    print("开始深度研究...")
    print()
    
    # 执行深度研究
    result = await researcher.research("人工智能")
    
    # 显示研究树
    tree = researcher.get_research_tree()
    
    print(f"✅ 研究完成!")
    print(f"   - 总查询数: {tree['total_queries']}")
    print(f"   - 完成查询: {tree['completed_queries']}")
    print(f"   - 发现数量: {tree['total_findings']}")
    print(f"   - 知识实体: {tree['knowledge_graph_size']}")
    print(f"   - 迭代轮数: {result.iterations}")
    print(f"   - 研究耗时: {result.duration:.2f}秒")
    print(f"   - 整体置信度: {result.confidence:.2f}")
    print()
    
    print("【查询树结构】")
    def print_tree(node, indent=0):
        prefix = "  " * indent
        status = "✅" if node['status'] == 'completed' else "⏳"
        print(f"{prefix}{status} {node['query']}")
        print(f"{prefix}   深度:{node['depth']} 发现:{node['findings_count']}")
        for child in node.get('children', []):
            print_tree(child, indent + 1)
    
    for root in tree['query_tree']:
        print_tree(root)
    
    print()
    print("【研究发现示例】")
    for finding in list(result.findings.values())[:3]:
        print(f"- {finding.content[:60]}...")
        print(f"  来源: {finding.source} | 置信度: {finding.confidence:.2f}")
        if finding.entities:
            print(f"  实体: {', '.join(finding.entities[:3])}")
        print()
    
    print("【知识图谱】")
    print(f"实体: {list(result.knowledge_graph.keys())[:5]}")
    print()
    
    print("="*60)
    print("🎯 深度研究的优势")
    print("="*60)
    print("1. ✅ 自动规划 - 分析主题，生成多角度查询")
    print("2. ✅ 关联展开 - 从结果中提取新概念，继续深挖")
    print("3. ✅ 多轮迭代 - 不满足于表面结果，持续探索")
    print("4. ✅ 交叉验证 - 多来源验证信息准确性")
    print("5. ✅ 知识图谱 - 结构化存储实体关系")
    print()
    
    print("对比传统Agent:")
    print("  传统: 1次搜索 → 3个结果 → 结束")
    print("  Nova: 规划 → 搜索 → 展开 → 深挖 → 验证 → 综合")
    print()


def demo_search_strategies():
    """演示不同搜索策略"""
    print("="*60)
    print("🔍 搜索策略对比")
    print("="*60)
    print()
    
    strategies = {
        "广度优先": "适合快速了解全貌",
        "深度优先": "适合深入研究特定方向",
        "自适应": "智能选择广度或深度",
        "迭代式": "多轮优化查询"
    }
    
    for name, desc in strategies.items():
        print(f"【{name}】")
        print(f"  特点: {desc}")
        print()
    
    print("Nova Agent 默认使用: 自适应 + 迭代式")
    print("根据任务自动选择最佳策略")
    print()


def demo_query_expansion():
    """演示查询扩展"""
    print("="*60)
    print("🔍 查询扩展示例")
    print("="*60)
    print()
    
    query = "人工智能"
    
    print(f"原始查询: {query}")
    print()
    print("扩展方式:")
    print("  语义扩展: AI、智能系统、机器学习")
    print("  时间扩展: AI历史、AI最新进展、AI未来趋势")
    print("  对比扩展: AI vs 传统编程、AI与人类智能")
    print("  因果扩展: AI发展原因、AI对社会的影响")
    print()
    
    print("Nova Agent 会自动生成这些扩展查询")
    print("确保调研全面、不遗漏重要信息")
    print()


async def main():
    """主函数"""
    await demo_deep_research()
    demo_search_strategies()
    demo_query_expansion()
    
    print("="*60)
    print("✅ 深度研究演示完成!")
    print("="*60)
    print()
    print("Nova Agent 解决了:")
    print("  ❌ 传统Agent只搜一次的问题 → ✅ 多轮迭代")
    print("  ❌ 不会关联展开的问题 → ✅ 自动扩展查询")
    print("  ❌ 只满足表面结果的问题 → ✅ 深度挖掘")
    print("  ❌ 策略死板的问题 → ✅ 自适应策略")
    print()


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
