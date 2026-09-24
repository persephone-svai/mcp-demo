"""Customer service tools: every tool is scoped to the caller's own tenancy."""
from fastmcp import FastMCP
from db import query
from tools.tenant_scope import caller_scope, my_leases

customer_service = FastMCP("customer_service")

LEASE_COLUMNS = (
    "lease_id", "lease_number", "property_id", "lease_type", "commencement_date",
    "expiration_date", "rent_commencement_date", "status", "original_term_months",
    "security_deposit", "currency_code",
)
LEASE_COLS = ", ".join(LEASE_COLUMNS)


@customer_service.tool
def get_my_account() -> dict:
    """The caller's email and the IDs of their leases and tenant accounts. Call first."""
    s = caller_scope()
    return {"email": s["email"], "lease_ids": s["leases"], "tenant_ids": s["tenants"]}


@customer_service.tool
def get_my_lease(lease_id: int) -> dict | None:
    """One of the caller's leases by lease_id. Errors if it isn't theirs."""
    ids = my_leases(lease_id, caller_scope())   # raises PermissionError if not theirs
    rows = query(f"SELECT {LEASE_COLS} FROM smartreit.lease WHERE lease_id = ANY(%s)", (ids,))
    return rows[0] if rows else None


@customer_service.tool
def get_my_leases() -> list[dict]:
    """All leases on the caller's own tenancy, soonest-expiring first."""
    leases = caller_scope()["leases"]
    if not leases:
        return []
    return query(
        f"SELECT {LEASE_COLS} FROM smartreit.lease WHERE lease_id = ANY(%s) "
        "ORDER BY expiration_date NULLS LAST, lease_id",
        (leases,),
    )


