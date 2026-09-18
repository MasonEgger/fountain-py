# ABOUTME: Tests for the TextRenderer and BinaryRenderer protocols.
# Verifies structural typing (runtime_checkable) and top-level export from fountain.
import fountain
from fountain import BinaryRenderer, FountainRenderer, HTMLRenderer, TextRenderer
from fountain.document import FountainDocument


class TestTextRendererProtocol:
    def test_text_renderer_is_runtime_checkable(self) -> None:
        assert isinstance(HTMLRenderer(), TextRenderer)
        assert isinstance(FountainRenderer(), TextRenderer)


class TestBinaryRendererProtocol:
    def test_binary_renderer_protocol_shape(self) -> None:
        assert getattr(BinaryRenderer, "_is_runtime_protocol", False) is True

        class TrivialBinaryRenderer:
            def render_bytes(self, document: FountainDocument) -> bytes:
                return b""

        assert isinstance(TrivialBinaryRenderer(), BinaryRenderer)
        assert not isinstance(HTMLRenderer(), BinaryRenderer)


class TestProtocolsExported:
    def test_protocols_exported(self) -> None:
        assert "TextRenderer" in fountain.__all__
        assert "BinaryRenderer" in fountain.__all__
