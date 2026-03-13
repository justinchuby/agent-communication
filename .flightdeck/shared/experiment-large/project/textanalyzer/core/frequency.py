"""Word frequency analyzer — counts word occurrences in token lists.

Owner: Team Alpha developer (see blackboard-alpha.md → alpha-frequency)

Implement:
    word_frequency(tokens: list[Token], top_n: int | None = None) -> FrequencyResult
        - Count occurrences of each token text (excluding stopwords if marked)
        - Compute relative frequency: count / total_non_stopword_tokens
        - Sort by count descending
        - If top_n is set, limit frequencies dict to top N entries
        - Return FrequencyResult with total_tokens, unique_tokens, frequencies, relative_frequencies

Dependencies: core.models (Token, FrequencyResult)
"""

from collections import Counter

from textanalyzer.core.models import Token, FrequencyResult


def word_frequency(
    tokens: list[Token], top_n: int | None = None
) -> FrequencyResult:
    """Count word occurrences in a token list, excluding stopwords.

    Args:
        tokens: List of Token objects from the tokenizer.
        top_n: If set, limit results to the N most frequent words.

    Returns:
        FrequencyResult with counts, relative frequencies, and totals.
    """
    non_stopword = [t for t in tokens if not t.is_stopword]
    total = len(non_stopword)

    counts = Counter(t.text for t in non_stopword)

    # Sort by count descending, then alphabetically for stable ordering
    sorted_items = sorted(counts.items(), key=lambda item: (-item[1], item[0]))

    if top_n is not None:
        sorted_items = sorted_items[:top_n]

    frequencies = dict(sorted_items)
    relative_frequencies = (
        {word: count / total for word, count in frequencies.items()}
        if total > 0
        else {}
    )

    return FrequencyResult(
        total_tokens=total,
        unique_tokens=len(set(t.text for t in non_stopword)),
        frequencies=frequencies,
        relative_frequencies=relative_frequencies,
    )
