#!/usr/bin/env python3
"""
Check if TODO.md file is empty or contains only whitespace.
Exit code 0 if file is empty/blank, 1 if it contains content.
"""

import sys
from pathlib import Path


def is_todo_empty(todo_path: Path) -> bool:
    """
    Check if TODO.md is empty or contains only whitespace.

    Args:
        todo_path: Path to the TODO.md file

    Returns:
        True if file is empty or blank, False if it contains content
    """
    if not todo_path.exists():
        print(f"TODO.md not found at {todo_path}")
        return True

    content = todo_path.read_text(encoding='utf-8').strip()
    return len(content) == 0


def main():
    """Main entry point."""
    # Assuming script is run from repository root
    repo_root = Path.cwd()
    todo_path = repo_root / "TODO.md"

    is_empty = is_todo_empty(todo_path)

    if is_empty:
        print("TODO.md is empty or blank")
        sys.exit(0)
    else:
        print("TODO.md contains content")
        sys.exit(1)


if __name__ == "__main__":
    main()
