#!/usr/bin/env python3
"""One-command installer for Personal Assistant.

Creates a virtual environment, installs dependencies, initializes .env,
and optionally launches the app.
"""

from __future__ import annotations

import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
VENV_DIR = ROOT / ".venv"
ENV_FILE = ROOT / ".env"
ENV_EXAMPLE = ROOT / ".env.example"


def run(cmd: list[str]) -> None:
    print("→", " ".join(cmd))
    subprocess.run(cmd, check=True)


def venv_python() -> Path:
    if platform.system() == "Windows":
        return VENV_DIR / "Scripts" / "python.exe"
    return VENV_DIR / "bin" / "python"


def ensure_python() -> None:
    if sys.version_info < (3, 10):
        raise SystemExit("Python 3.10+ is required.")


def create_venv() -> None:
    if not VENV_DIR.exists():
        run([sys.executable, "-m", "venv", str(VENV_DIR)])


def install_requirements() -> None:
    py = str(venv_python())
    run([py, "-m", "pip", "install", "--upgrade", "pip"])
    run([py, "-m", "pip", "install", "-r", str(ROOT / "requirements.txt")])


def initialize_env() -> None:
    if ENV_FILE.exists():
        return

    if ENV_EXAMPLE.exists():
        shutil.copy2(ENV_EXAMPLE, ENV_FILE)
    else:
        ENV_FILE.write_text("OPENAI_API_KEY=\n", encoding="utf-8")

    print(f"Created {ENV_FILE.name}. Add your OPENAI_API_KEY when ready.")


def launch() -> None:
    py = str(venv_python())
    run([py, "-m", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"])


def main() -> None:
    os.chdir(ROOT)
    ensure_python()
    create_venv()
    install_requirements()
    initialize_env()
    print("\nSetup complete.")
    answer = input("Launch now? [Y/n]: ").strip().lower()
    if answer in {"", "y", "yes"}:
        launch()
    else:
        if platform.system() == "Windows":
            print(r"Run later with: .venv\Scripts\python.exe -m uvicorn app:app --host 0.0.0.0 --port 8000")
        else:
            print("Run later with: .venv/bin/python -m uvicorn app:app --host 0.0.0.0 --port 8000")


if __name__ == "__main__":
    main()
