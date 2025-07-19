# Fountain-Py

[![CI](https://github.com/MasonEgger/fountain-py/workflows/CI/badge.svg)](https://github.com/MasonEgger/fountain-py/actions?query=workflow%3ACI)
[![PyPI version](https://badge.fury.io/py/fountain-py.svg)](https://badge.fury.io/py/fountain-py)
[![Python versions](https://img.shields.io/pypi/pyversions/fountain-py.svg)](https://pypi.org/project/fountain-py/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

A Python library for parsing [Fountain markup](https://fountain.io/), the screenwriting format. Fountain-Py converts Fountain scripts into structured Python objects and can render them as HTML or other formats.

## Features

- **Complete Fountain Support**: Parses all major Fountain elements including scenes, dialogue, action, transitions, and more
- **Type-Safe**: Built with full type hints and mypy compatibility  
- **Extensible**: Plugin architecture for custom renderers and output formats
- **Fast**: Efficient regex-based parsing with minimal dependencies
- **Well-Tested**: Comprehensive test suite with high coverage
- **Modern Python**: Supports Python 3.8+ with modern async/await patterns

## Quick Start

### Installation

```bash
pip install fountain-py
```

### Basic Usage

```python
from fountain import FountainParser

# Parse a Fountain script
parser = FountainParser()
with open("script.fountain", "r") as f:
    document = parser.parse(f.read())

# Access parsed elements
print(f"Title: {document.title}")
print(f"Characters: {document.get_characters()}")

# Render as HTML
from fountain.renderer import HTMLRenderer
renderer = HTMLRenderer()
html_output = renderer.render(document)
```

### Command Line Usage

```bash
# Convert Fountain to HTML
python -m fountain script.fountain --output script.html

# Get script statistics
python -m fountain script.fountain --stats
```

## Documentation

Full documentation is available at [fountain-py.readthedocs.io](https://fountain-py.readthedocs.io).

- [Installation Guide](https://fountain-py.readthedocs.io/en/latest/installation/)
- [Quick Start Tutorial](https://fountain-py.readthedocs.io/en/latest/quickstart/)
- [API Reference](https://fountain-py.readthedocs.io/en/latest/api/)
- [Examples](https://fountain-py.readthedocs.io/en/latest/examples/)

## Development

### Setup

```bash
# Clone the repository
git clone https://github.com/MasonEgger/fountain-py.git
cd fountain-py

# Install with development dependencies
uv sync --dev

# Install pre-commit hooks
pre-commit install
```

### Running Tests

```bash
# Run all tests
just test

# Run tests with coverage
just test-cov

# Run linting and formatting
just lint
just format

# Run type checking
just type-check
```

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

## Fountain Format

Fountain is a simple markup syntax for writing, editing and sharing screenplays in plain text. Learn more at [fountain.io](https://fountain.io/).

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- The [Fountain](https://fountain.io/) format creators
- The screenwriting community for feedback and testing