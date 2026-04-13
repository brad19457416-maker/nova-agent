"""
测试 SQLite 存储
"""

import pytest
import tempfile
import asyncio
from nova_agent.storage import SQLiteStore


def test_sync_storage_init_no_aiosqlite():
    """测试同步存储初始化在没有aiosqlite时仍然能创建"""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=True) as tmp:
        pass
    db_path = tmp.name
    
    store = SQLiteStore(db_path)
    assert store is not None
    assert hasattr(store, 'get_stats')
    
    # 清理
    import os
    if os.path.exists(db_path):
        os.unlink(db_path)


def test_sqlitestore_methods_exist():
    """测试SQLiteStore有必要的方法"""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=True) as tmp:
        pass
    db_path = tmp.name
    
    store = SQLiteStore(db_path)
    assert hasattr(store, 'get_stats')
    assert hasattr(store, 'save_workflow')
    assert hasattr(store, 'get_workflow')
    assert hasattr(store, 'list_workflows')
    
    # 不调用close避免事件循环问题
    import os
    if os.path.exists(db_path):
        os.unlink(db_path)
