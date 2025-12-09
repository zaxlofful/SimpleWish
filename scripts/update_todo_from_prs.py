#!/usr/bin/env python3
"""
Update TODO.md by removing items that have been completed via merged PRs.
This script looks for merged PRs with the todo-automation label and checks
if they reference specific TODO items that can be removed.
"""

import json
import re
import subprocess
import sys
from pathlib import Path


def get_merged_prs():
    """Get list of merged PRs with todo-automation label."""
    try:
        result = subprocess.run(
            [
                'gh', 'pr', 'list',
                '--state', 'merged',
                '--label', 'todo-automation',
                '--json', 'number,title,body,mergedAt',
                '--limit', '10'
            ],
            capture_output=True,
            text=True,
            check=True
        )
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Error fetching merged PRs: {e}")
        return []


def extract_completed_items(pr_body):
    """
    Extract completed TODO items from PR body.
    Looks for patterns like:
    - Fixed: <item>
    - Completed: <item>
    - Done: <item>
    Or markdown checkboxes that are checked: - [x] <item>
    """
    if not pr_body:
        return []

    completed = []

    # Pattern 1: Fixed/Completed/Done: <item>
    patterns = [
        r'(?:Fixed|Completed|Done|Resolved):\s*(.+)',
        r'-\s*\[x\]\s*(.+)',  # Checked markdown checkbox
    ]

    for pattern in patterns:
        matches = re.finditer(pattern, pr_body, re.IGNORECASE | re.MULTILINE)
        for match in matches:
            item = match.group(1).strip()
            if item:
                completed.append(item)

    return completed


def update_todo_file(todo_path, completed_items):
    """
    Remove completed items from TODO.md.
    Returns True if file was modified, False otherwise.
    """
    if not todo_path.exists():
        print("TODO.md not found")
        return False

    if not completed_items:
        print("No completed items to remove")
        return False

    try:
        content = todo_path.read_text(encoding='utf-8')
        lines = content.split('\n')
        modified_lines = []
        removed_count = 0

        for line in lines:
            should_keep = True
            line_stripped = line.strip()

            # Skip empty lines - always keep them
            if not line_stripped:
                modified_lines.append(line)
                continue

            # Check if this line matches any completed item
            for completed_item in completed_items:
                # Normalize both strings for comparison
                completed_normalized = completed_item.lower().strip()
                line_normalized = line_stripped.lower()

                # Remove markdown list markers and checkboxes for comparison
                # Pattern matches: bullets (-, *, +), numbered lists (1., 2.),
                # optional checkboxes ([x] or [ ]), with optional leading whitespace
                line_normalized = re.sub(
                    r'^\s*(?:[-*+]|\d+\.)\s*(?:\[[x ]\]\s*)?',
                    '',
                    line_normalized
                ).strip()

                # Check for substantial match using word-based comparison
                # to avoid false positives from simple substring matching
                completed_words = set(completed_normalized.split())
                line_words = set(line_normalized.split())

                # Match if completed item words are subset of line words,
                # or if there's exact equality
                exact_match = (completed_normalized == line_normalized)
                has_words = (completed_words and line_words)
                word_subset = has_words and completed_words.issubset(line_words)
                if exact_match or word_subset:
                    should_keep = False
                    removed_count += 1
                    print(f"Removing completed item: {line_stripped}")
                    break

            if should_keep:
                modified_lines.append(line)

        if removed_count > 0:
            new_content = '\n'.join(modified_lines)
            # Clean up multiple consecutive blank lines
            new_content = re.sub(r'\n{3,}', '\n\n', new_content)
            new_content = new_content.strip() + '\n' if new_content.strip() else ''

            todo_path.write_text(new_content, encoding='utf-8')
            print(f"Removed {removed_count} completed item(s) from TODO.md")
            return True
        else:
            print("No matching TODO items found to remove")
            return False

    except UnicodeDecodeError as e:
        print(f"Error reading TODO.md (encoding issue): {e}")
        return False
    except PermissionError as e:
        print(f"Error updating TODO.md (permission denied): {e}")
        return False
    except OSError as e:
        print(f"Error updating TODO.md (I/O error): {e}")
        return False


def main():
    """Main entry point."""
    repo_root = Path.cwd()
    todo_path = repo_root / "TODO.md"

    print("Fetching merged PRs with todo-automation label...")
    merged_prs = get_merged_prs()

    if not merged_prs:
        print("No merged TODO automation PRs found")
        sys.exit(0)

    print(f"Found {len(merged_prs)} merged PR(s)")

    # Collect all completed items from all merged PRs
    all_completed_items = []
    for pr in merged_prs:
        pr_number = pr.get('number')
        pr_title = pr.get('title')
        pr_body = pr.get('body', '')

        print(f"Processing PR #{pr_number}: {pr_title}")

        completed = extract_completed_items(pr_body)
        if completed:
            print(f"  Found {len(completed)} completed item(s)")
            all_completed_items.extend(completed)

    if all_completed_items:
        print(f"\nTotal completed items to remove: {len(all_completed_items)}")
        modified = update_todo_file(todo_path, all_completed_items)
        if modified:
            print("\nTODO.md has been updated")
            sys.exit(0)
        else:
            print("\nTODO.md was not modified")
            sys.exit(0)
    else:
        print("\nNo completed items found in merged PRs")
        sys.exit(0)


if __name__ == "__main__":
    main()
