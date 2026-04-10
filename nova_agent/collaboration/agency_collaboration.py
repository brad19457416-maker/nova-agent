"""
Agency Collaboration - Agency 风格用户参与协作

OpenAI Agency 启发：Human-in-the-loop，用户始终在循环中，
Project Manager + Workers 分工，用户提供目标和决策。
"""

import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class ProjectStep:
    """项目步骤"""

    step_name: str
    description: str
    status: str = "pending"  # pending → in_progress → done → blocked
    assigned_to: str = ""
    output: Optional[str] = None
    notes: List[str] = None

    def __post_init__(self):
        if self.notes is None:
            self.notes = []


class AgencyCollaboration:
    """
    Agency 风格用户参与协作

    架构：
    - 用户：提供目标，做关键决策
    - Project Manager Agent：分解任务，协调进度
    - Worker Agents：执行具体子任务
    - Shared Whiteboard：共享进度、决策、问题记录
    """

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.project_name: str = ""
        self.goal: str = ""
        self.steps: List[ProjectStep] = []
        self.whiteboard: Dict[str, Any] = {
            "decisions": [],
            "problems": [],
            "progress_notes": [],
        }
        self.current_step_index: int = 0

    def start_project(self, project_name: str, goal: str, steps: List[Dict]) -> Dict:
        """开始新项目"""
        self.project_name = project_name
        self.goal = goal

        # 创建步骤
        self.steps = []
        for i, step_dict in enumerate(steps):
            step = ProjectStep(
                step_name=step_dict.get("name", f"Step {i+1}"),
                description=step_dict.get("description", ""),
                assigned_to=step_dict.get("assigned_to", "worker"),
            )
            self.steps.append(step)

        self.current_step_index = 0
        logger.info(f"Started Agency project: {project_name}, {len(self.steps)} steps")

        return {
            "success": True,
            "project_name": project_name,
            "goal": goal,
            "next_step": self._get_current_step(),
            "total_steps": len(self.steps),
        }

    def _get_current_step(self) -> Optional[ProjectStep]:
        """获取当前步骤"""
        if self.current_step_index >= len(self.steps):
            return None
        return self.steps[self.current_step_index]

    def add_decision(self, decision: str, made_by: str = "user") -> None:
        """记录决策到白板"""
        self.whiteboard["decisions"].append(
            {
                "decision": decision,
                "made_by": made_by,
                "step": self.current_step_index,
                "timestamp": self._get_timestamp(),
            }
        )

    def add_problem(self, problem: str, reported_by: str) -> None:
        """记录问题到白板"""
        self.whiteboard["problems"].append(
            {
                "problem": problem,
                "reported_by": reported_by,
                "step": self.current_step_index,
                "timestamp": self._get_timestamp(),
            }
        )

    def complete_current_step(self, output: str) -> Dict:
        """完成当前步骤，下一步"""
        current = self._get_current_step()
        if current is None:
            return {"success": False, "error": "No current step", "project_complete": True}

        current.status = "done"
        current.output = output
        self.current_step_index += 1

        next_step = self._get_current_step()

        if next_step is None:
            # 项目完成
            return {"success": True, "project_complete": True, "summary": self.generate_summary()}

        return {
            "success": True,
            "project_complete": False,
            "next_step": next_step,
            "completed_steps": self.current_step_index,
        }

    def block_current_step(self, problem: str) -> Dict:
        """阻塞当前步骤，需要用户帮助"""
        current = self._get_current_step()
        if current:
            current.status = "blocked"
            self.add_problem(problem, "worker")

        return {"success": False, "blocked": True, "problem": problem, "current_step": current}

    def generate_summary(self) -> str:
        """生成项目总结"""
        summary = f"# {self.project_name} - 完成总结\n\n"
        summary += f"**目标:** {self.goal}\n\n"
        summary += "## 完成步骤\n\n"

        for i, step in enumerate(self.steps):
            status_icon = (
                "✅" if step.status == "done" else "⏸️" if step.status == "blocked" else "🔜"
            )
            summary += f"{status_icon} **{i+1}. {step.step_name}**: {step.description}\n"
            if step.output:
                summary += f"  输出: {step.output[:200]}...\n"

        if self.whiteboard["decisions"]:
            summary += "\n## 关键决策\n\n"
            for d in self.whiteboard["decisions"]:
                summary += f"- {d['decision']} (by {d['made_by']})\n"

        if self.whiteboard["problems"]:
            summary += "\n## 遇到的问题\n\n"
            for p in self.whiteboard["problems"]:
                summary += f"- {p['problem']}\n"

        return summary

    def get_status(self) -> Dict:
        """获取当前状态"""
        completed = sum(1 for s in self.steps if s.status == "done")
        blocked = sum(1 for s in self.steps if s.status == "blocked")

        return {
            "project_name": self.project_name,
            "goal": self.goal,
            "total_steps": len(self.steps),
            "completed_steps": completed,
            "blocked_steps": blocked,
            "current_step_index": self.current_step_index,
            "current_step": self._get_current_step(),
            "whiteboard": self.whiteboard,
            "project_complete": completed == len(self.steps),
        }

    def _get_timestamp(self) -> str:
        from datetime import datetime

        return datetime.utcnow().isoformat()
