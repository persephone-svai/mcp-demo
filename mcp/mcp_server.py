import logging
from pathlib import Path

from fastmcp import FastMCP
from tools.address import address
from tools.asset import asset
from tools.building import building
from tools.department import department
from tools.employee import employee
from tools.floor import floor
from tools.lease import lease
from tools.lease_party import lease_party
from tools.lease_rent_schedule import lease_rent_schedule
from tools.lease_space import lease_space
from tools.management_agreement import management_agreement
from tools.organization import organization
from tools.ownership_entity import ownership_entity
from tools.party import party
from tools.party_individual import party_individual
from tools.party_role import party_role
from tools.property import property_tools
from tools.property_operating_snapshot import property_operating_snapshot
from tools.security_deposit import security_deposit
from tools.space import space
from tools.tenant import tenant
from tools.tenant_billing import tenant_billing
from tools.tenant_improvement import tenant_improvement
from tools.vendor import vendor
from tools.work_order import work_order

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
