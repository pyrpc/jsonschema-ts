from __future__ import annotations

import atexit
import json
import os
import subprocess
import threading
from pathlib import Path

from jsonschema_ts._errors import ConversionError

_CACHE_DIR = Path.home() / ".jsonschema-ts"

_DAEMON: _NPXDaemon | None = None
_LOCK = threading.Lock()


def convert(schema: dict, options: dict | None = None) -> str:
    global _DAEMON
    with _LOCK:
        if _DAEMON is None:
            _DAEMON = _NPXDaemon()
        return _DAEMON.convert(schema, options or {})


def stop() -> None:
    global _DAEMON
    with _LOCK:
        if _DAEMON is not None:
            _DAEMON.stop()
            _DAEMON = None


class _NPXDaemon:
    def __init__(self) -> None:
        self._process: subprocess.Popen | None = None
        self._lock = threading.Lock()
        atexit.register(self.stop)

    def _ensure_package(self) -> str | None:
        npm = "npm.cmd" if os.name == "nt" else "npm"
        node_modules = _CACHE_DIR / "node_modules"
        pkg_dir = node_modules / "json-schema-to-typescript"
        if pkg_dir.is_dir():
            return str(node_modules)
        _CACHE_DIR.mkdir(parents=True, exist_ok=True)
        try:
            subprocess.run(
                [
                    npm, "install", "--prefix",
                    str(_CACHE_DIR), "json-schema-to-typescript",
                ],
                check=True,
                capture_output=True,
                timeout=60,
            )
        except Exception:
            return None
        return str(node_modules) if pkg_dir.is_dir() else None

    def start(self) -> None:
        if self._process is not None and self._process.poll() is None:
            return
        script_dir = os.path.dirname(os.path.abspath(__file__))
        script_path = os.path.join(script_dir, "_npx_daemon.js")
        env = os.environ.copy()
        node_path = self._ensure_package()
        if node_path is not None:
            env["JSONSCHEMA_TS_CACHE"] = node_path
        self._process = subprocess.Popen(
            ["node", script_path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env,
        )

    def convert(self, schema: dict, options: dict) -> str:
        with self._lock:
            self.start()
            msg = json.dumps({"schema": schema, "options": options})
            proc = self._process
            if proc is None or proc.stdin is None or proc.stdout is None:
                raise ConnectionError("Daemon process not available")
            proc.stdin.write(msg + "\n")
            proc.stdin.flush()
            line = proc.stdout.readline()
            if not line:
                raise ConnectionError("Daemon closed connection unexpectedly")
            result = json.loads(line.strip())
            if result.get("success"):
                return str(result["data"])
            raise ConversionError(result.get("error", "Unknown error from daemon"))

    def stop(self) -> None:
        with self._lock:
            proc = self._process
            if proc is not None and proc.poll() is None:
                if os.name == "nt":
                    proc.terminate()
                else:
                    proc.terminate()
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    proc.wait(timeout=5)
            self._process = None
