"""
List Directory Plugin - 列出目录内容
"""

import os

from nova_agent.tools.plugin_base import PluginBase, PluginResult


class ListDirectoryPlugin(PluginBase):
    """列出目录内容"""

    name = "list_directory"
    description = "List contents of a directory"
    version = "0.1.0"
    parameters_schema = {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Directory path"},
            "recursive": {"type": "boolean", "description": "List recursively", "default": False},
        },
        "required": ["path"],
    }

    def execute(self, parameters: dict, **kwargs) -> PluginResult:
        path = parameters["path"]
        recursive = parameters.get("recursive", False)

        path = os.path.expanduser(path)

        if not os.path.exists(path):
            return PluginResult(success=False, error=f"Path not found: {path}")

        if not os.path.isdir(path):
            return PluginResult(success=False, error=f"Not a directory: {path}")

        try:
            result = self._list(path, recursive)
            return PluginResult(success=True, result=result)
        except Exception as e:
            return PluginResult(success=False, error=f"Failed to list directory: {str(e)}")

    def _list(self, path: str, recursive: bool) -> dict:
        items = []
        dirs = 0
        files = 0

        for entry in os.scandir(path):
            items.append(
                {
                    "name": entry.name,
                    "path": entry.path,
                    "is_dir": entry.is_dir(),
                    "size": entry.stat().st_size,
                }
            )

            if entry.is_dir():
                dirs += 1
            else:
                files += 1

        items.sort(key=lambda x: (not x["is_dir"], x["name"]))

        return {
            "path": path,
            "items": items,
            "total_dirs": dirs,
            "total_files": files,
            "total_items": dirs + files,
        }
