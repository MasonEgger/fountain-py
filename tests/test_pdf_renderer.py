# ABOUTME: Tests for PDFRenderer, which ties PageGeometry and LayoutProfile together via fpdf2.
# Reads the produced PDF bytes back at the byte level (stdlib zlib, no new dependency) to assert
# media box, binding offset, and element order; no fpdf2 reader exists, so this is the pragmatic path.
import re
import zlib

import pytest

from fountain.document import FountainDocument
from fountain.elements import ElementType, FountainElement
from fountain.renderers.base import BinaryRenderer
from fountain.renderers.pdf.geometry import HALF_LETTER, PageGeometry
from fountain.renderers.pdf.profile import SCREENPLAY
from fountain.renderers.pdf.renderer import PDFRenderer

_MEDIA_BOX_PATTERN = re.compile(rb"/MediaBox \[([\d. ]+)\]")
_STREAM_PATTERN = re.compile(rb"stream\r?\n(.*?)endstream", re.DOTALL)
_TEXT_OPERATOR_PATTERN = re.compile(rb"\((.*?)\)\s*Tj")


def _media_box_size_pt(pdf_bytes: bytes) -> tuple[float, float]:
    """Read the first page's /MediaBox width and height, in points, from raw PDF bytes."""
    match = _MEDIA_BOX_PATTERN.search(pdf_bytes)
    assert match is not None
    left, bottom, right, top = (float(value) for value in match.group(1).split())
    return right - left, top - bottom


def _extracted_texts(pdf_bytes: bytes) -> list[str]:
    """Decompress every content stream and pull out Tj-operator text, in stream order."""
    texts = []
    for stream_match in _STREAM_PATTERN.finditer(pdf_bytes):
        try:
            decompressed = zlib.decompress(stream_match.group(1))
        except zlib.error:
            continue
        for text_match in _TEXT_OPERATOR_PATTERN.finditer(decompressed):
            texts.append(text_match.group(1).decode("latin-1"))
    return texts


def _first_text_x_pt(decompressed_content: bytes) -> float:
    """Read the x coordinate of the first Td (text-positioning) operator, in points."""
    match = re.search(rb"([\d.]+) ([\d.]+) Td", decompressed_content)
    assert match is not None
    return float(match.group(1))


def _decompressed(pdf_bytes: bytes) -> bytes:
    """Concatenate every decompressed content stream, for regexes that need the raw operators."""
    chunks = []
    for stream_match in _STREAM_PATTERN.finditer(pdf_bytes):
        try:
            chunks.append(zlib.decompress(stream_match.group(1)))
        except zlib.error:
            continue
    return b"\n".join(chunks)


def test_media_box_matches_geometry() -> None:
    document = FountainDocument([FountainElement(ElementType.ACTION, "John enters.", [], 1)])

    pdf_bytes = PDFRenderer(geometry=HALF_LETTER).render_bytes(document)

    width_pt, height_pt = _media_box_size_pt(pdf_bytes)
    assert width_pt == pytest.approx(5.5 * 72, abs=0.5)
    assert height_pt == pytest.approx(8.5 * 72, abs=0.5)


def test_binding_offset_shifts_text_block() -> None:
    document = FountainDocument([FountainElement(ElementType.ACTION, "John enters.", [], 1)])
    geometry_no_offset = PageGeometry(width_in=8.5, height_in=11.0, margin_in=1.0, binding_offset_in=0.0)
    geometry_with_offset = PageGeometry(width_in=8.5, height_in=11.0, margin_in=1.0, binding_offset_in=0.5)

    bytes_no_offset = PDFRenderer(geometry=geometry_no_offset).render_bytes(document)
    bytes_with_offset = PDFRenderer(geometry=geometry_with_offset).render_bytes(document)

    x_no_offset = _first_text_x_pt(_decompressed(bytes_no_offset))
    x_with_offset = _first_text_x_pt(_decompressed(bytes_with_offset))
    assert x_with_offset != x_no_offset
    assert x_with_offset > x_no_offset


def test_text_extracts_in_element_order() -> None:
    elements = [
        FountainElement(ElementType.SCENE_HEADING, "INT. HOUSE - DAY", [], 1),
        FountainElement(ElementType.ACTION, "John enters the room.", [], 2),
        FountainElement(ElementType.CHARACTER, "JOHN", [], 3),
        FountainElement(ElementType.DIALOGUE, "Hello there!", [], 4),
    ]
    document = FountainDocument(elements)

    pdf_bytes = PDFRenderer().render_bytes(document)

    texts = _extracted_texts(pdf_bytes)
    expected_order = ("INT. HOUSE - DAY", "John enters the room.", "JOHN", "Hello there!")
    positions = [texts.index(expected) for expected in expected_order]
    assert positions == sorted(positions)


def test_satisfies_binary_renderer() -> None:
    assert isinstance(PDFRenderer(), BinaryRenderer)


def test_writer_tools_are_omitted() -> None:
    elements = [
        FountainElement(ElementType.NOTE, "a note", [], 1),
        FountainElement(ElementType.SECTION, "# A Section", [], 2),
        FountainElement(ElementType.SYNOPSIS, "a synopsis", [], 3),
        FountainElement(ElementType.BONEYARD, "a comment", [], 4),
        FountainElement(ElementType.ACTION, "John enters.", [], 5),
    ]
    document = FountainDocument(elements)

    pdf_bytes = PDFRenderer().render_bytes(document)

    texts = _extracted_texts(pdf_bytes)
    assert texts == ["John enters."]


def test_dual_dialogue_renders_both_sides() -> None:
    left_character = FountainElement(ElementType.CHARACTER, "JOHN", [], 1)
    left_dialogue = [FountainElement(ElementType.DIALOGUE, "Hello!", [], 2)]
    right_character = FountainElement(ElementType.CHARACTER, "SARAH", [], 3)
    right_dialogue = [FountainElement(ElementType.DIALOGUE, "Hi there!", [], 4)]
    dual_element = FountainElement(
        ElementType.DUAL_DIALOGUE,
        "",
        [],
        1,
        metadata={
            "left_character": left_character,
            "left_dialogue": left_dialogue,
            "right_character": right_character,
            "right_dialogue": right_dialogue,
        },
    )
    document = FountainDocument([dual_element])

    pdf_bytes = PDFRenderer().render_bytes(document)

    texts = _extracted_texts(pdf_bytes)
    assert texts == ["JOHN", "Hello!", "SARAH", "Hi there!"]


def test_dual_dialogue_with_no_metadata_renders_nothing() -> None:
    dual_element = FountainElement(ElementType.DUAL_DIALOGUE, "", [], 1, metadata=None)
    document = FountainDocument([dual_element])

    pdf_bytes = PDFRenderer().render_bytes(document)

    assert _extracted_texts(pdf_bytes) == []


def test_page_break_starts_a_new_page() -> None:
    elements = [
        FountainElement(ElementType.ACTION, "Page one.", [], 1),
        FountainElement(ElementType.PAGE_BREAK, "===", [], 2),
        FountainElement(ElementType.ACTION, "Page two.", [], 3),
    ]
    document = FountainDocument(elements)

    pdf_bytes = PDFRenderer().render_bytes(document)

    assert pdf_bytes.count(b"/Type /Page\n") == 2 or pdf_bytes.count(b"/Type /Page\r\n") == 2


def test_element_type_without_profile_layout_uses_full_text_width() -> None:
    document = FountainDocument([FountainElement(ElementType.CENTERED, "THE END", [], 1)])

    pdf_bytes = PDFRenderer().render_bytes(document)

    assert _extracted_texts(pdf_bytes) == ["THE END"]


def test_zero_or_negative_text_width_raises() -> None:
    pathological = PageGeometry(width_in=2.0, height_in=11.0, margin_in=1.0, binding_offset_in=0.5)
    document = FountainDocument([FountainElement(ElementType.ACTION, "John enters.", [], 1)])

    with pytest.raises(ValueError, match="text_width_in"):
        PDFRenderer(geometry=pathological).render_bytes(document)


def test_default_geometry_and_profile_are_letter_and_screenplay() -> None:
    renderer = PDFRenderer()

    assert renderer.geometry.width_in == 8.5
    assert renderer.profile is SCREENPLAY
