import logging

from fastmcp import FastMCP
from tools.party import party
from tools.property import property_tools
from tools.property_operating_snapshot import property_operating_snapshot
from tools.space import space
from tools.tenant import tenant
from tools.tenant_billing import tenant_billing
from tools.tenant_improvement import tenant_improvement
from tools.vendor import vendor
from tools.work_order import work_order

# Logs go to stderr; never print() in tools (stdout carries the MCP protocol).
logging.basicConfig(level=logging.INFO)

mcp = FastMCP("smartreit")

# security_deposit is not mounted yet: its columns are a copy of work_order's.
for server in (party, property_tools, property_operating_snapshot, space,
               tenant, tenant_billing, tenant_improvement, vendor, work_order):
    mcp.mount(server)

if __name__ == "__main__":
    mcp.run()
