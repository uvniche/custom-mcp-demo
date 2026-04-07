from __future__ import annotations

import platform
import shlex
import subprocess
from pathlib import Path

from mcp.server.fastmcp import FastMCP


mcp = FastMCP("custom-mcp-server")


SYSTEM_NAME = platform.system()

# Keep command execution constrained to explicit, low-risk binaries.
COMMON_ALLOWED_BINARIES = {
    "python",
    "python3",
    "whoami",
}
OS_ALLOWED_BINARIES = {
    "Darwin": {"ls", "pwd", "date", "uptime", "open", "say"},
    "Linux": {"ls", "pwd", "date", "uptime", "xdg-open"},
    "Windows": {"cmd", "powershell", "whoami"},
}
ALLOWED_BINARIES = COMMON_ALLOWED_BINARIES | OS_ALLOWED_BINARIES.get(SYSTEM_NAME, set())


def _run_subprocess(command: list[str]) -> dict:
    completed = subprocess.run(
        command,
        capture_output=True,
        text=True,
        timeout=20,
        check=False,
    )
    return {
        "exit_code": completed.returncode,
        "stdout": completed.stdout.strip(),
        "stderr": completed.stderr.strip(),
    }


@mcp.tool()
def system_info() -> dict:
    """Return basic host information."""
    return {
        "platform": platform.platform(),
        "system": platform.system(),
        "release": platform.release(),
        "version": platform.version(),
        "machine": platform.machine(),
        "processor": platform.processor(),
    }


@mcp.tool()
def list_directory(path: str = ".") -> dict:
    """List files/directories for a given path."""
    p = Path(path).expanduser().resolve()
    if not p.exists():
        return {"ok": False, "error": f"Path does not exist: {p}"}
    if not p.is_dir():
        return {"ok": False, "error": f"Not a directory: {p}"}

    entries = sorted(item.name for item in p.iterdir())
    return {"ok": True, "path": str(p), "entries": entries}


@mcp.tool()
def run_safe_shell(command: str) -> dict:
    """Run a limited shell command from an allowlist of binaries."""
    parts = shlex.split(command)
    if not parts:
        return {"ok": False, "error": "Empty command"}

    binary = parts[0]
    if binary not in ALLOWED_BINARIES:
        return {
            "ok": False,
            "error": f"Binary '{binary}' is not allowed",
            "allowed_binaries": sorted(ALLOWED_BINARIES),
        }

    result = _run_subprocess(parts)
    return {"ok": True, "command": command, "system": SYSTEM_NAME, **result}


@mcp.tool()
def open_application(app_name: str) -> dict:
    """Open an application by name on macOS/Linux/Windows."""
    if SYSTEM_NAME == "Darwin":
        cmd = ["open", "-a", app_name]
    elif SYSTEM_NAME == "Linux":
        cmd = ["xdg-open", app_name]
    elif SYSTEM_NAME == "Windows":
        cmd = ["powershell", "-NoProfile", "-Command", f"Start-Process '{app_name}'"]
    else:
        return {"ok": False, "error": f"Unsupported OS: {SYSTEM_NAME}"}

    result = _run_subprocess(cmd)
    return {"ok": result["exit_code"] == 0, "app_name": app_name, **result}


@mcp.tool()
def lock_screen() -> dict:
    """Lock the screen on macOS/Linux/Windows."""
    if SYSTEM_NAME == "Darwin":
        # Uses AppleScript to trigger lock-screen shortcut.
        script = 'tell application "System Events" to keystroke "q" using {control down, command down}'
        cmd = ["osascript", "-e", script]
    elif SYSTEM_NAME == "Linux":
        # Common desktop environments expose loginctl lock-session.
        cmd = ["loginctl", "lock-session"]
    elif SYSTEM_NAME == "Windows":
        cmd = ["rundll32.exe", "user32.dll,LockWorkStation"]
    else:
        return {"ok": False, "error": f"Unsupported OS: {SYSTEM_NAME}"}

    result = _run_subprocess(cmd)
    return {"ok": result["exit_code"] == 0, "system": SYSTEM_NAME, **result}


if __name__ == "__main__":
    mcp.run()

