from fastmcp import FastMCP
from tools.space import space
from tools.tenant import tenant
from tools.tenant_billing import tenant_billing

mcp = FastMCP("smartreit")
mcp.mount(tenant)
mcp.mount(tenant_billing)
mcp.mount(space)

if __name__ == "__main__":
    mcp.run()