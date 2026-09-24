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

@customer_service.tool
def get_property(property_id: int) -> dict | None:
    """One of the caller's properties by property_id. Errors if it isn't theirs."""
    s = caller_scope()
    property_ids = [lease["property_id"] for lease in query(
        f"SELECT {LEASE_COLS} FROM smartreit.lease WHERE lease_id = ANY(%s)",
        (s["leases"],)
    )]
    if property_id not in property_ids:
        raise PermissionError("Property not found in caller's leases")
    rows = query("SELECT * FROM smartreit.property WHERE property_id = %s", (property_id,))
    return rows[0] if rows else None

@customer_service.tool
def get_rent_due(lease_id: int) -> dict | None:
    """The due amounts for one of the caller's leases by lease_id. Errors if it isn't theirs."""
    ids = my_leases(lease_id, caller_scope()) 
    rows = query(f"SELECT * FROM smartreit.lease_rent_schedule WHERE lease_id = ANY(%s)", (ids,))
    return rows[0] if rows else None

@customer_service.tool
def get_asset(lease_id: int) -> dict | None:
    """One of the caller's assets by lease_id. Errors if it isn't theirs."""
    ids = my_leases(lease_id, caller_scope())
    rows = query(f"SELECT * FROM smartreit.asset WHERE lease_id = ANY(%s)", (ids,))
    return rows[0] if rows else None

@customer_service.tool
def get_building(building_id: int) -> dict | None:
    """One of the caller's buildings by building_id. Errors if it isn't theirs."""
    s = caller_scope()
    building_ids = [lease["building_id"] for lease in query(
        f"SELECT {LEASE_COLS} FROM smartreit.lease WHERE lease_id = ANY(%s)",
        (s["leases"],)
    )]
    if building_id not in building_ids:
        raise PermissionError("Building not found in caller's leases")
    rows = query("SELECT * FROM smartreit.building WHERE building_id = %s", (building_id,))
    return rows[0] if rows else None

@customer_service.tool
def get_billings(tenant_id: int) -> list[dict]:
    """All billings for one of the caller's tenants by tenant_id. Errors if it isn't theirs."""
    s = caller_scope()
    tenant_ids = [lease["tenant_id"] for lease in query(
        f"SELECT {LEASE_COLS} FROM smartreit.lease WHERE lease_id = ANY(%s)",
        (s["leases"],)
    )]
    if tenant_id not in tenant_ids:
        raise PermissionError("Tenant not found in caller's leases")
    return query("SELECT * FROM smartreit.billing WHERE tenant_id = %s", (tenant_id,))

@customer_service.tool
def get_work_orders(lease_id: int) -> list[dict]:
    """All work orders for one of the caller's leases by lease_id. Errors if it isn't theirs."""
    get_asset(lease_id)  # raises PermissionError if not theirs
    return query("SELECT * FROM smartreit.work_order WHERE lease_id = %s", (lease_id,))

@customer_service.tool
def get_tenant_improvements(tenant_id: int) -> list[dict]:
    """All tenant improvements for one of the caller's tenants by tenant_id. Errors if it isn't theirs."""
    s = caller_scope()
    tenant_ids = [lease["tenant_id"] for lease in query(
        f"SELECT {LEASE_COLS} FROM smartreit.lease WHERE lease_id = ANY(%s)",
        (s["leases"],)
    )]
    if tenant_id not in tenant_ids:
        raise PermissionError("Tenant not found in caller's leases")
    return query("SELECT * FROM smartreit.tenant_improvement WHERE tenant_id = %s", (tenant_id,))