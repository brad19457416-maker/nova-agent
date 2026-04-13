#!/usr/bin/env python3
"""直接测试流程，一步一步来"""

import sys
import os
import json

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath('.'))

# 先测试导入
print("Testing imports...")
from nova_agent.llm.client_base import LLMClient
print("✓ LLMClient imported")

from nova_agent.skills.children_book_generator.core.story_conceiver import StoryConceiver
print("✓ StoryConceiver imported")

# 测试创建
class MockLLM(LLMClient):
    def complete(self, prompt, **kwargs):
        print(f"\n--- LLM called ---\nPrompt contains: {prompt[:100]}...\n")
        return '''```json
        {
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
        }
        ```'''
    
    def chat(self, messages, **kwargs):
        return self.complete(messages[-1]["content"])

print("\nCreating StoryConceiver...")
conceiver = StoryConceiver(MockLLM())
print("✓ Created")

print("\nRunning conceive...")
title, character, style, theme = conceiver.conceive(
    "一只爱冒险的小猫咪去森林探险",
    (3, 6),
    "咪咪",
    "水彩风"
)

print(f"\n✅ Result:")
print(f"  title: {title}")
print(f"  character: {character.name}, {character.age}岁, {character.personality}")
print(f"  style: {style.art_style}")
print(f"  theme: {theme}")

print("\n🎉 Stage 1 test PASSED!")
