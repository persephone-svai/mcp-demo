"""Who is the caller? Resolves the connection's tenant email to their tenancy."""
from fastmcp.server.dependencies import get_http_headers
from db import query

def caller_scope() -> dict:
    """The caller's email plus the IDs of their tenant accounts and leases."""
    headers = get_http_headers()
    email = headers.get("x-tenant-email")
    if not email:
        raise ValueError("Missing tenant email in headers")
    tenants = [r["tenant_id"] for r in query(
        "SELECT tenant_id FROM smartreit.tenant WHERE email = %s", (email,))]
    if not tenants:
        raise ValueError("Tenant not found")
    leases = [r["lease_id"] for r in query(
        "SELECT lease_id FROM smartreit.lease WHERE tenant_id = ANY(%s)", (tenants,))]
    return {"email": email, "tenants": tenants, "leases": leases}

def my_leases(lease_id: int, scope: dict) -> list[int]:
    """[lease_id] if it belongs to the caller; raises PermissionError otherwise."""
    if lease_id not in scope["leases"]:
        raise PermissionError(f"Lease {lease_id} is not on your account")
    return [lease_id]
