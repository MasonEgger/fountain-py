# ABOUTME: Subprocess tests for the `fountain` CLI (validate and render subcommands).
# Invokes `python -m fountain.cli` directly so the console-script entry point is exercised end to end.
# The missing-[pdf]-extra test calls main() in-process instead, since coverage cannot see into subprocesses.
import re
import subprocess
import sys
from pathlib import Path

import pytest

from fountain.cli import main
from fountain.parser import FountainParser
from fountain.renderers.pdf._deps import PDF_EXTRA_MESSAGE

WELL_FORMED_SCRIPT = """Title: Test Script
Author: Test Author

INT. HOUSE - DAY

John enters the room.

JOHN
Hello there!
"""

UNCLOSED_BONEYARD_SCRIPT = """INT. HOUSE - DAY

Action line.

/* unclosed comment
"""


def _run_cli(args: list[str], input_text: str | None = None) -> subprocess.CompletedProcess[str]:
    """Invoke the fountain CLI as a subprocess and capture its result.

    Args:
        args: Arguments to pass after ``python -m fountain.cli``.
        input_text: Optional text piped to stdin.

    Returns:
        The completed process, with stdout/stderr captured as text.
    """
    return subprocess.run(
        [sys.executable, "-m", "fountain.cli", *args],
        input=input_text,
        capture_output=True,
        text=True,
    )


def test_validate_clean_exits_zero(tmp_path: Path) -> None:
    script_path = tmp_path / "clean.fountain"
    script_path.write_text(WELL_FORMED_SCRIPT, encoding="utf-8")

    result = _run_cli(["validate", str(script_path)])

    assert result.stderr == ""
    assert result.returncode == 0


def test_validate_errors_exit_one(tmp_path: Path) -> None:
    script_path = tmp_path / "broken.fountain"
    script_path.write_text(UNCLOSED_BONEYARD_SCRIPT, encoding="utf-8")

    result = _run_cli(["validate", str(script_path)])

    assert re.search(r"\d+:error:unclosed-boneyard:", result.stdout) is not None
    assert result.returncode == 1


def test_render_html_to_stdout(tmp_path: Path) -> None:
    script_path = tmp_path / "script.fountain"
    script_path.write_text(WELL_FORMED_SCRIPT, encoding="utf-8")

    result = _run_cli(["render", str(script_path), "--format", "html"])

    assert '<div class="fountain-script">' in result.stdout
    assert result.returncode == 0


def test_render_json_matches_to_json(tmp_path: Path) -> None:
    script_path = tmp_path / "script.fountain"
    script_path.write_text(WELL_FORMED_SCRIPT, encoding="utf-8")

    result = _run_cli(["render", str(script_path), "--format", "json"])

    expected = FountainParser().parse_file(str(script_path)).to_json()
    assert result.stdout == expected
    assert result.returncode == 0


def test_validate_stdin() -> None:
    result = _run_cli(["validate", "-"], input_text=WELL_FORMED_SCRIPT)

    assert result.stderr == ""
    assert result.returncode == 0


def test_render_stdin(tmp_path: Path) -> None:
    result = _run_cli(["render", "-", "--format", "text"], input_text=WELL_FORMED_SCRIPT)

    assert "INT. HOUSE - DAY" in result.stdout
    assert result.returncode == 0


def test_render_to_output_file(tmp_path: Path) -> None:
    script_path = tmp_path / "script.fountain"
    script_path.write_text(WELL_FORMED_SCRIPT, encoding="utf-8")
    output_path = tmp_path / "out.fountain"

    result = _run_cli(["render", str(script_path), "--format", "fountain", "-o", str(output_path)])

    assert output_path.exists()
    assert output_path.read_text(encoding="utf-8") != ""
    assert result.stdout == ""
    assert result.returncode == 0


def test_render_pdf_to_output_file(tmp_path: Path) -> None:
    script_path = tmp_path / "script.fountain"
    script_path.write_text(WELL_FORMED_SCRIPT, encoding="utf-8")
    output_path = tmp_path / "out.pdf"

    result = _run_cli(["render", str(script_path), "--format", "pdf", "-o", str(output_path)])

    assert result.returncode == 0
    assert output_path.read_bytes().startswith(b"%PDF")


def test_render_pdf_to_stdout(tmp_path: Path) -> None:
    script_path = tmp_path / "script.fountain"
    script_path.write_text(WELL_FORMED_SCRIPT, encoding="utf-8")

    result = subprocess.run(
        [sys.executable, "-m", "fountain.cli", "render", str(script_path), "--format", "pdf"],
        capture_output=True,
    )

    assert result.returncode == 0
    assert result.stdout.startswith(b"%PDF")


def test_render_pdf_missing_extra_exits_nonzero_with_message(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """When fpdf2 is absent, the CLI translates PDFRenderer's ImportError into a clean exit, not a traceback."""
    script_path = tmp_path / "script.fountain"
    script_path.write_text(WELL_FORMED_SCRIPT, encoding="utf-8")
    monkeypatch.setitem(sys.modules, "fpdf", None)

    exit_code = main(["render", str(script_path), "--format", "pdf"])

    assert exit_code == 1
    assert PDF_EXTRA_MESSAGE in capsys.readouterr().err


def test_render_fdx_to_stdout(tmp_path: Path) -> None:
    script_path = tmp_path / "script.fountain"
    script_path.write_text(WELL_FORMED_SCRIPT, encoding="utf-8")

    result = _run_cli(["render", str(script_path), "--format", "fdx"])

    assert "FinalDraft" in result.stdout
    assert result.returncode == 0
