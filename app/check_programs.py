"""Run each catalog program's own --check. Not a user tool."""

from __future__ import annotations

import os
import subprocess
import sys

from app.catalog import load_catalog, repo_root_from


def main() -> int:
    root = repo_root_from()
    python = os.environ.get("PYTHON", "python")
    failed = 0
    for tool in load_catalog(root):
        text = tool.script.read_text(encoding="utf-8")
        if "--check" not in text:
            continue
        completed = subprocess.run(
            [python, str(tool.script), "--check"],
            cwd=root,
            capture_output=True,
            text=True,
            shell=False,
        )
        if completed.returncode == 0:
            print(f"pass {tool.name}")
            continue
        failed += 1
        detail = (completed.stderr or completed.stdout).strip()
        print(f"fail {tool.name}: {detail}", file=sys.stderr)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
