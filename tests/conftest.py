"""Pytest configuration and fixtures."""
import pytest
from pathlib import Path


@pytest.fixture
def fixtures_dir() -> Path:
    """Return the path to the fixtures directory."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def simple_fountain_script(fixtures_dir: Path) -> str:
    """Load the simple fountain script fixture."""
    return (fixtures_dir / "simple_script.fountain").read_text()


@pytest.fixture
def sample_fountain_text() -> str:
    """Return a sample Fountain text for testing."""
    return """Title: Test Script
Author: Test Author

FADE IN:

INT. COFFEE SHOP - DAY

JOHN enters the coffee shop.

JOHN
(excited)
This is a test!

FADE OUT."""