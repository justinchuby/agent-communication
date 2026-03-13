"""Unit tests for textanalyzer.core.tokenizer — tokenize function."""

import pytest
from textanalyzer.core.models import TextDocument, Token
from textanalyzer.core.tokenizer import tokenize, STOP_WORDS


class TestTokenize:
    def _make_doc(self, text):
        return TextDocument(
            content=text,
            source="<string>",
            char_count=len(text),
            line_count=text.count("\n") + 1,
        )

    def test_basic_split(self):
        doc = self._make_doc("Hello World")
        tokens = tokenize(doc)
        texts = [t.text for t in tokens]
        assert "hello" in texts
        assert "world" in texts
        assert len(tokens) == 2

    def test_punctuation_stripping(self):
        doc = self._make_doc("hello, world! foo.")
        tokens = tokenize(doc)
        texts = [t.text for t in tokens]
        assert "hello" in texts
        assert "world" in texts
        assert "foo" in texts
        # No punctuation-only tokens
        assert all(t.text.isalpha() or t.text.isalnum() for t in tokens if t.text)

    def test_lowercase(self):
        doc = self._make_doc("HELLO World FoO")
        tokens = tokenize(doc)
        assert all(t.text == t.text.lower() for t in tokens)

    def test_stopword_marking(self):
        doc = self._make_doc("the cat is on the mat")
        tokens = tokenize(doc, remove_stopwords=True)
        stopword_texts = {t.text for t in tokens if t.is_stopword}
        non_stopword_texts = {t.text for t in tokens if not t.is_stopword}
        assert "the" in stopword_texts
        assert "is" in stopword_texts
        assert "on" in stopword_texts
        assert "cat" in non_stopword_texts
        assert "mat" in non_stopword_texts

    def test_empty_document(self):
        doc = self._make_doc("")
        tokens = tokenize(doc)
        assert tokens == []

    def test_sequential_positions(self):
        doc = self._make_doc("one two three")
        tokens = tokenize(doc)
        positions = [t.position for t in tokens]
        assert positions == [0, 1, 2]

    def test_stop_words_set_exists(self):
        assert isinstance(STOP_WORDS, set)
        assert len(STOP_WORDS) >= 30
        assert "the" in STOP_WORDS
        assert "a" in STOP_WORDS

    def test_tokens_are_token_instances(self):
        doc = self._make_doc("word")
        tokens = tokenize(doc)
        assert all(isinstance(t, Token) for t in tokens)
