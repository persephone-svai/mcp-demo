"""Party tools (the people and companies behind tenants, vendors, etc.)."""
from fastmcp import FastMCP
from customer_service.db import query, build_where, cap_limit, contains, distinct_values

party = FastMCP("party")

TABLE = "smartreit.party"
PARTY_COLUMNS = (
    "party_id", "party_code", "display_name", "primary_email", "primary_phone",
    "mailing_address_id", "status",
)
PARTY_COLS = ", ".join(PARTY_COLUMNS)


@party.tool
def get_party(party_id: int | None = None,
              party_code: str | None = None) -> dict | None:
    """Get one party by party_id or party_code (give one). Returns null if not found.
    To search by name, email or phone, use find_parties."""
    if party_id is None and party_code is None:
        raise ValueError("Give party_id or party_code")
    where, params = build_where({"party_id": party_id, "party_code": party_code})
    rows = query(f"SELECT {PARTY_COLS} FROM {TABLE}{where} LIMIT 1", params)
    return rows[0] if rows else None


@party.tool
def find_parties(
    name_contains: str | None = None,
    email_contains: str | None = None,
    phone_contains: str | None = None,
    mailing_address_id: int | None = None,
    status: str | None = None,
    limit: int = 50,
) -> list[dict]:
    """Search parties. All filters optional, combined with AND.
    name_contains matches part of the display name or party code
    (case-insensitive), e.g. 'acme' finds 'Acme Corp'. Use this to turn a
    tenant or vendor name into a party_id, then call find_tenants(party_id=...)
    or find_vendors(party_id=...). Use party_filter_values for valid statuses."""
    where, params = build_where(
        {"mailing_address_id": mailing_address_id, "status": status},
        [("concat_ws(' ', display_name, party_code) ILIKE %s", contains(name_contains)),
         ("primary_email ILIKE %s", contains(email_contains)),
         ("primary_phone ILIKE %s", contains(phone_contains))],
    )
    sql = f"SELECT {PARTY_COLS} FROM {TABLE}{where} ORDER BY display_name LIMIT %s"
    return query(sql, params + [cap_limit(limit)])


@party.tool
def party_filter_values() -> dict:
    """List distinct status values in use, for find_parties."""
    return distinct_values(TABLE, ("status",))
