# Custom MCP Demo

# MCP

MCP (Model Context Protocol) is an open standard introduced by Anthropic in 2024. It gives AI clients a common way to call tools from external programs.

- The client sends a tool request.
- MCP server runs the mapped tool logic.
- The result comes back in a structured format.

## MCP in software development

- Build tools once and reuse them across MCP-compatible clients.
- Connect AI to real developer actions (APIs, scripts, files, local utilities).
- Enable AI automation workflows (for example: analyze logs -> run a script -> post a status update).
- Keep tool code in your repo, versioned with your app.
- Add new capabilities fast by creating new `@mcp.tool()` functions.

## Popular MCP servers

- `filesystem` (Anthropic): lets AI read, write, and browse local/project files.
- `github` (GitHub): lets AI work with repos, issues, PRs, and code context.
- `fetch` (Anthropic): lets AI pull and parse content from URLs/APIs.
- `postgres` (Anthropic): lets AI run SQL queries on Postgres databases.
- `sqlite` (Anthropic): lets AI query and update local SQLite databases.
- `playwright` (Microsoft): lets AI automate browser actions and UI testing.
- `vercel` (Vercel): lets AI inspect projects, deployments, logs, and environment context.
- `slack` (Slack): lets AI send messages and trigger Slack workflows.
- `memory` (Anthropic): lets AI store and retrieve persistent context across sessions.

## Custom MCP server (step by step)

Why people build custom MCP servers:

- **Automate repetitive workflows:** run your exact multi-step process (not generic tool flows).
- **Connect internal systems:** expose private APIs, scripts, and databases you actually use.
- **Add safety/control:** whitelist commands, enforce permissions, and keep audits in one place.
- **Match your stack:** shape tool inputs/outputs to your project conventions for better AI reliability.

### 1) Create a Python project with MCP

```toml
[project]
name = "custom-mcp"
version = "0.1.0"
description = "A local MCP server for safe laptop control actions."
readme = "README.md"
requires-python = ">=3.10"
dependencies = [
  "mcp>=1.0.0",
]

[build-system]
requires = ["setuptools>=68.0"]
build-backend = "setuptools.build_meta"
```

Install:

```bash
python3 -m pip install -e .
```

### 2) Initialize the server in `custom-mcp.py`

```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("custom-mcp-server")
```

### 3) Add tools with `@mcp.tool()`

Each decorated function becomes callable from any MCP-compatible client.

`system_info`: Returns OS and machine metadata for quick diagnostics.

```python
@mcp.tool()
def system_info() -> dict:
    return {
        "platform": platform.platform(),
        "system": platform.system(),
        "release": platform.release(),
        "version": platform.version(),
        "machine": platform.machine(),
        "processor": platform.processor(),
    }
```

`list_directory`: Validates a path and lists directory entries in sorted order.

```python
@mcp.tool()
def list_directory(path: str = ".") -> dict:
    p = Path(path).expanduser().resolve()
    if not p.exists():
        return {"ok": False, "error": f"Path does not exist: {p}"}
    if not p.is_dir():
        return {"ok": False, "error": f"Not a directory: {p}"}

    entries = sorted(item.name for item in p.iterdir())
    return {"ok": True, "path": str(p), "entries": entries}
```

`run_safe_shell`: Runs only commands from an OS-aware allowlist for safer execution.

```python
SYSTEM_NAME = platform.system()

COMMON_ALLOWED_BINARIES = {"python", "python3", "whoami"}
OS_ALLOWED_BINARIES = {
    "Darwin": {"ls", "pwd", "date", "uptime", "open", "say"},
    "Linux": {"ls", "pwd", "date", "uptime", "xdg-open"},
    "Windows": {"cmd", "powershell", "whoami"},
}
ALLOWED_BINARIES = COMMON_ALLOWED_BINARIES | OS_ALLOWED_BINARIES.get(SYSTEM_NAME, set())

@mcp.tool()
def run_safe_shell(command: str) -> dict:
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
    return {"ok": True, "command": command, **result}
```

`open_application`: Opens an app or file using native commands on each OS.

```python
@mcp.tool()
def open_application(app_name: str) -> dict:
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
```

`lock_screen`: Locks the current session using platform-specific commands.

```python
@mcp.tool()
def lock_screen() -> dict:
    if SYSTEM_NAME == "Darwin":
        script = 'tell application "System Events" to keystroke "q" using {control down, command down}'
        cmd = ["osascript", "-e", script]
    elif SYSTEM_NAME == "Linux":
        cmd = ["loginctl", "lock-session"]
    elif SYSTEM_NAME == "Windows":
        cmd = ["rundll32.exe", "user32.dll,LockWorkStation"]
    else:
        return {"ok": False, "error": f"Unsupported OS: {SYSTEM_NAME}"}

    result = _run_subprocess(cmd)
    return {"ok": result["exit_code"] == 0, **result}
```

### 4) Run the server

```python
if __name__ == "__main__":
    mcp.run()
```

### 5) Connect your MCP client to the server

Every MCP-compatible IDE or chat client has its own config format, but the core server launch settings are the same:

- command: `python3`
- args: path to `custom-mcp.py` (absolute path recommended)

Cursor example (`.cursor/mcp.json`):

```json
{
  "mcpServers": {
    "mcp-server": {
      "command": "python3",
      "args": [
        "./custom-mcp.py"
      ]
    }
  }
}
```

### 6) Reload MCP servers in your client

Restart MCP servers (or reload the window). Your client should discover these tools automatically.

## References

- [Model Context Protocol (Official Docs)](https://modelcontextprotocol.io/)
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- [Cursor MCP Documentation](https://docs.cursor.com/context/model-context-protocol)
- [Playwright MCP Server](https://github.com/microsoft/playwright-mcp)
- [This Demo Repository](https://github.com/uvniche/custom-mcp-demo.git)

