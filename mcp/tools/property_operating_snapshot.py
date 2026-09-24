"""Property operating snapshot tools (occupancy, rent, NOI, expenses over time)."""
from datetime import date
from fastmcp import FastMCP
from db import query, build_where, cap_limit

property_operating_snapshot = FastMCP("property_operating_snapshot")

TABLE = "smartreit.property_operating_snapshot"
SNAPSHOT_COLUMNS = (
    "snapshot_date", "property_id", "occupancy_percentage", "leased_percentage",
    "rentable_sf", "occupied_sf", "annualized_rent", "noi", "revenue",
    "operating_expense", "capex", "bad_debt",
)
SNAPSHOT_COLS = ", ".join(SNAPSHOT_COLUMNS)


@property_operating_snapshot.tool
def get_property_snapshot(property_id: int,
                          snapshot_date: date | None = None) -> dict | None:
    """Get one property's operating snapshot on or before snapshot_date.
    If snapshot_date is omitted, returns the most recent snapshot.
    Returns null if not found."""
    where, params = build_where(
        {"property_id": property_id},
        [("snapshot_date <= %s", snapshot_date or date.today())],
    )
    rows = query(f"SELECT {SNAPSHOT_COLS} FROM {TABLE}{where} "
                 "ORDER BY snapshot_date DESC LIMIT 1", params)
    return rows[0] if rows else None


@property_operating_snapshot.tool
def find_property_snapshots(
    property_id: int | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    min_occupancy_percentage: float | None = None,
    max_occupancy_percentage: float | None = None,
    min_noi: float | None = None,
    max_noi: float | None = None,
    min_bad_debt: float | None = None,
    max_bad_debt: float | None = None,
    order_by: str = "snapshot_date",
    descending: bool = True,
    limit: int = 50,
) -> list[dict]:
    """Search property operating snapshots. All filters optional, combined with AND.
    For one property's history, pass property_id with date_from/date_to.
    To rank properties, filter to one date and set order_by
    (snapshot_date, occupancy_percentage, leased_percentage, noi, revenue,
    annualized_rent, operating_expense, capex, bad_debt)."""
    allowed = {"snapshot_date", "occupancy_percentage", "leased_percentage", "noi",
               "revenue", "annualized_rent", "operating_expense", "capex", "bad_debt"}
    if order_by not in allowed:
        raise ValueError(f"order_by must be one of {sorted(allowed)}")
    where, params = build_where(
        {"property_id": property_id},
        [("snapshot_date >= %s", date_from),
         ("snapshot_date <= %s", date_to),
         ("occupancy_percentage >= %s", min_occupancy_percentage),
         ("occupancy_percentage <= %s", max_occupancy_percentage),
         ("noi >= %s", min_noi),
         ("noi <= %s", max_noi),
         ("bad_debt >= %s", min_bad_debt),
         ("bad_debt <= %s", max_bad_debt)],
    )
    direction = "DESC" if descending else "ASC"
    sql = (f"SELECT {SNAPSHOT_COLS} FROM {TABLE}{where} "
           f"ORDER BY {order_by} {direction} NULLS LAST, property_id LIMIT %s")
    return query(sql, params + [cap_limit(limit)])
