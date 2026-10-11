# ABOUTME: Property-based tests (hypothesis) for parsing and the JSON round trip.
# Generates screenplay-shaped text from Fountain line forms plus arbitrary markup characters.
from hypothesis import given
from hypothesis import strategies as st

from fountain.document import FountainDocument
from fountain.parser import FountainParser

# Line forms that exercise every element type, mixed with short runs of markup characters
# so the generated text also hits partial and malformed syntax.
_LINE_FORMS = [
    "",
    "  ",
    "\t",
    "INT. HOUSE - DAY",
    "JOHN",
    "MARY^",
    "@mcclane (O.S.)",
    "(softly)",
    "Hello there.",
    "CUT TO:",
    ">THE END<",
    "# Act One",
    "= A synopsis",
    "~la la la",
    "===",
    "[[a note]]",
    "/* boneyard */",
    "!Forced action",
    "**bold** and *italic* and _underline_",
    "Title: A Script",
]
fountain_text = st.lists(
    st.one_of(st.sampled_from(_LINE_FORMS), st.text(alphabet="ABCabc .*_\\^@!>#=~[]/()-:", max_size=12)),
    max_size=12,
).map("\n".join)


class TestParserProperties:
    @given(fountain_text)
    def test_parse_accepts_any_text(self, source: str) -> None:
        """Parsing is lenient: any input yields a document whose spans index into the element text."""
        document = FountainParser().parse(source)

        for element in document.elements:
            for span in element.formatting:
                assert 0 <= span.start <= span.end <= len(element.text)

    @given(st.text())
    def test_parse_accepts_arbitrary_unicode(self, source: str) -> None:
        """Arbitrary unicode, control characters included, never raises."""
        FountainParser().parse(source)

    @given(fountain_text)
    def test_json_round_trip_preserves_document(self, source: str) -> None:
        """from_json(to_json(document)) reproduces the document exactly."""
        document = FountainParser().parse(source)

        reconstructed = FountainDocument.from_json(document.to_json())

        assert reconstructed.to_dict() == document.to_dict()
