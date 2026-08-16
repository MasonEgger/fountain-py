# ABOUTME: Structural typing contracts every renderer satisfies.
# TextRenderer covers string output (HTML, Fountain, plain text, FDX); BinaryRenderer covers byte output (PDF).
from typing import Protocol, runtime_checkable

from fountain.document import FountainDocument


@runtime_checkable
class TextRenderer(Protocol):
    """Structural contract for renderers that produce text output.

    Any object with a matching ``render`` method satisfies this protocol,
    regardless of inheritance.
    """

    def render(self, document: FountainDocument) -> str:
        """Render a document to a string.

        Args:
            document: The parsed document to render.

        Returns:
            The rendered text.
        """
        ...


@runtime_checkable
class BinaryRenderer(Protocol):
    """Structural contract for renderers that produce binary output.

    Any object with a matching ``render_bytes`` method satisfies this
    protocol, regardless of inheritance.
    """

    def render_bytes(self, document: FountainDocument) -> bytes:
        """Render a document to bytes.

        Args:
            document: The parsed document to render.

        Returns:
            The rendered bytes.
        """
        ...
