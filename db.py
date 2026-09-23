import logging
import os
from pathlib import Path
import psycopg2.extras
from psycopg2.pool import ThreadedConnectionPool
from dotenv import load_dotenv



load_dotenv(dotenv_path=Path(__file__).parent / ".env")
DATABASE_NAME = os.getenv("DATABASE_NAME")
DATABASE_HOST = os.getenv("DATABASE_HOST")
DATABASE_USER = os.getenv("DATABASE_USER")
DATABASE_PASSWORD = os.getenv("DATABASE_PASSWORD")
DATABASE_PORT = os.getenv("DATABASE_PORT")

pool = ThreadedConnectionPool(
    minconn=1, maxconn=5,
    host=DATABASE_HOST, user=DATABASE_USER, password=DATABASE_PASSWORD,
    port=DATABASE_PORT, dbname=DATABASE_NAME,
    cursor_factory=psycopg2.extras.RealDictCursor,
)

def query(sql, params=()):
    conn = pool.getconn()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            rows = cur.fetchall()
        conn.rollback()
        return rows
    except Exception:
        conn.rollback()
        raise
    finally:
        pool.putconn(conn)

def build_where(exact: dict, ranges: list[tuple[str, object]] = ()):
    """exact: {column: value}; ranges: [("col >= %s", value), ...].
    Skips None values. Returns (where_sql, params)."""
    where, params = [], []
    for col, val in exact.items():
        if val is not None:
            where.append(f"{col} = %s"); params.append(val)
    for clause, val in ranges:
        if val is not None:
            where.append(clause); params.append(val)
    return (" WHERE " + " AND ".join(where)) if where else "", params