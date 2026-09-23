"""Tenant tools."""
from fastmcp import FastMCP
from db import query, build_where

tenant = FastMCP("tenant")

TENANT_COLS = ("tenant_id, party_id, tenant_type, credit_rating, industry_code, "
               "parent_tenant_id, status, verified_income, credit_score")

@tenant.tool
def get_tenant(tenant_id: int) -> dict | None:
    """Get a single tenant by tenant_id. Returns null if not found."""
    rows = query(f"SELECT {TENANT_COLS} FROM smartreit.tenant WHERE tenant_id = %s",
                 (tenant_id,))
    return rows[0] if rows else None

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
    Omit a filter to ignore it; call with no filters to list tenants.
    Use tenant_filter_values to see valid status, tenant_type,
    credit_rating and industry_code values."""
    where, params = build_where(
        {"tenant_id": tenant_id, "party_id": party_id, "tenant_type": tenant_type,
         "credit_rating": credit_rating, "industry_code": industry_code,
         "parent_tenant_id": parent_tenant_id, "status": status},
        [("credit_score >= %s", min_credit_score),
         ("verified_income >= %s", min_verified_income)],
    )
    sql = (f"SELECT {TENANT_COLS} FROM smartreit.tenant{where} "
           "ORDER BY tenant_id LIMIT %s")
    return query(sql, params + [min(limit, 200)])

@tenant.tool
def get_tenant_family(tenant_id: int) -> dict:
    """Get a tenant's parent (if any) and its direct subsidiaries."""
    parent = query(
        "SELECT p.tenant_id, p.party_id, p.tenant_type, p.credit_rating, "
        "p.industry_code, p.parent_tenant_id, p.status, p.verified_income, "
        "p.credit_score "
        "FROM smartreit.tenant t "
        "JOIN smartreit.tenant p ON p.tenant_id = t.parent_tenant_id "
        "WHERE t.tenant_id = %s", (tenant_id,))
    children = query(
        f"SELECT {TENANT_COLS} FROM smartreit.tenant WHERE parent_tenant_id = %s "
        "ORDER BY tenant_id LIMIT 200", (tenant_id,))
    return {"parent": parent[0] if parent else None, "subsidiaries": children}

@tenant.tool
def tenant_filter_values() -> dict:
    """List the distinct values in use for status, tenant_type,
    credit_rating and industry_code, to use as find_tenants filters."""
    return {
        col: [r[col] for r in query(
            f"SELECT DISTINCT {col} FROM smartreit.tenant "
            f"WHERE {col} IS NOT NULL ORDER BY 1")]
        for col in ("status", "tenant_type", "credit_rating", "industry_code")
    }