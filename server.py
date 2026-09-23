from anyio import Path
from fastmcp import FastMCP
from psycopg.rows import dict_row
import psycopg2
import psycopg2.extras
from psycopg2.pool import ThreadedConnectionPool
from dotenv import load_dotenv
import os
import logging
logging.basicConfig(level=logging.INFO)

load_dotenv(dotenv_path=Path(__file__).parent / ".env")
DATABASE_NAME = os.getenv("DATABASE_NAME")
DATABASE_HOST = os.getenv("DATABASE_HOST")
DATABASE_USER = os.getenv("DATABASE_USER")
DATABASE_PASSWORD = os.getenv("DATABASE_PASSWORD")
DATABASE_PORT = os.getenv("DATABASE_PORT")

logging.info("connecting to the database")
connection = psycopg2.connect(
    host=DATABASE_HOST,
    user=DATABASE_USER,
    password=DATABASE_PASSWORD,
    port=DATABASE_PORT,
    dbname=DATABASE_NAME,
    cursor_factory=psycopg2.extras.DictCursor
)

pool = ThreadedConnectionPool(
    minconn=1,
    maxconn=10,
    host=DATABASE_HOST,
    user=DATABASE_USER,
    password=DATABASE_PASSWORD,
    port=DATABASE_PORT,
    dbname=DATABASE_NAME,
    cursor_factory=psycopg2.extras.DictCursor
)

def query(sql, params=()):
    conn = pool.getconn()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            if cur.description:
                return cur.fetchall()
            return None
    finally:
        pool.putconn(conn)

logging.info(f"host={DATABASE_HOST!r} user={DATABASE_USER!r} port={DATABASE_PORT!r} pw_set={bool(DATABASE_PASSWORD)}")
logging.info("connected")
cur = connection.cursor(cursor_factory = psycopg2.extras.RealDictCursor)
logging.info("Created cursor")
logging.info("Database setup complete")

mcp = FastMCP("MCP Demo Server")

if __name__ == "__main__":
    mcp.run()