"""Tenant billing tools."""
from datetime import date
from fastmcp import FastMCP
from db import query, build_where

tenant_billing = FastMCP("tenant_billing")

BILL_COLS = ("bill_id, lease_id, tenant_id, charge_type, billing_date, "
             "due_date, amount, tax_amount, status")

@tenant_billing.tool
def get_billing(bill_id: int) -> dict | None:
    """Get a single bill by bill_id. Returns null if not found."""
    rows = query(f"SELECT {BILL_COLS} FROM smartreit.tenant_billing "
                 "WHERE bill_id = %s", (bill_id,))
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
    """Search bills. All filters optional, combined with AND.
    billed_from/billed_to filter on billing_date (inclusive).
    due_before filters on due_date, e.g. with status to find overdue bills.
    Newest bills first."""
    where, params = build_where(
        {"tenant_id": tenant_id, "lease_id": lease_id,
         "charge_type": charge_type, "status": status},
        [("billing_date >= %s", billed_from),
         ("billing_date <= %s", billed_to),
         ("due_date < %s", due_before)],
    )
    sql = (f"SELECT {BILL_COLS} FROM smartreit.tenant_billing{where} "
           "ORDER BY billing_date DESC, bill_id DESC LIMIT %s")
    return query(sql, params + [min(limit, 200)])

@tenant_billing.tool
def billing_summary(
    tenant_id: int | None = None,
    lease_id: int | None = None,
    billed_from: date | None = None,
    billed_to: date | None = None,
    group_by: str = "status",
) -> list[dict]:
    """Total amount, tax and bill count, grouped by status or charge_type.
    Use for balances owed, totals billed, and breakdowns by charge type."""
    if group_by not in {"status", "charge_type"}:
        raise ValueError("group_by must be 'status' or 'charge_type'")
    where, params = build_where(
        {"tenant_id": tenant_id, "lease_id": lease_id},
        [("billing_date >= %s", billed_from),
         ("billing_date <= %s", billed_to)],
    )
    sql = (f"SELECT {group_by}, COUNT(*) AS bills, "
           "SUM(amount) AS total_amount, "
           "SUM(COALESCE(tax_amount, 0)) AS total_tax, "
           "SUM(amount + COALESCE(tax_amount, 0)) AS total_with_tax "
           f"FROM smartreit.tenant_billing{where} "
           f"GROUP BY {group_by} ORDER BY {group_by}")
    return query(sql, params)