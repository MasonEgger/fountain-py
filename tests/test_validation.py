# ABOUTME: Tests for the Fountain validation API (ValidationIssue and validate()).
# Covers the ValidationIssue dataclass contract and diagnostic reporting.
"""Tests for the Fountain validation API."""

from __future__ import annotations

import dataclasses

import pytest

import fountain
from fountain.elements import ValidationIssue
from fountain.parser import FountainParser


def test_validation_issue_exported() -> None:
    """ValidationIssue is importable from the package top level and listed in __all__."""
    from fountain import ValidationIssue as ExportedValidationIssue

    assert ExportedValidationIssue is ValidationIssue
    assert "ValidationIssue" in fountain.__all__


def test_validation_issue_is_frozen_dataclass() -> None:
    """ValidationIssue constructs, reads back all fields, and is immutable."""
    issue = ValidationIssue(line_number=1, severity="error", code="x", message="y")

    assert issue.line_number == 1
    assert issue.severity == "error"
    assert issue.code == "x"
    assert issue.message == "y"

    with pytest.raises(dataclasses.FrozenInstanceError):
        issue.line_number = 2  # type: ignore[misc]
    with pytest.raises(dataclasses.FrozenInstanceError):
        issue.severity = "warning"  # type: ignore[misc]
    with pytest.raises(dataclasses.FrozenInstanceError):
        issue.code = "z"  # type: ignore[misc]
    with pytest.raises(dataclasses.FrozenInstanceError):
        issue.message = "w"  # type: ignore[misc]


def test_unclosed_boneyard_reports_error() -> None:
    """A boneyard opened with /* and never closed reports one error at the opening line."""
    text = "INT. HOUSE - DAY\n\nAction line.\n\n/* unclosed comment"

    issues = FountainParser().validate(text)

    assert len(issues) == 1
    assert issues[0].code == "unclosed-boneyard"
    assert issues[0].severity == "error"
    assert issues[0].line_number == 5


def test_unclosed_note_reports_error() -> None:
    """A note opened with [[ and never closed reports one error at the opening line."""
    text = "INT. HOUSE - DAY\n\n[[ unclosed note"

    issues = FountainParser().validate(text)

    assert len(issues) == 1
    assert issues[0].code == "unclosed-note"
    assert issues[0].severity == "error"
    assert issues[0].line_number == 3


def test_orphan_character_cue_reports_warning() -> None:
    """An uppercase cue demoted to action because no dialogue follows reports one warning."""
    text = "INT. HOUSE - DAY\n\nJOHN\n\nINT. KITCHEN - NIGHT"

    issues = FountainParser().validate(text)

    assert len(issues) == 1
    assert issues[0].code == "orphan-character-cue"
    assert issues[0].severity == "warning"
    assert issues[0].line_number == 3


def test_empty_document_reports_warning() -> None:
    """Input that parses to zero elements reports one empty-document warning."""
    issues = FountainParser().validate("")

    assert len(issues) == 1
    assert issues[0].code == "empty-document"
    assert issues[0].severity == "warning"


def test_well_formed_script_returns_empty_list() -> None:
    """A valid script produces no diagnostics."""
    text = "INT. HOUSE - DAY\n\nJOHN\nHello there."

    assert FountainParser().validate(text) == []


def test_validate_does_not_change_parse_output() -> None:
    """Running validate() first does not change a later parse() result."""
    text = "INT. HOUSE - DAY\n\nJOHN\nHello there.\n\n/* unclosed comment"

    parser = FountainParser()
    parser.validate(text)
    after_validate = parser.parse(text).to_dict()

    baseline = FountainParser().parse(text).to_dict()

    assert after_validate == baseline
