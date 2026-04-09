import os

_langfuse = None
_init_attempted = False


def get_langfuse():
    """Return the Langfuse client singleton, or None if not configured."""
    global _langfuse, _init_attempted
    if _init_attempted:
        return _langfuse

    _init_attempted = True
    public_key = os.environ.get("LANGFUSE_PUBLIC_KEY", "")
    if not public_key:
        return None

    try:
        from langfuse import Langfuse
        _langfuse = Langfuse()
        return _langfuse
    except Exception:
        return None
