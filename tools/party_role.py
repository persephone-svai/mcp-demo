"""Party role tools (details about the roles that parties can have)."""
from fastmcp import FastMCP
from db import query, build_where, cap_limit, contains

party_role = FastMCP("party_role")
TABLE = "smartreit.party_role"
PARTY_ROLE_COLUMNS = (
    "party_id", "party_role_id", "party_role", "effective_date", "end_date"
)
PARTY_ROLE_COLS = ", ".join(PARTY_ROLE_COLUMNS)

@party_role.tool
def get_party_role(party_role_id: int) -> dict | None:
    """Get the details of a party role by party_role_id.
    Returns null if not found."""
    rows = query(f"SELECT {PARTY_ROLE_COLS} FROM {TABLE} WHERE party_role_id = %s", (party_role_id,))
    return rows[0] if rows else None

@party_role.tool
def find_party_roles(
    party_id: int | None = None,
    party_role: str | None = None,
    effective_date: str | None = None,
    end_date: str | None = None,
    limit: int = 50,
) -> list[dict]:
    """Search party roles. All filters optional, combined with AND."""
    where, params = build_where(
        {"party_id": party_id},
        [("party_role = %s", party_role),
         ("effective_date >= %s", effective_date),
         ("end_date <= %s", end_date)],
    )
    sql = (f"SELECT {PARTY_ROLE_COLS} FROM {TABLE}{where} "
           "ORDER BY effective_date, end_date, party_role_id LIMIT %s")
    return query(sql, params + [cap_limit(limit)])
