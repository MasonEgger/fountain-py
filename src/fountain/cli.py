# ABOUTME: Command-line interface for validating and rendering Fountain screenplays.
# Exposes `validate` and `render` subcommands; the `fountain` console script calls main().
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import TYPE_CHECKING

from fountain.document import FountainDocument
from fountain.parser import FountainParser
from fountain.renderer import FountainRenderer, HTMLRenderer
from fountain.renderers.fdx import FDXRenderer
from fountain.renderers.pdf.renderer import PDFRenderer
from fountain.renderers.plaintext import PlainTextRenderer

if TYPE_CHECKING:
    from collections.abc import Callable

# Format-to-renderer mapping for the text-producing output formats. pdf is handled
# separately because it produces bytes and needs the missing-extra guard.
_TEXT_RENDERERS: dict[str, Callable[[FountainDocument], str]] = {
    "html": HTMLRenderer().render_page,
    "text": PlainTextRenderer().render,
    "fountain": FountainRenderer().render,
    "json": FountainDocument.to_json,
    "fdx": FDXRenderer().render,
}

_FORMAT_CHOICES = (*sorted(_TEXT_RENDERERS), "pdf")


def _run_validate(source: str) -> int:
    """Run the `validate` subcommand, printing one diagnostic per line.

    Args:
        source: The Fountain source text.

    Returns:
        0 if no issue has severity 'error', else 1.
    """
    issues = FountainParser().validate(source)
    for issue in issues:
        print(f"{issue.line_number}:{issue.severity}:{issue.code}:{issue.message}")
    return 1 if any(issue.severity == "error" for issue in issues) else 0


def _run_render(source: str, output_format: str, output_path: str | None) -> int:
    """Run the `render` subcommand, writing to ``output_path`` or stdout.

    Args:
        source: The Fountain source text.
        output_format: One of ``_FORMAT_CHOICES``.
        output_path: File to write, or None for stdout.

    Returns:
        The process exit code.
    """
    # pdf produces bytes and needs the optional [pdf] extra, so it gets its own path
    if output_format == "pdf":
        try:
            pdf_renderer = PDFRenderer()
        except ImportError as error:
            print(error, file=sys.stderr)
            return 1
        pdf_bytes = pdf_renderer.render_bytes(FountainParser().parse(source))
        if output_path:
            Path(output_path).write_bytes(pdf_bytes)
        else:
            sys.stdout.buffer.write(pdf_bytes)
        return 0

    output = _TEXT_RENDERERS[output_format](FountainParser().parse(source))
    if output_path:
        Path(output_path).write_text(output, encoding="utf-8")
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
        The process exit code: 1 when the input cannot be read.
    """
    args = _build_parser().parse_args(argv)

    # Read the source once; an unreadable file is a user error, not a traceback
    try:
        source = sys.stdin.read() if args.file == "-" else Path(args.file).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as error:
        print(f"fountain: cannot read {args.file}: {error}", file=sys.stderr)
        return 1

    if args.command == "validate":
        return _run_validate(source)
    return _run_render(source, args.format, args.output)


if __name__ == "__main__":
    sys.exit(main())
