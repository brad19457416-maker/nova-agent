"""
PluginManager - 插件管理器

管理插件加载、获取、启用禁用。
"""

from typing import Dict, Any, List, Optional
import importlib
import os
import sys
from pathlib import Path
import logging

from .plugin_base import PluginBase, PluginResult

logger = logging.getLogger(__name__)


class PluginManager:
    """插件管理器"""
    
    def __init__(self):
        self.plugins: Dict[str, PluginBase] = {}
        self.enabled: Dict[str, bool] = {}
    
    def register_plugin(self, plugin: PluginBase) -> bool:
        """注册插件"""
        if not plugin.name:
            logger.error("Plugin has no name")
            return False
        
        self.plugins[plugin.name] = plugin
        self.enabled[plugin.name] = True
        logger.debug(f"Registered plugin: {plugin.name}")
        return True
    
    def get_plugin(self, name: str) -> Optional[PluginBase]:
        """获取插件"""
        if name not in self.plugins:
            return None
        if not self.enabled.get(name, True):
            logger.warning(f"Plugin {name} is disabled")
            return None
        return self.plugins[name]
    
    def enable_plugin(self, name: str) -> bool:
        """启用插件"""
        if name not in self.plugins:
            return False
        self.enabled[name] = True
        return True
    
    def disable_plugin(self, name: str) -> bool:
        """禁用插件"""
        if name not in self.plugins:
            return False
        self.enabled[name] = False
        return True
    
    def load_plugin_from_path(self, path: str) -> bool:
        """从文件路径加载插件"""
        path = Path(path)
        if not path.exists():
            logger.error(f"Plugin path does not exist: {path}")
            return False
        
        # 添加到路径
        sys.path.insert(0, str(path.parent))
        
        try:
            module = importlib.import_module(path.stem)
            
            # 查找插件类
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (
                    isinstance(attr, type) 
                    and issubclass(attr, PluginBase) 
                    and attr != PluginBase
                ):
                    plugin = attr()
                    return self.register_plugin(plugin)
            
            logger.error(f"No PluginBase subclass found in {path}")
            return False
            
        except Exception as e:
            logger.error(f"Failed to load plugin from {path}: {e}")
            return False
    
    def load_plugins_from_directory(self, dir_path: str) -> int:
        """从目录批量加载插件"""
        loaded = 0
        dir_path = Path(dir_path)
        
        if not dir_path.exists():
            logger.warning(f"Plugin directory {dir_path} does not exist")
            return 0
        
        for file in dir_path.glob("*.py"):
            if file.name.startswith("_"):
                continue
            if self.load_plugin_from_path(str(file)):
                loaded += 1
        
        logger.info(f"Loaded {loaded} plugins from {dir_path}")
        return loaded
    
    def load_builtin_plugins(self) -> int:
        """加载内置插件"""
        builtin_dir = Path(__file__).parent / "builtin"
        return self.load_plugins_from_directory(str(builtin_dir))
    
    def list_plugins(self) -> List[Dict[str, Any]]:
        """列出所有插件"""
        result = []
        for name, plugin in self.plugins.items():
            result.append({
                "name": name,
                "description": plugin.description,
                "version": plugin.version,
                "enabled": self.enabled.get(name, True)
            })
        return result
    
    def execute_plugin(self, name: str, parameters: Dict[str, Any], **kwargs) -> PluginResult:
        """执行插件"""
        plugin = self.get_plugin(name)
        if plugin is None:
            return PluginResult(
                success=False,
                error=f"Plugin not found or disabled: {name}"
            )
        
        if not plugin.validate_parameters(parameters):
            return PluginResult(
                success=False,
                error=f"Parameter validation failed for {name}"
            )
        
        try:
            return plugin.execute(parameters, **kwargs)
        except Exception as e:
            logger.error(f"Plugin {name} execution failed: {e}")
            return PluginResult(
                success=False,
                error=str(e)
            )
