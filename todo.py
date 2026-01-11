#!/usr/bin/env python3
"""Simple CLI Todo App with persistent JSON storage."""

import json
import sys
from datetime import datetime, date
from pathlib import Path

TODO_FILE = Path(__file__).parent / "todos.json"


def load_todos() -> list[dict]:
    """Load todos from JSON file."""
    if TODO_FILE.exists():
        return json.loads(TODO_FILE.read_text())
    return []


def save_todos(todos: list[dict]) -> None:
    """Save todos to JSON file."""
    TODO_FILE.write_text(json.dumps(todos, indent=2))


def format_due_date(due: str | None, done: bool) -> str:
    """Format due date with overdue highlighting."""
    if not due:
        return ""
    due_date = datetime.strptime(due, "%Y-%m-%d").date()
    today = date.today()
    days_left = (due_date - today).days

    if done:
        return f" (due: {due})"
    elif days_left < 0:
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
        print("No todos yet. Add one with: todo add <task>")
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
    print("""
Todo App - Simple CLI Task Manager

Usage:
  todo                          List all todos
  todo add <task>               Add a new todo
  todo add <task> --due <date>  Add a todo with due date
  todo done <number>            Mark a todo as complete
  todo remove <number>          Remove a todo
  todo help                     Show this help message

Date formats:
  YYYY-MM-DD    e.g., 2026-01-15
  MM/DD/YYYY    e.g., 01/15/2026
  MM/DD         e.g., 01/15 (uses current year)
""")


def main() -> None:
    args = sys.argv[1:]

    if not args:
        list_todos()
        return

    command = args[0].lower()

    if command == "help":
        print_help()
    elif command == "add":
        if len(args) < 2:
            print("Usage: todo add <task> [--due <date>]")
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
            print("Usage: todo done <number>")
            return
        try:
            index = int(args[1])
            complete_todo(index)
        except ValueError:
            print("Please provide a valid number")
    elif command == "remove":
        if len(args) < 2:
            print("Usage: todo remove <number>")
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
