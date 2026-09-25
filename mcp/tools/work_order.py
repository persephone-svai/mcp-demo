"""Work order tools (maintenance and repair requests)."""
from datetime import date
from fastmcp import FastMCP
from customer_service.db import query, build_where, cap_limit, distinct_values

work_order = FastMCP("work_order")

TABLE = "smartreit.work_order"
WORK_ORDER_COLUMNS = (
    "work_order_id", "property_id", "building_id", "space_id", "asset_id",
    "requested_by_party_id", "assigned_employee_id", "vendor_id", "priority",
    "work_type", "description", "created_at", "scheduled_date", "completed_at", "status",
)
WORK_ORDER_COLS = ", ".join(WORK_ORDER_COLUMNS)


@work_order.tool
def get_work_order(work_order_id: int) -> dict | None:
    """Get a single work order by work_order_id. Returns null if not found."""
    rows = query(f"SELECT {WORK_ORDER_COLS} FROM {TABLE} WHERE work_order_id = %s",
                 (work_order_id,))
    return rows[0] if rows else None


@work_order.tool
def find_work_orders(
    property_id: int | None = None,
    building_id: int | None = None,
    space_id: int | None = None,
    asset_id: int | None = None,
    vendor_id: int | None = None,
    requested_by_party_id: int | None = None,
    assigned_employee_id: int | None = None,
    priority: str | None = None,
    work_type: str | None = None,
    status: str | None = None,
    created_from: date | None = None,
    created_to: date | None = None,
    scheduled_from: date | None = None,
    scheduled_to: date | None = None,
    completed: bool | None = None,
    limit: int = 50,
) -> list[dict]:
    """Search work orders. All filters optional, combined with AND. Newest first.
    Date ranges are inclusive. completed=true/false filters on whether completed_at is set.
    Use work_order_filter_values to see valid priority, work_type and status values."""
    conditions = []
    if completed is not None:
        conditions.append("completed_at IS NOT NULL" if completed else "completed_at IS NULL")
    where, params = build_where(
        {"property_id": property_id, "building_id": building_id, "space_id": space_id,
         "asset_id": asset_id, "vendor_id": vendor_id,
         "requested_by_party_id": requested_by_party_id,
         "assigned_employee_id": assigned_employee_id,
         "priority": priority, "work_type": work_type, "status": status},
        [("created_at >= %s", created_from),
         ("created_at < %s::date + 1", created_to),
         ("scheduled_date >= %s", scheduled_from),
         ("scheduled_date <= %s", scheduled_to)],
        conditions,
    )
    sql = (f"SELECT {WORK_ORDER_COLS} FROM {TABLE}{where} "
           "ORDER BY created_at DESC, work_order_id DESC LIMIT %s")
    return query(sql, params + [cap_limit(limit)])


@work_order.tool
def work_order_summary(
    group_by: str = "status",
    property_id: int | None = None,
    created_from: date | None = None,
    created_to: date | None = None,
) -> list[dict]:
    """Count work orders grouped by one of: status, priority, work_type,
    property_id, vendor_id. Includes how many are still open (no completed_at)."""
    allowed = {"status", "priority", "work_type", "property_id", "vendor_id"}
    if group_by not in allowed:
        raise ValueError(f"group_by must be one of {sorted(allowed)}")
    where, params = build_where(
        {"property_id": property_id},
        [("created_at >= %s", created_from),
         ("created_at < %s::date + 1", created_to)],
    )
    sql = (f"SELECT {group_by}, COUNT(*) AS work_orders, "
           "COUNT(*) FILTER (WHERE completed_at IS NULL) AS open_work_orders "
           f"FROM {TABLE}{where} GROUP BY {group_by} ORDER BY work_orders DESC")
    return query(sql, params)


@work_order.tool
def work_order_filter_values() -> dict:
    """List distinct priority, work_type and status values in use, for find_work_orders."""
    return distinct_values(TABLE, ("priority", "work_type", "status"))
