from fastmcp import FastMCP
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv
import os
import logging
logging.basicConfig(level=logging.INFO)

load_dotenv()
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
logging.info("connected")
cur = connection.cursor(cursor_factory = psycopg2.extras.RealDictCursor)
logging.info("Created cursor")
logging.info("Database setup complete")

mcp = FastMCP("MCP Demo Server")


@mcp.tool
def example_tool():
    return "This is an example tool."


if __name__ == "__main__":
    mcp.run()