"""Unit tests for textanalyzer.core.parser — parse_file and parse_string."""

import os
import tempfile

import pytest
from textanalyzer.core.models import TextDocument, EmptyDocumentError, ParseError
from textanalyzer.core.models import FileNotFoundError as TAFileNotFoundError
from textanalyzer.core.parser import parse_file, parse_string


class TestParseString:
    def test_happy_path(self):
        doc = parse_string("Hello world")
        assert isinstance(doc, TextDocument)
        assert doc.content == "Hello world"
        assert doc.source == "<string>"

    def test_custom_source(self):
        doc = parse_string("test", source="custom")
        assert doc.source == "custom"

    def test_empty_string_raises(self):
        with pytest.raises(EmptyDocumentError):
            parse_string("")

    def test_whitespace_only_raises(self):
        with pytest.raises(EmptyDocumentError):
            parse_string("   \n\t  ")

    def test_multiline_string(self):
        doc = parse_string("line1\nline2\nline3")
        assert doc.line_count == 3


class TestParseFile:
    def test_happy_path(self, tmp_path):
        f = tmp_path / "test.txt"
        f.write_text("Hello world", encoding="utf-8")
        doc = parse_file(str(f))
        assert isinstance(doc, TextDocument)
        assert doc.content == "Hello world"
        assert doc.source == str(f)

    def test_missing_file_raises(self):
        with pytest.raises(TAFileNotFoundError):
            parse_file("/nonexistent/path/to/file.txt")

    def test_empty_file_raises(self, tmp_path):
        f = tmp_path / "empty.txt"
        f.write_text("", encoding="utf-8")
        with pytest.raises(EmptyDocumentError):
            parse_file(str(f))

    def test_utf8_encoding(self, tmp_path):
        f = tmp_path / "unicode.txt"
        f.write_text("café résumé naïve", encoding="utf-8")
        doc = parse_file(str(f))
        assert "café" in doc.content

    def test_char_and_line_counts(self, tmp_path):
        content = "line1\nline2"
        f = tmp_path / "counted.txt"
        f.write_text(content, encoding="utf-8")
        doc = parse_file(str(f))
        assert doc.char_count == len(content)
        assert doc.line_count == 2
