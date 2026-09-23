from datetime import date

from anyio import Path
from fastmcp import FastMCP
from psycopg.rows import dict_row
import psycopg2
import psycopg2.extras
from psycopg2.pool import ThreadedConnectionPool
from dotenv import load_dotenv
import os
import logging
logging.basicConfig(level=logging.INFO)

load_dotenv(dotenv_path=Path(__file__).parent / ".env")
DATABASE_NAME = os.getenv("DATABASE_NAME")
DATABASE_HOST = os.getenv("DATABASE_HOST")
DATABASE_USER = os.getenv("DATABASE_USER")
DATABASE_PASSWORD = os.getenv("DATABASE_PASSWORD")
DATABASE_PORT = os.getenv("DATABASE_PORT")

logging.info("connecting to the database")
connection = psycopg2.connect(
    host=DATABASE_HOST,
    user=DATABASE_USER,
    password=DATABASE_PASSWORD,
    port=DATABASE_PORT,
    dbname=DATABASE_NAME,
    cursor_factory=psycopg2.extras.DictCursor
)

pool = ThreadedConnectionPool(
    minconn=1,
    maxconn=10,
    host=DATABASE_HOST,
    user=DATABASE_USER,
    password=DATABASE_PASSWORD,
    port=DATABASE_PORT,
    dbname=DATABASE_NAME,
    cursor_factory=psycopg2.extras.DictCursor
)

def query(sql, params=()):
    conn = pool.getconn()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            if cur.description:
                return cur.fetchall()
            return None
    finally:
        pool.putconn(conn)

logging.info(f"host={DATABASE_HOST!r} user={DATABASE_USER!r} port={DATABASE_PORT!r} pw_set={bool(DATABASE_PASSWORD)}")
logging.info("connected")
logging.info("Created cursor")
logging.info("Database setup complete")

mcp = FastMCP("MCP Demo Server")

@mcp.tool
def get_tenant(tenant_id: int) -> dict | None:
    """Get a single tenant by tenant_id. Returns null if not found."""
    rows = query("SELECT * FROM smartreit.tenant WHERE tenant_id = %s", (tenant_id,))
    return rows[0] if rows else None

@mcp.tool
def get_tenant_family(parent_id: int) -> list[dict]:
    """Get all tenants belonging to the same family by parent tenant ID."""
    return query("SELECT * FROM smartreit.tenant WHERE parent_tenant_id = %s", (parent_id,))

@mcp.tool
def get_all_tenants(limit: int = 50) -> list[dict]:
    """Get all tenants."""
    return query("SELECT * FROM smartreit.tenant ORDER BY tenant_id LIMIT %s", (min(limit, 200),))

@mcp.tool
def get_tenants_by_party(party_id: int) -> list[dict]:
    """Get all tenants by party_id."""
    return query("SELECT * FROM smartreit.tenant WHERE party_id = %s", (party_id,))

@mcp.tool
def get_all_active_tenants() -> list[dict]:
    """Get all active tenants."""
    return query("SELECT * FROM smartreit.tenant WHERE status = %s", ("active",))

@mcp.tool
def get_all_inactive_tenants() -> list[dict]:
    """Get all inactive tenants."""
    return query("SELECT * FROM smartreit.tenant WHERE status = %s", ("inactive",))

@mcp.tool
def get_all_tenants_by_industry(industry_code: str) -> list[dict]:
    """Get all tenants by their industry code."""
    return query("SELECT * FROM smartreit.tenant WHERE industry_code = %s", (industry_code,))

@mcp.tool
def get_all_tenants_by_credit_rating(credit_rating: str) -> list[dict]:
    """Get all tenants by their credit rating."""
    return query("SELECT * FROM smartreit.tenant WHERE credit_rating = %s", (credit_rating,))

@mcp.tool
def find_tenants(
    tenant_id: int | None = None,
    party_id: int | None = None,
    tenant_type: str | None = None,
    credit_rating: str | None = None,
    industry_code: str | None = None,
    parent_tenant_id: int | None = None,
    status: str | None = None,
    min_credit_score: int | None = None,
    min_verified_income: float | None = None,
    limit: int = 50,
) -> list[dict]:
    """Search tenants. All filters are optional and combined with AND.
    Omit a filter to ignore it. Use get_tenant to look up one tenant by ID.
    status: e.g. 'active', 'inactive'. tenant_type: e.g. 'corporate', 'individual'.
    """
    exact = {
        "tenant_id": tenant_id,
        "party_id": party_id,
        "tenant_type": tenant_type,
        "credit_rating": credit_rating,
        "industry_code": industry_code,
        "parent_tenant_id": parent_tenant_id,
        "status": status,
    }
    where, params = [], []
    for col, val in exact.items():
        if val is not None:
            where.append(f"{col} = %s")
            params.append(val)
    if min_credit_score is not None:
        where.append("credit_score >= %s")
        params.append(min_credit_score)
    if min_verified_income is not None:
        where.append("verified_income >= %s")
        params.append(min_verified_income)

    sql = "SELECT * FROM smartreit.tenant"
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY tenant_id LIMIT %s"
    params.append(min(limit, 200))
    return query(sql, params)

"""Tenant Billing related tools"""

BILL_COLS = ("bill_id, lease_id, tenant_id, charge_type, billing_date, "
             "due_date, amount, tax_amount, status")

@mcp.tool
def get_billing(bill_id: int) -> dict | None:
    """Get a single bill by bill_id. Returns null if not found."""
    rows = query(f"SELECT {BILL_COLS} FROM smartreit.tenant_billing "
                 "WHERE bill_id = %s", (bill_id,))
    return rows[0] if rows else None

@mcp.tool
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

@mcp.tool
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

"""Spaces (units/suites) management."""

SPACE_COLS = ("space_id, property_id, building_id, floor_id, space_code, space_type, "
              "rentable_sf, usable_sf, bedrooms, bathrooms, current_status")

@mcp.tool
def get_space(space_id: int) -> dict | None:
    """Get a single space by space_id. Returns null if not found."""
    rows = query(f"SELECT {SPACE_COLS} FROM smartreit.space WHERE space_id = %s",
                 (space_id,))
    return rows[0] if rows else None

@mcp.tool
def find_spaces(
    property_id: int | None = None,
    building_id: int | None = None,
    floor_id: int | None = None,
    space_code: str | None = None,
    space_type: str | None = None,
    current_status: str | None = None,
    min_rentable_sf: float | None = None,
    max_rentable_sf: float | None = None,
    min_bedrooms: int | None = None,
    min_bathrooms: float | None = None,
    limit: int = 50,
) -> list[dict]:
    """Search spaces (units/suites). All filters optional, combined with AND.
    Use current_status to find vacant/available space. Sizes are in square feet.
    Use space_filter_values to see valid space_type and current_status values."""
    exact = {"property_id": property_id, "building_id": building_id,
             "floor_id": floor_id, "space_code": space_code,
             "space_type": space_type, "current_status": current_status}
    where, params = [], []
    for col, val in exact.items():
        if val is not None:
            where.append(f"{col} = %s"); params.append(val)
    ranges = [("rentable_sf >= %s", min_rentable_sf),
              ("rentable_sf <= %s", max_rentable_sf),
              ("bedrooms >= %s", min_bedrooms),
              ("bathrooms >= %s", min_bathrooms)]
    for clause, val in ranges:
        if val is not None:
            where.append(clause); params.append(val)

    sql = f"SELECT {SPACE_COLS} FROM smartreit.space"
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY property_id, building_id, floor_id, space_code LIMIT %s"
    params.append(min(limit, 200))
    return query(sql, params)

@mcp.tool
def space_summary(
    group_by: str = "current_status",
    property_id: int | None = None,
    building_id: int | None = None,
) -> list[dict]:
    """Count spaces and total rentable/usable square feet, grouped by one of:
    current_status, space_type, property_id, building_id, floor_id.
    Use for occupancy, vacancy and inventory questions."""
    allowed = {"current_status", "space_type", "property_id", "building_id", "floor_id"}
    if group_by not in allowed:
        raise ValueError(f"group_by must be one of {sorted(allowed)}")
    where, params = [], []
    for col, val in {"property_id": property_id, "building_id": building_id}.items():
        if val is not None:
            where.append(f"{col} = %s"); params.append(val)

    sql = (f"SELECT {group_by}, COUNT(*) AS spaces, "
           f"SUM(rentable_sf) AS total_rentable_sf, SUM(usable_sf) AS total_usable_sf, "
           f"ROUND(100.0 * SUM(rentable_sf) / NULLIF(SUM(SUM(rentable_sf)) OVER (), 0), 1) "
           f"AS pct_of_rentable_sf "
           f"FROM smartreit.space")
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += f" GROUP BY {group_by} ORDER BY {group_by}"
    return query(sql, params)

@mcp.tool
def space_filter_values() -> dict:
    """List distinct space_type and current_status values in use."""
    return {
        col: [r[col] for r in query(
            f"SELECT DISTINCT {col} FROM smartreit.space "
            f"WHERE {col} IS NOT NULL ORDER BY 1")]
        for col in ("space_type", "current_status")
    }



if __name__ == "__main__":
    mcp.run()