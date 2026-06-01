# Contributing

## Development Setup

```bash
# Clone
git clone https://github.com/pyrpc/jsonschema-ts
cd jsonschema-ts

# Create virtualenv
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\Activate.ps1 on Windows

# Install dev dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install
```

## Running Tests

```bash
# All tests
pytest -v

# Unit tests only (no Node.js needed)
pytest -v -m "not integration"

# Integration tests (requires Node.js >= 18)
pytest -v -m integration

# Coverage report
pytest --cov=jsonschema_ts --cov-report=term-missing
```

## Code Style

- Ruff with line length 88
- Type hints on all public functions (3.11+ syntax)
- Private/internal functions prefixed with `_`
- Docstrings on all public API functions

Run linting:
```bash
ruff check .
ruff format --check .
```

## Pull Request Process

1. Create a feature branch from `main`
2. Write tests for any new functionality
3. Ensure all tests pass
4. Run `ruff check .` — no warnings
5. Update `CHANGELOG.md`
6. Open a PR with a clear description

## Release Process

1. Update version in `pyproject.toml` and `__init__.py`
2. Update `CHANGELOG.md`
3. Create a Git tag: `git tag v<version>`
4. Push tag: `git push origin v<version>`
5. CI publishes to PyPI automatically

## Project Structure

```
src/jsonschema_ts/        # Source code
  __init__.py             # Public API exports
  _converter.py           # convert(), convert_all(), _to_npx()
  _defs_collector.py      # collect_defs()
  _emitter.py             # assemble(), _strip_root_interface()
  _errors.py              # Exception classes
  _options.py             # Options dataclass
  _utils.py               # Utilities
tests/                    # Tests (mirrors src structure)
  fixtures/               # JSON Schema fixtures
docs/                     # Single-page doc site
```
