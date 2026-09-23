"""Tenant improvement (TI) tools: build-out budgets and spend per lease/space."""
from datetime import date
from fastmcp import FastMCP
from db import query, build_where, cap_limit

tenant_improvement = FastMCP("tenant_improvement")

TABLE = "smartreit.tenant_improvement"
TI_COLUMNS = (
    "ti_id", "lease_id", "property_id", "space_id", "approved_amount",
    "committed_amount", "actual_amount", "start_date", "completion_date",
)
TI_COLS = ", ".join(TI_COLUMNS)


def _in_progress_condition(in_progress: bool | None) -> list[str]:
    if in_progress is None:
        return []
    return ["completion_date IS NULL" if in_progress else "completion_date IS NOT NULL"]


@tenant_improvement.tool
def get_tenant_improvement(ti_id: int) -> dict | None:
    """Get a single tenant improvement by ti_id. Returns null if not found."""
    rows = query(f"SELECT {TI_COLS} FROM {TABLE} WHERE ti_id = %s", (ti_id,))
    return rows[0] if rows else None


@tenant_improvement.tool
def find_tenant_improvements(
    lease_id: int | None = None,
    property_id: int | None = None,
    space_id: int | None = None,
    in_progress: bool | None = None,
    started_from: date | None = None,
    started_to: date | None = None,
    completed_from: date | None = None,
    completed_to: date | None = None,
    min_approved_amount: float | None = None,
    over_budget: bool = False,
    limit: int = 50,
) -> list[dict]:
    """Search tenant improvements. All filters optional, combined with AND.
    in_progress=true means not yet completed (no completion_date); false means completed.
    over_budget=true returns only TIs whose actual_amount exceeds approved_amount.
    Newest start date first."""
    conditions = _in_progress_condition(in_progress)
    if over_budget:
        conditions.append("actual_amount > approved_amount")
    where, params = build_where(
        {"lease_id": lease_id, "property_id": property_id, "space_id": space_id},
        [("start_date >= %s", started_from),
         ("start_date <= %s", started_to),
         ("completion_date >= %s", completed_from),
         ("completion_date <= %s", completed_to),
         ("approved_amount >= %s", min_approved_amount)],
        conditions,
    )
    sql = (f"SELECT {TI_COLS} FROM {TABLE}{where} "
           "ORDER BY start_date DESC NULLS LAST, ti_id DESC LIMIT %s")
    return query(sql, params + [cap_limit(limit)])


@tenant_improvement.tool
def tenant_improvement_summary(
    group_by: str = "property_id",
    property_id: int | None = None,
    in_progress: bool | None = None,
) -> list[dict]:
    """Count TIs and total approved, committed and actual amounts, grouped by
    property_id, lease_id or space_id. remaining_budget = approved - actual.
    Use in_progress=true to count/total only ongoing TIs."""
    allowed = {"property_id", "lease_id", "space_id"}
    if group_by not in allowed:
        raise ValueError(f"group_by must be one of {sorted(allowed)}")
    where, params = build_where({"property_id": property_id}, [],
                                _in_progress_condition(in_progress))
    sql = (f"SELECT {group_by}, COUNT(*) AS tenant_improvements, "
           "SUM(approved_amount) AS total_approved, "
           "SUM(committed_amount) AS total_committed, "
           "SUM(actual_amount) AS total_actual, "
           "SUM(COALESCE(approved_amount, 0) - COALESCE(actual_amount, 0)) AS remaining_budget "
           f"FROM {TABLE}{where} GROUP BY {group_by} ORDER BY {group_by}")
    return query(sql, params)
