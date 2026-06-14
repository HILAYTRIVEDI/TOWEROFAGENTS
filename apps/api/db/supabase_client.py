from typing import Any

from core.config import Settings


def create_supabase_client(settings: Settings) -> Any:
    if not settings.supabase_url or not settings.supabase_service_role_key:
        raise RuntimeError("Supabase is not configured")

    from supabase import create_client

    return create_client(settings.supabase_url, settings.supabase_service_role_key)

