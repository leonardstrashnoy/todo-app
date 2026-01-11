"""Tests for the todo app."""

import json
from datetime import date, timedelta

import pytest

import todo


@pytest.fixture
def temp_todo_file(tmp_path, monkeypatch):
    """Use a temporary file for todos during tests."""
    todo_file = tmp_path / "todos.json"
    monkeypatch.setattr(todo, "TODO_FILE", todo_file)
    return todo_file


class TestParseDate:
    def test_iso_format(self):
        assert todo.parse_date("2026-01-15") == "2026-01-15"

    def test_us_format(self):
        assert todo.parse_date("01/15/2026") == "2026-01-15"

    def test_short_format_uses_current_year(self):
        result = todo.parse_date("01/15")
        assert result == f"{date.today().year}-01-15"

    def test_invalid_format(self):
        assert todo.parse_date("invalid") is None
        assert todo.parse_date("15-01-2026") is None


class TestFormatDueDate:
    def test_no_due_date(self):
        assert todo.format_due_date(None, False) == ""

    def test_done_task(self):
        assert todo.format_due_date("2026-01-15", True) == " (due: 2026-01-15)"

    def test_future_date(self):
        future = (date.today() + timedelta(days=10)).strftime("%Y-%m-%d")
        assert todo.format_due_date(future, False) == f" (due: {future})"

    def test_overdue(self):
        past = (date.today() - timedelta(days=1)).strftime("%Y-%m-%d")
        result = todo.format_due_date(past, False)
        assert "OVERDUE" in result
        assert "\033[91m" in result  # red color

    def test_due_today(self):
        today = date.today().strftime("%Y-%m-%d")
        result = todo.format_due_date(today, False)
        assert "TODAY" in result
        assert "\033[93m" in result  # yellow color

    def test_due_tomorrow(self):
        tomorrow = (date.today() + timedelta(days=1)).strftime("%Y-%m-%d")
        result = todo.format_due_date(tomorrow, False)
        assert "tomorrow" in result
        assert "\033[93m" in result  # yellow color


class TestLoadSaveTodos:
    def test_load_empty(self, temp_todo_file):
        assert todo.load_todos() == []

    def test_save_and_load(self, temp_todo_file):
        todos = [{"task": "Test task", "done": False}]
        todo.save_todos(todos)
        assert todo.load_todos() == todos

    def test_load_existing(self, temp_todo_file):
        data = [{"task": "Existing", "done": True}]
        temp_todo_file.write_text(json.dumps(data))
        assert todo.load_todos() == data


class TestAddTodo:
    def test_add_simple(self, temp_todo_file, capsys):
        todo.add_todo("Buy milk")
        todos = todo.load_todos()
        assert len(todos) == 1
        assert todos[0]["task"] == "Buy milk"
        assert todos[0]["done"] is False
        assert "due" not in todos[0]
        assert "Added: Buy milk" in capsys.readouterr().out

    def test_add_with_due_date(self, temp_todo_file, capsys):
        todo.add_todo("Meeting", "2026-01-15")
        todos = todo.load_todos()
        assert todos[0]["due"] == "2026-01-15"
        assert "due: 2026-01-15" in capsys.readouterr().out

    def test_add_invalid_date(self, temp_todo_file, capsys):
        todo.add_todo("Task", "invalid-date")
        assert todo.load_todos() == []
        assert "Invalid date format" in capsys.readouterr().out


class TestCompleteTodo:
    def test_complete(self, temp_todo_file, capsys):
        todo.save_todos([{"task": "Task 1", "done": False}])
        todo.complete_todo(1)
        assert todo.load_todos()[0]["done"] is True
        assert "Completed: Task 1" in capsys.readouterr().out

    def test_invalid_index(self, temp_todo_file, capsys):
        todo.save_todos([{"task": "Task 1", "done": False}])
        todo.complete_todo(5)
        assert todo.load_todos()[0]["done"] is False
        assert "Invalid todo number" in capsys.readouterr().out


class TestRemoveTodo:
    def test_remove(self, temp_todo_file, capsys):
        todo.save_todos([
            {"task": "Task 1", "done": False},
            {"task": "Task 2", "done": False},
        ])
        todo.remove_todo(1)
        todos = todo.load_todos()
        assert len(todos) == 1
        assert todos[0]["task"] == "Task 2"
        assert "Removed: Task 1" in capsys.readouterr().out

    def test_invalid_index(self, temp_todo_file, capsys):
        todo.save_todos([{"task": "Task 1", "done": False}])
        todo.remove_todo(0)
        assert len(todo.load_todos()) == 1
        assert "Invalid todo number" in capsys.readouterr().out


class TestListTodos:
    def test_empty_list(self, temp_todo_file, capsys):
        todo.list_todos()
        assert "No todos yet" in capsys.readouterr().out

    def test_list_with_todos(self, temp_todo_file, capsys):
        todo.save_todos([
            {"task": "Task 1", "done": False},
            {"task": "Task 2", "done": True},
        ])
        todo.list_todos()
        output = capsys.readouterr().out
        assert "Task 1" in output
        assert "Task 2" in output
        assert "[ ]" in output or "✓" in output
