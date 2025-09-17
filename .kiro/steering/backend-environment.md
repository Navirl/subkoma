## Python Virtual Environment

The backend uses `uv venv` for Python virtual environment management:

- Virtual environment location: `backend/.venv`
- Package manager: `uv` (modern Python package installer)
- Environment activation: Use `uv` commands or activate the `.venv` directly

## Command Execution Rules

When executing Python commands (pytest, python, pip, etc.) in the backend directory:

- **ALWAYS** use `uv run` to execute commands within the virtual environment
- **NEVER** run Python commands directly without the virtual environment
- Examples:
  - Use: `uv run pytest` instead of `pytest`
  - Use: `uv run python script.py` instead of `python script.py`
  - Use: `uv run pip install package` instead of `pip install package`

This ensures all Python operations use the correct virtual environment and dependencies.