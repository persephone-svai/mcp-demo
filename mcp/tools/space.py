"""Space tools (units/suites)."""
from fastmcp import FastMCP
from db import query, build_where, cap_limit, distinct_values

space = FastMCP("space")

TABLE = "smartreit.space"
SPACE_COLUMNS = (
    "space_id", "property_id", "building_id", "floor_id", "space_code", "space_type",
    "rentable_sf", "usable_sf", "bedrooms", "bathrooms", "current_status",
)
SPACE_COLS = ", ".join(SPACE_COLUMNS)


@space.tool
def get_space(space_id: int) -> dict | None:
    """Get a single space by space_id. Returns null if not found."""
    rows = query(f"SELECT {SPACE_COLS} FROM {TABLE} WHERE space_id = %s", (space_id,))
    return rows[0] if rows else None


@space.tool
def find_spaces(
    property_id: int | None = None,
    building_id: int | None = None,
    floor_id: int | None = None,
    space_code: str | None = None,
    space_type: str | None = None,
    current_status: str | None = None,
    min_rentable_sf: float | None = None,
    max_rentable_sf: float | None = None,
    min_bedrooms: int | None = None,
    min_bathrooms: float | None = None,
    limit: int = 50,
) -> list[dict]:
    """Search spaces (units/suites). All filters optional, combined with AND.
    Use current_status to find vacant/available space. Sizes are in square feet.
    Use space_filter_values to see valid space_type and current_status values."""
    where, params = build_where(
        {"property_id": property_id, "building_id": building_id,
         "floor_id": floor_id, "space_code": space_code,
         "space_type": space_type, "current_status": current_status},
        [("rentable_sf >= %s", min_rentable_sf),
         ("rentable_sf <= %s", max_rentable_sf),
         ("bedrooms >= %s", min_bedrooms),
         ("bathrooms >= %s", min_bathrooms)],
    )
    sql = (f"SELECT {SPACE_COLS} FROM {TABLE}{where} "
           "ORDER BY property_id, building_id, floor_id, space_code LIMIT %s")
    return query(sql, params + [cap_limit(limit)])


@space.tool
def space_summary(
    group_by: str = "current_status",
    property_id: int | None = None,
    building_id: int | None = None,
) -> list[dict]:
    """Count spaces and total rentable/usable square feet, grouped by one of:
    current_status, space_type, property_id, building_id, floor_id.
    Use for occupancy, vacancy and inventory questions."""
    allowed = {"current_status", "space_type", "property_id", "building_id", "floor_id"}
    if group_by not in allowed:
        raise ValueError(f"group_by must be one of {sorted(allowed)}")
    where, params = build_where({"property_id": property_id, "building_id": building_id})
    sql = (f"SELECT {group_by}, COUNT(*) AS spaces, "
           "SUM(rentable_sf) AS total_rentable_sf, SUM(usable_sf) AS total_usable_sf, "
           "ROUND(100.0 * SUM(rentable_sf) / NULLIF(SUM(SUM(rentable_sf)) OVER (), 0), 1) "
           "AS pct_of_rentable_sf "
           f"FROM {TABLE}{where} GROUP BY {group_by} ORDER BY {group_by}")
    return query(sql, params)


@space.tool
def space_filter_values() -> dict:
    """List distinct space_type and current_status values in use, for find_spaces."""
    return distinct_values(TABLE, ("space_type", "current_status"))
