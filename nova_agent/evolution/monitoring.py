"""
EvolutionMonitor - 进化监控

追踪进化前后效果对比，统计成功率、满意度，
可视化进化曲线。
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class EvolutionRecord:
    """进化记录"""

    timestamp: str
    before_success_rate: float
    after_success_rate: float
    num_skills_added: int
    description: str


class EvolutionMonitor:
    """进化监控器"""

    def __init__(self):
        self.records: List[EvolutionRecord] = []
        self.task_stats: Dict[str, Dict] = {}

    def record_evaluation(self, task_type: str, success: bool, confidence: float) -> None:
        """记录一次任务评估"""
        if task_type not in self.task_stats:
            self.task_stats[task_type] = {"total": 0, "success": 0, "confidence_sum": 0.0}

        stats = self.task_stats[task_type]
        stats["total"] += 1
        if success:
            stats["success"] += 1
        stats["confidence_sum"] += confidence

    def get_success_rate(self, task_type: Optional[str] = None) -> float:
        """获取成功率"""
        if task_type and task_type in self.task_stats:
            stats = self.task_stats[task_type]
            if stats["total"] == 0:
                return 0.0
            return stats["success"] / stats["total"]

        # 总体成功率
        total = sum(s["total"] for s in self.task_stats.values())
        success = sum(s["success"] for s in self.task_stats.values())
        if total == 0:
            return 0.0
        return success / total

    def record_evolution_step(
        self, before_rate: float, after_rate: float, num_skills: int, description: str
    ) -> None:
        """记录一次进化步骤"""
        record = EvolutionRecord(
            timestamp=datetime.utcnow().isoformat(),
            before_success_rate=before_rate,
            after_success_rate=after_rate,
            num_skills_added=num_skills,
            description=description,
        )
        self.records.append(record)

        improvement = after_rate - before_rate
        if improvement > 0:
            logger.info(
                f"Evolution step successful: +{improvement:.2%} improvement, added {num_skills} skills"
            )
        else:
            logger.warning(f"Evolution step: {improvement:.2%} change")

    def get_evolution_curve(self) -> List[Dict]:
        """获取进化曲线数据"""
        curve = []
        cumulative_skills = 0

        for record in self.records:
            cumulative_skills += record.num_skills_added
            curve.append(
                {
                    "timestamp": record.timestamp,
                    "success_rate": record.after_success_rate,
                    "cumulative_skills": cumulative_skills,
                }
            )

        return curve

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "total_evolution_steps": len(self.records),
            "current_overall_success_rate": self.get_success_rate(),
            "total_tasks": sum(s["total"] for s in self.task_stats.values()),
            "total_skills_learned": sum(r.num_skills_added for r in self.records),
            "task_types": list(self.task_stats.keys()),
        }

    def generate_report(self) -> str:
        """生成进化报告"""
        stats = self.get_stats()
        curve = self.get_evolution_curve()

        report = "📊 **Nova Agent 进化进度报告**\n\n"
        report += f"总体成功率: {stats['current_overall_success_rate']:.1%}\n"
        report += f"总任务数: {stats['total_tasks']}\n"
        report += f"进化步数: {stats['total_evolution_steps']}\n"
        report += f"学习到的技能: {stats['total_skills_learned']}\n\n"

        report += "**各任务类型成功率:**\n"
        for task_type, s in self.task_stats.items():
            rate = s["success"] / s["total"] if s["total"] > 0 else 0
            report += f"- {task_type}: {rate:.1%} ({s['success']}/{s['total']})\n"

        if len(curve) > 1:
            first_rate = curve[0]["success_rate"]
            last_rate = curve[-1]["success_rate"]
            improvement = last_rate - first_rate
            report += f"\n**改进:** {improvement:+.1%}\n"

        return report
