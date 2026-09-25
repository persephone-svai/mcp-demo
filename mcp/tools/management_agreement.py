"""Management agreement tools (who manages each property, on what terms)."""
from datetime import date
from fastmcp import FastMCP
from customer_service.db import query, build_where, cap_limit, distinct_values

management_agreement = FastMCP("management_agreement")

TABLE = "smartreit.management_agreement"
AGREEMENT_COLUMNS = (
    "agreement_id", "property_id", "manager_party_id", "start_date", "end_date",
    "fee_percentage", "monthly_fee", "status",
)
AGREEMENT_COLS = ", ".join(AGREEMENT_COLUMNS)


@management_agreement.tool
def get_management_agreement(agreement_id: int) -> dict | None:
    """Get a single management agreement by agreement_id. Returns null if not found."""
    rows = query(f"SELECT {AGREEMENT_COLS} FROM {TABLE} WHERE agreement_id = %s",
                 (agreement_id,))
    return rows[0] if rows else None


@management_agreement.tool
def find_management_agreements(
    property_id: int | None = None,
    manager_party_id: int | None = None,
    status: str | None = None,
    active_on: date | None = None,
    ending_from: date | None = None,
    ending_to: date | None = None,
    min_fee_percentage: float | None = None,
    max_fee_percentage: float | None = None,
    limit: int = 50,
) -> list[dict]:
    """Search management agreements. All filters optional, combined with AND.
    active_on returns agreements in force on that date (started on or before it,
    and no end_date or ending on or after it); e.g. pass today with property_id
    to find a property's current manager.
    ending_from/ending_to filter on end_date, for upcoming renewals.
    manager_party_id links to get_party / get_organization for the manager's name.
    Use management_agreement_filter_values for valid statuses. Newest first."""
    where, params = build_where(
        {"property_id": property_id, "manager_party_id": manager_party_id,
         "status": status},
        [("start_date <= %s", active_on),
         ("(end_date IS NULL OR end_date >= %s)", active_on),
         ("end_date >= %s", ending_from),
         ("end_date <= %s", ending_to),
         ("fee_percentage >= %s", min_fee_percentage),
         ("fee_percentage <= %s", max_fee_percentage)],
    )
    sql = (f"SELECT {AGREEMENT_COLS} FROM {TABLE}{where} "
           "ORDER BY start_date DESC NULLS LAST, agreement_id DESC LIMIT %s")
    return query(sql, params + [cap_limit(limit)])


@management_agreement.tool
def management_agreement_summary(
    group_by: str = "manager_party_id",
    status: str | None = None,
    active_on: date | None = None,
) -> list[dict]:
    """Count agreements, total monthly fees and average fee percentage, grouped by
    one of: manager_party_id, status, property_id. Pass active_on (e.g. today) to
    count only agreements in force on that date."""
    allowed = {"manager_party_id", "status", "property_id"}
    if group_by not in allowed:
        raise ValueError(f"group_by must be one of {sorted(allowed)}")
    where, params = build_where(
        {"status": status},
        [("start_date <= %s", active_on),
         ("(end_date IS NULL OR end_date >= %s)", active_on)],
    )
    sql = (f"SELECT {group_by}, COUNT(*) AS agreements, "
           "SUM(monthly_fee) AS total_monthly_fee, "
           "ROUND(AVG(fee_percentage)::numeric, 4) AS avg_fee_percentage "
           f"FROM {TABLE}{where} GROUP BY {group_by} ORDER BY agreements DESC")
    return query(sql, params)


@management_agreement.tool
def management_agreement_filter_values() -> dict:
    """List distinct status values in use, for find_management_agreements."""
    return distinct_values(TABLE, ("status",))
