"""Floor tools (floors within buildings)."""
from fastmcp import FastMCP
from customer_service.db import query, build_where, cap_limit, contains

floor = FastMCP("floor")

TABLE = "smartreit.floor"
FLOOR_COLUMNS = ("floor_id", "building_id", "floor_number", "floor_label",
                 "rentable_sf", "usable_sf")
FLOOR_COLS = ", ".join(FLOOR_COLUMNS)


@floor.tool
def get_floor(floor_id: int) -> dict | None:
    """Get a single floor by floor_id. Returns null if not found."""
    rows = query(f"SELECT {FLOOR_COLS} FROM {TABLE} WHERE floor_id = %s", (floor_id,))
    return rows[0] if rows else None


@floor.tool
def find_floors(
    building_id: int | None = None,
    floor_number: int | None = None,
    label_contains: str | None = None,
    min_rentable_sf: float | None = None,
    max_rentable_sf: float | None = None,
    limit: int = 50,
) -> list[dict]:
    """Search floors. All filters optional, combined with AND.
    label_contains matches part of floor_label, e.g. 'mezz' or 'lobby'.
    Sizes are in square feet. Ordered by building, then floor number."""
    where, params = build_where(
        {"building_id": building_id, "floor_number": floor_number},
        [("floor_label ILIKE %s", contains(label_contains)),
         ("rentable_sf >= %s", min_rentable_sf),
         ("rentable_sf <= %s", max_rentable_sf)],
    )
    sql = f"SELECT {FLOOR_COLS} FROM {TABLE}{where} ORDER BY building_id, floor_number LIMIT %s"
    return query(sql, params + [cap_limit(limit)])


@floor.tool
def floor_summary(building_id: int | None = None) -> list[dict]:
    """Count floors and total rentable/usable SF per building."""
    where, params = build_where({"building_id": building_id})
    sql = (f"SELECT building_id, COUNT(*) AS floors, "
           "SUM(rentable_sf) AS total_rentable_sf, SUM(usable_sf) AS total_usable_sf "
           f"FROM {TABLE}{where} GROUP BY building_id ORDER BY building_id")
    return query(sql, params)
