"""Start one skill program and collect its printed result."""

from __future__ import annotations

import ast
import os
import shutil
import subprocess
import uuid
from dataclasses import dataclass, field
from pathlib import Path

from app.catalog import Flag, Tool


@dataclass
class RunResult:
    exit_code: int
    text: str
    missing_input: bool
    files: list[Path] = field(default_factory=list)


def _coerce(flag: Flag, raw: object) -> list[str]:
    if raw is None or raw is False:
        return []
    if flag.type_name == "bool":
        return [flag.option] if raw else []
    if flag.repeat:
        values = raw if isinstance(raw, list) else [raw]
        args: list[str] = []
        for value in values:
            args.extend([flag.option, str(value)])
        return args
    return [flag.option, str(raw)]


def _rewrite_paths(stdout: str, job_dir: Path, cwd: Path) -> tuple[str, list[Path]]:
    lines: list[str] = []
    files: list[Path] = []
    for line in stdout.splitlines():
        prefix = ""
        if line.startswith("graph:"):
            prefix = "graph:"
        elif line.startswith("viewer:"):
            prefix = "viewer:"
        if not prefix:
            lines.append(line)
            continue
        raw = line.split(":", 1)[1].strip().strip('"')
        source = Path(raw)
        if not source.is_absolute():
            source = cwd / source
        if not source.is_file():
            lines.append(line)
            continue
        target = job_dir / source.name
        if source.resolve() != target.resolve():
            shutil.copy2(source, target)
        files.append(target)
        lines.append(f"{prefix} {target}")
    return "\n".join(lines), files


def _output_flags(script: Path) -> list[tuple[str, str]]:
    """Output-path flags are not user inputs. The runner fills them."""
    tree = ast.parse(script.read_text(encoding="utf-8"))
    found: list[tuple[str, str]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if not isinstance(func, ast.Attribute) or func.attr != "add_argument":
            continue
        if not node.args or not isinstance(node.args[0], ast.Constant):
            continue
        option = node.args[0].value
        if not isinstance(option, str) or not option.startswith("--out"):
            continue
        help_text = ""
        for keyword in node.keywords:
            if keyword.arg == "help" and isinstance(keyword.value, ast.Constant):
                if isinstance(keyword.value.value, str):
                    help_text = keyword.value.value
        found.append((option, help_text))
    return found


def _output_path(job_dir: Path, option: str, help_text: str) -> Path:
    lowered = help_text.lower()
    if "directory" in lowered:
        return job_dir
    stem = option[2:].replace("-", "_")
    if "pdf" in lowered:
        suffix = ".pdf"
    elif "html" in lowered:
        suffix = ".html"
    elif "table" in lowered or "ordinate" in lowered or "text" in lowered:
        suffix = ".txt"
    else:
        suffix = ".png"
    return job_dir / f"{stem}{suffix}"


def run_tool(
    tool: Tool,
    arguments: dict[str, object],
    *,
    repo_root: Path,
    timeout_sec: int = 60,
    result_root: Path | None = None,
) -> RunResult:
    job_dir = (result_root or repo_root / "app" / "data" / "results") / uuid.uuid4().hex
    job_dir.mkdir(parents=True, exist_ok=True)
    argv = [os.environ.get("PYTHON", "python"), str(tool.script)]
    for flag in tool.flags:
        argv.extend(_coerce(flag, arguments.get(flag.dest)))
    for option, help_text in _output_flags(tool.script):
        argv.extend([option, str(_output_path(job_dir, option, help_text))])
    env = os.environ.copy()
    env["MPLCONFIGDIR"] = str(job_dir / "mpl")
    (job_dir / "mpl").mkdir(exist_ok=True)
    completed = subprocess.run(
        argv,
        cwd=repo_root,
        capture_output=True,
        text=True,
        timeout=timeout_sec,
        env=env,
        shell=False,
    )
    stdout = completed.stdout or ""
    stderr = completed.stderr or ""
    missing = completed.returncode != 0 and "missing" in stderr.lower()
    if completed.returncode != 0:
        detail = stderr.strip() or stdout.strip() or f"exit {completed.returncode}"
        return RunResult(completed.returncode, detail, missing, [])
    text, files = _rewrite_paths(stdout.strip(), job_dir, repo_root)
    return RunResult(0, text, False, files)
