"""Building tools (buildings within properties)."""
from fastmcp import FastMCP
from db import query, build_where, cap_limit, contains, distinct_values

building = FastMCP("building")

TABLE = "smartreit.building"
BUILDING_COLUMNS = (
    "building_id", "property_id", "building_code", "building_name", "building_sf",
    "floor_count", "year_built", "construction_type", "address_id", "status",
)
BUILDING_COLS = ", ".join(BUILDING_COLUMNS)


@building.tool
def get_building(building_id: int | None = None,
                 building_code: str | None = None) -> dict | None:
    """Get one building by building_id or building_code (give one).
    Returns null if not found. To search by name, use find_buildings."""
    if building_id is None and building_code is None:
        raise ValueError("Give building_id or building_code")
    where, params = build_where({"building_id": building_id, "building_code": building_code})
    rows = query(f"SELECT {BUILDING_COLS} FROM {TABLE}{where} LIMIT 1", params)
    return rows[0] if rows else None


@building.tool
def find_buildings(
    property_id: int | None = None,
    name_contains: str | None = None,
    construction_type: str | None = None,
    status: str | None = None,
    min_building_sf: float | None = None,
    max_building_sf: float | None = None,
    built_after: int | None = None,
    built_before: int | None = None,
    limit: int = 50,
) -> list[dict]:
    """Search buildings. All filters optional, combined with AND.
    name_contains matches part of the building name or code (case-insensitive).
    built_after/built_before are years. Use building_filter_values for valid
    construction_type and status values."""
    where, params = build_where(
        {"property_id": property_id, "construction_type": construction_type,
         "status": status},
        [("concat_ws(' ', building_name, building_code) ILIKE %s", contains(name_contains)),
         ("building_sf >= %s", min_building_sf),
         ("building_sf <= %s", max_building_sf),
         ("year_built >= %s", built_after),
         ("year_built <= %s", built_before)],
    )
    sql = (f"SELECT {BUILDING_COLS} FROM {TABLE}{where} "
           "ORDER BY property_id, building_name LIMIT %s")
    return query(sql, params + [cap_limit(limit)])


@building.tool
def building_summary(group_by: str = "property_id",
                     property_id: int | None = None,
                     status: str | None = None) -> list[dict]:
    """Count buildings, total building SF and total floors, grouped by one of:
    property_id, construction_type, status."""
    allowed = {"property_id", "construction_type", "status"}
    if group_by not in allowed:
        raise ValueError(f"group_by must be one of {sorted(allowed)}")
    where, params = build_where({"property_id": property_id, "status": status})
    sql = (f"SELECT {group_by}, COUNT(*) AS buildings, "
           "SUM(building_sf) AS total_building_sf, SUM(floor_count) AS total_floors "
           f"FROM {TABLE}{where} GROUP BY {group_by} ORDER BY buildings DESC")
    return query(sql, params)


@building.tool
def building_filter_values() -> dict:
    """List distinct construction_type and status values in use, for find_buildings."""
    return distinct_values(TABLE, ("construction_type", "status"))
