"""Database operations for course catalog records."""

import sqlite3
from typing import Any

from app.database.connection import get_connection
from app.services.department_service import get_department
from app.utils.validators import normalize_bool, parse_integer, require_text


COURSE_SELECT = """
    SELECT c.id, c.course_code, c.course_name, c.theory_hours,
           c.laboratory_hours, c.department_id, c.is_active, c.created_at,
           d.name AS department_name, d.code AS department_code
    FROM courses c
    INNER JOIN departments d ON d.id = c.department_id
"""
VALID_CREDIT_HOURS = {(3, 1), (2, 1), (2, 0), (3, 0)}


def _row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    return dict(row)


def _include_departments(
    connection: sqlite3.Connection,
    rows: list[sqlite3.Row],
) -> list[dict[str, Any]]:
    courses = [_row_to_dict(row) for row in rows]
    if not courses:
        return courses
    placeholders = ", ".join("?" for _ in courses)
    department_rows = connection.execute(
        f"""
        SELECT cd.course_id, d.id, d.name, d.code
        FROM course_departments cd
        INNER JOIN departments d ON d.id = cd.department_id
        WHERE cd.course_id IN ({placeholders})
        ORDER BY d.name, d.id
        """,
        tuple(course["id"] for course in courses),
    ).fetchall()
    departments_by_course: dict[int, list[dict[str, Any]]] = {}
    for row in department_rows:
        departments_by_course.setdefault(row["course_id"], []).append(
            {"id": row["id"], "name": row["name"], "code": row["code"]}
        )
    for course in courses:
        departments = departments_by_course.get(course["id"], [])
        course["departments"] = departments
        course["department_ids"] = [department["id"] for department in departments]
    return courses


def list_courses(
    department_id: int | None = None,
    is_active: bool | None = None,
    search: str | None = None,
    theory_hours: int | None = None,
    laboratory_hours: int | None = None,
) -> list[dict[str, Any]]:
    conditions: list[str] = []
    values: list[Any] = []
    if department_id is not None:
        conditions.append(
            "EXISTS (SELECT 1 FROM course_departments cd "
            "WHERE cd.course_id = c.id AND cd.department_id = ?)"
        )
        values.append(department_id)
    if is_active is not None:
        conditions.append("c.is_active = ?")
        values.append(int(is_active))
    if search:
        conditions.append("(c.course_code LIKE ? OR c.course_name LIKE ?)")
        search_pattern = f"%{search.strip()}%"
        values.extend((search_pattern, search_pattern))
    if theory_hours is not None:
        conditions.append("c.theory_hours = ?")
        values.append(theory_hours)
    if laboratory_hours is not None:
        conditions.append("c.laboratory_hours = ?")
        values.append(laboratory_hours)
    where = f" WHERE {' AND '.join(conditions)}" if conditions else ""
    with get_connection() as connection:
        rows = connection.execute(
            COURSE_SELECT + where + " ORDER BY c.course_code",
            tuple(values),
        ).fetchall()
        return _include_departments(connection, rows)


def get_course(course_id: int) -> dict[str, Any] | None:
    with get_connection() as connection:
        row = connection.execute(
            COURSE_SELECT + " WHERE c.id = ?",
            (course_id,),
        ).fetchone()
        if row is None:
            return None
        return _include_departments(connection, [row])[0]


def _parse_department_ids(
    payload: dict[str, Any],
    current: dict[str, Any] | None = None,
) -> list[int]:
    raw_ids = payload.get("department_ids")
    if raw_ids is None:
        if "department_id" in payload:
            raw_ids = [payload["department_id"]]
        elif current is not None:
            raw_ids = current["department_ids"]
        else:
            raw_ids = []
    if not isinstance(raw_ids, list) or not raw_ids:
        raise ValueError("department_ids must be a non-empty list of department IDs")

    department_ids: list[int] = []
    for value in raw_ids:
        department_id = parse_integer(value, "department_ids")
        if department_id not in department_ids:
            department_ids.append(department_id)
    for department_id in department_ids:
        department = get_department(department_id)
        if department is None or not department["is_active"]:
            raise ValueError(f"Active department {department_id} not found")
    return department_ids


def _validated_course(payload: dict[str, Any], current: dict[str, Any] | None = None) -> dict[str, Any]:
    code = require_text(
        payload.get("course_code", current["course_code"] if current else None),
        "course_code",
    ).upper()
    name = require_text(
        payload.get("course_name", current["course_name"] if current else None),
        "course_name",
    )
    theory = parse_integer(
        payload.get("theory_hours", current["theory_hours"] if current else None),
        "theory_hours",
    )
    laboratory = parse_integer(
        payload.get(
            "laboratory_hours",
            current["laboratory_hours"] if current else None,
        ),
        "laboratory_hours",
    )
    department_ids = _parse_department_ids(payload, current)
    if (theory, laboratory) not in VALID_CREDIT_HOURS:
        raise ValueError("Credit hours must be one of 3+1, 2+1, 2+0, or 3+0")
    is_active = normalize_bool(
        payload.get("is_active", current["is_active"] if current else True)
    )
    return {
        "course_code": code,
        "course_name": name,
        "theory_hours": theory,
        "laboratory_hours": laboratory,
        "department_id": department_ids[0],
        "department_ids": department_ids,
        "is_active": is_active,
    }


def create_course_record(payload: dict[str, Any]) -> dict[str, Any]:
    course = _validated_course(payload)
    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO courses
                (course_code, course_name, theory_hours, laboratory_hours,
                 department_id, is_active)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                course["course_code"],
                course["course_name"],
                course["theory_hours"],
                course["laboratory_hours"],
                course["department_id"],
                course["is_active"],
            ),
        )
        connection.executemany(
            "INSERT INTO course_departments (course_id, department_id) VALUES (?, ?)",
            [(cursor.lastrowid, department_id) for department_id in course["department_ids"]],
        )
        connection.commit()
    record = get_course(cursor.lastrowid)
    if record is None:
        raise RuntimeError("Created course could not be retrieved")
    return record


def update_course_record(course_id: int, payload: dict[str, Any]) -> dict[str, Any]:
    current = get_course(course_id)
    if current is None:
        raise ValueError("Course not found")
    course = _validated_course(payload, current)
    with get_connection() as connection:
        connection.execute(
            """
            UPDATE courses
            SET course_code = ?, course_name = ?, theory_hours = ?,
                laboratory_hours = ?, department_id = ?, is_active = ?
            WHERE id = ?
            """,
            (
                course["course_code"],
                course["course_name"],
                course["theory_hours"],
                course["laboratory_hours"],
                course["department_id"],
                course["is_active"],
                course_id,
            ),
        )
        connection.execute(
            "DELETE FROM course_departments WHERE course_id = ?",
            (course_id,),
        )
        connection.executemany(
            "INSERT INTO course_departments (course_id, department_id) VALUES (?, ?)",
            [(course_id, department_id) for department_id in course["department_ids"]],
        )
        connection.commit()
    record = get_course(course_id)
    if record is None:
        raise RuntimeError("Updated course could not be retrieved")
    return record


def deactivate_course(course_id: int) -> dict[str, Any]:
    if get_course(course_id) is None:
        raise ValueError("Course not found")
    with get_connection() as connection:
        connection.execute("UPDATE courses SET is_active = 0 WHERE id = ?", (course_id,))
        connection.commit()
    record = get_course(course_id)
    if record is None:
        raise RuntimeError("Deactivated course could not be retrieved")
    return record
