# Repository Guidelines

- Run `pytest -q` before committing any changes.
- Install dependencies with `poetry install` (or `pip install -e .`) before running `pytest`.
- Use `scripts/gpt_openapi_generator.py` to generate OpenAPI specs.
- Generated specs should be placed in `openapi_generated/` and are ignored by Git.
