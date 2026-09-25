"""Security deposit tools (deposits held against leases)."""
from datetime import date
from fastmcp import FastMCP
from customer_service.db import query, build_where, cap_limit, distinct_values

security_deposit = FastMCP("security_deposit")

TABLE = "smartreit.security_deposit"
# account_number is deliberately left out so bank details never reach the agent.
DEPOSIT_COLUMNS = (
    "deposit_id", "lease_id", "tenant_id", "amount", "deposit_date",
    "interest_rate", "released_date", "status",
)
DEPOSIT_COLS = ", ".join(DEPOSIT_COLUMNS)


def _released_condition(released: bool | None) -> list[str]:
    if released is None:
        return []
    return ["released_date IS NOT NULL" if released else "released_date IS NULL"]


@security_deposit.tool
def get_security_deposit(deposit_id: int) -> dict | None:
    """Get a single security deposit by deposit_id. Returns null if not found."""
    rows = query(f"SELECT {DEPOSIT_COLS} FROM {TABLE} WHERE deposit_id = %s", (deposit_id,))
    return rows[0] if rows else None


@security_deposit.tool
def find_security_deposits(
    lease_id: int | None = None,
    tenant_id: int | None = None,
    status: str | None = None,
    released: bool | None = None,
    deposited_from: date | None = None,
    deposited_to: date | None = None,
    released_from: date | None = None,
    released_to: date | None = None,
    min_amount: float | None = None,
    max_amount: float | None = None,
    limit: int = 50,
) -> list[dict]:
    """Search security deposits. All filters optional, combined with AND. Newest first.
    released=false means still held (no released_date); true means returned/released.
    Date ranges are inclusive. Use security_deposit_filter_values for valid statuses."""
    where, params = build_where(
        {"lease_id": lease_id, "tenant_id": tenant_id, "status": status},
        [("deposit_date >= %s", deposited_from),
         ("deposit_date <= %s", deposited_to),
         ("released_date >= %s", released_from),
         ("released_date <= %s", released_to),
         ("amount >= %s", min_amount),
         ("amount <= %s", max_amount)],
        _released_condition(released),
    )
    sql = (f"SELECT {DEPOSIT_COLS} FROM {TABLE}{where} "
           "ORDER BY deposit_date DESC NULLS LAST, deposit_id DESC LIMIT %s")
    return query(sql, params + [cap_limit(limit)])


@security_deposit.tool
def security_deposit_summary(
    group_by: str = "status",
    tenant_id: int | None = None,
    lease_id: int | None = None,
    released: bool | None = None,
) -> list[dict]:
    """Count deposits and total amount, grouped by status or tenant_id.
    Use released=false for total deposits currently held."""
    allowed = {"status", "tenant_id"}
    if group_by not in allowed:
        raise ValueError(f"group_by must be one of {sorted(allowed)}")
    where, params = build_where({"tenant_id": tenant_id, "lease_id": lease_id}, [],
                                _released_condition(released))
    sql = (f"SELECT {group_by}, COUNT(*) AS deposits, SUM(amount) AS total_amount, "
           "ROUND(AVG(interest_rate)::numeric, 4) AS avg_interest_rate "
           f"FROM {TABLE}{where} GROUP BY {group_by} ORDER BY total_amount DESC NULLS LAST")
    return query(sql, params)


@security_deposit.tool
def security_deposit_filter_values() -> dict:
    """List distinct status values in use, for find_security_deposits."""
    return distinct_values(TABLE, ("status",))
