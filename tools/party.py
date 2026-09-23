from datetime import date
from fastmcp import FastMCP
from db import query, build_where

party = FastMCP()

PARTY_COLS = ("party_id, party_code, display_name, primary_email, primary_phone, mailing_address_id, status")

def get_party(party_id: int | None = None):
    where, params = build_where({"party_id": party_id})
    rows = query(f"SELECT {PARTY_COLS} FROM smartreit.party{where} LIMIT 1", params)
    return rows[0] if rows else None

def find_parties(party_id: int | None = None,
                 party_code: str | None = None,
                 display_name_contains: str | None = None,
                 primary_email_contains: str | None = None,
                 primary_phone_contains: str | None = None,
                 mailing_address_id: int | None = None,
                 status: str | None = None,
                 limit: int = 50) -> list[dict]:
    where, params = build_where(
        {"party_id": party_id, "party_code": party_code, "status": status},
        [("display_name ILIKE %s", f"%{display_name_contains}%" if display_name_contains else None),
         ("primary_email ILIKE %s", f"%{primary_email_contains}%" if primary_email_contains else None),
         ("primary_phone ILIKE %s", f"%{primary_phone_contains}%" if primary_phone_contains else None)]
    )
    sql = f"SELECT {PARTY_COLS} FROM smartreit.party{where} ORDER BY display_name LIMIT %s"
    return query(sql, params + [min(limit, 200)])
