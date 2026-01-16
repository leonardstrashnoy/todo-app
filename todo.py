#!/usr/bin/env python3
"""Simple CLI Todo App with persistent JSON storage."""

import json
import os
import sys
from datetime import datetime, date
from pathlib import Path

TODO_FILE = Path(__file__).parent / "todos.json"


def _normalize_todo(item: object) -> dict | None:
    if not isinstance(item, dict):
        return None
    task = item.get("task")
    done = item.get("done", False)
    if not isinstance(task, str) or not task.strip():
        return None
    todo: dict = {"task": task, "done": bool(done)}
    due = item.get("due")
    if isinstance(due, str) and due.strip():
        todo["due"] = due
    return todo


def load_todos() -> list[dict]:
    """Load todos from JSON file."""
    if TODO_FILE.exists():
        try:
            data = json.loads(TODO_FILE.read_text())
        except json.JSONDecodeError:
            return []
        if not isinstance(data, list):
            return []
        todos: list[dict] = []
        for item in data:
            normalized = _normalize_todo(item)
            if normalized is not None:
                todos.append(normalized)
        return todos
    return []


def save_todos(todos: list[dict]) -> None:
    """Save todos to JSON file."""
    TODO_FILE.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = TODO_FILE.with_suffix(TODO_FILE.suffix + ".tmp")
    tmp_path.write_text(json.dumps(todos, indent=2))
    os.replace(tmp_path, TODO_FILE)


def format_due_date(due: str | None, done: bool) -> str:
    """Format due date with overdue highlighting."""
    if not due:
        return ""
    if done:
        return f" (due: {due})"
    try:
        due_date = datetime.strptime(due, "%Y-%m-%d").date()
    except ValueError:
        return f" (due: {due})"
    today = date.today()
    days_left = (due_date - today).days

    if days_left < 0:
        return f" \033[91m(OVERDUE: {due})\033[0m"
    elif days_left == 0:
        return f" \033[93m(due: TODAY)\033[0m"
    elif days_left == 1:
        return f" \033[93m(due: tomorrow)\033[0m"
    else:
        return f" (due: {due})"


def list_todos() -> None:
    """Display all todos."""
    todos = load_todos()
    if not todos:
        print(f"No todos yet. Add one with: {Path(sys.argv[0]).name} add <task>")
        return

    print("\nYour Todos:")
    print("-" * 50)
    for i, todo in enumerate(todos, 1):
        status = "✓" if todo["done"] else " "
        due_str = format_due_date(todo.get("due"), todo["done"])
        print(f"  {i}. [{status}] {todo['task']}{due_str}")
    print()


def parse_date(date_str: str) -> str | None:
    """Parse date string and return YYYY-MM-DD format."""
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%m/%d"):
        try:
            parsed = datetime.strptime(date_str, fmt)
            if fmt == "%m/%d":
                parsed = parsed.replace(year=date.today().year)
            return parsed.strftime("%Y-%m-%d")
        except ValueError:
            continue
    return None


def add_todo(task: str, due: str | None = None) -> None:
    """Add a new todo."""
    todos = load_todos()
    todo = {"task": task, "done": False}
    if due:
        parsed_due = parse_date(due)
        if parsed_due:
            todo["due"] = parsed_due
        else:
            print(f"Invalid date format: {due}. Use YYYY-MM-DD or MM/DD")
            return
    todos.append(todo)
    save_todos(todos)
    due_msg = f" (due: {todo.get('due', 'none')})" if due else ""
    print(f"Added: {task}{due_msg}")


def complete_todo(index: int) -> None:
    """Mark a todo as complete."""
    todos = load_todos()
    if 1 <= index <= len(todos):
        todos[index - 1]["done"] = True
        save_todos(todos)
        print(f"Completed: {todos[index - 1]['task']}")
    else:
        print(f"Invalid todo number: {index}")


def remove_todo(index: int) -> None:
    """Remove a todo."""
    todos = load_todos()
    if 1 <= index <= len(todos):
        removed = todos.pop(index - 1)
        save_todos(todos)
        print(f"Removed: {removed['task']}")
    else:
        print(f"Invalid todo number: {index}")


def print_help() -> None:
    """Print usage instructions."""
    prog = Path(sys.argv[0]).name
    print("""
Todo App - Simple CLI Task Manager

Usage:
  {prog}                          List all todos
  {prog} add <task>               Add a new todo
  {prog} add <task> --due <date>  Add a todo with due date
  {prog} done <number>            Mark a todo as complete
  {prog} remove <number>          Remove a todo
  {prog} help                     Show this help message

Date formats:
  YYYY-MM-DD    e.g., 2026-01-15
  MM/DD/YYYY    e.g., 01/15/2026
  MM/DD         e.g., 01/15 (uses current year)
""".format(prog=prog))


def main() -> None:
    args = sys.argv[1:]
    prog = Path(sys.argv[0]).name

    if not args:
        list_todos()
        return

    command = args[0].lower()

    if command == "help":
        print_help()
    elif command == "add":
        if len(args) < 2:
            print(f"Usage: {prog} add <task> [--due <date>]")
            return
        due_date = None
        task_args = args[1:]
        if "--due" in task_args:
            due_idx = task_args.index("--due")
            if due_idx + 1 < len(task_args):
                due_date = task_args[due_idx + 1]
                task_args = task_args[:due_idx] + task_args[due_idx + 2:]
            else:
                print("Missing date after --due")
                return
        task = " ".join(task_args)
        if not task:
            print("Task description cannot be empty")
            return
        add_todo(task, due_date)
    elif command == "done":
        if len(args) < 2:
            print(f"Usage: {prog} done <number>")
            return
        try:
            index = int(args[1])
            complete_todo(index)
        except ValueError:
            print("Please provide a valid number")
    elif command == "remove":
        if len(args) < 2:
            print(f"Usage: {prog} remove <number>")
            return
        try:
            index = int(args[1])
            remove_todo(index)
        except ValueError:
            print("Please provide a valid number")
    else:
        print(f"Unknown command: {command}")
        print_help()


if __name__ == "__main__":
    main()
