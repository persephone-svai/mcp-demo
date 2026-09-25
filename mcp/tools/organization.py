"""Organization tools (details for parties that are companies)."""
from datetime import date
from fastmcp import FastMCP
from customer_service.db import query, build_where, cap_limit, contains, distinct_values

organization = FastMCP("organization")

TABLE = "smartreit.organization"
ORG_COLUMNS = (
    "party_id", "legal_name", "dba_date", "tax_id", "entity_type", "industry_code",
    "website", "incorporation_state", "parent_organization_id",
)
ORG_COLS = ", ".join(ORG_COLUMNS)


@organization.tool
def get_organization(party_id: int) -> dict | None:
    """Get the company details of a party that is an organization, by party_id.
    Returns null if not found (e.g. the party is an individual)."""
    rows = query(f"SELECT {ORG_COLS} FROM {TABLE} WHERE party_id = %s", (party_id,))
    return rows[0] if rows else None


@organization.tool
def find_organizations(
    name_contains: str | None = None,
    website_contains: str | None = None,
    entity_type: str | None = None,
    industry_code: str | None = None,
    incorporation_state: str | None = None,
    parent_organization_id: int | None = None,
    dba_from: date | None = None,
    dba_to: date | None = None,
    limit: int = 50,
) -> list[dict]:
    """Search organizations. All filters optional, combined with AND.
    name_contains matches part of the legal name (case-insensitive),
    e.g. 'acme' finds 'Acme Holdings LLC'. Returns party_id, which links to
    find_tenants(party_id=...) and find_vendors(party_id=...).
    Use organization_filter_values for valid entity_type, industry_code
    and incorporation_state values."""
    where, params = build_where(
        {"entity_type": entity_type, "industry_code": industry_code,
         "incorporation_state": incorporation_state,
         "parent_organization_id": parent_organization_id},
        [("legal_name ILIKE %s", contains(name_contains)),
         ("website ILIKE %s", contains(website_contains)),
         ("dba_date >= %s", dba_from),
         ("dba_date <= %s", dba_to)],
    )
    sql = f"SELECT {ORG_COLS} FROM {TABLE}{where} ORDER BY legal_name, party_id LIMIT %s"
    return query(sql, params + [cap_limit(limit)])


@organization.tool
def get_organization_family(party_id: int) -> dict:
    """Get an organization's parent company (if any) and its direct subsidiaries."""
    parent_cols = ", ".join(f"p.{c}" for c in ORG_COLUMNS)
    parent = query(
        f"SELECT {parent_cols} FROM {TABLE} o "
        f"JOIN {TABLE} p ON p.party_id = o.parent_organization_id "
        "WHERE o.party_id = %s", (party_id,))
    children = query(
        f"SELECT {ORG_COLS} FROM {TABLE} WHERE parent_organization_id = %s "
        "ORDER BY legal_name LIMIT %s", (party_id, cap_limit(200)))
    return {"parent": parent[0] if parent else None, "subsidiaries": children}


@organization.tool
def organization_summary(group_by: str = "entity_type") -> list[dict]:
    """Count organizations grouped by one of: entity_type, industry_code,
    incorporation_state."""
    allowed = {"entity_type", "industry_code", "incorporation_state"}
    if group_by not in allowed:
        raise ValueError(f"group_by must be one of {sorted(allowed)}")
    sql = (f"SELECT {group_by}, COUNT(*) AS organizations FROM {TABLE} "
           f"GROUP BY {group_by} ORDER BY organizations DESC")
    return query(sql)


@organization.tool
def organization_filter_values() -> dict:
    """List distinct entity_type, industry_code and incorporation_state values
    in use, for find_organizations."""
    return distinct_values(TABLE, ("entity_type", "industry_code", "incorporation_state"))