# 儿童绘本自动生成技能

## 描述

全自动从主题创意生成完整可出版的儿童绘本，包含故事创作、分镜、插图、排版全流程。

## 功能特点

- ✅ **全流程自动化**：从一句话主题 → 完整PDF绘本
- ✅ **适龄化适配**：支持 0-3 / 3-6 / 6-12 三个年龄段
- ✅ **多种风格支持**：水彩/卡通/水墨/油画棒/剪纸等预设风格
- ✅ **一致性保证**：角色和风格一致性控制
- ✅ **直接导出PDF**：可直接打印或电子发布

## 使用示例

```python
from nova_agent import NovaAgent
from nova_agent.skills.children_book_generator import ChildrenBookGenerator

# 获取LLM客户端
agent = NovaAgent()
llm = agent.llm_client

# 创建生成器
generator = ChildrenBookGenerator(
    llm_client=llm,
    image_api_key="YOUR_OPENAI_KEY",  # DALL-E 3 API Key
    image_backend="dalle",  # 或 "mock" 测试
)

# 生成完整绘本
pdf_path = generator.full_generate(
    topic="一只爱干净的小恐龙",
    target_age=(3, 6),
    character_name="小龙",
    style="水彩风",
)

print(f"绘本已生成: {pdf_path}")
```

## 架构

八阶段工作流：

1. **StoryConceiver** - 核心创意生成，确定主角、主题、风格方向
2. **StoryPlanner** - 故事结构设计，三幕结构分配到各页
3. **StoryboardWriter** - 分镜脚本创作，逐页写作文字和场景
4. **StyleDefiner** - 插图风格细化，确定色彩方案
5. **PromptEngineer** - 图像提示词工程，生成高质量AI画图提示
6. **ImageGenerator** - 图像生成，支持DALL-E 3等后端
7. **LayoutComposer** - 图文排版整合，处理文字位置
8. **OutputGenerator** - 导出PDF/PNG

## 配置文件

- `configs/age_profiles.json` - 年龄段配置
- `configs/style_templates.json` - 风格模板

## 依赖

- `Pillow` - 图像处理
- `reportlab` - PDF生成
- `requests` - API调用
