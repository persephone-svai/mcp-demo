# SmartREIT data tools — instructions for the agent

You have read-only access to a real-estate portfolio: properties, buildings,
floors, spaces, leases, tenants, billing, deposits, vendors, work orders,
assets, employees and the people/companies behind them. You cannot change data.

## Finding the right record

People refer to things by name; the tools work on IDs. Always resolve names first:

- Company or person (tenant, vendor, manager, guarantor) →
  `find_parties(name_contains=...)`, then use its `party_id`.
  More detail: `get_organization(party_id)` or `get_party_individual(party_id)`.
- From a party to their role:
  `find_tenants(party_id=...)`, `find_vendors(party_id=...)`,
  `find_employees(party_id=...)`, `find_lease_parties(party_id=...)`.
- Property → `find_properties(name_contains=...)` (matches name or code),
  or `find_properties_near(latitude, longitude)`.
- Building → `find_buildings(name_contains=...)`; address → `find_addresses(street_contains=...)`.
- Lease by number → `get_lease(lease_number=...)`.

If a search returns several matches, show them and ask which one is meant.
If it returns none, say so — never invent an ID or a record.

## Tool families

Each area has the same set of tools:

- `get_<thing>` — one record by ID; returns null if it doesn't exist.
- `find_<things>` — search with optional filters, combined with AND. Omit a
  filter to ignore it. Results are capped (default 50, max 200).
- `<thing>_summary` — counts, totals and averages computed by the database.
- `<thing>_filter_values` — the real status/type values in use.

## Rules

1. **Check valid values before filtering.** Status and type values are specific
   to this database. Call the matching `_filter_values` tool rather than guessing
   `'active'`, `'vacant'`, etc. A wrong value silently returns nothing.
2. **Use summaries for any number.** For counts, totals, averages, occupancy or
   "how much", call a `_summary` tool instead of adding up rows yourself.
3. **Narrow searches instead of paging.** If a result hits the limit, there are
   more rows: add filters (property, date range, status) rather than
   concluding the list is complete. Say when a list may be incomplete.
4. **"Current" means `active_on` = today.** Leases, rent schedules and
   management agreements accept `active_on` to return only what is in force on
   that date. Employees use `current=true`; work orders use `completed`;
   deposits use `released`; tenant improvements use `in_progress`.
5. **Dates** are `YYYY-MM-DD`. Date ranges (`_from`/`_to`) are inclusive.
6. **Units:** areas are square feet (`rentable_sf`, `usable_sf`, `leased_sf`).
   Money is in the record's currency (`lease.currency_code` if present).
   Rent schedule `amount` is per `amount_frequency`, so don't add amounts with
   different frequencies. Check how percentages are stored (e.g. 92 vs 0.92)
   from the data before filtering on them.
7. **Snapshots are periodic.** `get_property_snapshot` returns the latest
   snapshot on or before the date you give, which may be earlier than that date;
   report the actual `snapshot_date`.

## Common questions → tools

| Question | Tools |
|---|---|
| Who is the tenant in suite X / what's in space X? | `find_spaces` → `find_lease_spaces(space_id)` → `get_lease` → `get_tenant` → `get_party` |
| What spaces / rent does tenant Y have? | `find_parties` → `find_tenants(party_id)` → `find_leases(tenant_id, active_on=today)` → `find_lease_spaces(lease_id)`, `find_lease_rent_schedules(lease_id, active_on=today)` |
| Which leases expire soon? | `find_leases(expiring_from=today, expiring_to=...)` |
| How much does tenant Y owe? | `billing_summary(tenant_id=..., group_by="status")`; details via `find_billing` |
| Overdue bills | `find_billing(status=<unpaid value>, due_before=today)` |
| Vacancy / occupancy of a property | `space_summary(property_id=..., group_by="current_status")`, or `get_property_snapshot(property_id)` |
| Available space over N sq ft | `find_spaces(current_status=<vacant value>, min_rentable_sf=N)` |
| NOI / occupancy trend | `find_property_snapshots(property_id, date_from, date_to, order_by="snapshot_date")` |
| Rank properties by a metric | `find_property_snapshots(date_from=d, date_to=d, order_by="noi")` |
| Who manages property Z? | `find_management_agreements(property_id, active_on=today)` → `get_party(manager_party_id)` |
| Open work orders | `find_work_orders(completed=false, property_id=...)`; counts via `work_order_summary` |
| Vendors with lapsed insurance | `find_vendors(insurance_expires_before=today)` |
| Equipment due for replacement | `find_assets(due_for_replacement_by=...)` |
| Deposits currently held | `security_deposit_summary(released=false)` |
| Parent company / subsidiaries | `get_tenant_family`, `get_organization_family` |
| Someone's manager / team | `get_employee_team(employee_id)` |

## Privacy

Social security numbers, driver's licence numbers, dates of birth and bank
account numbers are not available through these tools. Don't try to obtain
them. Treat income, salary and tax IDs as confidential: share them only when
the user's question needs them.

## Answering

- Name the records you used (e.g. "Lease L-1042, Suite 400") so the user can check.
- If a tool errors with "permission denied for schema smartreit", the server's
  database access isn't set up. Say so rather than retrying.

<!-- GENERATED TOOL REFERENCE: edit gen_agent_instructions.py, not below -->

# Complete tool reference (generated from the code)

25 tables, 91 tools. Every tool is read-only. Parameters not listed as required are optional; omit them to not filter. `limit` defaults as shown and is clamped to 1..200. Dates are ISO `YYYY-MM-DD`. All filters in one call are combined with AND.

## ID cross-reference

For every ID column: the tool that resolves it to a record, and every tool that accepts it as a filter.

- `address_id` -> resolve with `get_address`; filter with: (none)
- `agreement_id` -> resolve with `get_management_agreement`; filter with: (none)
- `asset_id` -> resolve with `get_asset`; filter with: `find_work_orders`
- `assigned_employee_id` -> resolve with `get_employee`; filter with: `find_work_orders`
- `bill_id` -> resolve with `get_billing`; filter with: (none)
- `building_id` -> resolve with `get_building`; filter with: `find_assets`, `find_floors`, `find_spaces`, `find_work_orders`, `floor_summary`, `space_summary`
- `department_id` -> resolve with `get_department`; filter with: `find_employees`
- `deposit_id` -> resolve with `get_security_deposit`; filter with: (none)
- `employee_id` -> resolve with `get_employee`; filter with: `get_employee_team`
- `floor_id` -> resolve with `get_floor`; filter with: `find_spaces`
- `home_address_id` -> resolve with `get_address`; filter with: `find_party_individuals`
- `lease_id` -> resolve with `get_lease`; filter with: `billing_summary`, `find_billing`, `find_lease_parties`, `find_lease_rent_schedules`, `find_lease_spaces`, `find_security_deposits`, `find_tenant_improvements`, `lease_party_summary`, `lease_rent_schedule_summary`, `lease_space_summary`, `security_deposit_summary`
- `lease_party_id` -> resolve with `get_lease_party`; filter with: (none)
- `lease_space_id` -> resolve with `get_lease_space`; filter with: (none)
- `mailing_address_id` -> resolve with `get_address`; filter with: `find_parties`
- `manager_employee_id` -> resolve with `get_employee`; filter with: `find_employees`
- `manager_party_id` -> resolve with `get_party`; filter with: `find_management_agreements`
- `owned_entity_id` -> resolve with `(no get tool)`; filter with: `find_ownership_entities`
- `owner_id` -> resolve with `(no get tool)`; filter with: `find_ownership_entities`
- `ownership_entity_id` -> resolve with `get_ownership_entity`; filter with: `find_properties`
- `parent_organization_id` -> resolve with `get_organization (party_id of the parent company)`; filter with: `find_organizations`
- `parent_tenant_id` -> resolve with `get_tenant`; filter with: `find_tenants`
- `party_id` -> resolve with `get_party`; filter with: `find_employees`, `find_lease_parties`, `find_party_roles`, `find_tenants`, `find_vendors`, `get_organization`, `get_organization_family`, `get_party_individual`
- `party_role_id` -> resolve with `get_party_role`; filter with: (none)
- `property_id` -> resolve with `get_property`; filter with: `asset_summary`, `building_summary`, `find_assets`, `find_buildings`, `find_leases`, `find_management_agreements`, `find_property_snapshots`, `find_spaces`, `find_tenant_improvements`, `find_work_orders`, `get_property_snapshot`, `lease_summary`, `space_summary`, `tenant_improvement_summary`, `work_order_summary`
- `rent_schedule_id` -> resolve with `get_lease_rent_schedule`; filter with: (none)
- `requested_by_party_id` -> resolve with `get_party`; filter with: `find_work_orders`
- `space_id` -> resolve with `get_space`; filter with: `find_assets`, `find_lease_spaces`, `find_tenant_improvements`, `find_work_orders`, `lease_space_summary`
- `tenant_id` -> resolve with `get_tenant`; filter with: `billing_summary`, `find_billing`, `find_leases`, `find_security_deposits`, `get_tenant_family`, `security_deposit_summary`
- `ti_id` -> resolve with `get_tenant_improvement`; filter with: (none)
- `vendor_id` -> resolve with `get_vendor`; filter with: `find_work_orders`
- `work_location_property_id` -> resolve with `get_property`; filter with: `find_employees`
- `work_order_id` -> resolve with `get_work_order`; filter with: (none)

## Tool index

- **address** (`smartreit.address`): `get_address`, `find_addresses`, `find_addresses_near`, `address_summary`, `address_filter_values`
- **asset** (`smartreit.asset`): `get_asset`, `find_assets`, `asset_summary`, `asset_filter_values`
- **building** (`smartreit.building`): `get_building`, `find_buildings`, `building_summary`, `building_filter_values`
- **department** (`smartreit.department`): `get_department`, `find_departments`
- **employee** (`smartreit.employee`): `get_employee`, `find_employees`, `get_employee_team`, `employee_summary`, `employee_filter_values`
- **floor** (`smartreit.floor`): `get_floor`, `find_floors`, `floor_summary`
- **lease** (`smartreit.lease`): `get_lease`, `find_leases`, `lease_summary`, `lease_filter_values`
- **lease_party** (`smartreit.lease_party`): `get_lease_party`, `find_lease_parties`, `lease_party_summary`, `lease_party_filter_values`
- **lease_rent_schedule** (`smartreit.lease_rent_schedule`): `get_lease_rent_schedule`, `find_lease_rent_schedules`, `lease_rent_schedule_summary`, `lease_rent_schedule_filter_values`
- **lease_space** (`smartreit.lease_space`): `get_lease_space`, `find_lease_spaces`, `lease_space_summary`
- **management_agreement** (`smartreit.management_agreement`): `get_management_agreement`, `find_management_agreements`, `management_agreement_summary`, `management_agreement_filter_values`
- **organization** (`smartreit.organization`): `get_organization`, `find_organizations`, `get_organization_family`, `organization_summary`, `organization_filter_values`
- **ownership_entity** (`smartreit.ownership_entity`): `get_ownership_entity`, `find_ownership_entities`
- **party** (`smartreit.party`): `get_party`, `find_parties`, `party_filter_values`
- **party_individual** (`smartreit.party_individual`): `get_party_individual`, `find_party_individuals`
- **party_role** (`smartreit.party_role`): `get_party_role`, `find_party_roles`
- **property** (`smartreit.property`): `get_property`, `find_properties`, `find_properties_near`, `property_summary`, `property_filter_values`
- **property_operating_snapshot** (`smartreit.property_operating_snapshot`): `get_property_snapshot`, `find_property_snapshots`
- **security_deposit** (`smartreit.security_deposit`): `get_security_deposit`, `find_security_deposits`, `security_deposit_summary`, `security_deposit_filter_values`
- **space** (`smartreit.space`): `get_space`, `find_spaces`, `space_summary`, `space_filter_values`
- **tenant** (`smartreit.tenant`): `get_tenant`, `find_tenants`, `get_tenant_family`, `tenant_summary`, `tenant_filter_values`
- **tenant_billing** (`smartreit.tenant_billing`): `get_billing`, `find_billing`, `billing_summary`, `billing_filter_values`
- **tenant_improvement** (`smartreit.tenant_improvement`): `get_tenant_improvement`, `find_tenant_improvements`, `tenant_improvement_summary`
- **vendor** (`smartreit.vendor`): `get_vendor`, `find_vendors`, `vendor_summary`, `vendor_filter_values`
- **work_order** (`smartreit.work_order`): `get_work_order`, `find_work_orders`, `work_order_summary`, `work_order_filter_values`

## Table `smartreit.address` (module `tools/address.py`)

Columns returned by this table's tools: `address_id`, `address_line_1`, `address_line_2`, `city`, `county`, `state`, `postal_code`, `country`, `latitude`, `longitude`, `geocode_source`.
Never available (not selected): `created_at`, `updated_at`.

### `get_address`

Returns: `dict | None`.

Description: Get a single address by address_id. Returns null if not found.

Parameters:
- `address_id`: `int`, REQUIRED.

Example: `get_address(address_id=7)`

### `find_addresses`

Returns: `list[dict]`.

Description: Search addresses. All filters optional, combined with AND. street_contains matches part of address lines 1 or 2, e.g. 'maple st'. city, county, state and country are exact, case-insensitive matches. Use the address_id with find_properties / find_buildings. Use address_filter_values for the state and country values in use.

Parameters:
- `street_contains`: `str | None`, optional, default `None`. SQL: `concat_ws(' ', address_line_1, address_line_2) ILIKE <value>  (partial, case-insensitive: value is wrapped as %value%)`.
- `city`: `str | None`, optional, default `None`. SQL: `city ILIKE <value>`.
- `county`: `str | None`, optional, default `None`. SQL: `county ILIKE <value>`.
- `state`: `str | None`, optional, default `None`. SQL: `state ILIKE <value>`.
- `postal_code_prefix`: `str | None`, optional, default `None`. SQL: `postal_code ILIKE <value>  (prefix match: value%)`.
- `country`: `str | None`, optional, default `None`. SQL: `country ILIKE <value>`.
- `limit`: `int`, optional, default `50`. Max rows returned; clamped to 1..200.
Row order: `country, state, city, address_line_1`.

Example: `find_addresses(street_contains="<part of the text>", city="<exact text, any case>")`

### `find_addresses_near`

Returns: `list[dict]`.

Description: Find addresses within radius_km of a point, nearest first, with distance_km.

Parameters:
- `latitude`: `float`, REQUIRED.
- `longitude`: `float`, REQUIRED.
- `radius_km`: `float`, optional, default `10`.
- `limit`: `int`, optional, default `20`. Max rows returned; clamped to 1..200.

Extra / aggregate output fields: `distance_km`.
Row order: `distance_km`.

Example: `find_addresses_near(latitude=49.2827, longitude=-123.1207)`

### `address_summary`

Returns: `list[dict]`.

Description: Count addresses grouped by one of: city, county, state, country, geocode_source.

Parameters:
- `group_by`: `str`, optional, default `'state'`. Allowed values: `"city"`, `"country"`, `"county"`, `"geocode_source"`, `"state"`. Any other value raises an error.
- `country`: `str | None`, optional, default `None`. SQL: `country ILIKE <value>`.

Extra / aggregate output fields: `addresses`.
Row order: `addresses DESC`.

Example: `address_summary(country="<exact text, any case>", group_by="state")`

### `address_filter_values`

Returns: `dict`.

Description: List distinct state, country and geocode_source values in use.

Parameters:
- (none)

Example: `address_filter_values()`

## Table `smartreit.asset` (module `tools/asset.py`)

Columns returned by this table's tools: `asset_id`, `property_id`, `building_id`, `space_id`, `asset_type`, `asset_name`, `manufacturer`, `model`, `serial_number`, `installation_date`, `useful_life_years`, `replacement_cost`, `status`.
Links to other tables: `property_id` -> get_property; `building_id` -> get_building; `space_id` -> get_space.

### `get_asset`

Returns: `dict | None`.

Description: Get one asset by asset_id or serial_number (give one), with its replacement_due_date. Returns null if not found.

Parameters:
- `asset_id`: `int | None`, optional, default `None`. SQL: `asset_id = <value>`.
- `serial_number`: `str | None`, optional, default `None`. SQL: `serial_number = <value>`.
- Give at least one of: `asset_id`, `serial_number` (error otherwise).

Extra / aggregate output fields: `replacement_due_date`.

Example: `get_asset(asset_id=7)`

### `find_assets`

Returns: `list[dict]`.

Description: Search assets. All filters optional, combined with AND. name_contains matches part of the asset name, manufacturer or model. due_for_replacement_by returns assets whose useful life ends on or before that date (installation_date + useful_life_years); each result includes replacement_due_date. Use asset_filter_values for valid asset_type and status.

Parameters:
- `property_id`: `int | None`, optional, default `None`. SQL: `property_id = <value>`.
- `building_id`: `int | None`, optional, default `None`. SQL: `building_id = <value>`.
- `space_id`: `int | None`, optional, default `None`. SQL: `space_id = <value>`.
- `asset_type`: `str | None`, optional, default `None`. SQL: `asset_type = <value>`.
- `status`: `str | None`, optional, default `None`. SQL: `status = <value>`.
- `name_contains`: `str | None`, optional, default `None`. SQL: `concat_ws(' ', asset_name, manufacturer, model) ILIKE <value>  (partial, case-insensitive: value is wrapped as %value%)`.
- `installed_from`: `date | None`, optional, default `None`. SQL: `installation_date >= <value>`.
- `installed_to`: `date | None`, optional, default `None`. SQL: `installation_date <= <value>`.
- `due_for_replacement_by`: `date | None`, optional, default `None`. SQL: `(installation_date + useful_life_years * interval '1 year')::date <= <value>`.
- `limit`: `int`, optional, default `50`. Max rows returned; clamped to 1..200.

Extra / aggregate output fields: `replacement_due_date`.
Row order: `replacement_due_date NULLS LAST, asset_id`.

Example: `find_assets(asset_type="<a value from asset_filter_values()>", status="<a value from asset_filter_values()>")`

### `asset_summary`

Returns: `list[dict]`.

Description: Count assets and total replacement cost, grouped by one of: asset_type, status, property_id, building_id.

Parameters:
- `group_by`: `str`, optional, default `'asset_type'`. Allowed values: `"asset_type"`, `"building_id"`, `"property_id"`, `"status"`. Any other value raises an error.
- `property_id`: `int | None`, optional, default `None`. SQL: `property_id = <value>`.
- `status`: `str | None`, optional, default `None`. SQL: `status = <value>`.

Extra / aggregate output fields: `assets`, `total_replacement_cost`.
Row order: `assets DESC`.

Example: `asset_summary(status="<a value from asset_filter_values()>", property_id=7, group_by="status")`

### `asset_filter_values`

Returns: `dict`.

Description: List distinct asset_type and status values in use, for find_assets.

Parameters:
- (none)

Example: `asset_filter_values()`

## Table `smartreit.building` (module `tools/building.py`)

Columns returned by this table's tools: `building_id`, `property_id`, `building_code`, `building_name`, `building_sf`, `floor_count`, `year_built`, `construction_type`, `address_id`, `status`.
Links to other tables: `property_id` -> get_property; `address_id` -> get_address.

### `get_building`

Returns: `dict | None`.

Description: Get one building by building_id or building_code (give one). Returns null if not found. To search by name, use find_buildings.

Parameters:
- `building_id`: `int | None`, optional, default `None`. SQL: `building_id = <value>`.
- `building_code`: `str | None`, optional, default `None`. SQL: `building_code = <value>`.
- Give at least one of: `building_id`, `building_code` (error otherwise).

Example: `get_building(building_id=7)`

### `find_buildings`

Returns: `list[dict]`.

Description: Search buildings. All filters optional, combined with AND. name_contains matches part of the building name or code (case-insensitive). built_after/built_before are years. Use building_filter_values for valid construction_type and status values.

Parameters:
- `property_id`: `int | None`, optional, default `None`. SQL: `property_id = <value>`.
- `name_contains`: `str | None`, optional, default `None`. SQL: `concat_ws(' ', building_name, building_code) ILIKE <value>  (partial, case-insensitive: value is wrapped as %value%)`.
- `construction_type`: `str | None`, optional, default `None`. SQL: `construction_type = <value>`.
- `status`: `str | None`, optional, default `None`. SQL: `status = <value>`.
- `min_building_sf`: `float | None`, optional, default `None`. SQL: `building_sf >= <value>`.
- `max_building_sf`: `float | None`, optional, default `None`. SQL: `building_sf <= <value>`.
- `built_after`: `int | None`, optional, default `None`. SQL: `year_built >= <value>`.
- `built_before`: `int | None`, optional, default `None`. SQL: `year_built <= <value>`.
- `limit`: `int`, optional, default `50`. Max rows returned; clamped to 1..200.
Row order: `property_id, building_name`.

Example: `find_buildings(name_contains="<part of the text>", construction_type="<a value from building_filter_values()>")`

### `building_summary`

Returns: `list[dict]`.

Description: Count buildings, total building SF and total floors, grouped by one of: property_id, construction_type, status.

Parameters:
- `group_by`: `str`, optional, default `'property_id'`. Allowed values: `"construction_type"`, `"property_id"`, `"status"`. Any other value raises an error.
- `property_id`: `int | None`, optional, default `None`. SQL: `property_id = <value>`.
- `status`: `str | None`, optional, default `None`. SQL: `status = <value>`.

Extra / aggregate output fields: `buildings`, `total_building_sf`, `total_floors`.
Row order: `buildings DESC`.

Example: `building_summary(status="<a value from building_filter_values()>", property_id=7, group_by="status")`

### `building_filter_values`

Returns: `dict`.

Description: List distinct construction_type and status values in use, for find_buildings.

Parameters:
- (none)

Example: `building_filter_values()`

## Table `smartreit.department` (module `tools/department.py`)

Columns returned by this table's tools: `department_id`, `department_name`.

### `get_department`

Returns: `dict | None`.

Description: Get a single department by department_id. Returns null if not found.

Parameters:
- `department_id`: `int`, REQUIRED.

Example: `get_department(department_id=7)`

### `find_departments`

Returns: `list[dict]`.

Description: Search departments by part of the name (case-insensitive); call with no filter to list all. Use the department_id with find_employees.

Parameters:
- `name_contains`: `str | None`, optional, default `None`. SQL: `department_name ILIKE <value>  (partial, case-insensitive: value is wrapped as %value%)`.
- `limit`: `int`, optional, default `50`. Max rows returned; clamped to 1..200.
Row order: `department_name`.

Example: `find_departments(name_contains="<part of the text>")`

## Table `smartreit.employee` (module `tools/employee.py`)

Columns returned by this table's tools: `employee_id`, `party_id`, `employee_number`, `department_id`, `manager_employee_id`, `job_title`, `hire_date`, `termination_date`, `employment_status`, `work_location_property_id`, `base_salary`, `pay_frequency`.
Links to other tables: `party_id` -> get_party; `department_id` -> get_department; `work_location_property_id` -> get_property.

### `get_employee`

Returns: `dict | None`.

Description: Get one employee by employee_id or employee_number (give one). Returns null if not found. Names are on the party record (get_party_individual).

Parameters:
- `employee_id`: `int | None`, optional, default `None`. SQL: `employee_id = <value>`.
- `employee_number`: `str | None`, optional, default `None`. SQL: `employee_number = <value>`.
- Give at least one of: `employee_id`, `employee_number` (error otherwise).

Example: `get_employee(employee_id=7)`

### `find_employees`

Returns: `list[dict]`.

Description: Search employees. All filters optional, combined with AND. current=true means no termination_date; false means terminated. job_title_contains matches part of the title, e.g. 'manager'. Use employee_filter_values for valid employment_status and job_title values.

Parameters:
- `party_id`: `int | None`, optional, default `None`. SQL: `party_id = <value>`.
- `department_id`: `int | None`, optional, default `None`. SQL: `department_id = <value>`.
- `manager_employee_id`: `int | None`, optional, default `None`. SQL: `manager_employee_id = <value>`.
- `work_location_property_id`: `int | None`, optional, default `None`. SQL: `work_location_property_id = <value>`.
- `employment_status`: `str | None`, optional, default `None`. SQL: `employment_status = <value>`.
- `job_title_contains`: `str | None`, optional, default `None`. SQL: `job_title ILIKE <value>  (partial, case-insensitive: value is wrapped as %value%)`.
- `current`: `bool | None`, optional, default `None`. SQL: `true -> termination_date IS NULL; false -> termination_date IS NOT NULL`.
- `hired_from`: `date | None`, optional, default `None`. SQL: `hire_date >= <value>`.
- `hired_to`: `date | None`, optional, default `None`. SQL: `hire_date <= <value>`.
- `limit`: `int`, optional, default `50`. Max rows returned; clamped to 1..200.
Row order: `employee_id`.

Example: `find_employees(employment_status="<a value from employee_filter_values()>", job_title_contains="<part of the text>")`

### `get_employee_team`

Returns: `dict`.

Description: Get an employee's manager (if any) and their direct reports.

Parameters:
- `employee_id`: `int`, REQUIRED.
Row order: `employee_id`.

Example: `get_employee_team(employee_id=7)`

### `employee_summary`

Returns: `list[dict]`.

Description: Headcount grouped by one of: department_id, employment_status, job_title, work_location_property_id. Defaults to current employees only; pass current=null to include terminated staff.

Parameters:
- `group_by`: `str`, optional, default `'department_id'`. Allowed values: `"department_id"`, `"employment_status"`, `"job_title"`, `"work_location_property_id"`. Any other value raises an error.
- `current`: `bool | None`, optional, default `True`. SQL: `true -> termination_date IS NULL; false -> termination_date IS NOT NULL`.

Extra / aggregate output fields: `employees`.
Row order: `employees DESC`.

Example: `employee_summary(current=true, group_by="work_location_property_id")`

### `employee_filter_values`

Returns: `dict`.

Description: List distinct employment_status, job_title and pay_frequency values in use.

Parameters:
- (none)

Example: `employee_filter_values()`

## Table `smartreit.floor` (module `tools/floor.py`)

Columns returned by this table's tools: `floor_id`, `building_id`, `floor_number`, `floor_label`, `rentable_sf`, `usable_sf`.
Links to other tables: `building_id` -> get_building.

### `get_floor`

Returns: `dict | None`.

Description: Get a single floor by floor_id. Returns null if not found.

Parameters:
- `floor_id`: `int`, REQUIRED.

Example: `get_floor(floor_id=7)`

### `find_floors`

Returns: `list[dict]`.

Description: Search floors. All filters optional, combined with AND. label_contains matches part of floor_label, e.g. 'mezz' or 'lobby'. Sizes are in square feet. Ordered by building, then floor number.

Parameters:
- `building_id`: `int | None`, optional, default `None`. SQL: `building_id = <value>`.
- `floor_number`: `int | None`, optional, default `None`. SQL: `floor_number = <value>`.
- `label_contains`: `str | None`, optional, default `None`. SQL: `floor_label ILIKE <value>  (partial, case-insensitive: value is wrapped as %value%)`.
- `min_rentable_sf`: `float | None`, optional, default `None`. SQL: `rentable_sf >= <value>`.
- `max_rentable_sf`: `float | None`, optional, default `None`. SQL: `rentable_sf <= <value>`.
- `limit`: `int`, optional, default `50`. Max rows returned; clamped to 1..200.
Row order: `building_id, floor_number`.

Example: `find_floors(floor_number=7, label_contains="<part of the text>")`

### `floor_summary`

Returns: `list[dict]`.

Description: Count floors and total rentable/usable SF per building.

Parameters:
- `building_id`: `int | None`, optional, default `None`. SQL: `building_id = <value>`.

Extra / aggregate output fields: `floors`, `total_rentable_sf`, `total_usable_sf`.
Row order: `building_id`.

Example: `floor_summary(building_id=7)`

## Table `smartreit.lease` (module `tools/lease.py`)

Columns returned by this table's tools: `lease_id`, `lease_number`, `property_id`, `tenant_id`, `lease_type`, `commencement_date`, `expiration_date`, `execution_date`, `possession_date`, `rent_commencement_date`, `status`, `original_term_months`, `security_deposit`, `currency_code`.
Never available (not selected): `created_at`, `updated_at`.
Links to other tables: `property_id` -> get_property; `tenant_id` -> get_tenant.

### `get_lease`

Returns: `dict | None`.

Description: Get one lease by lease_id or lease_number (give one), including its free-text lease_terms_notes. Returns null if not found. Related: find_lease_spaces, find_lease_rent_schedules, find_lease_parties.

Parameters:
- `lease_id`: `int | None`, optional, default `None`. SQL: `lease_id = <value>`.
- `lease_number`: `str | None`, optional, default `None`. SQL: `lease_number = <value>`.
- Give at least one of: `lease_id`, `lease_number` (error otherwise).

Extra / aggregate output fields: `lease_terms_notes`.

Example: `get_lease(lease_id=7)`

### `find_leases`

Returns: `list[dict]`.

Description: Search leases. All filters optional, combined with AND. active_on returns leases in force on that date (commenced on or before it and not yet expired). expiring_from/expiring_to filter on expiration_date, e.g. for upcoming renewals. Ordered by expiration date, soonest first. Use lease_filter_values for valid lease_type, status and currency_code values.

Parameters:
- `property_id`: `int | None`, optional, default `None`. SQL: `property_id = <value>`.
- `tenant_id`: `int | None`, optional, default `None`. SQL: `tenant_id = <value>`.
- `lease_type`: `str | None`, optional, default `None`. SQL: `lease_type = <value>`.
- `status`: `str | None`, optional, default `None`. SQL: `status = <value>`.
- `currency_code`: `str | None`, optional, default `None`. SQL: `currency_code = <value>`.
- `active_on`: `date | None`, optional, default `None`. SQL: `commencement_date <= <value>` AND `(expiration_date IS NULL OR expiration_date >= <value>)`.
- `expiring_from`: `date | None`, optional, default `None`. SQL: `expiration_date >= <value>`.
- `expiring_to`: `date | None`, optional, default `None`. SQL: `expiration_date <= <value>`.
- `commenced_from`: `date | None`, optional, default `None`. SQL: `commencement_date >= <value>`.
- `commenced_to`: `date | None`, optional, default `None`. SQL: `commencement_date <= <value>`.
- `limit`: `int`, optional, default `50`. Max rows returned; clamped to 1..200.
Row order: `expiration_date NULLS LAST, lease_id`.

Example: `find_leases(lease_type="<a value from lease_filter_values()>", status="<a value from lease_filter_values()>")`

### `lease_summary`

Returns: `list[dict]`.

Description: Count leases, total security deposits and average original term (months), grouped by one of: status, lease_type, property_id, tenant_id. Pass active_on (e.g. today) to count only leases in force on that date.

Parameters:
- `group_by`: `str`, optional, default `'status'`. Allowed values: `"lease_type"`, `"property_id"`, `"status"`, `"tenant_id"`. Any other value raises an error.
- `property_id`: `int | None`, optional, default `None`. SQL: `property_id = <value>`.
- `active_on`: `date | None`, optional, default `None`. SQL: `commencement_date <= <value>` AND `(expiration_date IS NULL OR expiration_date >= <value>)`.

Extra / aggregate output fields: `avg_term_months`, `leases`, `total_security_deposit`.
Row order: `leases DESC`.

Example: `lease_summary(active_on="<today>", property_id=7, group_by="tenant_id")`

### `lease_filter_values`

Returns: `dict`.

Description: List distinct lease_type, status and currency_code values in use, for find_leases.

Parameters:
- (none)

Example: `lease_filter_values()`

## Table `smartreit.lease_party` (module `tools/lease_party.py`)

Columns returned by this table's tools: `lease_party_id`, `lease_id`, `party_id`, `role`.
Links to other tables: `lease_id` -> get_lease; `party_id` -> get_party.

### `get_lease_party`

Returns: `dict | None`.

Description: Get a single lease-party link by lease_party_id. Returns null if not found.

Parameters:
- `lease_party_id`: `int`, REQUIRED.

Example: `get_lease_party(lease_party_id=7)`

### `find_lease_parties`

Returns: `list[dict]`.

Description: Search lease-party links. All filters optional, combined with AND. Pass lease_id to see everyone on a lease, or party_id to find every lease a person/company is on. Use get_party for names. Use lease_party_filter_values for valid role values.

Parameters:
- `lease_id`: `int | None`, optional, default `None`. SQL: `lease_id = <value>`.
- `party_id`: `int | None`, optional, default `None`. SQL: `party_id = <value>`.
- `role`: `str | None`, optional, default `None`. SQL: `role = <value>`.
- `limit`: `int`, optional, default `50`. Max rows returned; clamped to 1..200.
Row order: `lease_id, role`.

Example: `find_lease_parties(role="<a value from lease_party_filter_values()>", lease_id=7)`

### `lease_party_summary`

Returns: `list[dict]`.

Description: Count lease-party links grouped by role or party_id.

Parameters:
- `group_by`: `str`, optional, default `'role'`. Allowed values: `"party_id"`, `"role"`. Any other value raises an error.
- `lease_id`: `int | None`, optional, default `None`. SQL: `lease_id = <value>`.

Extra / aggregate output fields: `lease_parties`.
Row order: `lease_parties DESC`.

Example: `lease_party_summary(lease_id=7, group_by="role")`

### `lease_party_filter_values`

Returns: `dict`.

Description: List distinct role values in use, for find_lease_parties.

Parameters:
- (none)

Example: `lease_party_filter_values()`

## Table `smartreit.lease_rent_schedule` (module `tools/lease_rent_schedule.py`)

Columns returned by this table's tools: `rent_schedule_id`, `lease_id`, `charge_type`, `start_date`, `end_date`, `amount`, `amount_frequency`, `rate_per_sf`, `escalation_type`, `escalation_percentage`.
Links to other tables: `lease_id` -> get_lease.

### `get_lease_rent_schedule`

Returns: `dict | None`.

Description: Get a single rent schedule line by rent_schedule_id. Returns null if not found.

Parameters:
- `rent_schedule_id`: `int`, REQUIRED.

Example: `get_lease_rent_schedule(rent_schedule_id=7)`

### `find_lease_rent_schedules`

Returns: `list[dict]`.

Description: Search rent schedule lines. All filters optional, combined with AND. active_on returns lines in effect on that date, e.g. a lease's current rent. amount is per amount_frequency (check it before comparing amounts). Use lease_rent_schedule_filter_values for valid charge_type, amount_frequency and escalation_type values.

Parameters:
- `lease_id`: `int | None`, optional, default `None`. SQL: `lease_id = <value>`.
- `charge_type`: `str | None`, optional, default `None`. SQL: `charge_type = <value>`.
- `amount_frequency`: `str | None`, optional, default `None`. SQL: `amount_frequency = <value>`.
- `escalation_type`: `str | None`, optional, default `None`. SQL: `escalation_type = <value>`.
- `active_on`: `date | None`, optional, default `None`. SQL: `start_date <= <value>` AND `(end_date IS NULL OR end_date >= <value>)`.
- `starting_from`: `date | None`, optional, default `None`. SQL: `start_date >= <value>`.
- `starting_to`: `date | None`, optional, default `None`. SQL: `start_date <= <value>`.
- `min_amount`: `float | None`, optional, default `None`. SQL: `amount >= <value>`.
- `max_amount`: `float | None`, optional, default `None`. SQL: `amount <= <value>`.
- `limit`: `int`, optional, default `50`. Max rows returned; clamped to 1..200.
Row order: `lease_id, start_date, rent_schedule_id`.

Example: `find_lease_rent_schedules(charge_type="<a value from lease_rent_schedule_filter_values()>", amount_frequency="<a value from lease_rent_schedule_filter_values()>")`

### `lease_rent_schedule_summary`

Returns: `list[dict]`.

Description: Count schedule lines, total amount and average rate per SF, grouped by one of: charge_type, amount_frequency, escalation_type, lease_id. Amounts are only comparable within one amount_frequency, so filter on it (or group by it) before reading total_amount.

Parameters:
- `group_by`: `str`, optional, default `'charge_type'`. Allowed values: `"amount_frequency"`, `"charge_type"`, `"escalation_type"`, `"lease_id"`. Any other value raises an error.
- `lease_id`: `int | None`, optional, default `None`. SQL: `lease_id = <value>`.
- `amount_frequency`: `str | None`, optional, default `None`. SQL: `amount_frequency = <value>`.
- `active_on`: `date | None`, optional, default `None`. SQL: `start_date <= <value>` AND `(end_date IS NULL OR end_date >= <value>)`.

Extra / aggregate output fields: `avg_rate_per_sf`, `schedule_lines`, `total_amount`.
Row order: `<group_by>`.

Example: `lease_rent_schedule_summary(amount_frequency="<a value from lease_rent_schedule_filter_values()>", active_on="<today>", group_by="lease_id")`

### `lease_rent_schedule_filter_values`

Returns: `dict`.

Description: List distinct charge_type, amount_frequency and escalation_type values in use.

Parameters:
- (none)

Example: `lease_rent_schedule_filter_values()`

## Table `smartreit.lease_space` (module `tools/lease_space.py`)

Columns returned by this table's tools: `lease_space_id`, `lease_id`, `space_id`, `leased_sf`, `is_primary`.
Links to other tables: `lease_id` -> get_lease; `space_id` -> get_space.

### `get_lease_space`

Returns: `dict | None`.

Description: Get a single lease-space link by lease_space_id. Returns null if not found.

Parameters:
- `lease_space_id`: `int`, REQUIRED.

Example: `get_lease_space(lease_space_id=7)`

### `find_lease_spaces`

Returns: `list[dict]`.

Description: Search lease-space links. All filters optional, combined with AND. Pass lease_id to list the spaces a lease covers, or space_id to find the leases on a space. is_primary marks a lease's main space.

Parameters:
- `lease_id`: `int | None`, optional, default `None`. SQL: `lease_id = <value>`.
- `space_id`: `int | None`, optional, default `None`. SQL: `space_id = <value>`.
- `is_primary`: `bool | None`, optional, default `None`. SQL: `is_primary = <value>`.
- `min_leased_sf`: `float | None`, optional, default `None`. SQL: `leased_sf >= <value>`.
- `max_leased_sf`: `float | None`, optional, default `None`. SQL: `leased_sf <= <value>`.
- `limit`: `int`, optional, default `50`. Max rows returned; clamped to 1..200.
Row order: `lease_id, is_primary DESC, space_id`.

Example: `find_lease_spaces(is_primary=true, min_leased_sf=1000.0)`

### `lease_space_summary`

Returns: `list[dict]`.

Description: Count spaces and total leased SF, grouped by lease_id or space_id.

Parameters:
- `group_by`: `str`, optional, default `'lease_id'`. Allowed values: `"lease_id"`, `"space_id"`. Any other value raises an error.
- `lease_id`: `int | None`, optional, default `None`. SQL: `lease_id = <value>`.
- `space_id`: `int | None`, optional, default `None`. SQL: `space_id = <value>`.

Extra / aggregate output fields: `spaces`, `total_leased_sf`.
Row order: `total_leased_sf DESC NULLS LAST`.

Example: `lease_space_summary(lease_id=7, space_id=7, group_by="space_id")`

## Table `smartreit.management_agreement` (module `tools/management_agreement.py`)

Columns returned by this table's tools: `agreement_id`, `property_id`, `manager_party_id`, `start_date`, `end_date`, `fee_percentage`, `monthly_fee`, `status`.
Links to other tables: `property_id` -> get_property; `manager_party_id` -> get_party.

### `get_management_agreement`

Returns: `dict | None`.

Description: Get a single management agreement by agreement_id. Returns null if not found.

Parameters:
- `agreement_id`: `int`, REQUIRED.

Example: `get_management_agreement(agreement_id=7)`

### `find_management_agreements`

Returns: `list[dict]`.

Description: Search management agreements. All filters optional, combined with AND. active_on returns agreements in force on that date (started on or before it, and no end_date or ending on or after it); e.g. pass today with property_id to find a property's current manager. ending_from/ending_to filter on end_date, for upcoming renewals. manager_party_id links to get_party / get_organization for the manager's name. Use management_agreement_filter_values for valid statuses. Newest first.

Parameters:
- `property_id`: `int | None`, optional, default `None`. SQL: `property_id = <value>`.
- `manager_party_id`: `int | None`, optional, default `None`. SQL: `manager_party_id = <value>`.
- `status`: `str | None`, optional, default `None`. SQL: `status = <value>`.
- `active_on`: `date | None`, optional, default `None`. SQL: `start_date <= <value>` AND `(end_date IS NULL OR end_date >= <value>)`.
- `ending_from`: `date | None`, optional, default `None`. SQL: `end_date >= <value>`.
- `ending_to`: `date | None`, optional, default `None`. SQL: `end_date <= <value>`.
- `min_fee_percentage`: `float | None`, optional, default `None`. SQL: `fee_percentage >= <value>`.
- `max_fee_percentage`: `float | None`, optional, default `None`. SQL: `fee_percentage <= <value>`.
- `limit`: `int`, optional, default `50`. Max rows returned; clamped to 1..200.
Row order: `start_date DESC NULLS LAST, agreement_id DESC`.

Example: `find_management_agreements(status="<a value from management_agreement_filter_values()>", active_on="<today>")`

### `management_agreement_summary`

Returns: `list[dict]`.

Description: Count agreements, total monthly fees and average fee percentage, grouped by one of: manager_party_id, status, property_id. Pass active_on (e.g. today) to count only agreements in force on that date.

Parameters:
- `group_by`: `str`, optional, default `'manager_party_id'`. Allowed values: `"manager_party_id"`, `"property_id"`, `"status"`. Any other value raises an error.
- `status`: `str | None`, optional, default `None`. SQL: `status = <value>`.
- `active_on`: `date | None`, optional, default `None`. SQL: `start_date <= <value>` AND `(end_date IS NULL OR end_date >= <value>)`.

Extra / aggregate output fields: `agreements`, `avg_fee_percentage`, `total_monthly_fee`.
Row order: `agreements DESC`.

Example: `management_agreement_summary(status="<a value from management_agreement_filter_values()>", active_on="<today>", group_by="status")`

### `management_agreement_filter_values`

Returns: `dict`.

Description: List distinct status values in use, for find_management_agreements.

Parameters:
- (none)

Example: `management_agreement_filter_values()`

## Table `smartreit.organization` (module `tools/organization.py`)

Columns returned by this table's tools: `party_id`, `legal_name`, `dba_date`, `tax_id`, `entity_type`, `industry_code`, `website`, `incorporation_state`, `parent_organization_id`.
Links to other tables: `parent_organization_id` -> get_organization (party_id of the parent company).

### `get_organization`

Returns: `dict | None`.

Description: Get the company details of a party that is an organization, by party_id. Returns null if not found (e.g. the party is an individual).

Parameters:
- `party_id`: `int`, REQUIRED.

Example: `get_organization(party_id=7)`

### `find_organizations`

Returns: `list[dict]`.

Description: Search organizations. All filters optional, combined with AND. name_contains matches part of the legal name (case-insensitive), e.g. 'acme' finds 'Acme Holdings LLC'. Returns party_id, which links to find_tenants(party_id=...) and find_vendors(party_id=...). Use organization_filter_values for valid entity_type, industry_code and incorporation_state values.

Parameters:
- `name_contains`: `str | None`, optional, default `None`. SQL: `legal_name ILIKE <value>  (partial, case-insensitive: value is wrapped as %value%)`.
- `website_contains`: `str | None`, optional, default `None`. SQL: `website ILIKE <value>  (partial, case-insensitive: value is wrapped as %value%)`.
- `entity_type`: `str | None`, optional, default `None`. SQL: `entity_type = <value>`.
- `industry_code`: `str | None`, optional, default `None`. SQL: `industry_code = <value>`.
- `incorporation_state`: `str | None`, optional, default `None`. SQL: `incorporation_state = <value>`.
- `parent_organization_id`: `int | None`, optional, default `None`. SQL: `parent_organization_id = <value>`.
- `dba_from`: `date | None`, optional, default `None`. SQL: `dba_date >= <value>`.
- `dba_to`: `date | None`, optional, default `None`. SQL: `dba_date <= <value>`.
- `limit`: `int`, optional, default `50`. Max rows returned; clamped to 1..200.
Row order: `legal_name, party_id`.

Example: `find_organizations(name_contains="<part of the text>", website_contains="<part of the text>")`

### `get_organization_family`

Returns: `dict`.

Description: Get an organization's parent company (if any) and its direct subsidiaries.

Parameters:
- `party_id`: `int`, REQUIRED.
Row order: `legal_name`.

Example: `get_organization_family(party_id=7)`

### `organization_summary`

Returns: `list[dict]`.

Description: Count organizations grouped by one of: entity_type, industry_code, incorporation_state.

Parameters:
- `group_by`: `str`, optional, default `'entity_type'`. Allowed values: `"entity_type"`, `"incorporation_state"`, `"industry_code"`. Any other value raises an error.

Extra / aggregate output fields: `organizations`.
Row order: `organizations DESC`.

Example: `organization_summary(group_by="industry_code")`

### `organization_filter_values`

Returns: `dict`.

Description: List distinct entity_type, industry_code and incorporation_state values in use, for find_organizations.

Parameters:
- (none)

Example: `organization_filter_values()`

## Table `smartreit.ownership_entity` (module `tools/ownership_entity.py`)

Columns returned by this table's tools: `ownership_entity_id`, `owner_id`, `owned_entity_id`, `effective_date`, `end_date`.

### `get_ownership_entity`

Returns: `dict | None`.

Description: Get the details of an ownership entity by ownership_entity_id. Returns null if not found.

Parameters:
- `ownership_entity_id`: `int`, REQUIRED.

Example: `get_ownership_entity(ownership_entity_id=7)`

### `find_ownership_entities`

Returns: `list[dict]`.

Description: Search ownership entities. All filters optional, combined with AND.

Parameters:
- `owner_id`: `int | None`, optional, default `None`. SQL: `owner_id = <value>`.
- `owned_entity_id`: `int | None`, optional, default `None`. SQL: `owned_entity_id = <value>`.
- `effective_date`: `date | None`, optional, default `None`. SQL: `effective_date >= <value>`.
- `end_date`: `date | None`, optional, default `None`. SQL: `end_date <= <value>`.
- `limit`: `int`, optional, default `50`. Max rows returned; clamped to 1..200.
Row order: `effective_date, end_date, ownership_entity_id`.

Example: `find_ownership_entities(effective_date="2026-01-31", end_date="2026-01-31")`

## Table `smartreit.party` (module `tools/party.py`)

Columns returned by this table's tools: `party_id`, `party_code`, `display_name`, `primary_email`, `primary_phone`, `mailing_address_id`, `status`.
Links to other tables: `mailing_address_id` -> get_address.

### `get_party`

Returns: `dict | None`.

Description: Get one party by party_id or party_code (give one). Returns null if not found. To search by name, email or phone, use find_parties.

Parameters:
- `party_id`: `int | None`, optional, default `None`. SQL: `party_id = <value>`.
- `party_code`: `str | None`, optional, default `None`. SQL: `party_code = <value>`.
- Give at least one of: `party_id`, `party_code` (error otherwise).

Example: `get_party(party_id=7)`

### `find_parties`

Returns: `list[dict]`.

Description: Search parties. All filters optional, combined with AND. name_contains matches part of the display name or party code (case-insensitive), e.g. 'acme' finds 'Acme Corp'. Use this to turn a tenant or vendor name into a party_id, then call find_tenants(party_id=...) or find_vendors(party_id=...). Use party_filter_values for valid statuses.

Parameters:
- `name_contains`: `str | None`, optional, default `None`. SQL: `concat_ws(' ', display_name, party_code) ILIKE <value>  (partial, case-insensitive: value is wrapped as %value%)`.
- `email_contains`: `str | None`, optional, default `None`. SQL: `primary_email ILIKE <value>  (partial, case-insensitive: value is wrapped as %value%)`.
- `phone_contains`: `str | None`, optional, default `None`. SQL: `primary_phone ILIKE <value>  (partial, case-insensitive: value is wrapped as %value%)`.
- `mailing_address_id`: `int | None`, optional, default `None`. SQL: `mailing_address_id = <value>`.
- `status`: `str | None`, optional, default `None`. SQL: `status = <value>`.
- `limit`: `int`, optional, default `50`. Max rows returned; clamped to 1..200.
Row order: `display_name`.

Example: `find_parties(name_contains="<part of the text>", email_contains="<part of the text>")`

### `party_filter_values`

Returns: `dict`.

Description: List distinct status values in use, for find_parties.

Parameters:
- (none)

Example: `party_filter_values()`

## Table `smartreit.party_individual` (module `tools/party_individual.py`)

Columns returned by this table's tools: `party_id`, `first_name`, `middle_name`, `last_name`, `email`, `phone`, `home_address_id`, `annual_income`.
Never available (not selected): `ssn`, `drivers_license_no`, `date_of_birth`.
Links to other tables: `home_address_id` -> get_address.

### `get_party_individual`

Returns: `dict | None`.

Description: Get the personal details of a party that is an individual, by party_id. Returns null if not found (e.g. the party is a company).

Parameters:
- `party_id`: `int`, REQUIRED.

Example: `get_party_individual(party_id=7)`

### `find_party_individuals`

Returns: `list[dict]`.

Description: Search individuals. All filters optional, combined with AND. first_name/last_name are exact, case-insensitive matches. name_contains matches part of the full name, e.g. 'jane sm' finds 'Jane Smith'. Returns party_id, which links to find_tenants(party_id=...) and get_party.

Parameters:
- `first_name`: `str | None`, optional, default `None`. SQL: `lower(first_name) = lower(<value>)`.
- `last_name`: `str | None`, optional, default `None`. SQL: `lower(last_name) = lower(<value>)`.
- `name_contains`: `str | None`, optional, default `None`. SQL: `concat_ws(' ', first_name, middle_name, last_name) ILIKE <value>  (partial, case-insensitive: value is wrapped as %value%)`.
- `email_contains`: `str | None`, optional, default `None`. SQL: `email ILIKE <value>  (partial, case-insensitive: value is wrapped as %value%)`.
- `phone_contains`: `str | None`, optional, default `None`. SQL: `phone ILIKE <value>  (partial, case-insensitive: value is wrapped as %value%)`.
- `home_address_id`: `int | None`, optional, default `None`. SQL: `home_address_id = <value>`.
- `min_annual_income`: `float | None`, optional, default `None`. SQL: `annual_income >= <value>`.
- `max_annual_income`: `float | None`, optional, default `None`. SQL: `annual_income <= <value>`.
- `limit`: `int`, optional, default `50`. Max rows returned; clamped to 1..200.
Row order: `last_name, first_name, party_id`.

Example: `find_party_individuals(first_name="text", last_name="text")`

## Table `smartreit.party_role` (module `tools/party_role.py`)

Columns returned by this table's tools: `party_id`, `party_role_id`, `party_role`, `effective_date`, `end_date`.

### `get_party_role`

Returns: `dict | None`.

Description: Get the details of a party role by party_role_id. Returns null if not found.

Parameters:
- `party_role_id`: `int`, REQUIRED.

Example: `get_party_role(party_role_id=7)`

### `find_party_roles`

Returns: `list[dict]`.

Description: Search party roles. All filters optional, combined with AND.

Parameters:
- `party_id`: `int | None`, optional, default `None`. SQL: `party_id = <value>`.
- `party_role`: `str | None`, optional, default `None`. SQL: `party_role = <value>`.
- `effective_date`: `str | None`, optional, default `None`. SQL: `effective_date >= <value>`.
- `end_date`: `str | None`, optional, default `None`. SQL: `end_date <= <value>`.
- `limit`: `int`, optional, default `50`. Max rows returned; clamped to 1..200.
Row order: `effective_date, end_date, party_role_id`.

Example: `find_party_roles(party_role="text", effective_date="text")`

## Table `smartreit.property` (module `tools/property.py`)

Columns returned by this table's tools: `property_id`, `property_code`, `property_name`, `property_type`, `subtype`, `ownership_entity_id`, `acquisition_date`, `disposition_date`, `acquisition_price`, `current_status`, `year_built`, `year_renovated`, `total_building_sf`, `total_land_acres`, `address_id`, `latitude`, `longitude`.
Never available (not selected): `created_at`, `updated_at`.
Links to other tables: `ownership_entity_id` -> get_ownership_entity; `address_id` -> get_address.

### `get_property`

Returns: `dict | None`.

Description: Get one property by property_id or property_code (give one). Returns null if not found. To search by name, use find_properties.

Parameters:
- `property_id`: `int | None`, optional, default `None`. SQL: `property_id = <value>`.
- `property_code`: `str | None`, optional, default `None`. SQL: `property_code = <value>`.
- Give at least one of: `property_id`, `property_code` (error otherwise).

Example: `get_property(property_id=7)`

### `find_properties`

Returns: `list[dict]`.

Description: Search properties. All filters optional, combined with AND. name_contains matches part of the property name or code (case-insensitive), e.g. 'maple' finds 'Maple Street Plaza'. Use this to find a property_id from a name. built_after/built_before are years. Use property_filter_values to see valid type, subtype and status values.

Parameters:
- `name_contains`: `str | None`, optional, default `None`. SQL: `concat_ws(' ', property_name, property_code) ILIKE <value>  (partial, case-insensitive: value is wrapped as %value%)`.
- `property_type`: `str | None`, optional, default `None`. SQL: `property_type = <value>`.
- `subtype`: `str | None`, optional, default `None`. SQL: `subtype = <value>`.
- `current_status`: `str | None`, optional, default `None`. SQL: `current_status = <value>`.
- `ownership_entity_id`: `int | None`, optional, default `None`. SQL: `ownership_entity_id = <value>`.
- `acquired_from`: `date | None`, optional, default `None`. SQL: `acquisition_date >= <value>`.
- `acquired_to`: `date | None`, optional, default `None`. SQL: `acquisition_date <= <value>`.
- `min_building_sf`: `float | None`, optional, default `None`. SQL: `total_building_sf >= <value>`.
- `max_building_sf`: `float | None`, optional, default `None`. SQL: `total_building_sf <= <value>`.
- `built_after`: `int | None`, optional, default `None`. SQL: `year_built >= <value>`.
- `built_before`: `int | None`, optional, default `None`. SQL: `year_built <= <value>`.
- `limit`: `int`, optional, default `50`. Max rows returned; clamped to 1..200.
Row order: `property_name`.

Example: `find_properties(name_contains="<part of the text>", property_type="<a value from property_filter_values()>")`

### `find_properties_near`

Returns: `list[dict]`.

Description: Find properties within radius_km of a point, nearest first. Returns each property with distance_km.

Parameters:
- `latitude`: `float`, REQUIRED.
- `longitude`: `float`, REQUIRED.
- `radius_km`: `float`, optional, default `10`.
- `limit`: `int`, optional, default `20`. Max rows returned; clamped to 1..200.

Extra / aggregate output fields: `distance_km`.
Row order: `distance_km`.

Example: `find_properties_near(latitude=49.2827, longitude=-123.1207)`

### `property_summary`

Returns: `list[dict]`.

Description: Portfolio totals grouped by one of: property_type, subtype, current_status, ownership_entity_id. Returns property count, total building SF, total land acres and total acquisition price per group.

Parameters:
- `group_by`: `str`, optional, default `'property_type'`. Allowed values: `"current_status"`, `"ownership_entity_id"`, `"property_type"`, `"subtype"`. Any other value raises an error.
- `current_status`: `str | None`, optional, default `None`. SQL: `current_status = <value>`.

Extra / aggregate output fields: `properties`, `total_acquisition_price`, `total_building_sf`, `total_land_acres`.
Row order: `properties DESC`.

Example: `property_summary(current_status="<a value from property_filter_values()>", group_by="subtype")`

### `property_filter_values`

Returns: `dict`.

Description: List distinct property_type, subtype and current_status values in use, for find_properties.

Parameters:
- (none)

Example: `property_filter_values()`

## Table `smartreit.property_operating_snapshot` (module `tools/property_operating_snapshot.py`)

Columns returned by this table's tools: `snapshot_date`, `property_id`, `occupancy_percentage`, `leased_percentage`, `rentable_sf`, `occupied_sf`, `annualized_rent`, `noi`, `revenue`, `operating_expense`, `capex`, `bad_debt`.
Links to other tables: `property_id` -> get_property.

### `get_property_snapshot`

Returns: `dict | None`.

Description: Get one property's operating snapshot on or before snapshot_date. If snapshot_date is omitted, returns the most recent snapshot. Returns null if not found.

Parameters:
- `property_id`: `int`, REQUIRED. SQL: `property_id = <value>`.
- `snapshot_date`: `date | None`, optional, default `None`. SQL: `snapshot_date <= <value>`.
Row order: `snapshot_date DESC`.

Example: `get_property_snapshot(property_id=7, snapshot_date="2026-01-31")`

### `find_property_snapshots`

Returns: `list[dict]`.

Description: Search property operating snapshots. All filters optional, combined with AND. For one property's history, pass property_id with date_from/date_to. To rank properties, filter to one date and set order_by (snapshot_date, occupancy_percentage, leased_percentage, noi, revenue, annualized_rent, operating_expense, capex, bad_debt).

Parameters:
- `property_id`: `int | None`, optional, default `None`. SQL: `property_id = <value>`.
- `date_from`: `date | None`, optional, default `None`. SQL: `snapshot_date >= <value>`.
- `date_to`: `date | None`, optional, default `None`. SQL: `snapshot_date <= <value>`.
- `min_occupancy_percentage`: `float | None`, optional, default `None`. SQL: `occupancy_percentage >= <value>`.
- `max_occupancy_percentage`: `float | None`, optional, default `None`. SQL: `occupancy_percentage <= <value>`.
- `min_noi`: `float | None`, optional, default `None`. SQL: `noi >= <value>`.
- `max_noi`: `float | None`, optional, default `None`. SQL: `noi <= <value>`.
- `min_bad_debt`: `float | None`, optional, default `None`. SQL: `bad_debt >= <value>`.
- `max_bad_debt`: `float | None`, optional, default `None`. SQL: `bad_debt <= <value>`.
- `order_by`: `str`, optional, default `'snapshot_date'`. Allowed values: `"annualized_rent"`, `"bad_debt"`, `"capex"`, `"leased_percentage"`, `"noi"`, `"occupancy_percentage"`, `"operating_expense"`, `"revenue"`, `"snapshot_date"`. Any other value raises an error.
- `descending`: `bool`, optional, default `True`. SQL: `true -> DESC; false -> ASC`.
- `limit`: `int`, optional, default `50`. Max rows returned; clamped to 1..200.
Row order: `<order_by> <direction> NULLS LAST, property_id`.

Example: `find_property_snapshots(date_from="2026-01-31", date_to="2026-01-31")`

## Table `smartreit.security_deposit` (module `tools/security_deposit.py`)

Columns returned by this table's tools: `deposit_id`, `lease_id`, `tenant_id`, `amount`, `deposit_date`, `interest_rate`, `released_date`, `status`.
Never available (not selected): `account_number`.
Links to other tables: `lease_id` -> get_lease; `tenant_id` -> get_tenant.

### `get_security_deposit`

Returns: `dict | None`.

Description: Get a single security deposit by deposit_id. Returns null if not found.

Parameters:
- `deposit_id`: `int`, REQUIRED.

Example: `get_security_deposit(deposit_id=7)`

### `find_security_deposits`

Returns: `list[dict]`.

Description: Search security deposits. All filters optional, combined with AND. Newest first. released=false means still held (no released_date); true means returned/released. Date ranges are inclusive. Use security_deposit_filter_values for valid statuses.

Parameters:
- `lease_id`: `int | None`, optional, default `None`. SQL: `lease_id = <value>`.
- `tenant_id`: `int | None`, optional, default `None`. SQL: `tenant_id = <value>`.
- `status`: `str | None`, optional, default `None`. SQL: `status = <value>`.
- `released`: `bool | None`, optional, default `None`. SQL: `true -> released_date IS NOT NULL; false -> released_date IS NULL`.
- `deposited_from`: `date | None`, optional, default `None`. SQL: `deposit_date >= <value>`.
- `deposited_to`: `date | None`, optional, default `None`. SQL: `deposit_date <= <value>`.
- `released_from`: `date | None`, optional, default `None`. SQL: `released_date >= <value>`.
- `released_to`: `date | None`, optional, default `None`. SQL: `released_date <= <value>`.
- `min_amount`: `float | None`, optional, default `None`. SQL: `amount >= <value>`.
- `max_amount`: `float | None`, optional, default `None`. SQL: `amount <= <value>`.
- `limit`: `int`, optional, default `50`. Max rows returned; clamped to 1..200.
Row order: `deposit_date DESC NULLS LAST, deposit_id DESC`.

Example: `find_security_deposits(status="<a value from security_deposit_filter_values()>", released=true)`

### `security_deposit_summary`

Returns: `list[dict]`.

Description: Count deposits and total amount, grouped by status or tenant_id. Use released=false for total deposits currently held.

Parameters:
- `group_by`: `str`, optional, default `'status'`. Allowed values: `"status"`, `"tenant_id"`. Any other value raises an error.
- `tenant_id`: `int | None`, optional, default `None`. SQL: `tenant_id = <value>`.
- `lease_id`: `int | None`, optional, default `None`. SQL: `lease_id = <value>`.
- `released`: `bool | None`, optional, default `None`. SQL: `true -> released_date IS NOT NULL; false -> released_date IS NULL`.

Extra / aggregate output fields: `avg_interest_rate`, `deposits`, `total_amount`.
Row order: `total_amount DESC NULLS LAST`.

Example: `security_deposit_summary(released=true, tenant_id=7, group_by="tenant_id")`

### `security_deposit_filter_values`

Returns: `dict`.

Description: List distinct status values in use, for find_security_deposits.

Parameters:
- (none)

Example: `security_deposit_filter_values()`

## Table `smartreit.space` (module `tools/space.py`)

Columns returned by this table's tools: `space_id`, `property_id`, `building_id`, `floor_id`, `space_code`, `space_type`, `rentable_sf`, `usable_sf`, `bedrooms`, `bathrooms`, `current_status`.
Links to other tables: `property_id` -> get_property; `building_id` -> get_building; `floor_id` -> get_floor.

### `get_space`

Returns: `dict | None`.

Description: Get a single space by space_id. Returns null if not found.

Parameters:
- `space_id`: `int`, REQUIRED.

Example: `get_space(space_id=7)`

### `find_spaces`

Returns: `list[dict]`.

Description: Search spaces (units/suites). All filters optional, combined with AND. Use current_status to find vacant/available space. Sizes are in square feet. Use space_filter_values to see valid space_type and current_status values.

Parameters:
- `property_id`: `int | None`, optional, default `None`. SQL: `property_id = <value>`.
- `building_id`: `int | None`, optional, default `None`. SQL: `building_id = <value>`.
- `floor_id`: `int | None`, optional, default `None`. SQL: `floor_id = <value>`.
- `space_code`: `str | None`, optional, default `None`. SQL: `space_code = <value>`.
- `space_type`: `str | None`, optional, default `None`. SQL: `space_type = <value>`.
- `current_status`: `str | None`, optional, default `None`. SQL: `current_status = <value>`.
- `min_rentable_sf`: `float | None`, optional, default `None`. SQL: `rentable_sf >= <value>`.
- `max_rentable_sf`: `float | None`, optional, default `None`. SQL: `rentable_sf <= <value>`.
- `min_bedrooms`: `int | None`, optional, default `None`. SQL: `bedrooms >= <value>`.
- `min_bathrooms`: `float | None`, optional, default `None`. SQL: `bathrooms >= <value>`.
- `limit`: `int`, optional, default `50`. Max rows returned; clamped to 1..200.
Row order: `property_id, building_id, floor_id, space_code`.

Example: `find_spaces(space_code="<a value from space_filter_values()>", space_type="<a value from space_filter_values()>")`

### `space_summary`

Returns: `list[dict]`.

Description: Count spaces and total rentable/usable square feet, grouped by one of: current_status, space_type, property_id, building_id, floor_id. Use for occupancy, vacancy and inventory questions.

Parameters:
- `group_by`: `str`, optional, default `'current_status'`. Allowed values: `"building_id"`, `"current_status"`, `"floor_id"`, `"property_id"`, `"space_type"`. Any other value raises an error.
- `property_id`: `int | None`, optional, default `None`. SQL: `property_id = <value>`.
- `building_id`: `int | None`, optional, default `None`. SQL: `building_id = <value>`.

Extra / aggregate output fields: `pct_of_rentable_sf`, `spaces`, `total_rentable_sf`, `total_usable_sf`.
Row order: `<group_by>`.

Example: `space_summary(property_id=7, building_id=7, group_by="space_type")`

### `space_filter_values`

Returns: `dict`.

Description: List distinct space_type and current_status values in use, for find_spaces.

Parameters:
- (none)

Example: `space_filter_values()`

## Table `smartreit.tenant` (module `tools/tenant.py`)

Columns returned by this table's tools: `tenant_id`, `party_id`, `tenant_type`, `credit_rating`, `industry_code`, `parent_tenant_id`, `status`, `verified_income`, `credit_score`.
Links to other tables: `party_id` -> get_party.

### `get_tenant`

Returns: `dict | None`.

Description: Get a single tenant by tenant_id. Returns null if not found. Tenant names live on the party record (see party_id / find_parties).

Parameters:
- `tenant_id`: `int`, REQUIRED.

Example: `get_tenant(tenant_id=7)`

### `find_tenants`

Returns: `list[dict]`.

Description: Search tenants. All filters are optional and combined with AND; call with no filters to list tenants. Use get_tenant for one tenant by ID. Use tenant_filter_values to see valid status, tenant_type, credit_rating and industry_code values.

Parameters:
- `party_id`: `int | None`, optional, default `None`. SQL: `party_id = <value>`.
- `tenant_type`: `str | None`, optional, default `None`. SQL: `tenant_type = <value>`.
- `credit_rating`: `str | None`, optional, default `None`. SQL: `credit_rating = <value>`.
- `industry_code`: `str | None`, optional, default `None`. SQL: `industry_code = <value>`.
- `parent_tenant_id`: `int | None`, optional, default `None`. SQL: `parent_tenant_id = <value>`.
- `status`: `str | None`, optional, default `None`. SQL: `status = <value>`.
- `min_credit_score`: `int | None`, optional, default `None`. SQL: `credit_score >= <value>`.
- `min_verified_income`: `float | None`, optional, default `None`. SQL: `verified_income >= <value>`.
- `limit`: `int`, optional, default `50`. Max rows returned; clamped to 1..200.
Row order: `tenant_id`.

Example: `find_tenants(tenant_type="<a value from tenant_filter_values()>", credit_rating="<a value from tenant_filter_values()>")`

### `get_tenant_family`

Returns: `dict`.

Description: Get a tenant's parent (if any) and its direct subsidiaries.

Parameters:
- `tenant_id`: `int`, REQUIRED.
Row order: `tenant_id`.

Example: `get_tenant_family(tenant_id=7)`

### `tenant_summary`

Returns: `list[dict]`.

Description: Count tenants with average credit score and verified income, grouped by one of: status, tenant_type, credit_rating, industry_code.

Parameters:
- `group_by`: `str`, optional, default `'status'`. Allowed values: `"credit_rating"`, `"industry_code"`, `"status"`, `"tenant_type"`. Any other value raises an error.
- `status`: `str | None`, optional, default `None`. SQL: `status = <value>`.

Extra / aggregate output fields: `avg_credit_score`, `avg_verified_income`, `tenants`.
Row order: `tenants DESC`.

Example: `tenant_summary(status="<a value from tenant_filter_values()>", group_by="tenant_type")`

### `tenant_filter_values`

Returns: `dict`.

Description: List distinct status, tenant_type, credit_rating and industry_code values in use, to pass as find_tenants filters.

Parameters:
- (none)

Example: `tenant_filter_values()`

## Table `smartreit.tenant_billing` (module `tools/tenant_billing.py`)

Columns returned by this table's tools: `bill_id`, `lease_id`, `tenant_id`, `charge_type`, `billing_date`, `due_date`, `amount`, `tax_amount`, `status`.
Links to other tables: `lease_id` -> get_lease; `tenant_id` -> get_tenant.

### `get_billing`

Returns: `dict | None`.

Description: Get a single bill by bill_id. Returns null if not found.

Parameters:
- `bill_id`: `int`, REQUIRED.

Example: `get_billing(bill_id=7)`

### `find_billing`

Returns: `list[dict]`.

Description: Search bills. All filters optional, combined with AND. Newest bills first. billed_from/billed_to filter on billing_date (inclusive). due_before filters on due_date, e.g. with status to find overdue bills. Use billing_filter_values to see valid charge_type and status values.

Parameters:
- `tenant_id`: `int | None`, optional, default `None`. SQL: `tenant_id = <value>`.
- `lease_id`: `int | None`, optional, default `None`. SQL: `lease_id = <value>`.
- `charge_type`: `str | None`, optional, default `None`. SQL: `charge_type = <value>`.
- `status`: `str | None`, optional, default `None`. SQL: `status = <value>`.
- `billed_from`: `date | None`, optional, default `None`. SQL: `billing_date >= <value>`.
- `billed_to`: `date | None`, optional, default `None`. SQL: `billing_date <= <value>`.
- `due_before`: `date | None`, optional, default `None`. SQL: `due_date < <value>`.
- `limit`: `int`, optional, default `50`. Max rows returned; clamped to 1..200.
Row order: `billing_date DESC, bill_id DESC`.

Example: `find_billing(charge_type="<a value from billing_filter_values()>", status="<a value from billing_filter_values()>")`

### `billing_summary`

Returns: `list[dict]`.

Description: Total amount, tax and bill count, grouped by status or charge_type. Use for balances owed, totals billed, and breakdowns by charge type.

Parameters:
- `group_by`: `str`, optional, default `'status'`. Allowed values: `"charge_type"`, `"status"`. Any other value raises an error.
- `tenant_id`: `int | None`, optional, default `None`. SQL: `tenant_id = <value>`.
- `lease_id`: `int | None`, optional, default `None`. SQL: `lease_id = <value>`.
- `billed_from`: `date | None`, optional, default `None`. SQL: `billing_date >= <value>`.
- `billed_to`: `date | None`, optional, default `None`. SQL: `billing_date <= <value>`.

Extra / aggregate output fields: `bills`, `total_amount`, `total_tax`, `total_with_tax`.
Row order: `<group_by>`.

Example: `billing_summary(billed_from="2026-01-31", billed_to="2026-01-31", group_by="status")`

### `billing_filter_values`

Returns: `dict`.

Description: List distinct charge_type and status values in use, for find_billing.

Parameters:
- (none)

Example: `billing_filter_values()`

## Table `smartreit.tenant_improvement` (module `tools/tenant_improvement.py`)

Columns returned by this table's tools: `ti_id`, `lease_id`, `property_id`, `space_id`, `approved_amount`, `committed_amount`, `actual_amount`, `start_date`, `completion_date`.
Links to other tables: `lease_id` -> get_lease; `property_id` -> get_property; `space_id` -> get_space.

### `get_tenant_improvement`

Returns: `dict | None`.

Description: Get a single tenant improvement by ti_id. Returns null if not found.

Parameters:
- `ti_id`: `int`, REQUIRED.

Example: `get_tenant_improvement(ti_id=7)`

### `find_tenant_improvements`

Returns: `list[dict]`.

Description: Search tenant improvements. All filters optional, combined with AND. in_progress=true means not yet completed (no completion_date); false means completed. over_budget=true returns only TIs whose actual_amount exceeds approved_amount. Newest start date first.

Parameters:
- `lease_id`: `int | None`, optional, default `None`. SQL: `lease_id = <value>`.
- `property_id`: `int | None`, optional, default `None`. SQL: `property_id = <value>`.
- `space_id`: `int | None`, optional, default `None`. SQL: `space_id = <value>`.
- `in_progress`: `bool | None`, optional, default `None`. SQL: `true -> completion_date IS NULL; false -> completion_date IS NOT NULL`.
- `started_from`: `date | None`, optional, default `None`. SQL: `start_date >= <value>`.
- `started_to`: `date | None`, optional, default `None`. SQL: `start_date <= <value>`.
- `completed_from`: `date | None`, optional, default `None`. SQL: `completion_date >= <value>`.
- `completed_to`: `date | None`, optional, default `None`. SQL: `completion_date <= <value>`.
- `min_approved_amount`: `float | None`, optional, default `None`. SQL: `approved_amount >= <value>`.
- `over_budget`: `bool`, optional, default `False`. SQL: `true -> actual_amount > approved_amount; false -> no filter`.
- `limit`: `int`, optional, default `50`. Max rows returned; clamped to 1..200.
Row order: `start_date DESC NULLS LAST, ti_id DESC`.

Example: `find_tenant_improvements(in_progress=true, started_from="2026-01-31")`

### `tenant_improvement_summary`

Returns: `list[dict]`.

Description: Count TIs and total approved, committed and actual amounts, grouped by property_id, lease_id or space_id. remaining_budget = approved - actual. Use in_progress=true to count/total only ongoing TIs.

Parameters:
- `group_by`: `str`, optional, default `'property_id'`. Allowed values: `"lease_id"`, `"property_id"`, `"space_id"`. Any other value raises an error.
- `property_id`: `int | None`, optional, default `None`. SQL: `property_id = <value>`.
- `in_progress`: `bool | None`, optional, default `None`. SQL: `true -> completion_date IS NULL; false -> completion_date IS NOT NULL`.

Extra / aggregate output fields: `remaining_budget`, `tenant_improvements`, `total_actual`, `total_approved`, `total_committed`.
Row order: `<group_by>`.

Example: `tenant_improvement_summary(in_progress=true, property_id=7, group_by="space_id")`

## Table `smartreit.vendor` (module `tools/vendor.py`)

Columns returned by this table's tools: `vendor_id`, `party_id`, `vendor_type`, `tax_id`, `insurance_expiration`, `status`.
Links to other tables: `party_id` -> get_party.

### `get_vendor`

Returns: `dict | None`.

Description: Get a single vendor by vendor_id. Returns null if not found. Vendor names live on the party record (see party_id / find_parties).

Parameters:
- `vendor_id`: `int`, REQUIRED.

Example: `get_vendor(vendor_id=7)`

### `find_vendors`

Returns: `list[dict]`.

Description: Search vendors. All filters optional, combined with AND. Use insurance_expires_before to find vendors whose insurance has lapsed or is about to. Use vendor_filter_values to see valid vendor_type and status values.

Parameters:
- `party_id`: `int | None`, optional, default `None`. SQL: `party_id = <value>`.
- `vendor_type`: `str | None`, optional, default `None`. SQL: `vendor_type = <value>`.
- `status`: `str | None`, optional, default `None`. SQL: `status = <value>`.
- `insurance_expires_before`: `date | None`, optional, default `None`. SQL: `insurance_expiration < <value>`.
- `insurance_expires_after`: `date | None`, optional, default `None`. SQL: `insurance_expiration > <value>`.
- `limit`: `int`, optional, default `50`. Max rows returned; clamped to 1..200.
Row order: `vendor_id`.

Example: `find_vendors(vendor_type="<a value from vendor_filter_values()>", status="<a value from vendor_filter_values()>")`

### `vendor_summary`

Returns: `list[dict]`.

Description: Count vendors grouped by status or vendor_type.

Parameters:
- `group_by`: `str`, optional, default `'status'`. Allowed values: `"status"`, `"vendor_type"`. Any other value raises an error.

Extra / aggregate output fields: `vendors`.
Row order: `vendors DESC`.

Example: `vendor_summary(group_by="vendor_type")`

### `vendor_filter_values`

Returns: `dict`.

Description: List distinct vendor_type and status values in use, for find_vendors.

Parameters:
- (none)

Example: `vendor_filter_values()`

## Table `smartreit.work_order` (module `tools/work_order.py`)

Columns returned by this table's tools: `work_order_id`, `property_id`, `building_id`, `space_id`, `asset_id`, `requested_by_party_id`, `assigned_employee_id`, `vendor_id`, `priority`, `work_type`, `description`, `created_at`, `scheduled_date`, `completed_at`, `status`.
Links to other tables: `property_id` -> get_property; `building_id` -> get_building; `space_id` -> get_space; `asset_id` -> get_asset; `requested_by_party_id` -> get_party; `assigned_employee_id` -> get_employee; `vendor_id` -> get_vendor.

### `get_work_order`

Returns: `dict | None`.

Description: Get a single work order by work_order_id. Returns null if not found.

Parameters:
- `work_order_id`: `int`, REQUIRED.

Example: `get_work_order(work_order_id=7)`

### `find_work_orders`

Returns: `list[dict]`.

Description: Search work orders. All filters optional, combined with AND. Newest first. Date ranges are inclusive. completed=true/false filters on whether completed_at is set. Use work_order_filter_values to see valid priority, work_type and status values.

Parameters:
- `property_id`: `int | None`, optional, default `None`. SQL: `property_id = <value>`.
- `building_id`: `int | None`, optional, default `None`. SQL: `building_id = <value>`.
- `space_id`: `int | None`, optional, default `None`. SQL: `space_id = <value>`.
- `asset_id`: `int | None`, optional, default `None`. SQL: `asset_id = <value>`.
- `vendor_id`: `int | None`, optional, default `None`. SQL: `vendor_id = <value>`.
- `requested_by_party_id`: `int | None`, optional, default `None`. SQL: `requested_by_party_id = <value>`.
- `assigned_employee_id`: `int | None`, optional, default `None`. SQL: `assigned_employee_id = <value>`.
- `priority`: `str | None`, optional, default `None`. SQL: `priority = <value>`.
- `work_type`: `str | None`, optional, default `None`. SQL: `work_type = <value>`.
- `status`: `str | None`, optional, default `None`. SQL: `status = <value>`.
- `created_from`: `date | None`, optional, default `None`. SQL: `created_at >= <value>`.
- `created_to`: `date | None`, optional, default `None`. SQL: `created_at < <value>::date + 1`.
- `scheduled_from`: `date | None`, optional, default `None`. SQL: `scheduled_date >= <value>`.
- `scheduled_to`: `date | None`, optional, default `None`. SQL: `scheduled_date <= <value>`.
- `completed`: `bool | None`, optional, default `None`. SQL: `true -> completed_at IS NOT NULL; false -> completed_at IS NULL`.
- `limit`: `int`, optional, default `50`. Max rows returned; clamped to 1..200.
Row order: `created_at DESC, work_order_id DESC`.

Example: `find_work_orders(priority="<a value from work_order_filter_values()>", work_type="<a value from work_order_filter_values()>")`

### `work_order_summary`

Returns: `list[dict]`.

Description: Count work orders grouped by one of: status, priority, work_type, property_id, vendor_id. Includes how many are still open (no completed_at).

Parameters:
- `group_by`: `str`, optional, default `'status'`. Allowed values: `"priority"`, `"property_id"`, `"status"`, `"vendor_id"`, `"work_type"`. Any other value raises an error.
- `property_id`: `int | None`, optional, default `None`. SQL: `property_id = <value>`.
- `created_from`: `date | None`, optional, default `None`. SQL: `created_at >= <value>`.
- `created_to`: `date | None`, optional, default `None`. SQL: `created_at < <value>::date + 1`.

Extra / aggregate output fields: `open_work_orders`, `work_orders`.
Row order: `work_orders DESC`.

Example: `work_order_summary(created_from="2026-01-31", created_to="2026-01-31", group_by="work_type")`

### `work_order_filter_values`

Returns: `dict`.

Description: List distinct priority, work_type and status values in use, for find_work_orders.

Parameters:
- (none)

Example: `work_order_filter_values()`

