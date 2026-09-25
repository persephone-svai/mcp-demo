import logging
from pathlib import Path

from fastmcp import FastMCP
from mcp.tools.address import address
from mcp.tools.asset import asset
from mcp.tools.building import building
from mcp.tools.department import department
from mcp.tools.employee import employee
from mcp.tools.floor import floor
from mcp.tools.lease import lease
from mcp.tools.lease_party import lease_party
from mcp.tools.lease_rent_schedule import lease_rent_schedule
from mcp.tools.lease_space import lease_space
from mcp.tools.management_agreement import management_agreement
from mcp.tools.organization import organization
from mcp.tools.ownership_entity import ownership_entity
from mcp.tools.party import party
from mcp.tools.party_individual import party_individual
from mcp.tools.party_role import party_role
from mcp.tools.property import property_tools
from mcp.tools.property_operating_snapshot import property_operating_snapshot
from mcp.tools.security_deposit import security_deposit
from mcp.tools.space import space
from mcp.tools.tenant import tenant
from mcp.tools.tenant_billing import tenant_billing
from mcp.tools.tenant_improvement import tenant_improvement
from mcp.tools.vendor import vendor
from mcp.tools.work_order import work_order

logging.basicConfig(level=logging.INFO)

# Sent to the connecting agent as the server's instructions.
INSTRUCTIONS = (Path(__file__).parent / "AGENT_INSTRUCTIONS.md").read_text(encoding="utf-8")

mcp = FastMCP("smartreit", instructions=INSTRUCTIONS)

for server in (
    address, asset, building, department, employee, floor,
    lease, lease_party, lease_rent_schedule, lease_space,
    management_agreement, organization, ownership_entity,
    party, party_individual, party_role,
    property_tools, property_operating_snapshot, security_deposit, space,
    tenant, tenant_billing, tenant_improvement, vendor, work_order,
):
    mcp.mount(server)

if __name__ == "__main__":
    mcp.run()
