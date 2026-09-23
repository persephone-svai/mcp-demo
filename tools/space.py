from datetime import date
from fastmcp import FastMCP
import mcp
from db import query, build_where

space = FastMCP("space")

"""Spaces (units/suites) management."""

SPACE_COLS = ("space_id, property_id, building_id, floor_id, space_code, space_type, "
              "rentable_sf, usable_sf, bedrooms, bathrooms, current_status")

@space.tool
def get_space(space_id: int) -> dict | None:
    """Get a single space by space_id. Returns null if not found."""
    rows = query(f"SELECT {SPACE_COLS} FROM smartreit.space WHERE space_id = %s",
                 (space_id,))
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
    exact = {"property_id": property_id, "building_id": building_id,
             "floor_id": floor_id, "space_code": space_code,
             "space_type": space_type, "current_status": current_status}
    where, params = [], []
    for col, val in exact.items():
        if val is not None:
            where.append(f"{col} = %s"); params.append(val)
    ranges = [("rentable_sf >= %s", min_rentable_sf),
              ("rentable_sf <= %s", max_rentable_sf),
              ("bedrooms >= %s", min_bedrooms),
              ("bathrooms >= %s", min_bathrooms)]
    for clause, val in ranges:
        if val is not None:
            where.append(clause); params.append(val)

    sql = f"SELECT {SPACE_COLS} FROM smartreit.space"
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY property_id, building_id, floor_id, space_code LIMIT %s"
    params.append(min(limit, 200))
    return query(sql, params)

@mcp.tool
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
    where, params = [], []
    for col, val in {"property_id": property_id, "building_id": building_id}.items():
        if val is not None:
            where.append(f"{col} = %s"); params.append(val)

    sql = (f"SELECT {group_by}, COUNT(*) AS spaces, "
           f"SUM(rentable_sf) AS total_rentable_sf, SUM(usable_sf) AS total_usable_sf, "
           f"ROUND(100.0 * SUM(rentable_sf) / NULLIF(SUM(SUM(rentable_sf)) OVER (), 0), 1) "
           f"AS pct_of_rentable_sf "
           f"FROM smartreit.space")
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += f" GROUP BY {group_by} ORDER BY {group_by}"
    return query(sql, params)

@spaces.tool
def space_filter_values() -> dict:
    """List distinct space_type and current_status values in use."""
    return {
        col: [r[col] for r in query(
            f"SELECT DISTINCT {col} FROM smartreit.space "
            f"WHERE {col} IS NOT NULL ORDER BY 1")]
        for col in ("space_type", "current_status")
    }
