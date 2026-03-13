"""Text file parser — converts raw text into TextDocument objects.

Provides two entry points for creating TextDocument instances:
    parse_file  — read a UTF-8 file from disk
    parse_string — create a document from an in-memory string

Dependencies: core.models (TextDocument, error types)
"""

import os
import unicodedata

from textanalyzer.core.models import (
    EmptyDocumentError,
    FileNotFoundError,
    ParseError,
    TextDocument,
)


def _strip_control_characters(text: str) -> str:
    """Remove control characters from *text*, preserving newlines."""
    return "".join(
        ch for ch in text
        if ch == "\n" or unicodedata.category(ch)[0] != "C"
    )


def parse_string(text: str, source: str = "<string>") -> TextDocument:
    """Create a ``TextDocument`` from an in-memory string.

    Parameters
    ----------
    text:
        Raw text content.
    source:
        Label describing where the text came from (default ``"<string>"``).

    Raises
    ------
    EmptyDocumentError
        If *text* is empty (or whitespace-only) after stripping.
    """
    content = _strip_control_characters(text)
    if not content.strip():
        raise EmptyDocumentError(f"Document from {source} is empty after stripping")

    return TextDocument(
        content=content,
        source=source,
        char_count=len(content),
        line_count=content.count("\n") + 1,
    )


def parse_file(path: str) -> TextDocument:
    """Read a UTF-8 file and return a ``TextDocument``.

    Parameters
    ----------
    path:
        Filesystem path to the text file.

    Raises
    ------
    FileNotFoundError
        If *path* does not exist.
    ParseError
        If the file cannot be decoded as UTF-8.
    EmptyDocumentError
        If the file content is empty after stripping control characters.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"File not found: {path}")

    try:
        with open(path, encoding="utf-8") as fh:
            raw = fh.read()
    except UnicodeDecodeError as exc:
        raise ParseError(f"Cannot decode {path} as UTF-8: {exc}") from exc

    return parse_string(raw, source=path)
