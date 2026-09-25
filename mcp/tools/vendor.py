"""Vendor tools (contractors and service providers)."""
from datetime import date
from fastmcp import FastMCP
from customer_service.db import query, build_where, cap_limit, distinct_values

vendor = FastMCP("vendor")

TABLE = "smartreit.vendor"
VENDOR_COLUMNS = (
    "vendor_id", "party_id", "vendor_type", "tax_id", "insurance_expiration", "status",
)
VENDOR_COLS = ", ".join(VENDOR_COLUMNS)


@vendor.tool
def get_vendor(vendor_id: int) -> dict | None:
    """Get a single vendor by vendor_id. Returns null if not found.
    Vendor names live on the party record (see party_id / find_parties)."""
    rows = query(f"SELECT {VENDOR_COLS} FROM {TABLE} WHERE vendor_id = %s", (vendor_id,))
    return rows[0] if rows else None


@vendor.tool
def find_vendors(
    party_id: int | None = None,
    vendor_type: str | None = None,
    status: str | None = None,
    insurance_expires_before: date | None = None,
    insurance_expires_after: date | None = None,
    limit: int = 50,
) -> list[dict]:
    """Search vendors. All filters optional, combined with AND.
    Use insurance_expires_before to find vendors whose insurance has lapsed or
    is about to. Use vendor_filter_values to see valid vendor_type and status values."""
    where, params = build_where(
        {"party_id": party_id, "vendor_type": vendor_type, "status": status},
        [("insurance_expiration < %s", insurance_expires_before),
         ("insurance_expiration > %s", insurance_expires_after)],
    )
    sql = f"SELECT {VENDOR_COLS} FROM {TABLE}{where} ORDER BY vendor_id LIMIT %s"
    return query(sql, params + [cap_limit(limit)])


@vendor.tool
def vendor_summary(group_by: str = "status") -> list[dict]:
    """Count vendors grouped by status or vendor_type."""
    allowed = {"status", "vendor_type"}
    if group_by not in allowed:
        raise ValueError(f"group_by must be one of {sorted(allowed)}")
    sql = (f"SELECT {group_by}, COUNT(*) AS vendors FROM {TABLE} "
           f"GROUP BY {group_by} ORDER BY vendors DESC")
    return query(sql)


@vendor.tool
def vendor_filter_values() -> dict:
    """List distinct vendor_type and status values in use, for find_vendors."""
    return distinct_values(TABLE, ("vendor_type", "status"))
