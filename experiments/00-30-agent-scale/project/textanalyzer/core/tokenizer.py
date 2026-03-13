"""Tokenizer — splits documents into individual tokens.

Splits document content on whitespace and punctuation, lowercases,
strips leading/trailing punctuation, filters empty strings, and
assigns sequential position indices starting from 0.

Public API:
    STOP_WORDS  — set of common English stop words
    tokenize()  — convert a TextDocument into a list of Token objects
"""

import re
import string

from textanalyzer.core.models import TextDocument, Token

STOP_WORDS: set[str] = {
    "a", "an", "the", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "can", "shall", "to", "of", "in", "for",
    "on", "with", "at", "by", "from",
}

_SPLIT_PATTERN = re.compile(r"[\s" + re.escape(string.punctuation) + r"]+")


def tokenize(
    document: TextDocument,
    remove_stopwords: bool = False,
) -> list[Token]:
    """Tokenize a document into a list of Token objects.

    Args:
        document: The TextDocument to tokenize.
        remove_stopwords: When True, tokens whose lowercased text appears
            in STOP_WORDS have ``is_stopword`` set to True.  They are still
            included in the output list.

    Returns:
        A list of Token objects with sequential position indices.
    """
    raw_parts = _SPLIT_PATTERN.split(document.content)
    words = [w.lower().strip(string.punctuation) for w in raw_parts]
    words = [w for w in words if w]

    tokens: list[Token] = []
    for position, word in enumerate(words):
        is_stopword = remove_stopwords and word in STOP_WORDS
        tokens.append(Token(text=word, position=position, is_stopword=is_stopword))

    return tokens
