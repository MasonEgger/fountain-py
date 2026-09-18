# ABOUTME: Tests for LayoutProfile, the pure-data per-element indent/width/font model for PDF export.
# Covers the SCREENPLAY preset's font and indent ordering, and that the profile carries no behavior.
import dataclasses

from fountain.elements import ElementType
from fountain.renderers.pdf.profile import SCREENPLAY


def test_screenplay_profile_fields() -> None:
    assert SCREENPLAY.font_name == "Courier"
    assert SCREENPLAY.font_size_pt == 12

    element_layout = SCREENPLAY.element_layout
    for element_type in (
        ElementType.SCENE_HEADING,
        ElementType.ACTION,
        ElementType.CHARACTER,
        ElementType.PARENTHETICAL,
        ElementType.DIALOGUE,
        ElementType.TRANSITION,
    ):
        assert element_type in element_layout

    cue_indent = element_layout[ElementType.CHARACTER].left_indent_in
    parenthetical_indent = element_layout[ElementType.PARENTHETICAL].left_indent_in
    dialogue_indent = element_layout[ElementType.DIALOGUE].left_indent_in
    action_indent = element_layout[ElementType.ACTION].left_indent_in

    assert cue_indent > parenthetical_indent > dialogue_indent > action_indent


def test_profile_is_data_only() -> None:
    assert dataclasses.is_dataclass(SCREENPLAY)

    profile_methods = {
        name for name in dir(SCREENPLAY) if callable(getattr(SCREENPLAY, name)) and not name.startswith("_")
    }
    assert profile_methods == set(), f"unexpected public methods on a data-only profile: {profile_methods}"

    # Only names dataclass generation itself puts on a frozen class body belong here;
    # a hand-written method would show up as an extra entry in LayoutProfile's own namespace.
    dataclass_generated = {"__init__", "__repr__", "__eq__", "__hash__", "__setattr__", "__delattr__", "__replace__"}
    own_methods = {name for name, value in vars(type(SCREENPLAY)).items() if callable(value) and name.startswith("__")}
    assert own_methods <= dataclass_generated, f"unexpected methods defined on LayoutProfile: {own_methods}"
