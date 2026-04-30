from pathlib import Path
import platform
import shutil
import subprocess
import sys

APP_NAME = "PersonalAssistant"
ENTRYPOINT = "desktop_app.py"


def run(command: list[str]) -> None:
    print("+", " ".join(command))
    subprocess.run(command, check=True)


def ensure_tooling() -> None:
    missing = []
    for cmd in ("pyinstaller",):
        if shutil.which(cmd) is None:
            missing.append(cmd)
    if missing:
        raise RuntimeError(
            "Missing required build tools: " + ", ".join(missing) + ". "
            "Install dependencies with: pip install -r requirements.txt"
        )


def build() -> Path:
    ensure_tooling()
    run([
        "pyinstaller",
        "--noconfirm",
        "--clean",
        "--onefile",
        "--windowed",
        "--name",
        APP_NAME,
        ENTRYPOINT,
    ])

    suffix = ".exe" if platform.system() == "Windows" else ""
    artifact = Path("dist") / f"{APP_NAME}{suffix}"
    if not artifact.exists():
        raise RuntimeError(f"Build completed but artifact was not found: {artifact}")
    return artifact


def main() -> int:
    try:
        artifact = build()
    except Exception as exc:  # pragma: no cover - build helper
        print(f"Build failed: {exc}")
        return 1

    print("\nDesktop build complete.")
    print(f"Artifact: {artifact.resolve()}")
    if platform.system() == "Windows":
        print(
            "Next step: compile installer.iss with Inno Setup to generate a distributable installer EXE."
        )
    else:
        print(
            "You can distribute this binary directly or wrap it with your platform's installer tooling."
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
