"""
Docker Sandbox - Docker 隔离沙箱

DeerFlow 启发，每个任务独立容器，安全隔离。
"""

import logging
import os
import time
from typing import Any, Optional

import docker

from .sandbox_base import Sandbox, SandboxResult

logger = logging.getLogger(__name__)


class DockerSandbox(Sandbox):
    """Docker 隔离沙箱"""

    def __init__(self, config: dict[str, Any]):
        self.image = config.get("image", "python:3.11-slim")
        self.working_dir = config.get("working_dir", "/mnt/workspace")
        self.client = docker.from_env()
        self.container = None
        self._ensure_image()

    def _ensure_image(self):
        """确保镜像存在"""
        try:
            self.client.images.get(self.image)
        except docker.errors.ImageNotFound:
            logger.info(f"Pulling docker image: {self.image}")
            self.client.images.pull(self.image)

    def _start_container(self):
        """启动容器"""
        if self.container is None or not self.is_alive():
            logger.info(f"Starting container from image: {self.image}")
            self.container = self.client.containers.run(
                self.image,
                command="tail -f /dev/null",  # 保持容器运行
                working_dir=self.working_dir,
                detach=True,
                volumes={},
                network_mode="bridge",
            )
            logger.info(f"Container started: {self.container.id[:12]}")

    def is_alive(self) -> bool:
        """检查容器是否活跃"""
        if self.container is None:
            return False
        try:
            self.container.reload()
            return self.container.status == "running"
        except Exception:
            return False

    def execute(
        self, command: str, working_dir: Optional[str] = None, timeout: int = 300
    ) -> SandboxResult:
        """在容器中执行命令"""
        start_time = time.time()
        self._start_container()

        cwd = working_dir if working_dir else self.working_dir
        full_command = f"cd {cwd} && {command}"

        try:
            exit_code, output = self.container.exec_run(full_command, workdir=cwd, timeout=timeout)

            duration = int((time.time() - start_time) * 1000)

            output_str = output.decode("utf-8", errors="replace")

            return SandboxResult(
                success=exit_code == 0,
                output=output_str,
                exit_code=exit_code,
                error="" if exit_code == 0 else output_str,
                duration_ms=duration,
            )

        except Exception as e:
            duration = int((time.time() - start_time) * 1000)
            return SandboxResult(
                success=False, output="", exit_code=-1, error=str(e), duration_ms=duration
            )

    def write_file(self, path: str, content: str) -> bool:
        """写入文件到容器"""
        self._start_container()

        try:
            # 使用 echo 写入，简单可靠
            content_escaped = content.replace("'", "\\'")
            command = f"mkdir -p $(dirname '{path}') && echo '{content_escaped}' > '{path}'"
            result = self.container.exec_run(command, workdir=self.working_dir)
            return result.exit_code == 0
        except Exception as e:
            logger.error(f"Failed to write file {path}: {e}")
            return False

    def read_file(self, path: str) -> Optional[str]:
        """从容器读取文件"""
        self._start_container()

        try:
            os.path.join(self.working_dir, path)
            result = self.container.exec_run(f"cat '{path}'", workdir=self.working_dir)
            if result.exit_code == 0:
                return result.output.decode("utf-8", errors="replace")
            return None
        except Exception as e:
            logger.error(f"Failed to read file {path}: {e}")
            return None

    def cleanup(self) -> None:
        """清理容器"""
        if self.container is not None:
            try:
                logger.info(f"Cleaning up container {self.container.id[:12]}")
                self.container.stop(timeout=10)
                self.container.remove()
            except Exception as e:
                logger.warning(f"Failed to cleanup container: {e}")
            self.container = None
