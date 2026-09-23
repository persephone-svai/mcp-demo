"""Tenant billing tools."""
from datetime import date
from fastmcp import FastMCP
from db import query, build_where, cap_limit, distinct_values

tenant_billing = FastMCP("tenant_billing")

TABLE = "smartreit.tenant_billing"
BILL_COLUMNS = (
    "bill_id", "lease_id", "tenant_id", "charge_type", "billing_date",
    "due_date", "amount", "tax_amount", "status",
)
BILL_COLS = ", ".join(BILL_COLUMNS)


@tenant_billing.tool
def get_billing(bill_id: int) -> dict | None:
    """Get a single bill by bill_id. Returns null if not found."""
    rows = query(f"SELECT {BILL_COLS} FROM {TABLE} WHERE bill_id = %s", (bill_id,))
    return rows[0] if rows else None


@tenant_billing.tool
def find_billing(
    tenant_id: int | None = None,
    lease_id: int | None = None,
    charge_type: str | None = None,
    status: str | None = None,
    billed_from: date | None = None,
    billed_to: date | None = None,
    due_before: date | None = None,
    limit: int = 50,
) -> list[dict]:
    """Search bills. All filters optional, combined with AND. Newest bills first.
    billed_from/billed_to filter on billing_date (inclusive).
    due_before filters on due_date, e.g. with status to find overdue bills.
    Use billing_filter_values to see valid charge_type and status values."""
    where, params = build_where(
        {"tenant_id": tenant_id, "lease_id": lease_id,
         "charge_type": charge_type, "status": status},
        [("billing_date >= %s", billed_from),
         ("billing_date <= %s", billed_to),
         ("due_date < %s", due_before)],
    )
    sql = (f"SELECT {BILL_COLS} FROM {TABLE}{where} "
           "ORDER BY billing_date DESC, bill_id DESC LIMIT %s")
    return query(sql, params + [cap_limit(limit)])


@tenant_billing.tool
def billing_summary(
    group_by: str = "status",
    tenant_id: int | None = None,
    lease_id: int | None = None,
    billed_from: date | None = None,
    billed_to: date | None = None,
) -> list[dict]:
    """Total amount, tax and bill count, grouped by status or charge_type.
    Use for balances owed, totals billed, and breakdowns by charge type."""
    allowed = {"status", "charge_type"}
    if group_by not in allowed:
        raise ValueError(f"group_by must be one of {sorted(allowed)}")
    where, params = build_where(
        {"tenant_id": tenant_id, "lease_id": lease_id},
        [("billing_date >= %s", billed_from),
         ("billing_date <= %s", billed_to)],
    )
    sql = (f"SELECT {group_by}, COUNT(*) AS bills, "
           "SUM(amount) AS total_amount, "
           "SUM(COALESCE(tax_amount, 0)) AS total_tax, "
           "SUM(amount + COALESCE(tax_amount, 0)) AS total_with_tax "
           f"FROM {TABLE}{where} GROUP BY {group_by} ORDER BY {group_by}")
    return query(sql, params)


@tenant_billing.tool
def billing_filter_values() -> dict:
    """List distinct charge_type and status values in use, for find_billing."""
    return distinct_values(TABLE, ("charge_type", "status"))
