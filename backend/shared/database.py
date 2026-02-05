"""
Supabase Database Client
"""
from __future__ import annotations

import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

_supabase_client: Client | None = None


def get_supabase() -> Client:
    """Gibt den Supabase Client zurück (Singleton Pattern)"""
    global _supabase_client
    if _supabase_client is None:
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")
        if not url or not key:
            raise ValueError("SUPABASE_URL und SUPABASE_KEY müssen in .env gesetzt sein")
        _supabase_client = create_client(url, key)
    return _supabase_client
