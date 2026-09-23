from datetime import date
from fastmcp import FastMCP
from db import query, build_where
from datetime import date
vendor = FastMCP("vendor")

VENDOR_COLS = ("vendor_id", "party_id", "vendor_type", 
               "tax_id", "insurance_expiration", "status")

@vendor.tool
def get_vendor(vendor_id: int) -> dict | None:
    """Get a single vendor by vendor_id. Returns null if not found."""
    rows = query(f"SELECT {VENDOR_COLS} FROM smartreit.vendor WHERE vendor_id = %s",
                 (vendor_id,))
    return rows[0] if rows else None

@vendor.tool
def find_vendors(
    vendor_id: int | None = None,
    party_id: int | None = None,
    vendor_type: str | None = None,
    tax_id: str | None = None,
    insurance_expiration: date | None = None,
    status: str | None = None,
    limit: int = 50,
) -> list[dict]:
    """Search vendors. All filters are optional and combined with AND.
    Omit a filter to ignore it; call with no filters to list vendors."""
    where, params = build_where(
        {"vendor_id": vendor_id, "party_id": party_id, "vendor_type": vendor_type,
         "tax_id": tax_id, "insurance_expiration": insurance_expiration, "status": status},
    )
    sql = (f"SELECT {VENDOR_COLS} FROM smartreit.vendor{where} "
           "ORDER BY vendor_id LIMIT %s")
    return query(sql, params + [min(limit, 200)])

@vendor.tool
def vendor_exists(vendor_id: int) -> bool:
    """Check if a vendor exists by vendor_id."""
    rows = query(f"SELECT 1 FROM smartreit.vendor WHERE vendor_id = %s", (vendor_id,))
    return bool(rows)

@vendor.tool
def count_active_vendors() -> int:
    """Count the total number of active vendors."""
    rows = query("SELECT COUNT(*) AS count FROM smartreit.vendor WHERE status = 'active'")
    return rows[0]["count"] if rows else 0

