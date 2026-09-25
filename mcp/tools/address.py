"""Address tools (street addresses and coordinates)."""
from fastmcp import FastMCP
from customer_service.db import query, build_where, cap_limit, contains, distinct_values

address = FastMCP("address")

TABLE = "smartreit.address"
ADDRESS_COLUMNS = (
    "address_id", "address_line_1", "address_line_2", "city", "county", "state",
    "postal_code", "country", "latitude", "longitude", "geocode_source",
)
ADDRESS_COLS = ", ".join(ADDRESS_COLUMNS)


@address.tool
def get_address(address_id: int) -> dict | None:
    """Get a single address by address_id. Returns null if not found."""
    rows = query(f"SELECT {ADDRESS_COLS} FROM {TABLE} WHERE address_id = %s", (address_id,))
    return rows[0] if rows else None


@address.tool
def find_addresses(
    street_contains: str | None = None,
    city: str | None = None,
    county: str | None = None,
    state: str | None = None,
    postal_code_prefix: str | None = None,
    country: str | None = None,
    limit: int = 50,
) -> list[dict]:
    """Search addresses. All filters optional, combined with AND.
    street_contains matches part of address lines 1 or 2, e.g. 'maple st'.
    city, county, state and country are exact, case-insensitive matches.
    Use the address_id with find_properties / find_buildings.
    Use address_filter_values for the state and country values in use."""
    where, params = build_where(
        {},
        [("concat_ws(' ', address_line_1, address_line_2) ILIKE %s", contains(street_contains)),
         ("city ILIKE %s", city),
         ("county ILIKE %s", county),
         ("state ILIKE %s", state),
         ("postal_code ILIKE %s", f"{postal_code_prefix}%" if postal_code_prefix else None),
         ("country ILIKE %s", country)],
    )
    sql = (f"SELECT {ADDRESS_COLS} FROM {TABLE}{where} "
           "ORDER BY country, state, city, address_line_1 LIMIT %s")
    return query(sql, params + [cap_limit(limit)])


@address.tool
def find_addresses_near(latitude: float, longitude: float,
                        radius_km: float = 10, limit: int = 20) -> list[dict]:
    """Find addresses within radius_km of a point, nearest first, with distance_km."""
    sql = f"""
        SELECT * FROM (
            SELECT {ADDRESS_COLS},
                   ROUND((6371 * acos(LEAST(1,
                       cos(radians(%s)) * cos(radians(latitude))
                       * cos(radians(longitude) - radians(%s))
                       + sin(radians(%s)) * sin(radians(latitude)))))::numeric, 2)
                   AS distance_km
            FROM {TABLE}
            WHERE latitude IS NOT NULL AND longitude IS NOT NULL
        ) a
        WHERE distance_km <= %s
        ORDER BY distance_km
        LIMIT %s
    """
    return query(sql, [latitude, longitude, latitude, radius_km, cap_limit(limit)])


@address.tool
def address_summary(group_by: str = "state", country: str | None = None) -> list[dict]:
    """Count addresses grouped by one of: city, county, state, country, geocode_source."""
    allowed = {"city", "county", "state", "country", "geocode_source"}
    if group_by not in allowed:
        raise ValueError(f"group_by must be one of {sorted(allowed)}")
    where, params = build_where({}, [("country ILIKE %s", country)])
    sql = (f"SELECT {group_by}, COUNT(*) AS addresses FROM {TABLE}{where} "
           f"GROUP BY {group_by} ORDER BY addresses DESC")
    return query(sql, params)


@address.tool
def address_filter_values() -> dict:
    """List distinct state, country and geocode_source values in use."""
    return distinct_values(TABLE, ("state", "country", "geocode_source"))
