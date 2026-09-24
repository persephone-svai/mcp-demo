"""Lease rent schedule tools (scheduled rent and charges, with escalations)."""
from datetime import date
from fastmcp import FastMCP
from db import query, build_where, cap_limit, distinct_values

lease_rent_schedule = FastMCP("lease_rent_schedule")

TABLE = "smartreit.lease_rent_schedule"
RENT_SCHEDULE_COLUMNS = (
    "rent_schedule_id", "lease_id", "charge_type", "start_date", "end_date", "amount",
    "amount_frequency", "rate_per_sf", "escalation_type", "escalation_percentage",
)
RENT_SCHEDULE_COLS = ", ".join(RENT_SCHEDULE_COLUMNS)


@lease_rent_schedule.tool
def get_lease_rent_schedule(rent_schedule_id: int) -> dict | None:
    """Get a single rent schedule line by rent_schedule_id. Returns null if not found."""
    rows = query(f"SELECT {RENT_SCHEDULE_COLS} FROM {TABLE} WHERE rent_schedule_id = %s",
                 (rent_schedule_id,))
    return rows[0] if rows else None


@lease_rent_schedule.tool
def find_lease_rent_schedules(
    lease_id: int | None = None,
    charge_type: str | None = None,
    amount_frequency: str | None = None,
    escalation_type: str | None = None,
    active_on: date | None = None,
    starting_from: date | None = None,
    starting_to: date | None = None,
    min_amount: float | None = None,
    max_amount: float | None = None,
    limit: int = 50,
) -> list[dict]:
    """Search rent schedule lines. All filters optional, combined with AND.
    active_on returns lines in effect on that date, e.g. a lease's current rent.
    amount is per amount_frequency (check it before comparing amounts).
    Use lease_rent_schedule_filter_values for valid charge_type,
    amount_frequency and escalation_type values."""
    where, params = build_where(
        {"lease_id": lease_id, "charge_type": charge_type,
         "amount_frequency": amount_frequency, "escalation_type": escalation_type},
        [("start_date <= %s", active_on),
         ("(end_date IS NULL OR end_date >= %s)", active_on),
         ("start_date >= %s", starting_from),
         ("start_date <= %s", starting_to),
         ("amount >= %s", min_amount),
         ("amount <= %s", max_amount)],
    )
    sql = (f"SELECT {RENT_SCHEDULE_COLS} FROM {TABLE}{where} "
           "ORDER BY lease_id, start_date, rent_schedule_id LIMIT %s")
    return query(sql, params + [cap_limit(limit)])


@lease_rent_schedule.tool
def lease_rent_schedule_summary(
    group_by: str = "charge_type",
    lease_id: int | None = None,
    amount_frequency: str | None = None,
    active_on: date | None = None,
) -> list[dict]:
    """Count schedule lines, total amount and average rate per SF, grouped by one of:
    charge_type, amount_frequency, escalation_type, lease_id.
    Amounts are only comparable within one amount_frequency, so filter on it
    (or group by it) before reading total_amount."""
    allowed = {"charge_type", "amount_frequency", "escalation_type", "lease_id"}
    if group_by not in allowed:
        raise ValueError(f"group_by must be one of {sorted(allowed)}")
    where, params = build_where(
        {"lease_id": lease_id, "amount_frequency": amount_frequency},
        [("start_date <= %s", active_on),
         ("(end_date IS NULL OR end_date >= %s)", active_on)],
    )
    sql = (f"SELECT {group_by}, COUNT(*) AS schedule_lines, SUM(amount) AS total_amount, "
           "ROUND(AVG(rate_per_sf)::numeric, 2) AS avg_rate_per_sf "
           f"FROM {TABLE}{where} GROUP BY {group_by} ORDER BY {group_by}")
    return query(sql, params)


@lease_rent_schedule.tool
def lease_rent_schedule_filter_values() -> dict:
    """List distinct charge_type, amount_frequency and escalation_type values in use."""
    return distinct_values(TABLE, ("charge_type", "amount_frequency", "escalation_type"))
