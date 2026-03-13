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

MAX_FILE_SIZE_BYTES: int = 10 * 1024 * 1024  # 10 MB default limit


def _strip_control_characters(text: str) -> str:
    """Remove control characters from *text*, preserving newlines."""
    return "".join(
        ch for ch in text
        if ch == "\n" or unicodedata.category(ch)[0] != "C"
    )


def _validate_path(path: str) -> str:
    """Resolve *path* and reject traversal attempts containing ``..``."""
    resolved = os.path.realpath(path)
    if ".." in os.path.normpath(path).split(os.sep):
        raise ParseError(
            f"Path traversal detected — refusing to open: {path}"
        )
    return resolved


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


def parse_file(
    path: str,
    *,
    max_size: int = MAX_FILE_SIZE_BYTES,
) -> TextDocument:
    """Read a UTF-8 file and return a ``TextDocument``.

    Parameters
    ----------
    path:
        Filesystem path to the text file.
    max_size:
        Maximum allowed file size in bytes (default 10 MB).

    Raises
    ------
    FileNotFoundError
        If *path* does not exist.
    ParseError
        If the file cannot be decoded as UTF-8, contains path traversal,
        exceeds *max_size*, or cannot be read due to permission errors.
    EmptyDocumentError
        If the file content is empty after stripping control characters.
    """
    resolved = _validate_path(path)

    try:
        size = os.path.getsize(resolved)
        if size > max_size:
            raise ParseError(
                f"File too large ({size} bytes, limit {max_size}): {path}"
            )
        with open(resolved, encoding="utf-8") as fh:
            raw = fh.read()
    except OSError as exc:
        if not os.path.exists(resolved):
            raise FileNotFoundError(f"File not found: {path}") from exc
        raise ParseError(f"Cannot read {path}: {exc}") from exc
    except UnicodeDecodeError as exc:
        raise ParseError(f"Cannot decode {path} as UTF-8: {exc}") from exc

    return parse_string(raw, source=path)
