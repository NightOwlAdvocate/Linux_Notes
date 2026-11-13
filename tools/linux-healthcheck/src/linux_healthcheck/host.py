"""Small host adapter that keeps system access mockable in tests."""

import os
import platform
import shutil
import subprocess
from pathlib import Path
from typing import List, Optional


class Host:
    """Read-only access to Linux files, metrics, and diagnostic commands."""

    def read_text(self, path: str) -> str:
        return Path(path).read_text(encoding="utf-8", errors="replace")

    def exists(self, path: str) -> bool:
        return Path(path).exists()

    def which(self, command: str) -> Optional[str]:
        return shutil.which(command)

    def run(self, command: List[str], timeout: int = 5) -> subprocess.CompletedProcess:
        return subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout,
        )

    def disk_usage(self, path: str):
        return shutil.disk_usage(path)

    def uname(self):
        return platform.uname()

    def load_average(self):
        return os.getloadavg()

    def cpu_count(self) -> int:
        return os.cpu_count() or 1
