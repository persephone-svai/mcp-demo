import logging
from pathlib import Path

from fastmcp import FastMCP

from tools import customer_service

logging.basicConfig(level=logging.INFO)

hr = FastMCP("smartreit-hr", instructions ="You are a human resources (HR) service assistant for employees. " \
"You can only see the caller's own account; the tools already know who they are. Call get_my_account first.")


hr.mount(customer_service.customer_service)


if __name__ == "__main__":
    hr.run(transport="http", host="0.0.0.0", port=9293)
