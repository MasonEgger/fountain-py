# ABOUTME: Subprocess tests for the `fountain` CLI (validate and render subcommands).
# Invokes `python -m fountain.cli` directly so the console-script entry point is exercised end to end.
import re
import subprocess
import sys
from pathlib import Path

from fountain.parser import FountainParser

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


def test_pdf_format_not_yet_available(tmp_path: Path) -> None:
    # fpdf2 is a dev dependency, so the CLI reaches past the missing-extra guard
    # (covered directly against require_fpdf() in tests/test_pdf_deps.py) to the
    # not-yet-implemented PDFRenderer branch, landing here until Step 6.4.
    script_path = tmp_path / "script.fountain"
    script_path.write_text(WELL_FORMED_SCRIPT, encoding="utf-8")

    result = _run_cli(["render", str(script_path), "--format", "pdf"])

    assert result.returncode != 0
    assert "PDF rendering is not yet available." in result.stderr


def test_render_fdx_to_stdout(tmp_path: Path) -> None:
    script_path = tmp_path / "script.fountain"
    script_path.write_text(WELL_FORMED_SCRIPT, encoding="utf-8")

    result = _run_cli(["render", str(script_path), "--format", "fdx"])

    assert "FinalDraft" in result.stdout
    assert result.returncode == 0
