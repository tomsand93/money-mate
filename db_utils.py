"""
Database helper — request-scoped DB instance retrieval.
"""
import json
import logging
from flask import g

from auth import auth

logger = logging.getLogger(__name__)


def get_db():
    """
    Return the DB instance for the current request, creating it if needed.
    Caches result on Flask's g object to avoid re-creating within one request.
    """
    if hasattr(g, '_database'):
        return g._database

    if auth.is_authenticated():
        from supabase_db import SupabaseDatabase
        db = SupabaseDatabase()
        user_info = auth.get_current_user()
        if user_info:
            db.set_user(user_info['id'])
        g._database = db
        return db

    # Fallback: local SQLite (development / unauthenticated)
    from database import ExpenseDatabase
    with open('config.json', 'r', encoding='utf-8') as f:
        cfg = json.load(f)
    db = ExpenseDatabase(cfg['database_file'])
    g._database = db
    return db
