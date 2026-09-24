"""Who is the caller? Resolves the connection's tenant email to their tenancy."""
from fastmcp.server.dependencies import get_http_headers
from db import query

def caller_scope() -> dict:
    """Return the caller's own account information based on their email."""
    headers = get_http_headers()
    email = headers.get("x-tenant-email")
    if not email:
        raise ValueError("Missing tenant email in headers")
    result = query("SELECT * FROM smartreit.tenant WHERE email = %s", (email,))
    if not result:
        raise ValueError("Tenant not found")
    return result[0]

def my_leases(tenant_id: int) -> list[dict]:
    """Return all leases for the given tenant."""
    leases = query("SELECT * FROM smartreit.lease WHERE tenant_id = %s", (tenant_id,))
    lease_id = [lease["lease_id"] for lease in leases]
    return lease_id
