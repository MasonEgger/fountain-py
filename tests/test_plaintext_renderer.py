# ABOUTME: Tests for the monospace plain-text renderer.
# Covers column indentation, width wrapping, transition alignment, and writer-tool omission.
from fountain import FountainParser, PlainTextRenderer, TextRenderer
from fountain.document import FountainDocument
from fountain.elements import ElementType, FountainElement


def _leading_spaces(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


class TestRelativeIndents:
    def test_relative_indents(self) -> None:
        elements = [
            FountainElement(ElementType.SCENE_HEADING, "INT. HOUSE - DAY", [], 1),
            FountainElement(ElementType.ACTION, "John walks in.", [], 2),
            FountainElement(ElementType.CHARACTER, "JOHN", [], 3),
            FountainElement(ElementType.PARENTHETICAL, "(excited)", [], 4),
            FountainElement(ElementType.DIALOGUE, "Hello!", [], 5),
        ]
        document = FountainDocument(elements)
        output = PlainTextRenderer().render(document)
        lines = output.splitlines()

        scene_line = next(line for line in lines if "INT. HOUSE - DAY" in line)
        action_line = next(line for line in lines if "John walks in." in line)
        cue_line = next(line for line in lines if "JOHN" in line)
        parenthetical_line = next(line for line in lines if "(excited)" in line)
        dialogue_line = next(line for line in lines if "Hello!" in line)

        assert _leading_spaces(scene_line) == 0
        assert _leading_spaces(action_line) == 0

        cue_indent = _leading_spaces(cue_line)
        parenthetical_indent = _leading_spaces(parenthetical_line)
        dialogue_indent = _leading_spaces(dialogue_line)

        assert cue_indent > parenthetical_indent > dialogue_indent > 0


class TestWrapNeverExceedsWidth:
    def test_wrap_never_exceeds_width(self) -> None:
        long_text = " ".join(["word"] * 60)
        elements = [FountainElement(ElementType.ACTION, long_text, [], 1)]
        document = FountainDocument(elements)
        output = PlainTextRenderer(width=40).render(document)

        for line in output.splitlines():
            assert len(line) <= 40


class TestTransitionRightAligned:
    def test_transition_right_aligned(self) -> None:
        elements = [FountainElement(ElementType.TRANSITION, "CUT TO:", [], 1)]
        document = FountainDocument(elements)
        renderer = PlainTextRenderer()
        output = renderer.render(document)
        transition_line = next(line for line in output.splitlines() if "CUT TO:" in line)

        assert transition_line.endswith("CUT TO:")
        assert len(transition_line) == renderer.width


class TestTransitionWrapsWithinWidth:
    def test_transition_wraps_within_width(self) -> None:
        long_transition = "SMASH CUT TO THE NEXT SCENE IN THE HALLWAY:"
        elements = [FountainElement(ElementType.TRANSITION, long_transition, [], 1)]
        document = FountainDocument(elements)
        renderer = PlainTextRenderer(width=20)
        output = renderer.render(document)

        for line in output.splitlines():
            assert len(line) <= renderer.width


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
        output = PlainTextRenderer().render(document)

        assert "a private note" not in output
        assert "ACT ONE" not in output
        assert "A quiet summary" not in output
        assert "cut content" not in output
        assert "The scene continues." in output


class TestSatisfiesTextRenderer:
    def test_satisfies_text_renderer(self) -> None:
        assert isinstance(PlainTextRenderer(), TextRenderer)


class TestPageBreak:
    def test_page_break_is_full_width_divider(self) -> None:
        elements = [FountainElement(ElementType.PAGE_BREAK, "===", [], 1)]
        document = FountainDocument(elements)
        renderer = PlainTextRenderer(width=20)
        output = renderer.render(document)

        assert output == "=" * 20


class TestDualDialogue:
    def test_dual_dialogue_renders_left_then_right(self) -> None:
        text = "JOHN\nI can't believe it!\n\nSARAH^\nNeither can I!"
        document = FountainParser().parse(text)
        output = PlainTextRenderer().render(document)
        lines = output.splitlines()

        john_index = next(index for index, line in enumerate(lines) if "JOHN" in line)
        sarah_index = next(index for index, line in enumerate(lines) if "SARAH" in line)
        assert john_index < sarah_index
        assert "I can't believe it!" in output
        assert "Neither can I!" in output

    def test_dual_dialogue_missing_metadata_renders_nothing(self) -> None:
        elements = [FountainElement(ElementType.DUAL_DIALOGUE, "", [], 1, metadata={})]
        document = FountainDocument(elements)
        output = PlainTextRenderer().render(document)

        assert output == ""


class TestCenteredAndLyrics:
    def test_centered_flush_left_and_lyrics_indented(self) -> None:
        elements = [
            FountainElement(ElementType.CENTERED, "THE END", [], 1),
            FountainElement(ElementType.LYRICS, "La la la", [], 2),
        ]
        document = FountainDocument(elements)
        output = PlainTextRenderer().render(document)
        lines = output.splitlines()

        centered_line = next(line for line in lines if "THE END" in line)
        lyrics_line = next(line for line in lines if "La la la" in line)
        assert _leading_spaces(centered_line) == 0
        assert _leading_spaces(lyrics_line) > 0


class TestTitlePageFallback:
    def test_unhandled_element_type_falls_back_to_flush_left(self) -> None:
        elements = [FountainElement(ElementType.TITLE_PAGE, "Title: My Script", [], 1)]
        document = FountainDocument(elements)
        output = PlainTextRenderer().render(document)

        assert "Title: My Script" in output
        assert _leading_spaces(output) == 0
