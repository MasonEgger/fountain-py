# ABOUTME: Command-line interface for validating and rendering Fountain screenplays.
# Exposes `validate` and `render` subcommands; the `fountain` console script calls main().
import argparse
import sys
from collections.abc import Callable
from pathlib import Path

from fountain.document import FountainDocument
from fountain.parser import FountainParser
from fountain.renderer import FountainRenderer, HTMLRenderer
from fountain.renderers.fdx import FDXRenderer
from fountain.renderers.plaintext import PlainTextRenderer

PDF_EXTRA_MESSAGE = 'Install the PDF extra: pip install "fountain-py[pdf]"'


def _render_html(document: FountainDocument) -> str:
    """Render a document as a standalone HTML page."""
    return HTMLRenderer().render_page(document)


def _render_text(document: FountainDocument) -> str:
    """Render a document as monospace plain text."""
    return PlainTextRenderer().render(document)


def _render_fountain(document: FountainDocument) -> str:
    """Render a document back to Fountain markup."""
    return FountainRenderer().render(document)


def _render_json(document: FountainDocument) -> str:
    """Render a document as formatted JSON."""
    return document.to_json()


def _render_fdx(document: FountainDocument) -> str:
    """Render a document as Final Draft (.fdx) XML."""
    return FDXRenderer().render(document)


# Format-to-renderer mapping for the text-producing output formats. pdf is handled
# separately because it produces bytes and needs the missing-extra guard.
_TEXT_RENDERERS: dict[str, Callable[[FountainDocument], str]] = {
    "html": _render_html,
    "text": _render_text,
    "fountain": _render_fountain,
    "json": _render_json,
    "fdx": _render_fdx,
}

_FORMAT_CHOICES = (*sorted(_TEXT_RENDERERS), "pdf")


def _read_source(file: str) -> str:
    """Read Fountain source text from a file path or stdin.

    Args:
        file: A filesystem path, or ``-`` to read from stdin.

    Returns:
        The raw Fountain source text.
    """
    if file == "-":
        return sys.stdin.read()
    return Path(file).read_text(encoding="utf-8")


def _load_document(file: str) -> FountainDocument:
    """Parse a Fountain file or stdin stream into a document.

    Args:
        file: A filesystem path, or ``-`` to read from stdin.

    Returns:
        The parsed document.
    """
    parser = FountainParser()
    if file == "-":
        return parser.parse(sys.stdin.read())
    return parser.parse_file(file)


def _run_validate(args: argparse.Namespace) -> int:
    """Run the `validate` subcommand.

    Args:
        args: Parsed command-line arguments.

    Returns:
        0 if no issue has severity 'error', else 1.
    """
    text = _read_source(args.file)
    issues = FountainParser().validate(text)
    for issue in issues:
        print(f"{issue.line_number}:{issue.severity}:{issue.code}:{issue.message}")
    return 1 if any(issue.severity == "error" for issue in issues) else 0


def _run_render(args: argparse.Namespace) -> int:
    """Run the `render` subcommand.

    Args:
        args: Parsed command-line arguments.

    Returns:
        The process exit code.
    """
    if args.format == "pdf":
        try:
            import fpdf  # type: ignore[import-untyped]  # noqa: F401
        except ImportError:
            print(PDF_EXTRA_MESSAGE, file=sys.stderr)
            return 1
        # Section 6 replaces this branch with the real PDFRenderer, writing bytes.
        # Unreachable until fpdf2 is installed as the [pdf] extra, so no test covers it yet.
        print("PDF rendering is not yet available.", file=sys.stderr)  # pragma: no cover
        return 1  # pragma: no cover

    render_format = _TEXT_RENDERERS.get(args.format)
    if render_format is None:
        # Unreachable today: every _FORMAT_CHOICES entry besides pdf (handled above)
        # is a _TEXT_RENDERERS key, so argparse never lets args.format reach here with
        # no match. Kept as a defensive guard for a future format added to
        # _FORMAT_CHOICES without a matching _TEXT_RENDERERS entry.
        print(f"{args.format} rendering is not yet available.", file=sys.stderr)  # pragma: no cover
        return 1  # pragma: no cover

    document = _load_document(args.file)
    output = render_format(document)

    if args.output:
        Path(args.output).write_text(output, encoding="utf-8")
    else:
        sys.stdout.write(output)
    return 0


def _build_parser() -> argparse.ArgumentParser:
    """Build the top-level argument parser for the `fountain` CLI.

    Returns:
        The configured parser.
    """
    parser = argparse.ArgumentParser(prog="fountain", description="Validate and render Fountain screenplays.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate_parser = subparsers.add_parser("validate", help="Validate a Fountain file and report diagnostics.")
    validate_parser.add_argument("file", help="Path to a .fountain file, or - to read from stdin.")

    render_parser = subparsers.add_parser("render", help="Render a Fountain file to another format.")
    render_parser.add_argument("file", help="Path to a .fountain file, or - to read from stdin.")
    render_parser.add_argument("--format", choices=_FORMAT_CHOICES, required=True, help="Output format.")
    render_parser.add_argument("-o", "--output", help="Write output to this file instead of stdout.")

    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the `fountain` CLI.

    Args:
        argv: Command-line arguments, excluding the program name. Defaults to
            ``sys.argv[1:]`` when None.

    Returns:
        The process exit code.
    """
    args = _build_parser().parse_args(argv)
    if args.command == "validate":
        return _run_validate(args)
    return _run_render(args)


if __name__ == "__main__":
    sys.exit(main())
