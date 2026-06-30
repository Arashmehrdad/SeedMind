# seedmind validation

> These commands are inferred from repository configuration. Prefer project documentation and configured scripts when they differ.

## Detected project types

- Python

## Suggested checks

- `.\.venv\Scripts\python.exe scripts\run_week8_reusable_skill.py`
- `.\.venv\Scripts\python.exe -m pytest tests/unit/skills -q --basetemp .tmp_pytest\week8-focused`
- `python -m pytest -q`
- `python -m ruff format --check .`
- `python -m ruff check .`
- `python -m mypy .`
- `python -m pip check`
- `git diff --check`

## Relevant configuration

- `pyproject.toml`
