"""Test check_todo.py script."""
from pathlib import Path

from scripts.check_todo import is_todo_empty


def test_is_todo_empty_with_empty_file(tmp_path):
    """Test that empty file is detected as empty."""
    todo_path = tmp_path / "todo.md"
    todo_path.write_text('', encoding='utf-8')
    assert is_todo_empty(todo_path) is True

def test_is_todo_empty_with_whitespace_only(tmp_path):
    """Test that whitespace-only file is detected as empty."""
    todo_path = tmp_path / "todo.md"
    todo_path.write_text('   \n\n  \t  ', encoding='utf-8')
    assert is_todo_empty(todo_path) is True

def test_is_todo_empty_with_content(tmp_path):
    """Test that file with content is detected as not empty."""
    todo_path = tmp_path / "todo.md"
    todo_path.write_text('1. Do something', encoding='utf-8')
    assert is_todo_empty(todo_path) is False

def test_is_todo_empty_with_nonexistent_file(tmp_path):
    """Test that nonexistent file is treated as empty."""
    todo_path = tmp_path / "nonexistent_todo_file_xyz.md"
    # Ensure it doesn't exist
    if todo_path.exists():
        todo_path.unlink()
    assert is_todo_empty(todo_path) is True
