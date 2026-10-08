"""Start one skill program and collect its printed result."""

from __future__ import annotations

import ast
import json
import os
import shutil
import subprocess
import uuid
from dataclasses import dataclass, field
from pathlib import Path

from app.catalog import Flag, Tool, is_output_option


@dataclass
class RunResult:
    exit_code: int
    text: str
    missing_input: bool
    files: list[Path] = field(default_factory=list)
    job_dir: Path | None = None


def _argument_value(arguments: dict[str, object], flag: Flag) -> object:
    for key in (flag.dest, flag.cli_name):
        if key in arguments:
            return arguments[key]
    return None


def _jsonable(value: object) -> object:
    dump = getattr(value, "model_dump", None)
    if callable(dump):
        return dump()
    if isinstance(value, list | tuple):
        return [_jsonable(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    return value


def _cli_text(raw: object) -> str:
    """Lists and objects become JSON so a native bank schedule stays valid."""
    if isinstance(raw, list | tuple | dict) or callable(getattr(raw, "model_dump", None)):
        return json.dumps(_jsonable(raw), separators=(",", ":"))
    return str(raw)


def _coerce(flag: Flag, raw: object) -> list[str]:
    if raw is None or raw is False:
        return []
    if flag.type_name == "bool":
        return [flag.option] if raw else []
    if flag.repeat:
        values = raw if isinstance(raw, list) else [raw]
        args: list[str] = []
        for value in values:
            args.extend([flag.option, _cli_text(value)])
        return args
    return [flag.option, _cli_text(raw)]


# Stdout keys whose values are downloadable result files (PNG, HTML, tables).
ARTIFACT_PREFIXES = (
    "graph:",
    "viewer:",
    "coefficients_graph:",
    "polar_graph:",
    "ordinates:",
    "table:",
)


def _artifact_prefix(line: str) -> str | None:
    for prefix in ARTIFACT_PREFIXES:
        if line.startswith(prefix):
            return prefix
    return None


def _rewrite_paths(stdout: str, job_dir: Path, cwd: Path) -> tuple[str, list[Path]]:
    lines: list[str] = []
    files: list[Path] = []
    for line in stdout.splitlines():
        prefix = _artifact_prefix(line)
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


def _given(arguments: dict[str, object], name: str) -> bool:
    value = arguments.get(name)
    return value is not None and value is not False


def _point_run_rejects_plot(help_text: str, arguments: dict[str, object]) -> bool:
    """A single altitude or delta-v point rejects a sweep plot path."""
    if "sweep" not in help_text.lower():
        return False
    if _given(arguments, "alt") and not _given(arguments, "alt_min") and not _given(arguments, "alt_max"):
        return True
    return _given(arguments, "dv") or _given(arguments, "payload")


def _instantaneous_run_rejects_plot(help_text: str, arguments: dict[str, object]) -> bool:
    """Mode 1 proportional navigation has no engagement figure."""
    if "engagement" not in help_text.lower():
        return False
    mode2 = _given(arguments, "range") or _given(arguments, "los_angle")
    mode1 = _given(arguments, "vc") or _given(arguments, "los_rate")
    return mode1 and not mode2


def _radial_doppler_rejects_plot(help_text: str, arguments: dict[str, object]) -> bool:
    """Radial Doppler close has no elevation-mask figure."""
    if "orbit path" not in help_text.lower():
        return False
    radial = _given(arguments, "v_radial")
    orbit = (
        _given(arguments, "alt")
        or _given(arguments, "a")
        or _given(arguments, "elev_min")
    )
    return radial and not orbit


def _omit_unrequested_plot(tool_name: str, option: str, arguments: dict[str, object]) -> bool:
    """lifting_entry_trajectory writes a PNG only when out is passed."""
    return tool_name == "lifting_entry_trajectory" and option == "--out" and not _given(arguments, "out")


def _skips_injected_plot(help_text: str, arguments: dict[str, object]) -> bool:
    return (
        _point_run_rejects_plot(help_text, arguments)
        or _instantaneous_run_rejects_plot(help_text, arguments)
        or _radial_doppler_rejects_plot(help_text, arguments)
    )


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
        if not isinstance(option, str) or not is_output_option(option):
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
    elif "png" in lowered:
        suffix = ".png"
    elif "html" in lowered:
        suffix = ".html"
    elif "table" in lowered or "ordinate" in lowered or "text" in lowered:
        suffix = ".txt"
    else:
        suffix = ".png"
    return job_dir / f"{stem}{suffix}"


def result_root_for(repo_root: Path) -> Path:
    """Directory a run may create. Lambda mounts /var/task read-only."""
    if os.environ.get("AWS_LAMBDA_FUNCTION_NAME"):
        return Path("/tmp/aerospace-results")
    preferred = repo_root / "app" / "data" / "results"
    if _creatable(preferred):
        return preferred
    return Path(os.environ.get("TMPDIR", "/tmp")) / "aerospace-results"


def _creatable(path: Path) -> bool:
    current = path
    while not current.exists():
        parent = current.parent
        if parent == current:
            return False
        current = parent
    return current.is_dir() and os.access(current, os.W_OK)


def release_job(job_dir: Path | None) -> None:
    """Remove a scratch directory. Local result files stay for inspection."""
    if job_dir is None:
        return
    resolved = job_dir.resolve()
    roots = [
        Path(os.environ.get("TMPDIR", "/tmp")).resolve(),
        Path("/tmp/aerospace-results").resolve(),
    ]
    ephemeral = False
    for root in roots:
        try:
            resolved.relative_to(root)
        except ValueError:
            continue
        ephemeral = True
        break
    if ephemeral:
        shutil.rmtree(job_dir, ignore_errors=True)


def run_tool(
    tool: Tool,
    arguments: dict[str, object],
    *,
    repo_root: Path,
    timeout_sec: int = 60,
    result_root: Path | None = None,
) -> RunResult:
    job_dir = (result_root or result_root_for(repo_root)) / uuid.uuid4().hex
    job_dir.mkdir(parents=True, exist_ok=True)
    argv = [os.environ.get("PYTHON", "python"), str(tool.script)]
    for flag in tool.flags:
        argv.extend(_coerce(flag, _argument_value(arguments, flag)))
    for option, help_text in _output_flags(tool.script):
        if _omit_unrequested_plot(tool.name, option, arguments):
            continue
        if _skips_injected_plot(help_text, arguments):
            continue
        argv.extend([option, str(_output_path(job_dir, option, help_text))])
    env = os.environ.copy()
    env["MPLCONFIGDIR"] = str(job_dir / "mpl")
    (job_dir / "mpl").mkdir(exist_ok=True)
    try:
        completed = subprocess.run(
            argv,
            cwd=repo_root,
            capture_output=True,
            text=True,
            timeout=timeout_sec,
            env=env,
            shell=False,
        )
    except subprocess.TimeoutExpired:
        return RunResult(124, "the program timed out", False, [], job_dir)
    stdout = completed.stdout or ""
    stderr = completed.stderr or ""
    missing = completed.returncode != 0 and "missing" in stderr.lower()
    if completed.returncode != 0:
        detail = stderr.strip() or stdout.strip() or f"exit {completed.returncode}"
        return RunResult(completed.returncode, detail, missing, [], job_dir)
    text, files = _rewrite_paths(stdout.strip(), job_dir, repo_root)
    return RunResult(0, text, False, files, job_dir)
