# Custom MCP Demo - macOS

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

```python
ALLOWED_BINARIES = {"ls", "pwd", "whoami", "date", "uptime", "open", "say"}

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

```python
@mcp.tool()
def open_application(app_name: str) -> dict:
    result = _run_subprocess(["open", "-a", app_name])
    return {"ok": result["exit_code"] == 0, "app_name": app_name, **result}
```

```python
@mcp.tool()
def lock_screen() -> dict:
    script = 'tell application "System Events" to keystroke "q" using {control down, command down}'
    result = _run_subprocess(["osascript", "-e", script])
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