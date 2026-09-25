import logging
from pathlib import Path
from fastmcp import FastMCP
from customer_service.tools import customer_service
logging.basicConfig(level=logging.INFO)

CS_INSTRUCTIONS = """
You are a customer service assistant for tenants. You can only see the caller's own
account; the tools already know who they are. Call get_my_account first. ...
"""

cs = FastMCP("smartreit", instructions=CS_INSTRUCTIONS)
cs.mount(customer_service)




if __name__ == "__main__":
    cs.run()
