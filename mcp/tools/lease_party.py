"""Lease party tools (who is on each lease: tenant, guarantor, broker, etc.)."""
from fastmcp import FastMCP
from customer_service.db import query, build_where, cap_limit, distinct_values

lease_party = FastMCP("lease_party")

TABLE = "smartreit.lease_party"
LEASE_PARTY_COLUMNS = ("lease_party_id", "lease_id", "party_id", "role")
LEASE_PARTY_COLS = ", ".join(LEASE_PARTY_COLUMNS)


@lease_party.tool
def get_lease_party(lease_party_id: int) -> dict | None:
    """Get a single lease-party link by lease_party_id. Returns null if not found."""
    rows = query(f"SELECT {LEASE_PARTY_COLS} FROM {TABLE} WHERE lease_party_id = %s",
                 (lease_party_id,))
    return rows[0] if rows else None


@lease_party.tool
def find_lease_parties(
    lease_id: int | None = None,
    party_id: int | None = None,
    role: str | None = None,
    limit: int = 50,
) -> list[dict]:
    """Search lease-party links. All filters optional, combined with AND.
    Pass lease_id to see everyone on a lease, or party_id to find every lease a
    person/company is on. Use get_party for names.
    Use lease_party_filter_values for valid role values."""
    where, params = build_where({"lease_id": lease_id, "party_id": party_id, "role": role})
    sql = f"SELECT {LEASE_PARTY_COLS} FROM {TABLE}{where} ORDER BY lease_id, role LIMIT %s"
    return query(sql, params + [cap_limit(limit)])


@lease_party.tool
def lease_party_summary(group_by: str = "role", lease_id: int | None = None) -> list[dict]:
    """Count lease-party links grouped by role or party_id."""
    allowed = {"role", "party_id"}
    if group_by not in allowed:
        raise ValueError(f"group_by must be one of {sorted(allowed)}")
    where, params = build_where({"lease_id": lease_id})
    sql = (f"SELECT {group_by}, COUNT(*) AS lease_parties FROM {TABLE}{where} "
           f"GROUP BY {group_by} ORDER BY lease_parties DESC")
    return query(sql, params)


@lease_party.tool
def lease_party_filter_values() -> dict:
    """List distinct role values in use, for find_lease_parties."""
    return distinct_values(TABLE, ("role",))
