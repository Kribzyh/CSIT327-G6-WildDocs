"""Supabase client integration has been removed.

This module provides a minimal fallback so other parts of the codebase
that import `get_supabase_service` won't raise ImportError at import time.

If you need to restore Supabase support, restore the original
implementation from `services/supabase_client.py.bak`.
"""

class _StubService:
    def __getattr__(self, name):
        def _missing(*args, **kwargs):
            raise RuntimeError(
                "Supabase integration has been removed. Call to '%s' is not available." % name
            )
        return _missing

def get_supabase_service():
    """Return a stub service that raises clear errors if used."""
    return _StubService()