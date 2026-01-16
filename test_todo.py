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


class TestNormalizeTodo:
    def test_valid_todo(self):
        result = todo._normalize_todo({"task": "Test", "done": False})
        assert result == {"task": "Test", "done": False}

    def test_valid_todo_with_due(self):
        result = todo._normalize_todo({"task": "Test", "done": True, "due": "2026-01-15"})
        assert result == {"task": "Test", "done": True, "due": "2026-01-15"}

    def test_missing_task(self):
        assert todo._normalize_todo({"done": False}) is None

    def test_empty_task(self):
        assert todo._normalize_todo({"task": "", "done": False}) is None
        assert todo._normalize_todo({"task": "   ", "done": False}) is None

    def test_non_string_task(self):
        assert todo._normalize_todo({"task": 123, "done": False}) is None
        assert todo._normalize_todo({"task": None, "done": False}) is None

    def test_missing_done_defaults_false(self):
        result = todo._normalize_todo({"task": "Test"})
        assert result == {"task": "Test", "done": False}

    def test_done_coerced_to_bool(self):
        result = todo._normalize_todo({"task": "Test", "done": "yes"})
        assert result["done"] is True
        result = todo._normalize_todo({"task": "Test", "done": 0})
        assert result["done"] is False

    def test_non_dict_returns_none(self):
        assert todo._normalize_todo("not a dict") is None
        assert todo._normalize_todo(["task", "done"]) is None
        assert todo._normalize_todo(None) is None

    def test_empty_due_ignored(self):
        result = todo._normalize_todo({"task": "Test", "done": False, "due": ""})
        assert "due" not in result
        result = todo._normalize_todo({"task": "Test", "done": False, "due": "   "})
        assert "due" not in result

    def test_extra_fields_stripped(self):
        result = todo._normalize_todo({"task": "Test", "done": False, "extra": "field"})
        assert result == {"task": "Test", "done": False}


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

    def test_invalid_date_format(self):
        result = todo.format_due_date("not-a-date", False)
        assert result == " (due: not-a-date)"
        assert "OVERDUE" not in result


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

    def test_load_corrupt_json(self, temp_todo_file):
        temp_todo_file.write_text("not valid json {{{")
        assert todo.load_todos() == []

    def test_load_non_list_json(self, temp_todo_file):
        temp_todo_file.write_text(json.dumps({"task": "Test", "done": False}))
        assert todo.load_todos() == []

    def test_load_filters_invalid_items(self, temp_todo_file):
        data = [
            {"task": "Valid", "done": False},
            {"task": "", "done": False},  # empty task
            "not a dict",
            {"done": True},  # missing task
            {"task": "Also valid", "done": True},
        ]
        temp_todo_file.write_text(json.dumps(data))
        result = todo.load_todos()
        assert len(result) == 2
        assert result[0]["task"] == "Valid"
        assert result[1]["task"] == "Also valid"

    def test_load_normalizes_items(self, temp_todo_file):
        data = [{"task": "Test", "done": "truthy", "extra": "removed"}]
        temp_todo_file.write_text(json.dumps(data))
        result = todo.load_todos()
        assert result == [{"task": "Test", "done": True}]


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
