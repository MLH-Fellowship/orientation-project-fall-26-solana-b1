"""
Utilities for auto-generating and sanitizing conversation titles.
"""

DEFAULT_TITLE = "New Conversation"

_FALLBACK_MAX_LEN = 50
_LLM_MAX_LEN = 80


def fallback_title(user_content: str, max_len: int = _FALLBACK_MAX_LEN) -> str:
    """
    Return the first `max_len` characters of the user's message, normalized
    and truncated at a word boundary where possible.
    """
    text = " ".join(user_content.split())
    if len(text) <= max_len:
        return text
    truncated = text[:max_len]

    last_space = truncated.rfind(" ")
    if last_space > 0:
        truncated = truncated[:last_space]
    return truncated + "…"


def normalize_llm_title(raw: str, max_len: int = _LLM_MAX_LEN) -> str | None:
    """
    Sanitize a raw LLM title string.

    Returns None if the result is unusable (empty or too long after cleanup),
    so the caller can fall back to `fallback_title`.
    """
    title = raw.strip().strip("\"'")
    if not title or len(title) > max_len:
        return None
    return title


def resolve_title(user_content: str, assistant_content: str, llm_generate: callable) -> str:
    """
    Try to get a title from `llm_generate()`, clean it up, and return it.
    Falls back to `fallback_title(user_content)` if generation raises or
    returns unusable text.
    """
    try:
        raw = llm_generate()
        title = normalize_llm_title(raw)
        if title:
            return title
    except Exception:
        pass
    return fallback_title(user_content)
