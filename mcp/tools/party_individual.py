"""Party individual tools (personal details for parties that are people)."""
from fastmcp import FastMCP
from customer_service.db import query, build_where, cap_limit, contains

party_individual = FastMCP("party_individual")

TABLE = "smartreit.party_individual"
# Deliberately NOT exposed to the agent: ssn, drivers_license_no, date_of_birth.
# They are never selected or searchable, so they can't end up in the model's context.
INDIVIDUAL_COLUMNS = (
    "party_id", "first_name", "middle_name", "last_name", "email", "phone",
    "home_address_id", "annual_income",
)
INDIVIDUAL_COLS = ", ".join(INDIVIDUAL_COLUMNS)


@party_individual.tool
def get_party_individual(party_id: int) -> dict | None:
    """Get the personal details of a party that is an individual, by party_id.
    Returns null if not found (e.g. the party is a company)."""
    rows = query(f"SELECT {INDIVIDUAL_COLS} FROM {TABLE} WHERE party_id = %s", (party_id,))
    return rows[0] if rows else None


@party_individual.tool
def find_party_individuals(
    first_name: str | None = None,
    last_name: str | None = None,
    name_contains: str | None = None,
    email_contains: str | None = None,
    phone_contains: str | None = None,
    home_address_id: int | None = None,
    min_annual_income: float | None = None,
    max_annual_income: float | None = None,
    limit: int = 50,
) -> list[dict]:
    """Search individuals. All filters optional, combined with AND.
    first_name/last_name are exact, case-insensitive matches.
    name_contains matches part of the full name, e.g. 'jane sm' finds 'Jane Smith'.
    Returns party_id, which links to find_tenants(party_id=...) and get_party."""
    where, params = build_where(
        {"home_address_id": home_address_id},
        [("lower(first_name) = lower(%s)", first_name),
         ("lower(last_name) = lower(%s)", last_name),
         ("concat_ws(' ', first_name, middle_name, last_name) ILIKE %s",
          contains(name_contains)),
         ("email ILIKE %s", contains(email_contains)),
         ("phone ILIKE %s", contains(phone_contains)),
         ("annual_income >= %s", min_annual_income),
         ("annual_income <= %s", max_annual_income)],
    )
    sql = (f"SELECT {INDIVIDUAL_COLS} FROM {TABLE}{where} "
           "ORDER BY last_name, first_name, party_id LIMIT %s")
    return query(sql, params + [cap_limit(limit)])
