# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A simple CLI todo application with persistent JSON storage. Single-file Python app (`todo.py`) that stores todos in `todos.json`.

## Running the App

```bash
cd todo-app

# Run directly (requires execute permission)
./todo.py

# Or with Python
python3 todo.py
```

## CLI Commands

- `todo` - List all todos
- `todo add <task>` - Add a new todo
- `todo add <task> --due <date>` - Add with due date (formats: YYYY-MM-DD, MM/DD/YYYY, MM/DD)
- `todo done <number>` - Mark as complete
- `todo remove <number>` - Remove a todo

## Architecture

- **Storage**: JSON file (`todos.json`) in same directory as script, using `pathlib.Path`
- **Todo structure**: `{"task": str, "done": bool, "due"?: str (YYYY-MM-DD)}`
- **Index**: 1-based for user-facing commands (converted to 0-based internally)
- **Due date highlighting**: Uses ANSI escape codes for overdue (red) and today/tomorrow (yellow)
