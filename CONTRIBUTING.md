# Contributing to Fountain-Py

We love your input! We want to make contributing to this project as easy and transparent as possible.

## Development Process

1. Fork the repo and create your branch from `main`
2. If you've added code that should be tested, add tests
3. Ensure the test suite passes
4. Make sure your code follows the style guidelines
5. Issue that pull request!

## Development Setup

```bash
# Clone your fork
git clone https://github.com/your-username/fountain-py.git
cd fountain-py

# Install development dependencies
uv sync --dev

# Install pre-commit hooks
pre-commit install
```

## Running Tests

```bash
# Run all tests
uv run pytest

# Run tests with coverage
uv run pytest --cov=fountain --cov-report=html

# Run specific test file
uv run pytest tests/test_parser.py
```

## Code Style

We use:
- `ruff` for linting and formatting
- `mypy` for type checking
- All code must have type hints
- Follow PEP8 conventions

Run these checks locally:
```bash
# Format code
uv run ruff format src/ tests/

# Check linting
uv run ruff check src/ tests/

# Type checking
uv run mypy src/
```

## Pull Request Process

1. Update the README.md with details of changes if needed
2. Update the CHANGELOG.md with your changes
3. The PR will be merged once you have the sign-off of at least one maintainer

## Reporting Bugs

1. Use the GitHub Issues tracker
2. Include a clear title and description
3. Provide example code if possible
4. Include error messages and stack traces
5. Mention your Python version and OS

## Suggesting Features

1. Open an issue with the "enhancement" label
2. Clearly describe the feature and its use case
3. Provide examples of how it would work
4. Be open to discussion and feedback

## Code of Conduct

Please note we have a code of conduct. Follow it in all your interactions with the project.

## License

By contributing, you agree that your contributions will be licensed under the MIT License.