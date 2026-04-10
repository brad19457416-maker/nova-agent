"""
SQLite存储

功能:
- 工作流执行记录
- 技能配置存储
- 反模式学习
- 用户反馈存储
- 统计数据

使用示例:
    store = SQLiteStore("./data/nova.db")
    
    # 保存执行记录
    store.save_execution("research", {"task": "xxx"}, result, "completed", 1500)
    
    # 查询执行历史
    history = store.get_execution_history("research", limit=10)
    
    # 统计数据
    stats = store.get_stats()
"""

import sqlite3
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class SQLiteStore:
    """
    SQLite存储
    
    数据库表:
    - workflows: 工作流配置
    - skills: 技能配置
    - antipatterns: 反模式
    - executions: 执行记录
    - feedback: 用户反馈
    - sessions: 会话记录
    """
    
    def __init__(self, db_path: str = "./data/nova.db"):
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._init_tables()
        logger.info(f"SQLite store initialized: {db_path}")
    
    def _init_tables(self):
        """初始化表"""
        self.conn.executescript('''
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
        self.conn.commit()
    
    # ==================== 工作流 ====================
    
    def save_workflow(self, name: str, config: Dict, version: str = "1.0.0"):
        """保存工作流配置"""
        now = datetime.now().isoformat()
        self.conn.execute('''
            INSERT OR REPLACE INTO workflows (name, config, version, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (name, json.dumps(config, ensure_ascii=False), version, now, now))
        self.conn.commit()
        logger.info(f"Saved workflow: {name}")
    
    def get_workflow(self, name: str) -> Optional[Dict]:
        """获取工作流配置"""
        cursor = self.conn.execute(
            'SELECT config FROM workflows WHERE name = ?', (name,)
        )
        row = cursor.fetchone()
        return json.loads(row['config']) if row else None
    
    def list_workflows(self) -> List[Dict]:
        """列出所有工作流"""
        cursor = self.conn.execute('SELECT name, version, created_at FROM workflows ORDER BY name')
        return [dict(row) for row in cursor.fetchall()]
    
    # ==================== 技能 ====================
    
    def save_skill(self, name: str, config: Dict, version: str = "1.0.0"):
        """保存技能配置"""
        now = datetime.now().isoformat()
        self.conn.execute('''
            INSERT OR REPLACE INTO skills (name, config, version, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (name, json.dumps(config, ensure_ascii=False), version, now, now))
        self.conn.commit()
        logger.info(f"Saved skill: {name}")
    
    def get_skill(self, name: str) -> Optional[Dict]:
        """获取技能配置"""
        cursor = self.conn.execute(
            'SELECT config FROM skills WHERE name = ?', (name,)
        )
        row = cursor.fetchone()
        return json.loads(row['config']) if row else None
    
    def list_skills(self) -> List[Dict]:
        """列出所有技能"""
        cursor = self.conn.execute('SELECT name, version, created_at FROM skills ORDER BY name')
        return [dict(row) for row in cursor.fetchall()]
    
    # ==================== 反模式 ====================
    
    def save_antipattern(self, name: str, description: str, category: str, 
                        severity: str = "major", keywords: List[str] = None):
        """保存反模式"""
        now = datetime.now().isoformat()
        self.conn.execute('''
            INSERT INTO antipatterns (name, description, category, severity, keywords, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (name, description, category, severity, json.dumps(keywords or []), now))
        self.conn.commit()
        logger.info(f"Saved antipattern: {name}")
    
    def get_antipatterns(self, category: Optional[str] = None) -> List[Dict]:
        """获取反模式"""
        if category:
            cursor = self.conn.execute(
                'SELECT * FROM antipatterns WHERE category = ?', (category,)
            )
        else:
            cursor = self.conn.execute('SELECT * FROM antipatterns')
        
        results = []
        for row in cursor.fetchall():
            r = dict(row)
            r['keywords'] = json.loads(r['keywords'] or '[]')
            results.append(r)
        return results
    
    # ==================== 执行记录 ====================
    
    def save_execution(self, workflow_name: str, input_data: Dict, 
                      output_data: Any, status: str, duration_ms: int,
                      metadata: Dict = None) -> int:
        """保存执行记录"""
        now = datetime.now().isoformat()
        cursor = self.conn.execute('''
            INSERT INTO executions (workflow_name, input_data, output_data, status, duration_ms, created_at, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (workflow_name, json.dumps(input_data, ensure_ascii=False), 
               json.dumps(output_data, ensure_ascii=False, default=str),
               status, duration_ms, now, json.dumps(metadata or {})))
        self.conn.commit()
        return cursor.lastrowid
    
    def get_execution(self, execution_id: int) -> Optional[Dict]:
        """获取执行记录"""
        cursor = self.conn.execute(
            'SELECT * FROM executions WHERE id = ?', (execution_id,)
        )
        row = cursor.fetchone()
        if not row:
            return None
        
        result = dict(row)
        result['input_data'] = json.loads(result['input_data'])
        result['output_data'] = json.loads(result['output_data'])
        result['metadata'] = json.loads(result['metadata'] or '{}')
        return result
    
    def get_execution_history(self, workflow_name: Optional[str] = None, 
                             limit: int = 10) -> List[Dict]:
        """获取执行历史"""
        if workflow_name:
            cursor = self.conn.execute('''
                SELECT id, workflow_name, status, duration_ms, created_at
                FROM executions 
                WHERE workflow_name = ?
                ORDER BY created_at DESC
                LIMIT ?
            ''', (workflow_name, limit))
        else:
            cursor = self.conn.execute('''
                SELECT id, workflow_name, status, duration_ms, created_at
                FROM executions 
                ORDER BY created_at DESC
                LIMIT ?
            ''', (limit,))
        
        return [dict(row) for row in cursor.fetchall()]
    
    # ==================== 反馈 ====================
    
    def save_feedback(self, execution_id: int, rating: int, comment: str,
                     issues: List[str] = None):
        """保存用户反馈"""
        now = datetime.now().isoformat()
        self.conn.execute('''
            INSERT INTO feedback (execution_id, rating, comment, issues, created_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (execution_id, rating, comment, json.dumps(issues or []), now))
        self.conn.commit()
        logger.info(f"Saved feedback for execution: {execution_id}")
    
    def get_feedback(self, execution_id: int) -> List[Dict]:
        """获取反馈"""
        cursor = self.conn.execute(
            'SELECT * FROM feedback WHERE execution_id = ?', (execution_id,)
        )
        results = []
        for row in cursor.fetchall():
            r = dict(row)
            r['issues'] = json.loads(r['issues'] or '[]')
            results.append(r)
        return results
    
    # ==================== 统计 ====================
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        # 执行统计
        cursor = self.conn.execute('''
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed,
                SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed,
                AVG(duration_ms) as avg_duration,
                MAX(duration_ms) as max_duration,
                MIN(duration_ms) as min_duration
            FROM executions
        ''')
        exec_row = cursor.fetchone()
        
        # 反馈统计
        cursor = self.conn.execute('''
            SELECT AVG(rating) as avg_rating, COUNT(*) as total
            FROM feedback
            WHERE rating IS NOT NULL
        ''')
        feedback_row = cursor.fetchone()
        
        return {
            "total_executions": exec_row['total'] or 0,
            "completed_executions": exec_row['completed'] or 0,
            "failed_executions": exec_row['failed'] or 0,
            "avg_duration_ms": round(exec_row['avg_duration'] or 0, 0),
            "max_duration_ms": exec_row['max_duration'] or 0,
            "min_duration_ms": exec_row['min_duration'] or 0,
            "total_feedback": feedback_row['total'] or 0,
            "avg_rating": round(feedback_row['avg_rating'] or 0, 1),
            "workflows_count": self._count('workflows'),
            "skills_count": self._count('skills'),
            "antipatterns_count": self._count('antipatterns')
        }
    
    def _count(self, table: str) -> int:
        """统计数量"""
        cursor = self.conn.execute(f'SELECT COUNT(*) as cnt FROM {table}')
        return cursor.fetchone()['cnt']
    
    def close(self):
        """关闭连接"""
        self.conn.close()
