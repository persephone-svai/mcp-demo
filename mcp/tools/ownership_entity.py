from fastmcp import FastMCP
from customer_service.db import query, build_where, cap_limit, contains
from datetime import date

ownership_entity = FastMCP("ownership_entity")
TABLE = "smartreit.ownership_entity"
OWNER_COLUMNS = (
    "ownership_entity_id", "owner_id", "owned_entity_id", "effective_date", "end_date"
)
OWNER_COLS = ", ".join(OWNER_COLUMNS)

@ownership_entity.tool
def get_ownership_entity(ownership_entity_id: int) -> dict | None:
    """Get the details of an ownership entity by ownership_entity_id.
    Returns null if not found."""
    rows = query(f"SELECT {OWNER_COLS} FROM {TABLE} WHERE ownership_entity_id = %s", (ownership_entity_id,))
    return rows[0] if rows else None

@ownership_entity.tool
def find_ownership_entities(
    owner_id: int | None = None,
    owned_entity_id: int | None = None,
    effective_date: date | None = None,
    end_date: date | None = None,
    limit: int = 50,
) -> list[dict]:
    """Search ownership entities. All filters optional, combined with AND."""
    where, params = build_where(
        {"owner_id": owner_id, "owned_entity_id": owned_entity_id},
        [("effective_date >= %s", effective_date),
         ("end_date <= %s", end_date)],
    )
    sql = (f"SELECT {OWNER_COLS} FROM {TABLE}{where} "
           "ORDER BY effective_date, end_date, ownership_entity_id LIMIT %s")
    return query(sql, params + [cap_limit(limit)])