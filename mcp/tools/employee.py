"""Employee tools (staff, reporting lines and departments)."""
from datetime import date
from fastmcp import FastMCP
from customer_service.db import query, build_where, cap_limit, contains, distinct_values

employee = FastMCP("employee")

TABLE = "smartreit.employee"
EMPLOYEE_COLUMNS = (
    "employee_id", "party_id", "employee_number", "department_id", "manager_employee_id",
    "job_title", "hire_date", "termination_date", "employment_status",
    "work_location_property_id", "base_salary", "pay_frequency",
)
EMPLOYEE_COLS = ", ".join(EMPLOYEE_COLUMNS)


@employee.tool
def get_employee(employee_id: int | None = None,
                 employee_number: str | None = None) -> dict | None:
    """Get one employee by employee_id or employee_number (give one).
    Returns null if not found. Names are on the party record (get_party_individual)."""
    if employee_id is None and employee_number is None:
        raise ValueError("Give employee_id or employee_number")
    where, params = build_where({"employee_id": employee_id,
                                 "employee_number": employee_number})
    rows = query(f"SELECT {EMPLOYEE_COLS} FROM {TABLE}{where} LIMIT 1", params)
    return rows[0] if rows else None


@employee.tool
def find_employees(
    party_id: int | None = None,
    department_id: int | None = None,
    manager_employee_id: int | None = None,
    work_location_property_id: int | None = None,
    employment_status: str | None = None,
    job_title_contains: str | None = None,
    current: bool | None = None,
    hired_from: date | None = None,
    hired_to: date | None = None,
    limit: int = 50,
) -> list[dict]:
    """Search employees. All filters optional, combined with AND.
    current=true means no termination_date; false means terminated.
    job_title_contains matches part of the title, e.g. 'manager'.
    Use employee_filter_values for valid employment_status and job_title values."""
    conditions = []
    if current is not None:
        conditions.append("termination_date IS NULL" if current else "termination_date IS NOT NULL")
    where, params = build_where(
        {"party_id": party_id, "department_id": department_id,
         "manager_employee_id": manager_employee_id,
         "work_location_property_id": work_location_property_id,
         "employment_status": employment_status},
        [("job_title ILIKE %s", contains(job_title_contains)),
         ("hire_date >= %s", hired_from),
         ("hire_date <= %s", hired_to)],
        conditions,
    )
    sql = f"SELECT {EMPLOYEE_COLS} FROM {TABLE}{where} ORDER BY employee_id LIMIT %s"
    return query(sql, params + [cap_limit(limit)])


@employee.tool
def get_employee_team(employee_id: int) -> dict:
    """Get an employee's manager (if any) and their direct reports."""
    manager_cols = ", ".join(f"m.{c}" for c in EMPLOYEE_COLUMNS)
    manager = query(
        f"SELECT {manager_cols} FROM {TABLE} e "
        f"JOIN {TABLE} m ON m.employee_id = e.manager_employee_id "
        "WHERE e.employee_id = %s", (employee_id,))
    reports = query(
        f"SELECT {EMPLOYEE_COLS} FROM {TABLE} WHERE manager_employee_id = %s "
        "ORDER BY employee_id LIMIT %s", (employee_id, cap_limit(200)))
    return {"manager": manager[0] if manager else None, "direct_reports": reports}


@employee.tool
def employee_summary(group_by: str = "department_id",
                     current: bool | None = True) -> list[dict]:
    """Headcount grouped by one of: department_id, employment_status, job_title,
    work_location_property_id. Defaults to current employees only;
    pass current=null to include terminated staff."""
    allowed = {"department_id", "employment_status", "job_title", "work_location_property_id"}
    if group_by not in allowed:
        raise ValueError(f"group_by must be one of {sorted(allowed)}")
    conditions = []
    if current is not None:
        conditions.append("termination_date IS NULL" if current else "termination_date IS NOT NULL")
    where, params = build_where({}, [], conditions)
    sql = (f"SELECT {group_by}, COUNT(*) AS employees FROM {TABLE}{where} "
           f"GROUP BY {group_by} ORDER BY employees DESC")
    return query(sql, params)


@employee.tool
def employee_filter_values() -> dict:
    """List distinct employment_status, job_title and pay_frequency values in use."""
    return distinct_values(TABLE, ("employment_status", "job_title", "pay_frequency"))
