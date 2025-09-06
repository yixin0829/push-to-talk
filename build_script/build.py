#!/usr/bin/env python3
import argparse
import os
import platform
import subprocess
import sys
from pathlib import Path


def run_command(command: list[str], cwd: Path | None = None) -> int:
    process = subprocess.run(command, cwd=cwd, text=True)
    return process.returncode


def is_windows() -> bool:
    return platform.system() == "Windows"


def is_macos() -> bool:
    return platform.system() == "Darwin"


def is_linux() -> bool:
    return platform.system() == "Linux"


def build_windows(repo_root: Path) -> bool:
    print("Building for Windows...")
    # Invoke PyInstaller directly to avoid interactive pause in build.bat
    return (
        run_command(["uv", "run", "pyinstaller", "push_to_talk.spec"], cwd=repo_root)
        == 0
    )


def build_macos(repo_root: Path) -> bool:
    print("Building for macOS...")
    script = repo_root / "build_macos.sh"
    if not script.exists():
        print("build_macos.sh not found.")
        return False
    # Ensure executable bit (best-effort)
    try:
        mode = os.stat(script).st_mode
        os.chmod(script, mode | 0o111)
    except Exception:
        pass
    return run_command(["bash", str(script)], cwd=repo_root) == 0


def build_linux(repo_root: Path) -> bool:
    print("Building for Linux...")
    script = repo_root / "build_linux.sh"
    if not script.exists():
        print("build_linux.sh not found.")
        return False
    # Ensure executable bit (best-effort)
    try:
        mode = os.stat(script).st_mode
        os.chmod(script, mode | 0o111)
    except Exception:
        pass
    return run_command(["bash", str(script)], cwd=repo_root) == 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build PushToTalk for selected platforms using PyInstaller (via uv)."
    )
    parser.add_argument(
        "--platform",
        "-p",
        choices=["windows", "macos", "linux", "all"],
        default="all",
        help="Platform to build. Note: PyInstaller cannot cross-compile; you must build on each target OS.",
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent

    target = args.platform
    overall_success = True

    if target in ("windows", "all"):
        if is_windows():
            overall_success &= build_windows(repo_root)
        elif target == "windows":
            print(
                "Cannot build Windows executable on non-Windows host. Run this on Windows."
            )
            overall_success = False
        else:
            print("Skipping Windows build: not on Windows host.")

    if target in ("macos", "all"):
        if is_macos():
            overall_success &= build_macos(repo_root)
        elif target == "macos":
            print("Cannot build macOS executable on non-macOS host. Run this on macOS.")
            overall_success = False
        else:
            print("Skipping macOS build: not on macOS host.")

    if target in ("linux", "all"):
        if is_linux():
            overall_success &= build_linux(repo_root)
        elif target == "linux":
            print("Cannot build Linux executable on non-Linux host. Run this on Linux.")
            overall_success = False
        else:
            print("Skipping Linux build: not on Linux host.")

    if overall_success:
        print("Build(s) completed successfully.")
        return 0
    else:
        print("One or more builds failed.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
