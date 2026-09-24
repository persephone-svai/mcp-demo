"""Tenant tools."""
from fastmcp import FastMCP
from db import query, build_where, cap_limit, distinct_values

tenant = FastMCP("tenant")

TABLE = "smartreit.tenant"
TENANT_COLUMNS = (
    "tenant_id", "party_id", "tenant_type", "credit_rating", "industry_code",
    "parent_tenant_id", "status", "verified_income", "credit_score",
)
TENANT_COLS = ", ".join(TENANT_COLUMNS)


@tenant.tool
def get_tenant(tenant_id: int) -> dict | None:
    """Get a single tenant by tenant_id. Returns null if not found.
    Tenant names live on the party record (see party_id / find_parties)."""
    rows = query(f"SELECT {TENANT_COLS} FROM {TABLE} WHERE tenant_id = %s", (tenant_id,))
    return rows[0] if rows else None


@tenant.tool
def find_tenants(
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
    """Search tenants. All filters are optional and combined with AND;
    call with no filters to list tenants. Use get_tenant for one tenant by ID.
    Use tenant_filter_values to see valid status, tenant_type,
    credit_rating and industry_code values."""
    where, params = build_where(
        {"party_id": party_id, "tenant_type": tenant_type,
         "credit_rating": credit_rating, "industry_code": industry_code,
         "parent_tenant_id": parent_tenant_id, "status": status},
        [("credit_score >= %s", min_credit_score),
         ("verified_income >= %s", min_verified_income)],
    )
    sql = f"SELECT {TENANT_COLS} FROM {TABLE}{where} ORDER BY tenant_id LIMIT %s"
    return query(sql, params + [cap_limit(limit)])


@tenant.tool
def get_tenant_family(tenant_id: int) -> dict:
    """Get a tenant's parent (if any) and its direct subsidiaries."""
    parent_cols = ", ".join(f"p.{c}" for c in TENANT_COLUMNS)
    parent = query(
        f"SELECT {parent_cols} FROM {TABLE} t "
        f"JOIN {TABLE} p ON p.tenant_id = t.parent_tenant_id "
        "WHERE t.tenant_id = %s", (tenant_id,))
    children = query(
        f"SELECT {TENANT_COLS} FROM {TABLE} WHERE parent_tenant_id = %s "
        "ORDER BY tenant_id LIMIT %s", (tenant_id, cap_limit(200)))
    return {"parent": parent[0] if parent else None, "subsidiaries": children}


@tenant.tool
def tenant_summary(group_by: str = "status", status: str | None = None) -> list[dict]:
    """Count tenants with average credit score and verified income, grouped by
    one of: status, tenant_type, credit_rating, industry_code."""
    allowed = {"status", "tenant_type", "credit_rating", "industry_code"}
    if group_by not in allowed:
        raise ValueError(f"group_by must be one of {sorted(allowed)}")
    where, params = build_where({"status": status})
    sql = (f"SELECT {group_by}, COUNT(*) AS tenants, "
           "ROUND(AVG(credit_score)) AS avg_credit_score, "
           "ROUND(AVG(verified_income)::numeric, 2) AS avg_verified_income "
           f"FROM {TABLE}{where} GROUP BY {group_by} ORDER BY tenants DESC")
    return query(sql, params)


@tenant.tool
def tenant_filter_values() -> dict:
    """List distinct status, tenant_type, credit_rating and industry_code values
    in use, to pass as find_tenants filters."""
    return distinct_values(TABLE, ("status", "tenant_type", "credit_rating", "industry_code"))
