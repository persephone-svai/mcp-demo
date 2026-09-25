"""Asset tools (equipment such as HVAC, elevators and roofs)."""
from datetime import date
from fastmcp import FastMCP
from customer_service.db import query, build_where, cap_limit, contains, distinct_values

asset = FastMCP("asset")

TABLE = "smartreit.asset"
ASSET_COLUMNS = (
    "asset_id", "property_id", "building_id", "space_id", "asset_type", "asset_name",
    "manufacturer", "model", "serial_number", "installation_date", "useful_life_years",
    "replacement_cost", "status",
)
ASSET_COLS = ", ".join(ASSET_COLUMNS)
# End of useful life, returned with every asset and used by due_for_replacement_by.
REPLACEMENT_DUE = "(installation_date + useful_life_years * interval '1 year')::date"


@asset.tool
def get_asset(asset_id: int | None = None, serial_number: str | None = None) -> dict | None:
    """Get one asset by asset_id or serial_number (give one), with its
    replacement_due_date. Returns null if not found."""
    if asset_id is None and serial_number is None:
        raise ValueError("Give asset_id or serial_number")
    where, params = build_where({"asset_id": asset_id, "serial_number": serial_number})
    rows = query(f"SELECT {ASSET_COLS}, {REPLACEMENT_DUE} AS replacement_due_date "
                 f"FROM {TABLE}{where} LIMIT 1", params)
    return rows[0] if rows else None


@asset.tool
def find_assets(
    property_id: int | None = None,
    building_id: int | None = None,
    space_id: int | None = None,
    asset_type: str | None = None,
    status: str | None = None,
    name_contains: str | None = None,
    installed_from: date | None = None,
    installed_to: date | None = None,
    due_for_replacement_by: date | None = None,
    limit: int = 50,
) -> list[dict]:
    """Search assets. All filters optional, combined with AND.
    name_contains matches part of the asset name, manufacturer or model.
    due_for_replacement_by returns assets whose useful life ends on or before
    that date (installation_date + useful_life_years); each result includes
    replacement_due_date. Use asset_filter_values for valid asset_type and status."""
    where, params = build_where(
        {"property_id": property_id, "building_id": building_id, "space_id": space_id,
         "asset_type": asset_type, "status": status},
        [("concat_ws(' ', asset_name, manufacturer, model) ILIKE %s", contains(name_contains)),
         ("installation_date >= %s", installed_from),
         ("installation_date <= %s", installed_to),
         (f"{REPLACEMENT_DUE} <= %s", due_for_replacement_by)],
    )
    sql = (f"SELECT {ASSET_COLS}, {REPLACEMENT_DUE} AS replacement_due_date "
           f"FROM {TABLE}{where} ORDER BY replacement_due_date NULLS LAST, asset_id LIMIT %s")
    return query(sql, params + [cap_limit(limit)])


@asset.tool
def asset_summary(group_by: str = "asset_type",
                  property_id: int | None = None,
                  status: str | None = None) -> list[dict]:
    """Count assets and total replacement cost, grouped by one of:
    asset_type, status, property_id, building_id."""
    allowed = {"asset_type", "status", "property_id", "building_id"}
    if group_by not in allowed:
        raise ValueError(f"group_by must be one of {sorted(allowed)}")
    where, params = build_where({"property_id": property_id, "status": status})
    sql = (f"SELECT {group_by}, COUNT(*) AS assets, "
           "SUM(replacement_cost) AS total_replacement_cost "
           f"FROM {TABLE}{where} GROUP BY {group_by} ORDER BY assets DESC")
    return query(sql, params)


@asset.tool
def asset_filter_values() -> dict:
    """List distinct asset_type and status values in use, for find_assets."""
    return distinct_values(TABLE, ("asset_type", "status"))
