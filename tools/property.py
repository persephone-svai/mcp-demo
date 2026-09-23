"""Property tools (buildings/assets in the portfolio)."""
from datetime import date
from fastmcp import FastMCP
from db import query, build_where, cap_limit, contains, distinct_values

# Named property_tools because `property` is a Python built-in.
property_tools = FastMCP("property")

TABLE = "smartreit.property"
PROPERTY_COLUMNS = (
    "property_id", "property_code", "property_name", "property_type", "subtype",
    "ownership_entity_id", "acquisition_date", "disposition_date",
    "acquisition_price", "current_status", "year_built", "year_renovated",
    "total_building_sf", "total_land_acres", "address_id", "latitude", "longitude",
)
PROPERTY_COLS = ", ".join(PROPERTY_COLUMNS)


@property_tools.tool
def get_property(property_id: int | None = None,
                 property_code: str | None = None) -> dict | None:
    """Get one property by property_id or property_code (give one).
    Returns null if not found. To search by name, use find_properties."""
    if property_id is None and property_code is None:
        raise ValueError("Give property_id or property_code")
    where, params = build_where({"property_id": property_id,
                                 "property_code": property_code})
    rows = query(f"SELECT {PROPERTY_COLS} FROM {TABLE}{where} LIMIT 1", params)
    return rows[0] if rows else None


@property_tools.tool
def find_properties(
    name_contains: str | None = None,
    property_type: str | None = None,
    subtype: str | None = None,
    current_status: str | None = None,
    ownership_entity_id: int | None = None,
    acquired_from: date | None = None,
    acquired_to: date | None = None,
    min_building_sf: float | None = None,
    max_building_sf: float | None = None,
    built_after: int | None = None,
    built_before: int | None = None,
    limit: int = 50,
) -> list[dict]:
    """Search properties. All filters optional, combined with AND.
    name_contains matches part of the property name or code (case-insensitive),
    e.g. 'maple' finds 'Maple Street Plaza'. Use this to find a property_id
    from a name. built_after/built_before are years.
    Use property_filter_values to see valid type, subtype and status values."""
    where, params = build_where(
        {"property_type": property_type, "subtype": subtype,
         "current_status": current_status,
         "ownership_entity_id": ownership_entity_id},
        [("concat_ws(' ', property_name, property_code) ILIKE %s", contains(name_contains)),
         ("acquisition_date >= %s", acquired_from),
         ("acquisition_date <= %s", acquired_to),
         ("total_building_sf >= %s", min_building_sf),
         ("total_building_sf <= %s", max_building_sf),
         ("year_built >= %s", built_after),
         ("year_built <= %s", built_before)],
    )
    sql = f"SELECT {PROPERTY_COLS} FROM {TABLE}{where} ORDER BY property_name LIMIT %s"
    return query(sql, params + [cap_limit(limit)])


@property_tools.tool
def find_properties_near(latitude: float, longitude: float,
                         radius_km: float = 10, limit: int = 20) -> list[dict]:
    """Find properties within radius_km of a point, nearest first.
    Returns each property with distance_km."""
    sql = f"""
        SELECT * FROM (
            SELECT {PROPERTY_COLS},
                   ROUND((6371 * acos(LEAST(1,
                       cos(radians(%s)) * cos(radians(latitude))
                       * cos(radians(longitude) - radians(%s))
                       + sin(radians(%s)) * sin(radians(latitude)))))::numeric, 2)
                   AS distance_km
            FROM {TABLE}
            WHERE latitude IS NOT NULL AND longitude IS NOT NULL
        ) p
        WHERE distance_km <= %s
        ORDER BY distance_km
        LIMIT %s
    """
    return query(sql, [latitude, longitude, latitude, radius_km, cap_limit(limit)])


@property_tools.tool
def property_summary(group_by: str = "property_type",
                     current_status: str | None = None) -> list[dict]:
    """Portfolio totals grouped by one of: property_type, subtype,
    current_status, ownership_entity_id. Returns property count, total building SF,
    total land acres and total acquisition price per group."""
    allowed = {"property_type", "subtype", "current_status", "ownership_entity_id"}
    if group_by not in allowed:
        raise ValueError(f"group_by must be one of {sorted(allowed)}")
    where, params = build_where({"current_status": current_status})
    sql = (f"SELECT {group_by}, COUNT(*) AS properties, "
           "SUM(total_building_sf) AS total_building_sf, "
           "SUM(total_land_acres) AS total_land_acres, "
           "SUM(acquisition_price) AS total_acquisition_price "
           f"FROM {TABLE}{where} GROUP BY {group_by} ORDER BY properties DESC")
    return query(sql, params)


@property_tools.tool
def property_filter_values() -> dict:
    """List distinct property_type, subtype and current_status values in use,
    for find_properties."""
    return distinct_values(TABLE, ("property_type", "subtype", "current_status"))
