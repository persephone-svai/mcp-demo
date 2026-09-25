"""Customer service tools: every tool is scoped to the caller's own tenancy.

Column lists mirror the matching tools in mcp/tools/ so both servers describe
the same columns. Keep them in sync when a table changes.
"""
from fastmcp import FastMCP
from db import query
from tools.tenant_scope import caller_scope, require_mine

customer_service = FastMCP("customer_service")

# mcp/tools/lease.py
LEASE_COLS = ", ".join((
    "lease_id", "lease_number", "property_id", "tenant_id", "lease_type",
    "commencement_date", "expiration_date", "execution_date", "possession_date",
    "rent_commencement_date", "status", "original_term_months", "security_deposit",
    "currency_code",
))
# mcp/tools/property.py
PROPERTY_COLS = ", ".join((
    "property_id", "property_code", "property_name", "property_type", "subtype",
    "ownership_entity_id", "acquisition_date", "disposition_date",
    "acquisition_price", "current_status", "year_built", "year_renovated",
    "total_building_sf", "total_land_acres", "address_id", "latitude", "longitude",
))
# mcp/tools/building.py
BUILDING_COLS = ", ".join((
    "building_id", "property_id", "building_code", "building_name", "building_sf",
    "floor_count", "year_built", "construction_type", "address_id", "status",
))
# mcp/tools/asset.py
ASSET_COLS = ", ".join((
    "asset_id", "property_id", "building_id", "space_id", "asset_type", "asset_name",
    "manufacturer", "model", "serial_number", "installation_date", "useful_life_years",
    "replacement_cost", "status",
))
REPLACEMENT_DUE = "(installation_date + useful_life_years * interval '1 year')::date"
# mcp/tools/lease_rent_schedule.py
RENT_SCHEDULE_COLS = ", ".join((
    "rent_schedule_id", "lease_id", "charge_type", "start_date", "end_date", "amount",
    "amount_frequency", "rate_per_sf", "escalation_type", "escalation_percentage",
))
# mcp/tools/tenant_billing.py
BILL_COLS = ", ".join((
    "bill_id", "lease_id", "tenant_id", "charge_type", "billing_date",
    "due_date", "amount", "tax_amount", "status",
))
# mcp/tools/work_order.py
WORK_ORDER_COLS = ", ".join((
    "work_order_id", "property_id", "building_id", "space_id", "asset_id",
    "requested_by_party_id", "assigned_employee_id", "vendor_id", "priority",
    "work_type", "description", "created_at", "scheduled_date", "completed_at", "status",
))
# mcp/tools/tenant_improvement.py
TI_COLS = ", ".join((
    "ti_id", "lease_id", "property_id", "space_id", "approved_amount",
    "committed_amount", "actual_amount", "start_date", "completion_date",
))


def _lease_spaces(lease_id: int) -> list[int]:
    """space_ids a lease covers (smartreit.lease_space)."""
    return [r["space_id"] for r in query(
        "SELECT space_id FROM smartreit.lease_space WHERE lease_id = %s", (lease_id,))]


@customer_service.tool
def get_my_account() -> dict:
    """The caller's email and the IDs on their tenancy: party, tenant accounts,
    leases, and the properties, buildings and spaces those leases cover. Call first."""
    s = caller_scope()
    return {"email": s["email"], "party_ids": s["parties"], "tenant_ids": s["tenants"],
            "lease_ids": s["leases"], "property_ids": s["properties"],
            "building_ids": s["buildings"], "space_ids": s["spaces"]}


@customer_service.tool
def get_my_leases() -> list[dict]:
    """All leases on the caller's own tenancy, soonest-expiring first."""
    leases = caller_scope()["leases"]
    if not leases:
        return []
    return query(
        f"SELECT {LEASE_COLS} FROM smartreit.lease WHERE lease_id = ANY(%s) "
        "ORDER BY expiration_date NULLS LAST, lease_id",
        (leases,))


@customer_service.tool
def get_my_lease(lease_id: int) -> dict | None:
    """One of the caller's leases by lease_id, including its free-text
    lease_terms_notes. Errors if it isn't theirs."""
    require_mine("Lease", lease_id, caller_scope()["leases"])
    rows = query(f"SELECT {LEASE_COLS}, lease_terms_notes FROM smartreit.lease "
                 "WHERE lease_id = %s", (lease_id,))
    return rows[0] if rows else None


@customer_service.tool
def get_property(property_id: int) -> dict | None:
    """A property one of the caller's leases is at, by property_id. Errors if it isn't theirs."""
    require_mine("Property", property_id, caller_scope()["properties"])
    rows = query(f"SELECT {PROPERTY_COLS} FROM smartreit.property WHERE property_id = %s",
                 (property_id,))
    return rows[0] if rows else None


@customer_service.tool
def get_building(building_id: int) -> dict | None:
    """A building containing a space the caller leases, by building_id.
    Errors if it isn't theirs."""
    require_mine("Building", building_id, caller_scope()["buildings"])
    rows = query(f"SELECT {BUILDING_COLS} FROM smartreit.building WHERE building_id = %s",
                 (building_id,))
    return rows[0] if rows else None


@customer_service.tool
def get_rent_due(lease_id: int, current_only: bool = False) -> list[dict]:
    """Scheduled rent and charges for one of the caller's leases, by lease_id,
    ordered by start_date. amount is per amount_frequency. current_only=true
    returns only lines in effect today. Errors if the lease isn't theirs."""
    require_mine("Lease", lease_id, caller_scope()["leases"])
    current = (" AND start_date <= CURRENT_DATE "
               "AND (end_date IS NULL OR end_date >= CURRENT_DATE)") if current_only else ""
    return query(
        f"SELECT {RENT_SCHEDULE_COLS} FROM smartreit.lease_rent_schedule "
        f"WHERE lease_id = %s{current} ORDER BY start_date, rent_schedule_id",
        (lease_id,))


@customer_service.tool
def get_assets(lease_id: int) -> list[dict]:
    """Equipment (HVAC, etc.) in the spaces one of the caller's leases covers,
    by lease_id, with replacement_due_date. Errors if the lease isn't theirs."""
    require_mine("Lease", lease_id, caller_scope()["leases"])
    spaces = _lease_spaces(lease_id)
    if not spaces:
        return []
    return query(
        f"SELECT {ASSET_COLS}, {REPLACEMENT_DUE} AS replacement_due_date "
        "FROM smartreit.asset WHERE space_id = ANY(%s) ORDER BY asset_id",
        (spaces,))


@customer_service.tool
def get_billings(tenant_id: int) -> list[dict]:
    """All bills for one of the caller's tenant accounts, by tenant_id, newest first.
    Errors if it isn't theirs."""
    require_mine("Tenant", tenant_id, caller_scope()["tenants"])
    return query(
        f"SELECT {BILL_COLS} FROM smartreit.tenant_billing WHERE tenant_id = %s "
        "ORDER BY billing_date DESC, bill_id DESC",
        (tenant_id,))


@customer_service.tool
def get_work_orders(lease_id: int) -> list[dict]:
    """Work orders for one of the caller's leases, by lease_id, newest first:
    those on the lease's spaces, plus any the caller requested at the lease's
    property. Errors if the lease isn't theirs."""
    s = caller_scope()
    require_mine("Lease", lease_id, s["leases"])
    lease = query("SELECT property_id FROM smartreit.lease WHERE lease_id = %s", (lease_id,))
    property_id = lease[0]["property_id"] if lease else None
    return query(
        f"SELECT {WORK_ORDER_COLS} FROM smartreit.work_order "
        "WHERE space_id = ANY(%s) "
        "OR (requested_by_party_id = ANY(%s) AND property_id = %s) "
        "ORDER BY created_at DESC, work_order_id DESC",
        (_lease_spaces(lease_id), s["parties"], property_id))


@customer_service.tool
def get_tenant_improvements(lease_id: int) -> list[dict]:
    """Tenant improvements (build-out budgets and spend) for one of the caller's
    leases, by lease_id, newest start first. Errors if the lease isn't theirs."""
    require_mine("Lease", lease_id, caller_scope()["leases"])
    return query(
        f"SELECT {TI_COLS} FROM smartreit.tenant_improvement WHERE lease_id = %s "
        "ORDER BY start_date DESC NULLS LAST, ti_id DESC",
        (lease_id,))
