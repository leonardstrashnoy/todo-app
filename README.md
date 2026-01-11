# Todo App

A simple command-line todo application with persistent JSON storage.

## Features

- Add, complete, and remove todos
- Optional due dates with overdue highlighting
- Persistent storage in JSON format

## Usage

```bash
./todo.py                           # List all todos
./todo.py add "Buy groceries"       # Add a todo
./todo.py add "Meeting" --due 01/15 # Add with due date
./todo.py done 1                    # Mark todo #1 as complete
./todo.py remove 1                  # Remove todo #1
./todo.py help                      # Show help
```

## Date Formats

- `YYYY-MM-DD` (e.g., 2026-01-15)
- `MM/DD/YYYY` (e.g., 01/15/2026)
- `MM/DD` (e.g., 01/15 - uses current year)

## Requirements

Python 3.10+ (uses modern type hints)
