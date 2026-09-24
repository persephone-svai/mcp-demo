import logging
from pathlib import Path

from fastmcp import FastMCP

from tools import employee, department, customer_service

logging.basicConfig(level=logging.INFO)

mcp = FastMCP("smartreit", instructions ="You are a customer service assistant for tenants. " \
"You can only see the caller's own account; the tools already know who they are. Call get_my_account first.")




for server in (
    employee, department
): 
    mcp.mount(server)


if __name__ == "__main__":
    mcp.run()
