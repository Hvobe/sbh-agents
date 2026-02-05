"""
PostgreSQL Database Client
"""
from __future__ import annotations

import os
import json
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()

_connection = None


def get_connection():
    """Gibt die PostgreSQL Connection zurück (Singleton Pattern)"""
    global _connection
    if _connection is None or _connection.closed:
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            raise ValueError("DATABASE_URL muss in .env gesetzt sein")
        _connection = psycopg2.connect(database_url)
    return _connection


def execute_query(query: str, params: tuple = None, fetch: bool = True) -> list[dict] | None:
    """Führt eine SQL-Query aus und gibt Ergebnisse als Liste von Dicts zurück"""
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, params)
            if fetch:
                return [dict(row) for row in cur.fetchall()]
            conn.commit()
            return None
    except Exception as e:
        conn.rollback()
        raise e


def execute_insert(table: str, data: dict) -> dict | None:
    """Fügt einen Datensatz ein und gibt ihn zurück"""
    columns = ", ".join(data.keys())
    placeholders = ", ".join(["%s"] * len(data))
    query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders}) RETURNING *"

    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, tuple(data.values()))
            result = cur.fetchone()
            conn.commit()
            return dict(result) if result else None
    except Exception as e:
        conn.rollback()
        raise e


def execute_update(table: str, data: dict, where: str, where_params: tuple) -> dict | None:
    """Aktualisiert einen Datensatz und gibt ihn zurück"""
    set_clause = ", ".join([f"{k} = %s" for k in data.keys()])
    query = f"UPDATE {table} SET {set_clause} WHERE {where} RETURNING *"

    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, tuple(data.values()) + where_params)
            result = cur.fetchone()
            conn.commit()
            return dict(result) if result else None
    except Exception as e:
        conn.rollback()
        raise e


# Kompatibilitäts-Wrapper für bestehenden Code
class SupabaseCompatTable:
    """Wrapper der Supabase-ähnliche Syntax auf psycopg2 mappt"""

    def __init__(self, table_name: str):
        self.table_name = table_name
        self._select_columns = "*"
        self._where_clauses = []
        self._where_params = []
        self._order_by = None
        self._order_desc = False
        self._limit_val = None
        self._single = False

    def select(self, columns: str = "*"):
        self._select_columns = columns
        return self

    def eq(self, column: str, value):
        self._where_clauses.append(f"{column} = %s")
        self._where_params.append(value)
        return self

    def order(self, column: str, desc: bool = False):
        self._order_by = column
        self._order_desc = desc
        return self

    def limit(self, count: int):
        self._limit_val = count
        return self

    def single(self):
        self._single = True
        return self

    def insert(self, data: dict):
        self._insert_data = data
        return self

    def update(self, data: dict):
        self._update_data = data
        return self

    def execute(self):
        # INSERT
        if hasattr(self, '_insert_data'):
            result = execute_insert(self.table_name, self._insert_data)
            return _SupabaseResult([result] if result else [])

        # UPDATE
        if hasattr(self, '_update_data'):
            if not self._where_clauses:
                raise ValueError("UPDATE ohne WHERE nicht erlaubt")
            where = " AND ".join(self._where_clauses)
            result = execute_update(self.table_name, self._update_data, where, tuple(self._where_params))
            return _SupabaseResult([result] if result else [])

        # SELECT
        query = f"SELECT {self._select_columns} FROM {self.table_name}"

        if self._where_clauses:
            query += " WHERE " + " AND ".join(self._where_clauses)

        if self._order_by:
            query += f" ORDER BY {self._order_by}"
            if self._order_desc:
                query += " DESC"

        if self._limit_val:
            query += f" LIMIT {self._limit_val}"

        results = execute_query(query, tuple(self._where_params) if self._where_params else None)

        if self._single:
            return _SupabaseResult(results[:1] if results else [], single=True)

        return _SupabaseResult(results or [])


class _SupabaseResult:
    """Wrapper für Supabase-ähnliches Result-Format"""

    def __init__(self, data: list, single: bool = False):
        if single:
            self.data = data[0] if data else None
        else:
            self.data = data


class SupabaseCompat:
    """Kompatibilitäts-Layer der Supabase-Syntax auf PostgreSQL mappt"""

    def table(self, name: str) -> SupabaseCompatTable:
        return SupabaseCompatTable(name)


def get_supabase():
    """Gibt einen Supabase-kompatiblen Client zurück"""
    return SupabaseCompat()
