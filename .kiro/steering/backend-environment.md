# Backend Environment Setup

## Python Virtual Environment

The backend uses `uv venv` for Python virtual environment management:

- Virtual environment location: `backend/.venv`
- Package manager: `uv` (modern Python package installer)
- Environment activation: Use `uv` commands or activate the `.venv` directly

## Usage

When working with the backend:
1. Ensure `uv` is installed
2. Virtual environment is located at `backend/.venv`
3. Use `uv pip install` for package management
4. Dependencies are managed through `backend/requirements.txt`