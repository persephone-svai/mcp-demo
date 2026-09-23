"""Lease tools (the lease contract: parties, dates, term and status)."""
from datetime import date
from fastmcp import FastMCP
from db import query, build_where, cap_limit, distinct_values

lease = FastMCP("lease")

TABLE = "smartreit.lease"
LEASE_COLUMNS = (
    "lease_id", "lease_number", "property_id", "tenant_id", "lease_type",
    "commencement_date", "expiration_date", "execution_date", "possession_date",
    "rent_commencement_date", "status", "original_term_months", "security_deposit",
    "currency_code",
)
LEASE_COLS = ", ".join(LEASE_COLUMNS)


@lease.tool
def get_lease(lease_id: int | None = None, lease_number: str | None = None) -> dict | None:
    """Get one lease by lease_id or lease_number (give one), including its
    free-text lease_terms_notes. Returns null if not found.
    Related: find_lease_spaces, find_lease_rent_schedules, find_lease_parties."""
    if lease_id is None and lease_number is None:
        raise ValueError("Give lease_id or lease_number")
    where, params = build_where({"lease_id": lease_id, "lease_number": lease_number})
    rows = query(f"SELECT {LEASE_COLS}, lease_terms_notes FROM {TABLE}{where} LIMIT 1", params)
    return rows[0] if rows else None


@lease.tool
def find_leases(
    property_id: int | None = None,
    tenant_id: int | None = None,
    lease_type: str | None = None,
    status: str | None = None,
    currency_code: str | None = None,
    active_on: date | None = None,
    expiring_from: date | None = None,
    expiring_to: date | None = None,
    commenced_from: date | None = None,
    commenced_to: date | None = None,
    limit: int = 50,
) -> list[dict]:
    """Search leases. All filters optional, combined with AND.
    active_on returns leases in force on that date (commenced on or before it and
    not yet expired). expiring_from/expiring_to filter on expiration_date, e.g. for
    upcoming renewals. Ordered by expiration date, soonest first.
    Use lease_filter_values for valid lease_type, status and currency_code values."""
    where, params = build_where(
        {"property_id": property_id, "tenant_id": tenant_id, "lease_type": lease_type,
         "status": status, "currency_code": currency_code},
        [("commencement_date <= %s", active_on),
         ("(expiration_date IS NULL OR expiration_date >= %s)", active_on),
         ("expiration_date >= %s", expiring_from),
         ("expiration_date <= %s", expiring_to),
         ("commencement_date >= %s", commenced_from),
         ("commencement_date <= %s", commenced_to)],
    )
    sql = (f"SELECT {LEASE_COLS} FROM {TABLE}{where} "
           "ORDER BY expiration_date NULLS LAST, lease_id LIMIT %s")
    return query(sql, params + [cap_limit(limit)])


@lease.tool
def lease_summary(
    group_by: str = "status",
    property_id: int | None = None,
    active_on: date | None = None,
) -> list[dict]:
    """Count leases, total security deposits and average original term (months),
    grouped by one of: status, lease_type, property_id, tenant_id.
    Pass active_on (e.g. today) to count only leases in force on that date."""
    allowed = {"status", "lease_type", "property_id", "tenant_id"}
    if group_by not in allowed:
        raise ValueError(f"group_by must be one of {sorted(allowed)}")
    where, params = build_where(
        {"property_id": property_id},
        [("commencement_date <= %s", active_on),
         ("(expiration_date IS NULL OR expiration_date >= %s)", active_on)],
    )
    sql = (f"SELECT {group_by}, COUNT(*) AS leases, "
           "SUM(security_deposit) AS total_security_deposit, "
           "ROUND(AVG(original_term_months), 1) AS avg_term_months "
           f"FROM {TABLE}{where} GROUP BY {group_by} ORDER BY leases DESC")
    return query(sql, params)


@lease.tool
def lease_filter_values() -> dict:
    """List distinct lease_type, status and currency_code values in use, for find_leases."""
    return distinct_values(TABLE, ("lease_type", "status", "currency_code"))
