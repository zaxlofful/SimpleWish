"""Test update_todo_from_prs.py script."""
import tempfile
from pathlib import Path

from scripts.update_todo_from_prs import (
    extract_completed_items,
    update_todo_file,
)


def test_extract_completed_items_fixed_pattern():
    """Test extraction of items with 'Fixed:' pattern."""
    pr_body = """
    This PR fixes the following items:
    Fixed: Add coloring by CSS
    Fixed: Create transparent QR codes
    """
    items = extract_completed_items(pr_body)
    assert len(items) == 2
    assert 'Add coloring by CSS' in items
    assert 'Create transparent QR codes' in items


def test_extract_completed_items_checkbox_pattern():
    """Test extraction of checked markdown checkboxes."""
    pr_body = """
    Completed items:
    - [x] Implement feature A
    - [ ] Pending feature B
    - [x] Fix bug C
    """
    items = extract_completed_items(pr_body)
    assert len(items) == 2
    assert any('feature A' in item for item in items)
    assert any('bug C' in item for item in items)


def test_extract_completed_items_multiple_patterns():
    """Test extraction with multiple patterns."""
    pr_body = """
    Done: Complete task 1
    - [x] Complete task 2
    Completed: Finish task 3
    """
    items = extract_completed_items(pr_body)
    assert len(items) >= 3


def test_extract_completed_items_empty_body():
    """Test extraction with empty body."""
    items = extract_completed_items("")
    assert items == []


def test_extract_completed_items_none_body():
    """Test extraction with None body."""
    items = extract_completed_items(None)
    assert items == []


def test_update_todo_file_removes_matching_items():
    """Test that matching items are removed from TODO.md."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        todo_path = Path(f.name)

    try:
        # Create TODO.md with some items
        todo_content = """1. Coloring by CSS
2. Create transparent QR codes
3. Some other task
"""
        todo_path.write_text(todo_content, encoding='utf-8')

        completed_items = ['Coloring by CSS']
        modified = update_todo_file(todo_path, completed_items)

        assert modified is True

        # Check that the item was removed
        new_content = todo_path.read_text(encoding='utf-8')
        assert 'Coloring by CSS' not in new_content
        assert 'transparent QR codes' in new_content
        assert 'Some other task' in new_content
    finally:
        todo_path.unlink()


def test_update_todo_file_no_matching_items():
    """Test that file is not modified when no items match."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        todo_path = Path(f.name)

    try:
        todo_content = """1. Task A
2. Task B
"""
        todo_path.write_text(todo_content, encoding='utf-8')

        completed_items = ['Nonexistent Task']
        modified = update_todo_file(todo_path, completed_items)

        assert modified is False

        # Check content unchanged
        new_content = todo_path.read_text(encoding='utf-8')
        assert 'Task A' in new_content
        assert 'Task B' in new_content
    finally:
        todo_path.unlink()


def test_update_todo_file_empty_completed_items():
    """Test that file is not modified with empty completed items list."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        todo_path = Path(f.name)

    try:
        todo_content = """1. Task A
2. Task B
"""
        todo_path.write_text(todo_content, encoding='utf-8')

        modified = update_todo_file(todo_path, [])

        assert modified is False
    finally:
        todo_path.unlink()


def test_update_todo_file_nonexistent_file():
    """Test handling of nonexistent TODO file."""
    temp_dir = tempfile.gettempdir()
    todo_path = Path(temp_dir) / 'nonexistent_update_todo_xyz.md'

    # Ensure it doesn't exist
    if todo_path.exists():
        todo_path.unlink()

    completed_items = ['Some Task']
    modified = update_todo_file(todo_path, completed_items)

    assert modified is False
