"""Who is the caller? Resolves the connection's tenant email to their tenancy.

How the tables link (column names as in mcp/tools/*):
  party.primary_email        -> the caller's email
  tenant.party_id            -> party.party_id
  lease.tenant_id            -> tenant.tenant_id   (lease.property_id -> property)
  lease_space.lease_id       -> lease.lease_id     (lease_space.space_id -> space)
  space.building_id          -> building.building_id
"""
from fastmcp.server.dependencies import get_http_headers
from db import query


def caller_scope() -> dict:
    """The caller's email plus the IDs of everything on their tenancy:
    parties, tenant accounts, leases, and the properties, buildings and
    spaces those leases cover."""
    headers = get_http_headers()
    email = (headers.get("x-tenant-email") or "").strip()
    if not email:
        raise ValueError("Missing tenant email in headers")

    # smartreit.tenant has no email column; the email is on the tenant's party.
    rows = query(
        "SELECT t.tenant_id, t.party_id FROM smartreit.tenant t "
        "JOIN smartreit.party p ON p.party_id = t.party_id "
        "WHERE lower(p.primary_email) = lower(%s) ORDER BY t.tenant_id",
        (email,))
    if not rows:
        raise ValueError("Tenant not found")
    tenants = [r["tenant_id"] for r in rows]
    parties = sorted({r["party_id"] for r in rows})

    lease_rows = query(
        "SELECT lease_id, property_id FROM smartreit.lease "
        "WHERE tenant_id = ANY(%s) ORDER BY lease_id", (tenants,))
    leases = [r["lease_id"] for r in lease_rows]
    properties = sorted({r["property_id"] for r in lease_rows if r["property_id"] is not None})

    space_rows = query(
        "SELECT DISTINCT ls.space_id, s.building_id FROM smartreit.lease_space ls "
        "JOIN smartreit.space s ON s.space_id = ls.space_id "
        "WHERE ls.lease_id = ANY(%s)", (leases,))
    spaces = sorted({r["space_id"] for r in space_rows})
    buildings = sorted({r["building_id"] for r in space_rows if r["building_id"] is not None})

    return {"email": email, "parties": parties, "tenants": tenants, "leases": leases,
            "properties": properties, "buildings": buildings, "spaces": spaces}


def require_mine(kind: str, value: int, allowed: list[int]) -> None:
    """Raise PermissionError unless value is one of the caller's IDs of this kind."""
    if value not in allowed:
        raise PermissionError(f"{kind} {value} is not on your account")
