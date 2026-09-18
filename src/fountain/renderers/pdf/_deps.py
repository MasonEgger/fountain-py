# ABOUTME: Import guard for the optional [pdf] extra fpdf2 dependency.
# Raises a clear, install-command-naming error when fpdf2 is not installed.
from types import ModuleType

PDF_EXTRA_MESSAGE = 'Install the PDF extra: pip install "fountain-py[pdf]"'


def require_fpdf() -> ModuleType:
    """Import and return the fpdf module, guarding for the optional extra.

    Returns:
        The imported ``fpdf`` module.

    Raises:
        ImportError: If fpdf2 is not installed, naming the install command.
    """
    try:
        import fpdf
    except ImportError as exc:
        raise ImportError(PDF_EXTRA_MESSAGE) from exc
    return fpdf
