"""Text statistics — computes aggregate metrics for a document.

Owner: Team Alpha developer (see blackboard-alpha.md → alpha-statistics)

Implement:
    compute_statistics(document: TextDocument, tokens: list[Token]) -> StatisticsResult
        - char_count: len(document.content)
        - word_count: len(tokens) (all tokens, including stopwords)
        - sentence_count: count of sentence-ending punctuation (. ! ?) in document.content
        - avg_word_length: mean of len(token.text) for all tokens
        - vocabulary_size: number of unique token texts
        - lexical_diversity: vocabulary_size / word_count (0.0 if word_count is 0)
        - Return StatisticsResult

Dependencies: core.models (TextDocument, Token, StatisticsResult)
"""

from textanalyzer.core.models import TextDocument, Token, StatisticsResult

SENTENCE_ENDINGS = frozenset(".!?")


def compute_statistics(
    document: TextDocument, tokens: list[Token]
) -> StatisticsResult:
    """Compute aggregate text statistics for a document.

    Args:
        document: The parsed text document.
        tokens: All tokens produced by the tokenizer (including stopwords).

    Returns:
        A StatisticsResult with character, word, sentence, and diversity metrics.
    """
    char_count = len(document.content)
    word_count = len(tokens)
    sentence_count = sum(1 for ch in document.content if ch in SENTENCE_ENDINGS)

    if word_count > 0:
        avg_word_length = sum(len(t.text) for t in tokens) / word_count
    else:
        avg_word_length = 0.0

    vocabulary_size = len({t.text for t in tokens})
    lexical_diversity = vocabulary_size / word_count if word_count > 0 else 0.0

    return StatisticsResult(
        char_count=char_count,
        word_count=word_count,
        sentence_count=sentence_count,
        avg_word_length=avg_word_length,
        vocabulary_size=vocabulary_size,
        lexical_diversity=lexical_diversity,
    )
