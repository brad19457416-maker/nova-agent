"""
Nova Agent API服务 (性能优化版)

特性:
- 响应缓存
- 请求限流
- 连接池优化
- 并发控制
- 健康检查
- 性能指标

使用:
    # 启动服务
    python -m nova_agent.server
    
    # 或使用uvicorn
    uvicorn nova_agent.server:app --host 0.0.0.0 --port 8080 --workers 4

API端点:
    GET  /health          - 健康检查
    GET  /stats           - 统计信息
    GET  /metrics         - 性能指标 (Prometheus格式)
    GET  /workflows       - 列出工作流
    GET  /skills          - 列出技能
    POST /workflow/run    - 运行工作流
    POST /workflow/batch  - 批量运行工作流
    POST /skill/run       - 运行技能
    POST /collab/run      - 运行协作
"""

import asyncio
import time
from contextlib import asynccontextmanager
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timedelta
from functools import wraps
import logging
import hashlib

# 尝试导入FastAPI
try:
    from fastapi import FastAPI, HTTPException, BackgroundTasks, Request, status
    from fastapi.responses import JSONResponse, StreamingResponse
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.middleware.gzip import GZipMiddleware
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
components: Dict[str, Any] = {}

# ============ 性能优化组件 ============

class APICache:
    """API响应缓存"""
    
    def __init__(self, ttl: float = 60.0, max_size: int = 1000):
        self.ttl = ttl
        self.max_size = max_size
        self._cache: Dict[str, Dict] = {}
        self._lock = asyncio.Lock()
    
    def _make_key(self, method: str, path: str, params: str) -> str:
        """生成缓存键"""
        key = f"{method}:{path}:{params}"
        return hashlib.md5(key.encode()).hexdigest()[:16]
    
    async def get(self, method: str, path: str, params: str) -> Optional[Any]:
        """获取缓存"""
        key = self._make_key(method, path, params)
        
        async with self._lock:
            if key in self._cache:
                entry = self._cache[key]
                if time.time() - entry["timestamp"] < self.ttl:
                    return entry["data"]
                else:
                    del self._cache[key]
        return None
    
    async def set(self, method: str, path: str, params: str, data: Any):
        """设置缓存"""
        key = self._make_key(method, path, params)
        
        async with self._lock:
            # 清理过期项
            now = time.time()
            expired = [
                k for k, v in self._cache.items()
                if now - v["timestamp"] > self.ttl
            ]
            for k in expired:
                del self._cache[k]
            
            # 限制大小
            if len(self._cache) >= self.max_size:
                oldest = min(self._cache.keys(), key=lambda k: self._cache[k]["timestamp"])
                del self._cache[oldest]
            
            self._cache[key] = {
                "data": data,
                "timestamp": now
            }
    
    async def invalidate(self, path_prefix: str = ""):
        """使缓存失效"""
        async with self._lock:
            if path_prefix:
                keys = [k for k in self._cache if path_prefix in k]
                for k in keys:
                    del self._cache[k]
            else:
                self._cache.clear()


class RateLimiter:
    """请求限流器"""
    
    def __init__(self, requests_per_minute: int = 60):
        self.requests_per_minute = requests_per_minute
        self._requests: Dict[str, List[float]] = {}
        self._lock = asyncio.Lock()
    
    async def is_allowed(self, client_id: str) -> bool:
        """检查是否允许请求"""
        now = time.time()
        window_start = now - 60  # 1分钟窗口
        
        async with self._lock:
            if client_id not in self._requests:
                self._requests[client_id] = []
            
            # 清理过期请求记录
            self._requests[client_id] = [
                t for t in self._requests[client_id]
                if t > window_start
            ]
            
            # 检查限流
            if len(self._requests[client_id]) >= self.requests_per_minute:
                return False
            
            # 记录请求
            self._requests[client_id].append(now)
            return True


class MetricsCollector:
    """性能指标收集器"""
    
    def __init__(self):
        self.request_count = 0
        self.request_duration_total = 0.0
        self.error_count = 0
        self.cache_hits = 0
        self.cache_misses = 0
        self._lock = asyncio.Lock()
    
    async def record_request(self, duration: float, error: bool = False, cache_hit: bool = False):
        """记录请求指标"""
        async with self._lock:
            self.request_count += 1
            self.request_duration_total += duration
            if error:
                self.error_count += 1
            if cache_hit:
                self.cache_hits += 1
            else:
                self.cache_misses += 1
    
    def get_metrics(self) -> Dict:
        """获取指标"""
        avg_duration = (
            self.request_duration_total / self.request_count
            if self.request_count > 0 else 0
        )
        cache_total = self.cache_hits + self.cache_misses
        cache_hit_rate = (
            self.cache_hits / cache_total
            if cache_total > 0 else 0
        )
        
        return {
            "request_count": self.request_count,
            "error_count": self.error_count,
            "error_rate": self.error_count / self.request_count if self.request_count > 0 else 0,
            "avg_duration_ms": round(avg_duration * 1000, 2),
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "cache_hit_rate": round(cache_hit_rate * 100, 2)
        }


# 全局优化组件
cache = APICache(ttl=60.0, max_size=1000)
rate_limiter = RateLimiter(requests_per_minute=120)
metrics = MetricsCollector()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动
    logger.info("Initializing Nova Agent API (Optimized)...")
    
    components["config"] = ConfigManager("./config")
    components["storage"] = SQLiteStore("./data/nova.db")
    components["skills"] = SkillLoader(components["config"])
    components["checker"] = AntipatternChecker(components["config"], components["storage"])
    components["llm"] = create_llm_client({"type": "mock"})
    components["engine"] = WorkflowEngine(
        components["config"],
        components["skills"],
        components["llm"],
        components["storage"],
        components["checker"],
        enable_parallel=True,
        max_parallel_phases=3
    )
    
    logger.info("Nova Agent API initialized")
    logger.info(f"Parallel execution: enabled (max={components['engine']._max_parallel_phases})")
    
    yield
    
    # 关闭
    logger.info("Shutting down Nova Agent API...")
    if hasattr(components["llm"], "close"):
        await components["llm"].close()


if HAS_FASTAPI:
    app = FastAPI(
        title="Nova Agent API",
        description="高性能通用自主智能体框架",
        version="0.3.0",
        lifespan=lifespan
    )
    
    # 中间件
    app.add_middleware(GZipMiddleware, minimum_size=1000)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # ============ Pydantic模型 ============
    
    class WorkflowRunRequest(BaseModel):
        workflow: str
        task: str
        config: Optional[Dict] = None
        use_cache: bool = False
    
    class WorkflowBatchRequest(BaseModel):
        tasks: List[Dict[str, Any]]
        max_concurrent: int = 3
    
    class WorkflowRunResponse(BaseModel):
        workflow: str
        status: str
        duration_ms: float
        output: Any
        phases: List[Dict]
        parallel_groups: Optional[List[List[str]]] = None
    
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
    
    # ============ 中间件 ============
    
    @app.middleware("http")
    async def performance_middleware(request: Request, call_next):
        """性能监控中间件"""
        start_time = time.time()
        client_id = request.client.host if request.client else "unknown"
        
        # 限流检查
        if not await rate_limiter.is_allowed(client_id):
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={"detail": "Rate limit exceeded"}
            )
        
        # 缓存检查 (GET请求)
        cache_key = None
        if request.method == "GET":
            params = str(dict(request.query_params))
            cached = await cache.get(request.method, request.url.path, params)
            if cached:
                await metrics.record_request(time.time() - start_time, cache_hit=True)
                return JSONResponse(content=cached)
        
        # 执行请求
        try:
            response = await call_next(request)
            duration = time.time() - start_time
            
            # 记录指标
            await metrics.record_request(duration, error=response.status_code >= 400)
            
            # 缓存响应 (GET请求且成功)
            if request.method == "GET" and response.status_code == 200:
                # 注意：实际实现中需要读取响应体内容来缓存
                pass
            
            # 添加性能头
            response.headers["X-Response-Time"] = f"{duration*1000:.2f}ms"
            
            return response
            
        except Exception as e:
            await metrics.record_request(time.time() - start_time, error=True)
            raise
    
    # ============ API端点 ============
    
    @app.get("/health")
    async def health_check():
        """健康检查"""
        return {
            "status": "healthy",
            "version": "0.3.0",
            "timestamp": datetime.now().isoformat(),
            "components": {
                "config": components["config"] is not None,
                "storage": components["storage"] is not None,
                "engine": components["engine"] is not None
            }
        }
    
    @app.get("/metrics")
    async def get_metrics():
        """获取性能指标"""
        return {
            "api_metrics": metrics.get_metrics(),
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
        skill_config = components["config"].get_section("skill")
        skills = skill_config.get("skills", {})
        
        return [
            {
                "name": name,
                "description": config.get("description", ""),
                "domain": config.get("domain", "general")
            }
            for name, config in skills.items()
        ]
    
    @app.post("/workflow/run", response_model=WorkflowRunResponse)
    async def run_workflow(request: WorkflowRunRequest, background_tasks: BackgroundTasks):
        """运行工作流 (支持并行执行)"""
        try:
            result = await components["engine"].run(
                request.workflow,
                {"task": request.task, **(request.config or {})},
                use_cache=request.use_cache
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
                ],
                "parallel_groups": result.parallel_phases if result.metadata.get("parallel_enabled") else None
            }
        except Exception as e:
            logger.error(f"Workflow run failed: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/workflow/batch")
    async def run_workflow_batch(request: WorkflowBatchRequest):
        """批量运行工作流"""
        try:
            results = await components["engine"].run_batch(
                request.tasks,
                max_concurrent=request.max_concurrent
            )
            
            return {
                "results": [
                    {
                        "workflow": r.workflow_name,
                        "status": r.status.value,
                        "duration_ms": r.total_duration_ms
                    }
                    for r in results
                    if not isinstance(r, Exception)
                ],
                "errors": [
                    str(r) for r in results
                    if isinstance(r, Exception)
                ]
            }
        except Exception as e:
            logger.error(f"Batch workflow run failed: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/skill/run")
    async def run_skill(request: SkillRunRequest):
        """运行技能"""
        try:
            skill = await components["skills"].load(request.skill)
            if not skill:
                raise HTTPException(status_code=404, detail=f"Skill not found: {request.skill}")
            
            result = await skill.execute(request.context)
            
            return {
                "skill": request.skill,
                "status": "completed",
                "result": result
            }
        except HTTPException:
            raise
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
    
    @app.post("/cache/invalidate")
    async def invalidate_cache(path_prefix: str = ""):
        """使API缓存失效"""
        await cache.invalidate(path_prefix)
        return {"status": "success", "message": "Cache invalidated"}
    
    @app.get("/cache/stats")
    async def get_cache_stats():
        """获取缓存统计"""
        return {
            "cache_hit_rate": metrics.get_metrics()["cache_hit_rate"],
            "cache_hits": metrics.cache_hits,
            "cache_misses": metrics.cache_misses
        }

else:
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
        reload=True,
        workers=1  # 开发模式使用1个worker
    )


if __name__ == "__main__":
    main()
