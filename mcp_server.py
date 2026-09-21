from fastmcp import FastMCP
import psycopg2
import psycopg2.extras


mcp = FastMCP("MCP Demo Server")

@mcp.tool
def example_tool():
    return "This is an example tool."


if __name__ == "__main__":
    mcp.run()