# ABOUTME: Tests for the require_fpdf() import guard on the optional [pdf] extra.
# Covers the happy path (fpdf2 installed) and the missing-extra ImportError message.
import re
import sys

import pytest

from fountain.renderers.pdf._deps import PDF_EXTRA_MESSAGE, require_fpdf


def test_require_fpdf_returns_module_when_installed() -> None:
    fpdf = require_fpdf()

    assert fpdf.__name__ == "fpdf"


def test_require_fpdf_raises_with_extra_install_message(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setitem(sys.modules, "fpdf", None)

    with pytest.raises(ImportError, match=re.escape(PDF_EXTRA_MESSAGE)):
        require_fpdf()
