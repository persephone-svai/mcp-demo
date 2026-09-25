"""Department tools."""
from fastmcp import FastMCP
from customer_service.db import query, build_where, cap_limit, contains

department = FastMCP("department")

TABLE = "smartreit.department"
DEPARTMENT_COLUMNS = ("department_id", "department_name")
DEPARTMENT_COLS = ", ".join(DEPARTMENT_COLUMNS)


@department.tool
def get_department(department_id: int) -> dict | None:
    """Get a single department by department_id. Returns null if not found."""
    rows = query(f"SELECT {DEPARTMENT_COLS} FROM {TABLE} WHERE department_id = %s",
                 (department_id,))
    return rows[0] if rows else None


@department.tool
def find_departments(name_contains: str | None = None, limit: int = 50) -> list[dict]:
    """Search departments by part of the name (case-insensitive); call with no
    filter to list all. Use the department_id with find_employees."""
    where, params = build_where({}, [("department_name ILIKE %s", contains(name_contains))])
    sql = f"SELECT {DEPARTMENT_COLS} FROM {TABLE}{where} ORDER BY department_name LIMIT %s"
    return query(sql, params + [cap_limit(limit)])
