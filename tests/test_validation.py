# ABOUTME: Tests for the Fountain validation API (ValidationIssue and validate()).
# Covers the ValidationIssue dataclass contract and diagnostic reporting.
"""Tests for the Fountain validation API."""

from __future__ import annotations

import dataclasses

import pytest

from fountain.elements import ValidationIssue


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
