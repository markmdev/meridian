"""
claude_runner — shared module for claude -p subprocess invocations.

Self-contained, no external dependencies. Provides environment isolation,
CLI argument construction, subprocess execution, stream-json parsing,
and prompt template loading.
"""

import json
import os
import subprocess
from pathlib import Path


def build_env(headless_key: str = "MERIDIAN_HEADLESS") -> dict:
    """Build an isolated environment for claude -p subprocesses.

    Sets the headless guard key so hooks exit immediately in the subprocess,
    and removes CLAUDECODE and CLAUDE_CODE_ENTRYPOINT to avoid session
    interference with the parent Claude Code process.
    """
    env = os.environ.copy()
    env[headless_key] = "1"
    env.pop("CLAUDECODE", None)
    env.pop("CLAUDE_CODE_ENTRYPOINT", None)
    return env


def build_args(
    model: str = "claude-opus-4-6",
    output_format: str | None = "stream-json",
    allowed_tools: str | None = "Write,Read,Edit",
    system_prompt: str | None = None,
    skip_permissions: bool = True,
    no_session_persistence: bool = True,
    setting_sources: str | None = "user",
    verbose: bool = True,
    extra_args: list[str] | None = None,
) -> list[str]:
    """Construct the CLI argument list for claude -p.

    All parameters are optional with sensible defaults matching the session-learner
    pattern. Callers override what they need.
    """
    args = ["claude", "-p", "--model", model]

    if output_format:
        args.extend(["--output-format", output_format])
    if verbose:
        args.append("--verbose")
    if allowed_tools:
        args.extend(["--allowedTools", allowed_tools])
    if system_prompt:
        args.extend(["--system-prompt", system_prompt])
    if skip_permissions:
        args.append("--dangerously-skip-permissions")
    if no_session_persistence:
        args.append("--no-session-persistence")
    if setting_sources:
        args.extend(["--setting-sources", setting_sources])
    if extra_args:
        args.extend(extra_args)

    return args


def run(
    prompt: str,
    args: list[str] | None = None,
    env: dict | None = None,
    cwd: str | None = None,
    timeout: int = 180,
) -> dict:
    """Execute claude -p and return the result.

    Returns: {"success": bool, "exit_code": int, "stdout": str, "stderr": str}
    """
    if args is None:
        args = build_args()
    if env is None:
        env = build_env()

    result = {
        "success": False,
        "exit_code": -1,
        "stdout": "",
        "stderr": "",
    }

    try:
        proc = subprocess.run(
            args,
            input=prompt,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=cwd,
            env=env,
        )
        result["exit_code"] = proc.returncode
        result["stdout"] = proc.stdout or ""
        result["stderr"] = proc.stderr or ""
        result["success"] = proc.returncode == 0
    except subprocess.TimeoutExpired:
        result["exit_code"] = -2
        result["stderr"] = f"Timed out after {timeout}s"
    except FileNotFoundError:
        result["exit_code"] = -3
        result["stderr"] = "claude CLI not found"
    except BrokenPipeError as e:
        result["exit_code"] = -4
        result["stderr"] = f"BrokenPipeError: {e}"
    except OSError as e:
        result["exit_code"] = -5
        result["stderr"] = f"OSError: {e}"

    return result


def parse_stream_json(stdout: str) -> tuple[list[dict], str]:
    """Parse stream-json output into (tools_used, text_output).

    tools_used: list of {"tool": "Write", "file": "/path/to/file"}
    text_output: the final result text from the "result" entry
    """
    tools_used = []
    result_text = ""

    for line in stdout.strip().split("\n"):
        if not line.strip():
            continue
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue

        # Collect tool usage from assistant messages
        msg = entry.get("message", {})
        content = msg.get("content", [])
        if isinstance(content, list):
            for block in content:
                if block.get("type") == "tool_use":
                    tool_entry = {"tool": block.get("name", "unknown")}
                    input_data = block.get("input", {})
                    file_path = (
                        input_data.get("file_path")
                        or input_data.get("path")
                        or ""
                    )
                    if file_path:
                        tool_entry["file"] = file_path
                    tools_used.append(tool_entry)

        # The result entry contains the final response text
        if entry.get("type") == "result":
            r = entry.get("result", "")
            if r and isinstance(r, str):
                result_text = r

    return tools_used, result_text


def load_template(path: str | Path, **variables: str) -> str:
    """Read a .md template file and substitute {{variable}} placeholders.

    Usage:
        prompt = load_template("prompts/agent.md", transcript=text, workspace=ws)
    """
    content = Path(path).read_text()
    for key, value in variables.items():
        content = content.replace("{{" + key + "}}", value)
    return content
