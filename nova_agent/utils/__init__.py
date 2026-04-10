"""
连接池管理器

提供HTTP连接池复用，减少连接建立开销
"""

import aiohttp
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


class ConnectionPool:
    """
    HTTP连接池管理器
    
    特性:
    - 连接复用
    - 自动清理
    - 限流控制
    - 连接保活
    
    使用示例:
        pool = ConnectionPool()
        session = await pool.get_session("http://localhost:11434")
        async with session.post(...) as resp:
            ...
    """
    
    def __init__(
        self,
        total_limit: int = 10,
        limit_per_host: int = 5,
        keepalive_timeout: int = 30,
        ttl_dns_cache: int = 300
    ):
        """
        初始化连接池

        Args:
            total_limit: 总连接数限制
            limit_per_host: 单主机连接限制
            keepalive_timeout: 连接保活时间(秒)
            ttl_dns_cache: DNS缓存时间(秒)
        """
        self._connector = aiohttp.TCPConnector(
            limit=total_limit,
            limit_per_host=limit_per_host,
            enable_cleanup_closed=True,
            force_close=False,
            ttl_dns_cache=ttl_dns_cache,
            keepalive_timeout=keepalive_timeout
        )
        
        self._sessions: Dict[str, aiohttp.ClientSession] = {}
        self._default_timeout = aiohttp.ClientTimeout(total=120)
        
        logger.info(
            f"ConnectionPool initialized: "
            f"total_limit={total_limit}, per_host={limit_per_host}"
        )
    
    async def get_session(
        self,
        base_url: str,
        timeout: Optional[aiohttp.ClientTimeout] = None
    ) -> aiohttp.ClientSession:
        """
        获取或创建会话

        Args:
            base_url: 基础URL，用于会话缓存键
            timeout: 请求超时设置

        Returns:
            aiohttp.ClientSession实例
        """
        if base_url not in self._sessions:
            self._sessions[base_url] = aiohttp.ClientSession(
                connector=self._connector,
                timeout=timeout or self._default_timeout,
                raise_for_status=False
            )
            logger.debug(f"Created new session for {base_url}")
        
        return self._sessions[base_url]
    
    async def close(self):
        """关闭所有会话和连接器"""
        logger.info("Closing connection pool...")
        
        # 关闭所有会话
        for url, session in self._sessions.items():
            if not session.closed:
                await session.close()
                logger.debug(f"Closed session for {url}")
        
        self._sessions.clear()
        
        # 关闭连接器
        if not self._connector.closed:
            await self._connector.close()
        
        logger.info("Connection pool closed")
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()


class ConnectionPoolManager:
    """
    全局连接池管理器
    
    管理多个连接池实例，支持按用途隔离
    """
    
    _instance: Optional['ConnectionPoolManager'] = None
    _pools: Dict[str, ConnectionPool] = {}
    
    @classmethod
    def get_instance(cls) -> 'ConnectionPoolManager':
        """获取单例实例"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def get_pool(
        self,
        name: str = "default",
        total_limit: int = 10,
        limit_per_host: int = 5
    ) -> ConnectionPool:
        """
        获取或创建连接池

        Args:
            name: 连接池名称
            total_limit: 总连接数限制
            limit_per_host: 单主机连接限制

        Returns:
            ConnectionPool实例
        """
        if name not in self._pools:
            self._pools[name] = ConnectionPool(
                total_limit=total_limit,
                limit_per_host=limit_per_host
            )
            logger.info(f"Created connection pool: {name}")
        
        return self._pools[name]
    
    async def close_all(self):
        """关闭所有连接池"""
        logger.info("Closing all connection pools...")
        for name, pool in self._pools.items():
            await pool.close()
            logger.info(f"Closed pool: {name}")
        self._pools.clear()
