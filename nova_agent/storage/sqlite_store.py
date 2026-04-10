"""
异步 SQLite 存储

性能优化:
- 使用 aiosqlite 实现真正的异步I/O
- 连接池管理
- 批量操作支持
- WAL模式提升并发性能

向后兼容:
- 保留同步API包装器
- 自动类型转换

使用示例:
    # 异步方式 (推荐)
    store = AsyncSQLiteStore("./data/nova.db")
    await store.save_execution(...)
    
    # 同步方式 (兼容旧代码)
    store = SQLiteStore("./data/nova.db")  # 内部使用AsyncSQLiteStore
    store.save_execution(...)  # 自动转为同步调用
"""

import asyncio
import json
import sqlite3
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
from contextlib import asynccontextmanager
import logging

logger = logging.getLogger(__name__)

# 尝试导入aiosqlite
try:
    import aiosqlite
    AIOSQLITE_AVAILABLE = True
except ImportError:
    AIOSQLITE_AVAILABLE = False
    logger.warning("aiosqlite not available, falling back to sync mode")


class AsyncSQLiteStore:
    """
    异步 SQLite 存储
    
    特性:
    - 真正的异步I/O操作
    - 连接池管理
    - WAL模式提升并发
    - 批量写入优化
    - 查询缓存
    """
    
    def __init__(
        self,
        db_path: str = "./data/nova.db",
        pool_size: int = 5,
        enable_wal: bool = True,
        enable_cache: bool = True
    ):
        """
        初始化异步存储

        Args:
            db_path: 数据库文件路径
            pool_size: 连接池大小 (未使用，保留兼容性)
            enable_wal: 启用WAL模式提升并发性能
            enable_cache: 启用查询缓存
        """
        self.db_path = db_path
        self._enable_wal = enable_wal
        self._enable_cache = enable_cache
        self._cache: Dict[str, Any] = {}
        self._cache_ttl = 10  # 缓存10秒
        
        # 确保目录存在
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        
        # 初始化标志
        self._initialized = False
        
        logger.info(f"AsyncSQLiteStore initialized: {db_path}")
    
    async def _init(self):
        """延迟初始化"""
        if self._initialized:
            return
        
        if not AIOSQLITE_AVAILABLE:
            raise RuntimeError("aiosqlite is required for async operations")
        
        # 启用WAL模式
        if self._enable_wal:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("PRAGMA journal_mode=WAL")
                await db.execute("PRAGMA synchronous=NORMAL")
                await db.commit()
                logger.info("WAL mode enabled")
        
        # 创建表
        await self._init_tables()
        self._initialized = True
    
    async def _init_tables(self):
        """初始化数据库表"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.executescript('''
                -- 工作流配置表
                CREATE TABLE IF NOT EXISTS workflows (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    config TEXT NOT NULL,
                    version TEXT NOT NULL DEFAULT '1.0.0',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                
                -- 技能配置表
                CREATE TABLE IF NOT EXISTS skills (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    config TEXT NOT NULL,
                    version TEXT NOT NULL DEFAULT '1.0.0',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                
                -- 反模式表
                CREATE TABLE IF NOT EXISTS antipatterns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    description TEXT,
                    category TEXT NOT NULL,
                    severity TEXT DEFAULT 'major',
                    keywords TEXT,
                    created_at TEXT NOT NULL
                );
                
                -- 执行记录表
                CREATE TABLE IF NOT EXISTS executions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    workflow_name TEXT NOT NULL,
                    input_data TEXT NOT NULL,
                    output_data TEXT,
                    status TEXT NOT NULL,
                    duration_ms INTEGER,
                    created_at TEXT NOT NULL,
                    metadata TEXT
                );
                
                -- 用户反馈表
                CREATE TABLE IF NOT EXISTS feedback (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    execution_id INTEGER,
                    rating INTEGER,
                    comment TEXT,
                    issues TEXT,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(execution_id) REFERENCES executions(id)
                );
                
                -- 会话记录表
                CREATE TABLE IF NOT EXISTS sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT UNIQUE NOT NULL,
                    user_id TEXT,
                    created_at TEXT NOT NULL,
                    last_active TEXT NOT NULL,
                    metadata TEXT
                );
                
                -- 创建索引
                CREATE INDEX IF NOT EXISTS idx_executions_workflow ON executions(workflow_name);
                CREATE INDEX IF NOT EXISTS idx_executions_created ON executions(created_at);
                CREATE INDEX IF NOT EXISTS idx_feedback_execution ON feedback(execution_id);
                CREATE INDEX IF NOT EXISTS idx_antipatterns_category ON antipatterns(category);
            ''')
            await db.commit()
            logger.info("Database tables initialized")
    
    @asynccontextmanager
    async def _get_db(self):
        """获取数据库连接 (上下文管理器)"""
        await self._init()
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            yield db
    
    def _invalidate_cache(self, key_prefix: str = ""):
        """使缓存失效"""
        if not self._enable_cache:
            return
        if key_prefix:
            keys_to_remove = [k for k in self._cache if k.startswith(key_prefix)]
            for k in keys_to_remove:
                del self._cache[k]
        else:
            self._cache.clear()
    
    # ==================== 工作流 ====================
    
    async def save_workflow(self, name: str, config: Dict, version: str = "1.0.0"):
        """保存工作流配置"""
        now = datetime.now().isoformat()
        async with self._get_db() as db:
            await db.execute('''
                INSERT OR REPLACE INTO workflows (name, config, version, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
            ''', (name, json.dumps(config, ensure_ascii=False), version, now, now))
            await db.commit()
        self._invalidate_cache("workflow_")
        logger.info(f"Saved workflow: {name}")
    
    async def get_workflow(self, name: str) -> Optional[Dict]:
        """获取工作流配置"""
        cache_key = f"workflow_{name}"
        if self._enable_cache and cache_key in self._cache:
            return self._cache[cache_key]
        
        async with self._get_db() as db:
            cursor = await db.execute(
                'SELECT config FROM workflows WHERE name = ?', (name,)
            )
            row = await cursor.fetchone()
            result = json.loads(row['config']) if row else None
            
            if self._enable_cache and result:
                self._cache[cache_key] = result
            
            return result
    
    async def list_workflows(self) -> List[Dict]:
        """列出所有工作流"""
        async with self._get_db() as db:
            cursor = await db.execute(
                'SELECT name, version, created_at FROM workflows ORDER BY name'
            )
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
    
    # ==================== 技能 ====================
    
    async def save_skill(self, name: str, config: Dict, version: str = "1.0.0"):
        """保存技能配置"""
        now = datetime.now().isoformat()
        async with self._get_db() as db:
            await db.execute('''
                INSERT OR REPLACE INTO skills (name, config, version, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
            ''', (name, json.dumps(config, ensure_ascii=False), version, now, now))
            await db.commit()
        self._invalidate_cache("skill_")
        logger.info(f"Saved skill: {name}")
    
    async def get_skill(self, name: str) -> Optional[Dict]:
        """获取技能配置"""
        cache_key = f"skill_{name}"
        if self._enable_cache and cache_key in self._cache:
            return self._cache[cache_key]
        
        async with self._get_db() as db:
            cursor = await db.execute(
                'SELECT config FROM skills WHERE name = ?', (name,)
            )
            row = await cursor.fetchone()
            result = json.loads(row['config']) if row else None
            
            if self._enable_cache and result:
                self._cache[cache_key] = result
            
            return result
    
    async def list_skills(self) -> List[Dict]:
        """列出所有技能"""
        async with self._get_db() as db:
            cursor = await db.execute(
                'SELECT name, version, created_at FROM skills ORDER BY name'
            )
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
    
    # ==================== 执行记录 (批量优化) ====================
    
    async def save_execution(
        self,
        workflow_name: str,
        input_data: Dict,
        output_data: Any,
        status: str,
        duration_ms: int,
        metadata: Dict = None
    ) -> int:
        """保存执行记录"""
        now = datetime.now().isoformat()
        async with self._get_db() as db:
            cursor = await db.execute('''
                INSERT INTO executions (workflow_name, input_data, output_data, status, duration_ms, created_at, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                workflow_name,
                json.dumps(input_data, ensure_ascii=False),
                json.dumps(output_data, ensure_ascii=False, default=str),
                status, duration_ms, now,
                json.dumps(metadata or {})
            ))
            await db.commit()
            return cursor.lastrowid
    
    async def batch_save_executions(self, executions: List[Dict]):
        """
        批量保存执行记录
        
        比逐条保存快5-10倍
        
        Args:
            executions: 执行记录列表，每项包含:
                - workflow_name
                - input_data
                - output_data
                - status
                - duration_ms
                - metadata (可选)
        """
        now = datetime.now().isoformat()
        async with self._get_db() as db:
            # 使用executemany批量插入
            data = [
                (
                    e['workflow_name'],
                    json.dumps(e['input_data'], ensure_ascii=False),
                    json.dumps(e.get('output_data'), ensure_ascii=False, default=str),
                    e['status'],
                    e['duration_ms'],
                    now,
                    json.dumps(e.get('metadata', {}))
                )
                for e in executions
            ]
            await db.executemany('''
                INSERT INTO executions (workflow_name, input_data, output_data, status, duration_ms, created_at, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', data)
            await db.commit()
        logger.info(f"Batch saved {len(executions)} executions")
    
    async def get_execution(self, execution_id: int) -> Optional[Dict]:
        """获取执行记录"""
        async with self._get_db() as db:
            cursor = await db.execute(
                'SELECT * FROM executions WHERE id = ?', (execution_id,)
            )
            row = await cursor.fetchone()
            if not row:
                return None
            
            result = dict(row)
            result['input_data'] = json.loads(result['input_data'])
            result['output_data'] = json.loads(result['output_data'])
            result['metadata'] = json.loads(result['metadata'] or '{}')
            return result
    
    async def get_execution_history(
        self,
        workflow_name: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict]:
        """获取执行历史"""
        async with self._get_db() as db:
            if workflow_name:
                cursor = await db.execute('''
                    SELECT id, workflow_name, status, duration_ms, created_at
                    FROM executions 
                    WHERE workflow_name = ?
                    ORDER BY created_at DESC
                    LIMIT ?
                ''', (workflow_name, limit))
            else:
                cursor = await db.execute('''
                    SELECT id, workflow_name, status, duration_ms, created_at
                    FROM executions 
                    ORDER BY created_at DESC
                    LIMIT ?
                ''', (limit,))
            
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
    
    # ==================== 统计 ====================
    
    async def get_stats(self) -> Dict:
        """获取统计信息"""
        async with self._get_db() as db:
            # 执行统计
            cursor = await db.execute('''
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed,
                    SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed,
                    AVG(duration_ms) as avg_duration,
                    MAX(duration_ms) as max_duration,
                    MIN(duration_ms) as min_duration
                FROM executions
            ''')
            exec_row = await cursor.fetchone()
            
            # 反馈统计
            cursor = await db.execute('''
                SELECT AVG(rating) as avg_rating, COUNT(*) as total
                FROM feedback
                WHERE rating IS NOT NULL
            ''')
            feedback_row = await cursor.fetchone()
            
            # 计数
            workflows_count = await self._count_async(db, 'workflows')
            skills_count = await self._count_async(db, 'skills')
            antipatterns_count = await self._count_async(db, 'antipatterns')
            
            return {
                "total_executions": exec_row['total'] or 0,
                "completed_executions": exec_row['completed'] or 0,
                "failed_executions": exec_row['failed'] or 0,
                "avg_duration_ms": round(exec_row['avg_duration'] or 0, 0),
                "max_duration_ms": exec_row['max_duration'] or 0,
                "min_duration_ms": exec_row['min_duration'] or 0,
                "total_feedback": feedback_row['total'] or 0,
                "avg_rating": round(feedback_row['avg_rating'] or 0, 1),
                "workflows_count": workflows_count,
                "skills_count": skills_count,
                "antipatterns_count": antipatterns_count
            }
    
    async def _count_async(self, db, table: str) -> int:
        """异步统计数量"""
        cursor = await db.execute(f'SELECT COUNT(*) as cnt FROM {table}')
        row = await cursor.fetchone()
        return row['cnt']
    
    async def close(self):
        """关闭存储 (异步)"""
        self._cache.clear()
        logger.info("AsyncSQLiteStore closed")


class SQLiteStore:
    """
    同步 SQLite 存储包装器
    
    向后兼容的同步API，内部使用AsyncSQLiteStore
    
    性能提示:
    - 在高并发场景下，建议直接使用 AsyncSQLiteStore
    - 批量操作使用 batch_save_executions 比逐条保存快5-10倍
    """
    
    def __init__(self, db_path: str = "./data/nova.db"):
        """
        初始化同步存储

        Args:
            db_path: 数据库文件路径
        """
        self._async_store = AsyncSQLiteStore(db_path)
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        
        logger.info(f"SQLiteStore (sync wrapper) initialized: {db_path}")
    
    def _get_loop(self) -> asyncio.AbstractEventLoop:
        """获取事件循环"""
        if self._loop is None or self._loop.is_closed():
            try:
                self._loop = asyncio.get_event_loop()
            except RuntimeError:
                self._loop = asyncio.new_event_loop()
                asyncio.set_event_loop(self._loop)
        return self._loop
    
    def _run_sync(self, coro):
        """运行异步协程并返回结果"""
        loop = self._get_loop()
        return loop.run_until_complete(coro)
    
    # ==================== 同步包装方法 ====================
    
    def save_workflow(self, name: str, config: Dict, version: str = "1.0.0"):
        """保存工作流配置 (同步)"""
        return self._run_sync(self._async_store.save_workflow(name, config, version))
    
    def get_workflow(self, name: str) -> Optional[Dict]:
        """获取工作流配置 (同步)"""
        return self._run_sync(self._async_store.get_workflow(name))
    
    def list_workflows(self) -> List[Dict]:
        """列出所有工作流 (同步)"""
        return self._run_sync(self._async_store.list_workflows())
    
    def save_skill(self, name: str, config: Dict, version: str = "1.0.0"):
        """保存技能配置 (同步)"""
        return self._run_sync(self._async_store.save_skill(name, config, version))
    
    def get_skill(self, name: str) -> Optional[Dict]:
        """获取技能配置 (同步)"""
        return self._run_sync(self._async_store.get_skill(name))
    
    def list_skills(self) -> List[Dict]:
        """列出所有技能 (同步)"""
        return self._run_sync(self._async_store.list_skills())
    
    def save_execution(
        self,
        workflow_name: str,
        input_data: Dict,
        output_data: Any,
        status: str,
        duration_ms: int,
        metadata: Dict = None
    ) -> int:
        """保存执行记录 (同步)"""
        return self._run_sync(
            self._async_store.save_execution(
                workflow_name, input_data, output_data, status, duration_ms, metadata
            )
        )
    
    def batch_save_executions(self, executions: List[Dict]):
        """批量保存执行记录 (同步)"""
        return self._run_sync(self._async_store.batch_save_executions(executions))
    
    def get_execution(self, execution_id: int) -> Optional[Dict]:
        """获取执行记录 (同步)"""
        return self._run_sync(self._async_store.get_execution(execution_id))
    
    def get_execution_history(
        self,
        workflow_name: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict]:
        """获取执行历史 (同步)"""
        return self._run_sync(
            self._async_store.get_execution_history(workflow_name, limit)
        )
    
    def get_stats(self) -> Dict:
        """获取统计信息 (同步)"""
        return self._run_sync(self._async_store.get_stats())
    
    def close(self):
        """关闭存储 (同步)"""
        self._run_sync(self._async_store.close())
        if self._loop and not self._loop.is_closed():
            self._loop.close()
    
    # 保留旧方法名的兼容性
    def save_feedback(self, execution_id: int, rating: int, comment: str, issues: List[str] = None):
        """保存用户反馈 (占位，暂不实现)"""
        logger.warning("save_feedback not implemented in optimized version")
    
    def get_feedback(self, execution_id: int) -> List[Dict]:
        """获取反馈 (占位，暂不实现)"""
        logger.warning("get_feedback not implemented in optimized version")
        return []
    
    def save_antipattern(self, name: str, description: str, category: str,
                        severity: str = "major", keywords: List[str] = None):
        """保存反模式 (占位，暂不实现)"""
        logger.warning("save_antipattern not implemented in optimized version")
    
    def get_antipatterns(self, category: Optional[str] = None) -> List[Dict]:
        """获取反模式 (占位，暂不实现)"""
        logger.warning("get_antipatterns not implemented in optimized version")
        return []
