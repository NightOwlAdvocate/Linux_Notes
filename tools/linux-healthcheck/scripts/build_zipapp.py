"""Build a single-file zipapp without third-party tools."""

import shutil
import tempfile
import zipapp
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parents[1]
SOURCE_DIR = PROJECT_DIR / "src"
OUTPUT = PROJECT_DIR / "dist" / "linux-healthcheck.pyz"


def main() -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as temp_dir:
        staging = Path(temp_dir)
        shutil.copytree(SOURCE_DIR / "linux_healthcheck", staging / "linux_healthcheck")
        (staging / "__main__.py").write_text(
            "from linux_healthcheck.cli import main\nraise SystemExit(main())\n",
            encoding="utf-8",
        )
        zipapp.create_archive(
            staging,
            target=OUTPUT,
            interpreter="/usr/bin/env python3",
            compressed=True,
        )
    print(OUTPUT)


if __name__ == "__main__":
    main()
