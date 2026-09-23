"""Lease space tools (which spaces each lease covers, and how much SF)."""
from fastmcp import FastMCP
from db import query, build_where, cap_limit

lease_space = FastMCP("lease_space")

TABLE = "smartreit.lease_space"
LEASE_SPACE_COLUMNS = ("lease_space_id", "lease_id", "space_id", "leased_sf", "is_primary")
LEASE_SPACE_COLS = ", ".join(LEASE_SPACE_COLUMNS)


@lease_space.tool
def get_lease_space(lease_space_id: int) -> dict | None:
    """Get a single lease-space link by lease_space_id. Returns null if not found."""
    rows = query(f"SELECT {LEASE_SPACE_COLS} FROM {TABLE} WHERE lease_space_id = %s",
                 (lease_space_id,))
    return rows[0] if rows else None


@lease_space.tool
def find_lease_spaces(
    lease_id: int | None = None,
    space_id: int | None = None,
    is_primary: bool | None = None,
    min_leased_sf: float | None = None,
    max_leased_sf: float | None = None,
    limit: int = 50,
) -> list[dict]:
    """Search lease-space links. All filters optional, combined with AND.
    Pass lease_id to list the spaces a lease covers, or space_id to find the
    leases on a space. is_primary marks a lease's main space."""
    where, params = build_where(
        {"lease_id": lease_id, "space_id": space_id, "is_primary": is_primary},
        [("leased_sf >= %s", min_leased_sf),
         ("leased_sf <= %s", max_leased_sf)],
    )
    sql = (f"SELECT {LEASE_SPACE_COLS} FROM {TABLE}{where} "
           "ORDER BY lease_id, is_primary DESC, space_id LIMIT %s")
    return query(sql, params + [cap_limit(limit)])


@lease_space.tool
def lease_space_summary(group_by: str = "lease_id",
                        lease_id: int | None = None,
                        space_id: int | None = None) -> list[dict]:
    """Count spaces and total leased SF, grouped by lease_id or space_id."""
    allowed = {"lease_id", "space_id"}
    if group_by not in allowed:
        raise ValueError(f"group_by must be one of {sorted(allowed)}")
    where, params = build_where({"lease_id": lease_id, "space_id": space_id})
    sql = (f"SELECT {group_by}, COUNT(*) AS spaces, SUM(leased_sf) AS total_leased_sf "
           f"FROM {TABLE}{where} GROUP BY {group_by} ORDER BY total_leased_sf DESC NULLS LAST")
    return query(sql, params)
