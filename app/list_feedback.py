"""Print newest thumbs-down notes from the usage table.

  python -m app.list_feedback
  python -m app.list_feedback --limit 20
"""

from __future__ import annotations

import argparse
import sys

from app.catalog import repo_root_from
from app.config import load_settings
from app.feedback import FeedbackError, format_feedback, list_feedback


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="List thumbs-down chat feedback.")
    parser.add_argument("--limit", type=int, default=50, help="How many notes to print")
    args = parser.parse_args(argv)
    settings = load_settings(str(repo_root_from()))
    try:
        items = list_feedback(settings, args.limit)
    except FeedbackError as error:
        print(error.message, file=sys.stderr)
        return 1
    print(format_feedback(items))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
