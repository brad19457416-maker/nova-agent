"""插件化工具系统"""

from .plugin_base import PluginBase, PluginResult
from .plugin_manager import PluginManager
from .registry import PluginRegistry

__all__ = [
    "PluginBase",
    "PluginResult",
    "PluginManager",
    "PluginRegistry"
]
