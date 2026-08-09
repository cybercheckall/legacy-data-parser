"""
dev.py - Development launcher with auto-restart on code changes.

Usage:
    python dev.py

Watches project *.py files (skips .venv / dist / build). When a file changes,
stops the running Owl process and starts a fresh one.
"""

from __future__ import annotations

import os
import signal
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
POLL_SECONDS = 0.6
RESTART_SETTLE_SECONDS = 0.35
SKIP_PARTS = {".venv", "venv", "dist", "build", "__pycache__", ".git"}


def _iter_py_files() -> list[Path]:
    files = []
    for path in ROOT.rglob("*.py"):
        if any(part in SKIP_PARTS for part in path.parts):
            continue
        files.append(path)
    return files


def _snapshot() -> dict[str, float]:
    snap = {}
    for path in _iter_py_files():
        try:
            snap[str(path)] = path.stat().st_mtime
        except OSError:
            continue
    return snap


def _start_app() -> subprocess.Popen:
    env = os.environ.copy()
    env["OWL_DEV_RELOAD"] = "1"
    print(f"[dev] starting Owl  ({sys.executable} main.py)", flush=True)
    return subprocess.Popen(
        [sys.executable, str(ROOT / "main.py")],
        cwd=str(ROOT),
        env=env,
    )


def _stop_app(proc: subprocess.Popen | None):
    if proc is None or proc.poll() is not None:
        return
    print("[dev] restarting — code changed", flush=True)
    proc.send_signal(signal.SIGTERM)
    try:
        proc.wait(timeout=4)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait(timeout=2)
    time.sleep(RESTART_SETTLE_SECONDS)


def main() -> int:
    print("[dev] auto-reload on · edit any .py and Owl will restart", flush=True)
    print("[dev] Ctrl+C to stop", flush=True)

    mtimes = _snapshot()
    proc = _start_app()

    try:
        while True:
            time.sleep(POLL_SECONDS)
            if proc.poll() is not None:
                code = proc.returncode
                print(f"[dev] Owl exited ({code}). Waiting for file changes…", flush=True)
                # Wait until something changes, then restart
                while True:
                    time.sleep(POLL_SECONDS)
                    now = _snapshot()
                    if now != mtimes:
                        mtimes = now
                        break
                proc = _start_app()
                continue

            now = _snapshot()
            if now != mtimes:
                mtimes = now
                _stop_app(proc)
                proc = _start_app()
    except KeyboardInterrupt:
        print("\n[dev] stopping", flush=True)
        _stop_app(proc)
        return 0


if __name__ == "__main__":
    sys.exit(main())
