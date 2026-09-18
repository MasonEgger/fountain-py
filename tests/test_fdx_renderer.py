# ABOUTME: Tests for the Final Draft (FDX) XML renderer.
# Covers well-formedness, per-type paragraph mapping, title page, dual dialogue, and writer-tool omission.
import xml.etree.ElementTree as ET
from pathlib import Path

from fountain import FountainParser, TextRenderer
from fountain.document import FountainDocument
from fountain.elements import ElementType, FountainElement
from fountain.renderers.fdx import FDXRenderer

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def _dual_dialogue_paragraphs(root: ET.Element) -> list[tuple[str, str]]:
    """Extract (Type, Text) pairs from the first DualDialogue block in an FDX tree."""
    dual_dialogue = root.find(".//DualDialogue")
    assert dual_dialogue is not None
    pairs = []
    for paragraph in dual_dialogue.findall("Paragraph"):
        text_element = paragraph.find("Text")
        assert text_element is not None
        pairs.append((paragraph.get("Type", ""), text_element.text or ""))
    return pairs


class TestWellFormedXml:
    def test_output_is_wellformed_xml(self) -> None:
        document = FountainDocument([FountainElement(ElementType.ACTION, "He runs.", [], 1)])
        output = FDXRenderer().render(document)
        root = ET.fromstring(output)
        assert root.tag == "FinalDraft"


class TestParagraphTypeMapping:
    def test_paragraph_type_mapping(self) -> None:
        elements = [
            FountainElement(ElementType.SCENE_HEADING, "INT. HOUSE - DAY", [], 1),
            FountainElement(ElementType.ACTION, "John walks in.", [], 2),
            FountainElement(ElementType.CHARACTER, "JOHN", [], 3),
            FountainElement(ElementType.PARENTHETICAL, "(excited)", [], 4),
            FountainElement(ElementType.DIALOGUE, "Hello!", [], 5),
            FountainElement(ElementType.TRANSITION, "CUT TO:", [], 6),
        ]
        document = FountainDocument(elements)
        root = ET.fromstring(FDXRenderer().render(document))

        expected = {
            "Scene Heading": "INT. HOUSE - DAY",
            "Action": "John walks in.",
            "Character": "JOHN",
            "Parenthetical": "(excited)",
            "Dialogue": "Hello!",
            "Transition": "CUT TO:",
        }
        for paragraph_type, text in expected.items():
            matches = [paragraph for paragraph in root.iter("Paragraph") if paragraph.get("Type") == paragraph_type]
            assert len(matches) == 1
            text_element = matches[0].find("Text")
            assert text_element is not None
            assert text_element.text == text


class TestTitlePageMaps:
    def test_title_page_maps(self) -> None:
        source = "Title: My Screenplay\nAuthor: Jane Doe\n\nINT. HOUSE - DAY\n\nAction here.\n"
        document = FountainParser().parse(source)
        root = ET.fromstring(FDXRenderer().render(document))

        title_page = root.find("TitlePage")
        assert title_page is not None

        texts = [text_element.text for text_element in title_page.iter("Text")]
        assert "My Screenplay" in texts
        assert "Jane Doe" in texts


class TestDualDialogueEmitsBothBlocks:
    def test_dual_dialogue_emits_both_blocks(self) -> None:
        document = FountainParser().parse("BRICK\nHi.\n\nSTEEL^\nHello.")
        root = ET.fromstring(FDXRenderer().render(document))

        rendered_pairs = _dual_dialogue_paragraphs(root)

        fixture_root = ET.parse(FIXTURES_DIR / "dual_dialogue.fdx").getroot()
        fixture_pairs = _dual_dialogue_paragraphs(fixture_root)

        assert rendered_pairs == fixture_pairs
        assert any(text == "BRICK" for paragraph_type, text in rendered_pairs if paragraph_type == "Character")
        assert any(text == "STEEL" for paragraph_type, text in rendered_pairs if paragraph_type == "Character")


class TestCenteredAndLyricsMapping:
    def test_centered_maps_to_action_with_alignment(self) -> None:
        document = FountainDocument([FountainElement(ElementType.CENTERED, "THE END", [], 1)])
        root = ET.fromstring(FDXRenderer().render(document))

        paragraph = root.find(".//Paragraph[@Type='Action']")
        assert paragraph is not None
        assert paragraph.get("Alignment") == "Center"
        text_element = paragraph.find("Text")
        assert text_element is not None
        assert text_element.text == "THE END"

    def test_lyrics_maps_to_dialogue_without_alignment(self) -> None:
        document = FountainDocument([FountainElement(ElementType.LYRICS, "La la la", [], 1)])
        root = ET.fromstring(FDXRenderer().render(document))

        paragraph = root.find(".//Paragraph[@Type='Dialogue']")
        assert paragraph is not None
        assert paragraph.get("Alignment") is None


class TestUnmappedTypesAreSkipped:
    def test_page_break_produces_no_paragraph(self) -> None:
        elements = [
            FountainElement(ElementType.PAGE_BREAK, "===", [], 1),
            FountainElement(ElementType.ACTION, "The scene continues.", [], 2),
        ]
        document = FountainDocument(elements)
        root = ET.fromstring(FDXRenderer().render(document))

        assert len(list(root.iter("Paragraph"))) == 1


class TestDualDialogueMissingMetadata:
    def test_dual_dialogue_missing_metadata_renders_nothing(self) -> None:
        document = FountainDocument([FountainElement(ElementType.DUAL_DIALOGUE, "", [], 1, metadata={})])
        root = ET.fromstring(FDXRenderer().render(document))

        assert root.find(".//DualDialogue") is None


class TestWriterToolsOmitted:
    def test_writer_tools_omitted(self) -> None:
        elements = [
            FountainElement(ElementType.NOTE, "[[a private note]]", [], 1),
            FountainElement(ElementType.SECTION, "ACT ONE", [], 2),
            FountainElement(ElementType.SYNOPSIS, "A quiet summary", [], 3),
            FountainElement(ElementType.BONEYARD, "/* cut content */", [], 4),
            FountainElement(ElementType.ACTION, "The scene continues.", [], 5),
        ]
        document = FountainDocument(elements)
        output = FDXRenderer().render(document)

        assert "a private note" not in output
        assert "ACT ONE" not in output
        assert "A quiet summary" not in output
        assert "cut content" not in output
        assert "The scene continues." in output


class TestSatisfiesTextRenderer:
    def test_satisfies_text_renderer(self) -> None:
        assert isinstance(FDXRenderer(), TextRenderer)
