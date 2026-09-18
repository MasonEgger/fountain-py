# ABOUTME: Tests for PageGeometry, the pure-data page size/margin/binding model for PDF export.
# Covers the LETTER/A4/HALF_LETTER presets, custom geometry, and binding-offset-driven text width.
import pytest

from fountain.renderers.pdf.geometry import A4, HALF_LETTER, LETTER, PageGeometry


def test_presets_dimensions() -> None:
    assert LETTER.width_in == 8.5
    assert LETTER.height_in == 11.0

    assert A4.width_in == pytest.approx(210 / 25.4, abs=0.02)
    assert A4.height_in == pytest.approx(297 / 25.4, abs=0.02)

    assert HALF_LETTER.width_in == 5.5
    assert HALF_LETTER.height_in == 8.5


def test_custom_geometry() -> None:
    geometry = PageGeometry(width_in=6, height_in=9, margin_in=1, binding_offset_in=0.25)

    assert geometry.width_in == 6
    assert geometry.height_in == 9
    assert geometry.margin_in == 1
    assert geometry.binding_offset_in == 0.25


def test_text_block_shrinks_with_binding_offset() -> None:
    without_offset = PageGeometry(width_in=8.5, height_in=11.0, margin_in=1.0, binding_offset_in=0.0)
    with_offset = PageGeometry(width_in=8.5, height_in=11.0, margin_in=1.0, binding_offset_in=0.5)

    assert with_offset.text_width_in < without_offset.text_width_in
