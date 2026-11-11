# University Course & Teacher Allocation Management System

FastAPI backend for managing departments, academic terms, sections, designations,
teachers, courses, preferences, offerings, workloads, and course allocations.
Application request bodies are parsed from `Request` as dictionaries; the
database uses Python's built-in `sqlite3` module.

## Project layout

- `app/main.py` creates the FastAPI application and registers route modules.
- `app/database/connection.py` centralizes SQLite connections and additive
  migrations for existing term and allocation records.
- `app/database/schema.sql` defines the relational tables and integrity rules.
- `app/routes/` contains HTTP handlers and request/response validation.
- `app/services/` contains SQL access and business rules.
- `app/utils/` contains JSON request and common input helpers.
- `tests/` contains the existing database foundation tests.

## Setup and start

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
.venv/bin/python -m uvicorn app.main:app --reload
```

By default, the database is `university.db` in the project root. Set
`DATABASE_PATH` to use another SQLite file. The database schema and additive
columns are initialized when the application starts. Swagger UI is available at
<http://127.0.0.1:8000/docs>.

The admin web interface is available at <http://127.0.0.1:8000/>. It includes
screens for departments, academic terms, sections, designations, teachers,
courses, preferences, offerings, workload, allocations, and reports. The course
form supports selecting multiple departments.

## API overview

### Health and foundation

- `GET /health`
- `GET /health/database`

### Departments and sections

- `POST`, `GET /departments`; `GET`, `PUT`, `DELETE /departments/{department_id}`
- `GET /departments/{department_id}/sections`
- `POST`, `GET /sections`; `GET`, `PUT`, `DELETE /sections/{section_id}`
- `DELETE /sections/{section_id}/permanent`

Department deletes and the standard section delete endpoint deactivate records.
The Sections screen also offers permanent deletion, which removes a section and
its offerings, allocations, and allocation history. Sections are unique by
department, academic term, and name.

### Academic terms and designations

- `POST`, `GET /academic-terms`; `GET`, `PUT /academic-terms/{term_id}`
- `PUT /academic-terms/{term_id}/activate`, `PUT /academic-terms/{term_id}/deactivate`
- `POST`, `GET /designations`; `GET`, `PUT`, `DELETE /designations/{designation_id}`

Academic terms are activated and deactivated independently. Sections and course
offerings can be managed for active or inactive terms. Workload and automatic
allocation are scoped to the term selected in the UI. Workload, automatic
allocation, teacher reports, and unallocated-offering reports default to the
most recently created active term when an API caller omits `term_id`.
Department reports and allocation history include all terms when `term_id` is
omitted. Each allocation stores the workload and designation limit snapshots
used at assignment time.

### Teachers and courses

- `POST`, `GET /teachers`; `GET`, `PUT`, `DELETE /teachers/{teacher_id}`
- `GET /teachers/{teacher_id}/allocated-courses`
- `POST`, `GET /courses`; `GET`, `PUT`, `DELETE /courses/{course_id}`

Teacher listing accepts optional `department_id` and `is_active` filters.
Course listing accepts optional `department_id`, `is_active`, `search`,
`theory_hours`, and `laboratory_hours` filters. Course hours must be one of
`3+1`, `2+1`, `2+0`, or `3+0`. Deletes deactivate records.

Courses may belong to multiple departments. Create a course with
`department_ids`; the legacy single `department_id` field remains accepted for
older clients. Course responses include the `departments` array and
`department_ids`. Course offerings are allowed only for sections belonging to a
department associated with that course.

Example course request:

```json
{
  "course_code": "CSC111",
  "course_name": "Object Oriented Programming",
  "theory_hours": 3,
  "laboratory_hours": 1,
  "department_ids": [1, 2]
}
```

### Preferences and offerings

- `POST`, `GET /teachers/{teacher_id}/preferences`
- `GET /courses/{course_id}/interested-teachers`
- `PUT`, `DELETE /preferences/{preference_id}`
- `POST`, `GET /offerings`
- `GET /sections/{section_id}/offerings`
- `GET /departments/{department_id}/offerings`
- `DELETE /offerings/{offering_id}` (pending offerings only)

Example preference request:

```json
{
  "preferences": [
    {"course_id": 1, "priority": 1},
    {"course_id": 2, "priority": 2}
  ]
}
```

Example offering request:

```json
{
  "course_id": 1,
  "section_id": 1
}
```

### Workload and allocations

- `GET /workload?term_id=1`
- `GET /workload/{teacher_id}?term_id=1`
- `GET /workload/limits`
- `GET /workload/department/{department_id}?term_id=1`
- `POST /allocations/auto/preview`
- `POST /allocations/auto/execute`
- `POST /allocations/manual`
- `GET /allocations`
- `PUT /allocations/{allocation_id}` (reassign)
- `DELETE /allocations/{allocation_id}` (remove)
- `GET /allocations/history`

Example manual allocation:

```json
{
  "offering_id": 1,
  "teacher_id": 1,
  "override_preference": false,
  "reason": "Preferred instructor"
}
```

Automatic allocation ranks interested eligible teachers by preference priority,
then current term workload, then teacher name. It excludes any assignment that
would exceed the teacher's maximum workload. Both automatic execution and manual
changes use SQLite transactions and write allocation history. Manual assignments
without a matching preference require `override_preference: true`; this never
bypasses the maximum workload limit.

Workload status is `SAFE` when allocated hours are at or below standard,
`EXTENDED` when above standard but within maximum, and `EXCEEDED` above maximum.
An allocation that would exceed maximum is rejected and therefore cannot be
created through the API.

### Reports

- `GET /reports/teacher/{teacher_id}?term_id=1`
- `GET /reports/department/{department_id}?term_id=1`
- `GET /reports/section/{section_id}`
- `GET /reports/unallocated?term_id=1`
- `GET /reports/history?term_id=1`

The history report preserves assignment, reassignment, and removal events,
including the workload/limit snapshots stored when those changes occurred.
