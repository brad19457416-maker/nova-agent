"""
Local Sandbox - 本地执行沙箱

用于开发测试，直接在本地执行命令。
注意：生产环境推荐使用 DockerSandbox 隔离。
"""

import logging
import os
import subprocess
import time
from typing import Any, Dict, Optional

from .sandbox_base import Sandbox, SandboxResult

logger = logging.getLogger(__name__)


class LocalSandbox(Sandbox):
    """本地执行沙箱"""

    def __init__(self, config: Dict[str, Any]):
        self.workdir = config.get("workdir", "/tmp/nova-agent-local")
        os.makedirs(self.workdir, exist_ok=True)

    def execute(
        self, command: str, working_dir: Optional[str] = None, timeout: int = 300
    ) -> SandboxResult:
        """在本地执行命令"""
        start_time = time.time()
        cwd = working_dir if working_dir else self.workdir

        try:
            result = subprocess.run(
                command, shell=True, cwd=cwd, capture_output=True, text=True, timeout=timeout
            )

            duration = int((time.time() - start_time) * 1000)

            return SandboxResult(
                success=result.returncode == 0,
                output=result.stdout,
                exit_code=result.returncode,
                error=result.stderr,
                duration_ms=duration,
            )

        except subprocess.TimeoutExpired:
            duration = int((time.time() - start_time) * 1000)
            return SandboxResult(
                success=False,
                output="",
                exit_code=-1,
                error=f"Timeout after {timeout} seconds",
                duration_ms=duration,
            )
        except Exception as e:
            duration = int((time.time() - start_time) * 1000)
            return SandboxResult(
                success=False, output="", exit_code=-1, error=str(e), duration_ms=duration
            )

    def write_file(self, path: str, content: str) -> bool:
        """写入文件"""
        full_path = os.path.join(self.workdir, path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        try:
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(content)
            return True
        except Exception as e:
            logger.error(f"Failed to write file {path}: {e}")
            return False

    def read_file(self, path: str) -> Optional[str]:
        """读取文件"""
        full_path = os.path.join(self.workdir, path)
        try:
            with open(full_path, encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            logger.error(f"Failed to read file {path}: {e}")
            return None

    def file_exists(self, path: str) -> bool:
        """检查文件是否存在"""
        full_path = os.path.join(self.workdir, path)
        return os.path.exists(full_path)

    def list_files(self, path: str = "") -> list[str]:
        """列出目录文件"""
        full_path = os.path.join(self.workdir, path)
        if not os.path.exists(full_path):
            return []
        return os.listdir(full_path)

    def cleanup(self) -> None:
        """清理（本地沙箱默认不清理，保持文件供调试"""
        pass

    def get_full_path(self, path: str) -> str:
        """获取完整路径"""
        return os.path.join(self.workdir, path)
