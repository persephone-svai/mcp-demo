from datetime import date
from fastmcp import FastMCP
from db import query, build_where

SECURITY_DEPOSIT_COLS = ("work_order_id", "property_id", "building_id", "space_id", "asset_id",
                         "requested_by_party_id", "assigned_employee_id", "vendor_id", "priority",
                         "work_type", "description", "created_at", "scheduled_date", "completed_at",
                         "status")

security_deposit = FastMCP("security_deposit")

@security_deposit.tool
def find_security_deposits(
    work_order_id: int | None = None,
    property_id: int | None = None,
    building_id: int | None = None,
    space_id: int | None = None,
    asset_id: int | None = None,
    requested_by_party_id: int | None = None,
    assigned_employee_id: int | None = None,
    vendor_id: int | None = None,
    priority: str | None = None,
    work_type: str | None = None,
    status: str | None = None,
    limit: int = 50,
) -> list[dict]:
    """Search security deposits. All filters are optional and combined with AND.
    Omit a filter to ignore it; call with no filters to list security deposits."""
    where, params = build_where(
        {"work_order_id": work_order_id, "property_id": property_id, "building_id": building_id,
         "space_id": space_id, "asset_id": asset_id, "requested_by_party_id": requested_by_party_id,
         "assigned_employee_id": assigned_employee_id, "vendor_id": vendor_id, "priority": priority,
         "work_type": work_type, "status": status},
    )
    sql = (f"SELECT * FROM smartreit.security_deposit{where} "
           "ORDER BY work_order_id LIMIT %s")
    return query(sql, params + [min(limit, 200)])

