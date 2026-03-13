"""Sentiment analyzer — scores text positivity/negativity using a lexicon.

Counts tokens that appear in built-in positive/negative word lists,
computes a normalised score, and assigns a human-readable label.

Public API:
    POSITIVE_WORDS     — set of positive-sentiment words (≥30)
    NEGATIVE_WORDS     — set of negative-sentiment words (≥30)
    analyze_sentiment() — score a token list and return a SentimentResult
"""

from textanalyzer.core.models import Token, SentimentResult

POSITIVE_WORDS: set[str] = {
    "good", "great", "excellent", "wonderful", "fantastic", "amazing",
    "love", "happy", "joy", "beautiful", "brilliant", "outstanding",
    "superb", "perfect", "delightful", "pleasant", "terrific", "marvelous",
    "lovely", "nice", "fine", "awesome", "magnificent", "splendid",
    "glorious", "blessed", "grateful", "cheerful", "hopeful", "optimistic",
}

NEGATIVE_WORDS: set[str] = {
    "bad", "terrible", "awful", "horrible", "hate", "sad", "angry",
    "disgusting", "dreadful", "miserable", "pathetic", "poor", "ugly",
    "vile", "wretched", "nasty", "unpleasant", "disappointing", "inferior",
    "lousy", "atrocious", "appalling", "ghastly", "grim", "horrendous",
    "abysmal", "dire", "painful", "tragic", "worst",
}


def analyze_sentiment(tokens: list[Token]) -> SentimentResult:
    """Score sentiment of a token list using the built-in lexicons.

    Only non-stopword tokens are considered.  The score is computed as
    ``(positive_count - negative_count) / total_non_stopword_tokens``,
    clamped to [-1.0, 1.0].

    Args:
        tokens: Token objects (typically produced by ``tokenize()``).

    Returns:
        A SentimentResult with score, label, and per-polarity counts.
    """
    non_stopword_tokens = [t for t in tokens if not t.is_stopword]
    total = len(non_stopword_tokens)

    if total == 0:
        return SentimentResult(
            score=0.0,
            label="neutral",
            positive_count=0,
            negative_count=0,
        )

    positive_count = sum(1 for t in non_stopword_tokens if t.text in POSITIVE_WORDS)
    negative_count = sum(1 for t in non_stopword_tokens if t.text in NEGATIVE_WORDS)

    raw_score = (positive_count - negative_count) / total
    score = max(-1.0, min(1.0, raw_score))

    if score > 0.05:
        label = "positive"
    elif score < -0.05:
        label = "negative"
    else:
        label = "neutral"

    return SentimentResult(
        score=score,
        label=label,
        positive_count=positive_count,
        negative_count=negative_count,
    )
