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

MAX_LIMIT = 200


def build_where(exact: dict, ranges: list[tuple[str, object]] = (),
                conditions: list[str] = ()):
    """Build a WHERE clause from optional filters.
    exact:      {column: value} -> "column = %s"
    ranges:     [("col >= %s", value), ...] -> clause with one %s
    conditions: ["col IS NULL", ...] -> fixed clauses with no parameter
    None values are skipped. Returns (where_sql, params)."""
    where, params = [], []
    for col, val in exact.items():
        if val is not None:
            where.append(f"{col} = %s"); params.append(val)
    for clause, val in ranges:
        if val is not None:
            where.append(clause); params.append(val)
    where.extend(conditions)
    return (" WHERE " + " AND ".join(where)) if where else "", params


def cap_limit(limit: int) -> int:
    """Keep a caller-supplied limit between 1 and MAX_LIMIT."""
    return max(1, min(limit, MAX_LIMIT))


def contains(text: str | None) -> str | None:
    """ILIKE pattern for a partial, case-insensitive match (None if no text)."""
    return f"%{text}%" if text else None


def distinct_values(table: str, columns: tuple[str, ...]) -> dict:
    """Distinct non-null values in use for each column (hardcoded names only)."""
    return {
        col: [r[col] for r in query(
            f"SELECT DISTINCT {col} FROM {table} WHERE {col} IS NOT NULL ORDER BY 1")]
        for col in columns
    }
