import mcp
from db import query
from datetime import date
from fastmcp import FastMCP

tenant_billing = FastMCP("tenant_billing")

"""Tenant Billing related tools"""

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
    exact = {"tenant_id": tenant_id, "lease_id": lease_id,
             "charge_type": charge_type, "status": status}
    where, params = [], []
    for col, val in exact.items():
        if val is not None:
            where.append(f"{col} = %s")
            params.append(val)
    if billed_from is not None:
        where.append("billing_date >= %s"); params.append(billed_from)
    if billed_to is not None:
        where.append("billing_date <= %s"); params.append(billed_to)
    if due_before is not None:
        where.append("due_date < %s"); params.append(due_before)

    sql = f"SELECT {BILL_COLS} FROM smartreit.tenant_billing"
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY billing_date DESC, bill_id DESC LIMIT %s"
    params.append(min(limit, 200))
    return query(sql, params)

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
    where, params = [], []
    for col, val in {"tenant_id": tenant_id, "lease_id": lease_id}.items():
        if val is not None:
            where.append(f"{col} = %s"); params.append(val)
    if billed_from is not None:
        where.append("billing_date >= %s"); params.append(billed_from)
    if billed_to is not None:
        where.append("billing_date <= %s"); params.append(billed_to)

    sql = (f"SELECT {group_by}, COUNT(*) AS bills, SUM(amount) AS total_amount, "
           f"SUM(tax_amount) AS total_tax, SUM(amount + tax_amount) AS total_with_tax "
           f"FROM smartreit.tenant_billing")
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += f" GROUP BY {group_by} ORDER BY {group_by}"
    return query(sql, params)
