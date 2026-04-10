"""
Agency Collaboration Example

Agency 模式示例：大型项目协作，用户参与循环中
"""

from nova_agent.collaboration.agency_collaboration import AgencyCollaboration

# 创建协作项目
agency = AgencyCollaboration()

# 启动项目
result = agency.start_project(
    project_name="Nova Agent 开发",
    goal="构建一个新一代自主智能体，融合多个前沿项目精华",
    steps=[
        {
            "name": "需求分析",
            "description": "分析现有项目，收集各个架构的优点",
            "assigned_to": "worker"
        },
        {
            "name": "架构设计",
            "description": "设计整体架构，整合各个优点",
            "assigned_to": "worker"
        },
        {
            "name": "编码实现",
            "description": "编写代码实现各个模块",
            "assigned_to": "worker"
        },
        {
            "name": "测试验证",
            "description": "测试验证功能完整性",
            "assigned_to": "user"
        }
    ]
)

print(f"项目启动: {result['project_name']}")
print(f"目标: {result['goal']}")
print(f"下一步: {result['next_step'].step_name} - {result['next_step'].description}")

# 用户可以逐步推进，随时介入
# current_status = agency.get_status()
# agency.complete_current_step("完成了需求分析，结论是...")
