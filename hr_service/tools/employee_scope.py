"""Who is the caller? Resolves the connection's employee email to their employee record."""

from fastmcp.server.dependencies import get_http_headers
from db import query

def caller_scope() -> dict:
    email = get_http_headers().get("x-employee-email")
    if not email:
        raise PermissionError("No employee email found in headers")
    rows = query("SELECT e.employee_id, e.party_id, e.department_id, e.manager_employee_id, "
        "e.work_location_property_id FROM smartreit.employee e "
        "JOIN smartreit.party p ON p.party_id = e.party_id "
        "WHERE lower(p.primary_email) = lower(%s) AND e.termination_date IS NULL",
        (email,))
    if not rows:
        raise PermissionError(f"No active employee record found for email {email}")
    me = rows[0]
    reports = [r["employee_id"] for r in query(
        "SELECT employee_id FROM smartreit.employee "
        "WHERE manager_employee_id = %s AND termination_date IS NULL",
        (me["employee_id"],))]
    return {"email": email, **me, "direct_reports": reports}    
