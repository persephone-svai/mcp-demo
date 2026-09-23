from fastmcp import FastMCP
from db import query

tenant = FastMCP("tenant")

@tenant.tool
def get_tenant(tenant_id: int) -> dict | None:
    """Get a single tenant by tenant_id. Returns null if not found."""
    rows = query("SELECT * FROM smartreit.tenant WHERE tenant_id = %s", (tenant_id,))
    return rows[0] if rows else None

@tenant.tool
def get_tenant_family(parent_id: int) -> list[dict]:
    """Get all tenants belonging to the same family by parent tenant ID."""
    return query("SELECT * FROM smartreit.tenant WHERE parent_tenant_id = %s", (parent_id,))

@tenant.tool
def get_all_tenants(limit: int = 50) -> list[dict]:
    """Get all tenants."""
    return query("SELECT * FROM smartreit.tenant ORDER BY tenant_id LIMIT %s", (min(limit, 200),))

@tenant.tool
def get_tenants_by_party(party_id: int) -> list[dict]:
    """Get all tenants by party_id."""
    return query("SELECT * FROM smartreit.tenant WHERE party_id = %s", (party_id,))

@tenant.tool
def get_all_active_tenants() -> list[dict]:
    """Get all active tenants."""
    return query("SELECT * FROM smartreit.tenant WHERE status = %s", ("active",))

@tenant.tool
def get_all_inactive_tenants() -> list[dict]:
    """Get all inactive tenants."""
    return query("SELECT * FROM smartreit.tenant WHERE status = %s", ("inactive",))

@tenant.tool
def get_all_tenants_by_industry(industry_code: str) -> list[dict]:
    """Get all tenants by their industry code."""
    return query("SELECT * FROM smartreit.tenant WHERE industry_code = %s", (industry_code,))

@tenant.tool
def get_all_tenants_by_credit_rating(credit_rating: str) -> list[dict]:
    """Get all tenants by their credit rating."""
    return query("SELECT * FROM smartreit.tenant WHERE credit_rating = %s", (credit_rating,))

@tenant.tool
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