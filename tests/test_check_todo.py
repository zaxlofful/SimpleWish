"""Test check_todo.py script."""
import tempfile
from pathlib import Path

from scripts.check_todo import is_todo_empty


def test_is_todo_empty_with_empty_file():
    """Test that empty file is detected as empty."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        todo_path = Path(f.name)

    try:
        todo_path.write_text('', encoding='utf-8')
        assert is_todo_empty(todo_path) is True
    finally:
        todo_path.unlink()


def test_is_todo_empty_with_whitespace_only():
    """Test that whitespace-only file is detected as empty."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        todo_path = Path(f.name)

    try:
        todo_path.write_text('   \n\n  \t  ', encoding='utf-8')
        assert is_todo_empty(todo_path) is True
    finally:
        todo_path.unlink()


def test_is_todo_empty_with_content():
    """Test that file with content is detected as not empty."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        todo_path = Path(f.name)

    try:
        todo_path.write_text('1. Do something', encoding='utf-8')
        assert is_todo_empty(todo_path) is False
    finally:
        todo_path.unlink()


def test_is_todo_empty_with_nonexistent_file():
    """Test that nonexistent file is treated as empty."""
    todo_path = Path('/tmp/nonexistent_todo_file_xyz.md')
    assert is_todo_empty(todo_path) is True
