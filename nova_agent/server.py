"""
Nova Agent API服务

FastAPI实现的HTTP API

使用:
    # 启动服务
    python -m nova_agent.server
    
    # 或使用uvicorn
    uvicorn nova_agent.server:app --host 0.0.0.0 --port 8080

API端点:
    GET  /health          - 健康检查
    GET  /stats           - 统计信息
    GET  /workflows       - 列出工作流
    GET  /skills          - 列出技能
    POST /workflow/run    - 运行工作流
    POST /skill/run       - 运行技能
    POST /collab/run      - 运行协作
"""

import asyncio
from contextlib import asynccontextmanager
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

# 尝试导入FastAPI
try:
    from fastapi import FastAPI, HTTPException, BackgroundTasks
    from fastapi.responses import StreamingResponse
    from pydantic import BaseModel
    HAS_FASTAPI = True
except ImportError:
    HAS_FASTAPI = False
    print("Warning: FastAPI not installed. API service unavailable.")
    print("Install: pip install fastapi uvicorn")

from .config import ConfigManager
from .storage import SQLiteStore
from .skills import SkillLoader, AntipatternChecker
from .workflow import WorkflowEngine
from .collaboration import LeadSubCollaboration
from .llm import create_llm_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 全局组件
components = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动
    logger.info("Initializing Nova Agent API...")
    
    components["config"] = ConfigManager("./config")
    components["storage"] = SQLiteStore("./data/nova.db")
    components["skills"] = SkillLoader(components["config"])
    components["checker"] = AntipatternChecker(components["config"], components["storage"])
    components["llm"] = create_llm_client({"type": "mock"})  # 默认使用mock
    components["engine"] = WorkflowEngine(
        components["config"],
        components["skills"],
        components["llm"],
        components["storage"],
        components["checker"]
    )
    
    logger.info("Nova Agent API initialized")
    
    yield
    
    # 关闭
    logger.info("Shutting down Nova Agent API...")
    if hasattr(components["llm"], "close"):
        await components["llm"].close()


if HAS_FASTAPI:
    app = FastAPI(
        title="Nova Agent API",
        description="通用自主智能体框架",
        version="0.3.0",
        lifespan=lifespan
    )
    
    # ============== Pydantic模型 ==============
    
    class WorkflowRunRequest(BaseModel):
        workflow: str
        task: str
        config: Optional[Dict] = None
    
    class WorkflowRunResponse(BaseModel):
        workflow: str
        status: str
        duration_ms: float
        output: Any
        phases: List[Dict]
    
    class SkillRunRequest(BaseModel):
        skill: str
        context: Dict
    
    class CollabRunRequest(BaseModel):
        task: str
        max_subs: int = 4
        parallel: bool = True
    
    class StatsResponse(BaseModel):
        total_executions: int
        completed_executions: int
        failed_executions: int
        avg_duration_ms: float
        workflows_count: int
        skills_count: int
        antipatterns_count: int
    
    # ============== API端点 ==============
    
    @app.get("/health")
    async def health_check():
        """健康检查"""
        return {
            "status": "healthy",
            "version": "0.3.0",
            "timestamp": datetime.now().isoformat()
        }
    
    @app.get("/stats", response_model=StatsResponse)
    async def get_stats():
        """获取统计信息"""
        return components["storage"].get_stats()
    
    @app.get("/workflows")
    async def list_workflows():
        """列出工作流"""
        workflow_config = components["config"].get_section("workflow")
        workflows = workflow_config.get("workflows", {})
        
        return [
            {
                "name": name,
                "description": config.get("description", ""),
                "phases": config.get("phases", []),
                "version": config.get("version", "1.0.0")
            }
            for name, config in workflows.items()
        ]
    
    @app.get("/skills")
    async def list_skills():
        """列出技能"""
        skills = components["skills"].list_skills()
        
        return [
            {
                "name": name,
                "description": components["skills"].get_config(name).description
            }
            for name in skills
        ]
    
    @app.post("/workflow/run")
    async def run_workflow(request: WorkflowRunRequest, background_tasks: BackgroundTasks):
        """运行工作流"""
        try:
            result = await components["engine"].run(
                request.workflow,
                {"task": request.task, **(request.config or {})}
            )
            
            return {
                "workflow": result.workflow_name,
                "status": result.status.value,
                "duration_ms": result.total_duration_ms,
                "output": result.final_output,
                "phases": [
                    {
                        "phase": p.phase,
                        "status": p.status.value,
                        "duration_ms": p.duration_ms
                    }
                    for p in result.phases
                ]
            }
        except Exception as e:
            logger.error(f"Workflow run failed: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/skill/run")
    async def run_skill(request: SkillRunRequest):
        """运行技能"""
        try:
            skill = components["skills"].load(request.skill)
            result = await skill.execute(request.context)
            
            return {
                "skill": request.skill,
                "status": "completed",
                "result": result
            }
        except Exception as e:
            logger.error(f"Skill run failed: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/collab/run")
    async def run_collab(request: CollabRunRequest):
        """运行协作"""
        try:
            collab = LeadSubCollaboration(
                components["llm"],
                max_subs=request.max_subs
            )
            
            result = await collab.execute(
                request.task,
                {"max_subs": request.max_subs, "parallel": request.parallel}
            )
            
            return {
                "task": result.task,
                "subtasks_count": result.subtasks_count,
                "duration_ms": result.duration_ms,
                "output": result.final_result
            }
        except Exception as e:
            logger.error(f"Collab run failed: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/executions")
    async def get_executions(workflow: Optional[str] = None, limit: int = 10):
        """获取执行历史"""
        return components["storage"].get_execution_history(workflow, limit)
    
    @app.post("/feedback")
    async def submit_feedback(execution_id: int, rating: int, comment: str):
        """提交反馈"""
        components["storage"].save_feedback(execution_id, rating, comment)
        return {"status": "success"}

else:
    # 没有FastAPI时的占位
    app = None


def main():
    """主入口"""
    if not HAS_FASTAPI:
        print("Error: FastAPI is required for API server")
        print("Install: pip install fastapi uvicorn")
        return
    
    import uvicorn
    uvicorn.run(
        "nova_agent.server:app",
        host="0.0.0.0",
        port=8080,
        reload=True
    )


if __name__ == "__main__":
    main()
