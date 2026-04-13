#!/usr/bin/env python3
import json
data = {
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
resp = '''```json
%s
```''' % json.dumps(data)
print("Response:")
print(repr(resp))
print("\nAfter extraction:")
if "```json" in resp:
    resp = resp.split("```json")[1].split("```")[0]
elif "```" in resp:
    resp = resp.split("```")[1]
print(repr(resp.strip()))
data = json.loads(resp.strip())
print("\nParsed:")
print(f"title = {data['title']}")
print(f"character.name = {data['character']['name']}")
