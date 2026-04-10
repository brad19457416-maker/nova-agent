"""
Nova Agent v0.3.0 CLI入口

使用示例:
    # 运行工作流
    python -m nova_agent.v0_3.main workflow research "调研Python异步编程"
    
    # 使用技能
    python -m nova_agent.v0_3.main skill research_skill "分析代码性能"
    
    # 协作模式
    python -m nova_agent.v0_3.main collab "实现用户系统"
    
    # 查看统计
    python -m nova_agent.v0_3.main stats
"""

import asyncio
import argparse
import json
import sys
from pathlib import Path
from typing import Dict, Any

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from nova_agent.v0_3.config import ConfigManager
from nova_agent.v0_3.storage import SQLiteStore
from nova_agent.v0_3.skills import SkillLoader, AntipatternChecker
from nova_agent.v0_3.workflow import WorkflowEngine
from nova_agent.v0_3.collaboration import LeadSubCollaboration


class NovaAgentCLI:
    """Nova Agent CLI"""
    
    def __init__(self, config_dir: str = "./config", db_path: str = "./data/nova.db"):
        self.config = ConfigManager(config_dir)
        self.storage = SQLiteStore(db_path)
        self.skills = SkillLoader(self.config)
        self.checker = AntipatternChecker(self.config, self.storage)
        self.engine = WorkflowEngine(
            self.config, 
            self.skills, 
            llm_client=None,
            storage=self.storage,
            antipattern_checker=self.checker
        )
    
    async def run_workflow(self, workflow_name: str, task: str) -> Dict:
        """运行工作流"""
        print(f"🚀 运行工作流: {workflow_name}")
        print(f"📋 任务: {task}\n")
        
        result = await self.engine.run(workflow_name, {"task": task})
        
        print(f"\n✅ 工作流完成: {result.status.value}")
        print(f"⏱️  执行时间: {result.total_duration_ms:.0f}ms")
        print(f"📊 阶段数: {len(result.phases)}")
        
        if result.metadata.get("antipattern_warnings"):
            warnings = result.metadata["antipattern_warnings"]
            print(f"⚠️  反模式警告: {len(warnings)}")
            for w in warnings[:3]:
                print(f"   - [{w['severity']}] {w['name']}")
        
        print(f"\n📄 输出:")
        print(json.dumps(result.final_output, indent=2, ensure_ascii=False)[:500])
        
        return {
            "status": result.status.value,
            "duration_ms": result.total_duration_ms,
            "output": result.final_output
        }
    
    async def run_skill(self, skill_name: str, task: str) -> Dict:
        """运行技能"""
        print(f"🔧 运行技能: {skill_name}")
        print(f"📋 任务: {task}\n")
        
        skill = self.skills.load(skill_name)
        result = await skill.execute({"task": task})
        
        print(f"\n✅ 技能执行完成")
        print(f"📄 输出:")
        print(json.dumps(result, indent=2, ensure_ascii=False)[:500])
        
        return result
    
    async def run_collab(self, task: str, max_subs: int = 4) -> Dict:
        """运行协作"""
        print(f"🤝 运行协作模式: Lead/Sub")
        print(f"📋 任务: {task}\n")
        
        collab = LeadSubCollaboration(llm_client=None, max_subs=max_subs)
        result = await collab.execute(task, {"max_subs": max_subs})
        
        print(f"\n✅ 协作完成")
        print(f"⏱️  执行时间: {result.duration_ms:.2f}ms")
        print(f"📊 子任务数: {result.subtasks_count}")
        
        print(f"\n📄 最终输出:")
        print(str(result.final_result)[:500])
        
        return {
            "task": result.task,
            "duration_ms": result.duration_ms,
            "output": result.final_result
        }
    
    def show_stats(self) -> Dict:
        """显示统计"""
        stats = self.storage.get_stats()
        
        print("📊 Nova Agent 统计\n")
        print(f"执行统计:")
        print(f"  - 总执行: {stats['total_executions']}")
        print(f"  - 完成: {stats['completed_executions']}")
        print(f"  - 失败: {stats['failed_executions']}")
        print(f"  - 平均耗时: {stats['avg_duration_ms']:.0f}ms")
        
        print(f"\n资源统计:")
        print(f"  - 工作流: {stats['workflows_count']}")
        print(f"  - 技能: {stats['skills_count']}")
        print(f"  - 反模式: {stats['antipatterns_count']}")
        
        if stats['total_feedback'] > 0:
            print(f"\n反馈统计:")
            print(f"  - 反馈数: {stats['total_feedback']}")
            print(f"  - 平均评分: {stats['avg_rating']}")
        
        return stats
    
    def list_workflows(self) -> None:
        """列出工作流"""
        print("📋 可用工作流:\n")
        
        workflow_config = self.config.get_section("workflow")
        workflows = workflow_config.get("workflows", {})
        
        for name, config in workflows.items():
            print(f"  - {name}: {config.get('description', '')}")
            print(f"    阶段: {', '.join(config.get('phases', []))}")
    
    def list_skills(self) -> None:
        """列出技能"""
        print("🔧 可用技能:\n")
        
        skills = self.skills.list_skills()
        for name in skills:
            config = self.skills.get_config(name)
            print(f"  - {name}: {config.description if config else ''}")


def main():
    """主入口"""
    parser = argparse.ArgumentParser(
        description="Nova Agent v0.3.0 - 通用自主智能体框架",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 运行调研工作流
  python -m nova_agent.v0_3.main workflow research "调研Python异步编程"
  
  # 运行写作工作流
  python -m nova_agent.v0_3.main workflow writing "写一章科幻小说"
  
  # 使用技能
  python -m nova_agent.v0_3.main skill research_skill "分析代码"
  
  # 协作模式
  python -m nova_agent.v0_3.main collab "实现用户系统"
  
  # 查看统计
  python -m nova_agent.v0_3.main stats
  
  # 列出资源
  python -m nova_agent.v0_3.main list --workflows
  python -m nova_agent.v0_3.main list --skills
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="可用命令")
    
    # workflow命令
    workflow_parser = subparsers.add_parser("workflow", help="运行工作流")
    workflow_parser.add_argument("name", help="工作流名称")
    workflow_parser.add_argument("task", help="任务描述")
    
    # skill命令
    skill_parser = subparsers.add_parser("skill", help="运行技能")
    skill_parser.add_argument("name", help="技能名称")
    skill_parser.add_argument("task", help="任务描述")
    
    # collab命令
    collab_parser = subparsers.add_parser("collab", help="协作模式")
    collab_parser.add_argument("task", help="任务描述")
    collab_parser.add_argument("--subs", type=int, default=4, help="Sub Agent数量")
    
    # stats命令
    subparsers.add_parser("stats", help="查看统计")
    
    # list命令
    list_parser = subparsers.add_parser("list", help="列出资源")
    list_parser.add_argument("--workflows", action="store_true", help="列出工作流")
    list_parser.add_argument("--skills", action="store_true", help="列出技能")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    cli = NovaAgentCLI()
    
    try:
        if args.command == "workflow":
            asyncio.run(cli.run_workflow(args.name, args.task))
        
        elif args.command == "skill":
            asyncio.run(cli.run_skill(args.name, args.task))
        
        elif args.command == "collab":
            asyncio.run(cli.run_collab(args.task, args.subs))
        
        elif args.command == "stats":
            cli.show_stats()
        
        elif args.command == "list":
            if args.workflows:
                cli.list_workflows()
            elif args.skills:
                cli.list_skills()
            else:
                cli.list_workflows()
                print()
                cli.list_skills()
    
    except KeyboardInterrupt:
        print("\n\n⚠️ 用户中断")
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
