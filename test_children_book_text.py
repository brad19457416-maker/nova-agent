#!/usr/bin/env python3
"""
测试儿童绘本生成 - 纯文本流程（不生成图片）
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, '/root/.openclaw/workspace/nova-agent')

from nova_agent import NovaAgent
from nova_agent.skills.children_book_generator import ChildrenBookGenerator


def main():
    # 创建 Nova Agent，获取 LLM 客户端
    print("🚀 初始化 Nova Agent...")
    agent = NovaAgent()
    llm = agent.llm_client
    
    # 创建生成器（使用 mock 图片后端，不实际生成图片）
    generator = ChildrenBookGenerator(
        llm_client=llm,
        image_api_key=None,
        image_backend="mock",  # mock 模式，不生成图片
        output_dir="./output/childrens_books",
    )
    
    # 生成绘本 - 主题：一只爱冒险的小猫咪去森林探险
    print("\n✍️  开始生成绘本故事...\n")
    print("主题：一只爱冒险的小猫咪去森林探险")
    print("适合年龄：3-6岁")
    print("风格：水彩风\n")
    
    book = generator.generate(
        topic="一只爱冒险的小猫咪去森林探险",
        target_age=(3, 6),
        character_name="咪咪",
        style="水彩风",
        total_pages=12,  # 测试用短一点，12页
    )
    
    # 输出结果
    print("\n" + "="*60)
    print("📖 生成完成！故事概要：")
    print("="*60)
    print(book.to_summary())
    print("\n--- 每页内容 ---\n")
    
    for page in sorted(book.pages, key=lambda p: p.page_number):
        print(f"📄 第 {page.page_number} 页")
        print(f"文字: {page.text}")
        print(f"场景: {page.scene_description}")
        print(f"提示词: {page.image_prompt}")
        print("-" * 40)
    
    # 保存文本结果
    output_dir = "./output/childrens_books"
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, f"{book.title}_text.txt")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(book.to_summary() + "\n\n")
        for page in sorted(book.pages, key=lambda p: p.page_number):
            f.write(f"第 {page.page_number} 页\n")
            f.write(f"文字: {page.text}\n")
            f.write(f"场景: {page.scene_description}\n")
            f.write(f"提示词: {page.image_prompt}\n\n")
    
    print(f"\n💾 文本结果已保存到: {output_file}")
    print("\n✅ 纯文本测试完成！")


if __name__ == "__main__":
    main()
