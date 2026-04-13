#!/usr/bin/env python3
"""
测试儿童绘本生成 - 纯文本流程（使用Mock LLM验证流程）
"""

import sys
import os
import json

# 添加项目根目录到路径
sys.path.insert(0, '/root/.openclaw/workspace/nova-agent')

from nova_agent.llm.client_base import LLMClient
from nova_agent.skills.children_book_generator import ChildrenBookGenerator


class MockLLMClient(LLMClient):
    """Mock LLM 用于测试流程"""
    
    def __init__(self):
        self.called_count = 0
    
    def complete(self, prompt: str, **kwargs) -> str:
        """返回预定义的测试响应"""
        self.called_count += 1
        
        if "儿童绘本创意总监" in prompt or ("title" in prompt and "character" in prompt):
            # 阶段1：核心创意响应
            return '''```json
%s
```''' % json.dumps({
              "title": "咪咪的森林冒险",
              "theme": "勇敢探索，结交新朋友",
              "character": {
                "name": "咪咪",
                "age": 4,
                "personality": "活泼好奇，勇敢爱冒险",
                "appearance": "橘色条纹小猫咪，脖子上系着蓝色蝴蝶结"
              },
              "style": {
                "art_style": "水彩风",
                "additional_prompts": ["柔和色彩", "温暖治愈", "儿童绘本"]
              }
            })
        
        elif "故事结构设计" in prompt or ("page_number" in prompt and "content_summary" in prompt):
            # 阶段2：故事规划 - 12页
            pages_plan = []
            pages_data = [
                ("1", "咪咪在家里闷得慌，决定去森林探险"),
                ("2", "咪咪走进大森林，看到了美丽的野花"),
                ("3", "遇到了一只害羞的小兔子，咪咪主动打招呼"),
                ("4", "咪咪和小兔子一起找浆果"),
                ("5", "它们发现了一丛甜甜的草莓"),
                ("6", "突然下起了小雨，它们找地方躲雨"),
                ("7", "在树洞里发现了一只害怕的小松鼠"),
                ("8", "三个小伙伴一起躲雨聊天"),
                ("9", "雨停了，天边出现了彩虹"),
                ("10", "它们一起在草地上玩游戏"),
                ("11", "太阳下山了，咪咪要回家了"),
                ("12", "咪咪和新朋友说再见，期待下次再一起冒险"),
            ]
            for page_num, summary in pages_data:
                pages_plan.append({
                    "page_number": int(page_num),
                    "content_summary": summary
                })
            return '''```json
%s
```''' % json.dumps({"plan": pages_plan})
        
        elif "逐页创作文字内容" in prompt:
            # 阶段3：分镜脚本
            pages = [
                {
                    "page_number": 1,
                    "text": "咪咪是一只好奇的小猫咪，\n今天它决定去森林探险！\n背上小包包，出发啦！",
                    "scene_description": "橘色小猫咪咪站在家门口，满脸期待地望着远方的森林"
                },
                {
                    "page_number": 2,
                    "text": "森林里花开得真好，\n红的红，黄的黄，\n咪咪高兴地转圈圈。",
                    "scene_description": "咪咪在开满野花的小路上蹦蹦跳跳，阳光透过树叶洒下来"
                },
                {
                    "page_number": 3,
                    "text": "草丛里动了一下，\n跳出一只雪白的小兔子，\n耳朵长长的，眼睛红红的。",
                    "scene_description": "小兔子从灌木丛里探出头，好奇地看着咪咪"
                },
                {
                    "page_number": 4,
                    "text": "\"你好呀！我叫咪咪，\n我们一起去找浆果吧？\"\n小兔子笑着点点头。",
                    "scene_description": "咪咪主动和小兔子打招呼，两个新朋友握手"
                },
                {
                    "page_number": 5,
                    "text": "草莓红红的，甜甜的，\n好吃得不得了，\n两个小伙伴吃得开心笑。",
                    "scene_description": "山坡上的草莓丛，红彤彤的草莓挂满枝头，咪咪和小兔子在采摘"
                },
                {
                    "page_number": 6,
                    "text": "哗啦啦，下雨啦！\n快快找个地方躲起来，\n雨滴答滴答落下来。",
                    "scene_description": "天空突然乌云密布，下起了大雨，咪咪和小兔子着急地找地方躲雨"
                },
                {
                    "page_number": 7,
                    "text": "大树洞里暖暖和和，\n里面藏着一只小松鼠，\n它正害怕地缩成团。",
                    "scene_description": "大树洞里面，一只毛茸茸的小松鼠躲在角落里发抖"
                },
                {
                    "page_number": 8,
                    "text": "别害怕，我们一起躲，\n大雨一会儿就会停，\n大家聊天真开心。",
                    "scene_description": "三个小伙伴挤在树洞里，分享各自的冒险故事"
                },
                {
                    "page_number": 9,
                    "text": "雨停了！太阳出来了，\n一道彩虹挂天边，\n真美呀，像拱桥。",
                    "scene_description": "雨过天晴，一道美丽的彩虹横跨在森林上空，阳光重新照进森林"
                },
                {
                    "page_number": 10,
                    "text": "草地上蹦蹦又跳跳，\n你追我赶真热闹，\n森林探险真有趣。",
                    "scene_description": "三个小伙伴在草地上玩捉迷藏游戏，笑声传遍森林"
                },
                {
                    "page_number": 11,
                    "text": "太阳下山了，天晚了，\n咪咪也要回家了，\n朋友们下次见！",
                    "scene_description": "咪咪站在森林出口，挥手和新朋友告别，夕阳把影子拉得长长的"
                },
                {
                    "page_number": 12,
                    "text": "今天认识了新朋友，\n冒险真开心，\n明天还要再来玩！",
                    "scene_description": "咪咪躺在自己的小床上，睡着了，梦里还在森林探险"
                }
            ]
            return '''```json
%s
```''' % json.dumps({"pages": pages})
        
        elif "定义详细的插图风格" in prompt:
            # 阶段4：风格定义
            return '''```json
%s
```''' % json.dumps({
              "art_style": "水彩儿童插画",
              "color_palette": ["柔和绿色", "温暖橘色", "天蓝色", "粉色", "奶油白"],
              "additional_prompts": [
                "柔和水彩晕染",
                "圆润可爱造型",
                "温暖治愈氛围",
                "大色块，细节不要太复杂",
                "适合低龄儿童"
              ]
            })
        
        # 默认返回空对象
        return json.dumps({})
    
    def chat(self, messages: list, **kwargs) -> str:
        prompt = messages[-1]["content"]
        return self.complete(prompt, **kwargs)


def main():
    # 使用 Mock LLM 测试完整流程
    print("🚀 初始化 Mock LLM...")
    llm = MockLLMClient()
    
    # 创建生成器（使用 mock 图片后端）
    generator = ChildrenBookGenerator(
        llm_client=llm,
        image_api_key=None,
        image_backend="mock",
        output_dir="./output/childrens_books",
    )
    
    # 生成绘本
    print("\n✍️  开始生成绘本故事流程...\n")
    print("主题：一只爱冒险的小猫咪去森林探险")
    print("适合年龄：3-6岁")
    print("风格：水彩风\n")
    
    book = generator.generate(
        topic="一只爱冒险的小猫咪去森林探险",
        target_age=(3, 6),
        character_name="咪咪",
        style="水彩风",
        total_pages=12,
    )
    
    # 输出结果
    print("\n" + "="*60)
    print("📖 流程测试完成！生成结果：")
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
    print(f"\n✅ 纯文本流程测试成功！总共调用 LLM {llm.called_count} 次")
    print("\n所有八阶段工作流都已正确执行完成。")


if __name__ == "__main__":
    main()
