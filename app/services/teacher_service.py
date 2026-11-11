"""Database operations for teacher profiles."""

import sqlite3
from typing import Any

from app.database.connection import get_connection
from app.services.department_service import get_department
from app.services.designation_service import get_designation
from app.utils.validators import normalize_bool, parse_integer, require_text


TEACHER_SELECT = """
    SELECT t.id, t.full_name, t.employee_code, t.department_id,
           t.designation_id, t.is_active, t.created_at,
           d.name AS department_name, d.code AS department_code,
           g.name AS designation_name
    FROM teachers t
    INNER JOIN departments d ON d.id = t.department_id
    INNER JOIN designations g ON g.id = t.designation_id
"""


def _row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    return dict(row)


def list_teachers(
    department_id: int | None = None,
    is_active: bool | None = None,
) -> list[dict[str, Any]]:
    conditions: list[str] = []
    values: list[Any] = []
    if department_id is not None:
        conditions.append("t.department_id = ?")
        values.append(department_id)
    if is_active is not None:
        conditions.append("t.is_active = ?")
        values.append(int(is_active))
    where = f" WHERE {' AND '.join(conditions)}" if conditions else ""
    with get_connection() as connection:
        rows = connection.execute(
            TEACHER_SELECT + where + " ORDER BY t.full_name, t.id",
            tuple(values),
        ).fetchall()
    return [_row_to_dict(row) for row in rows]


def get_teacher(teacher_id: int) -> dict[str, Any] | None:
    with get_connection() as connection:
        row = connection.execute(
            TEACHER_SELECT + " WHERE t.id = ?",
            (teacher_id,),
        ).fetchone()
    return None if row is None else _row_to_dict(row)


def _validated_profile(payload: dict[str, Any], current: dict[str, Any] | None = None) -> dict[str, Any]:
    full_name = require_text(payload.get("full_name", current["full_name"] if current else None), "full_name")
    employee_code = payload.get("employee_code", current["employee_code"] if current else None)
    if employee_code is not None:
        employee_code = require_text(employee_code, "employee_code").upper()
    department_id = parse_integer(
        payload.get("department_id", current["department_id"] if current else None),
        "department_id",
    )
    designation_id = parse_integer(
        payload.get("designation_id", current["designation_id"] if current else None),
        "designation_id",
    )
    department = get_department(department_id)
    if department is None or not department["is_active"]:
        raise ValueError("Active department not found")
    designation = get_designation(designation_id)
    if designation is None or not designation["is_active"]:
        raise ValueError("Active designation not found")
    is_active = normalize_bool(
        payload.get("is_active", current["is_active"] if current else True)
    )
    return {
        "full_name": full_name,
        "employee_code": employee_code,
        "department_id": department_id,
        "designation_id": designation_id,
        "is_active": is_active,
    }


def create_teacher_record(payload: dict[str, Any]) -> dict[str, Any]:
    profile = _validated_profile(payload)
    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO teachers
                (full_name, employee_code, department_id, designation_id, is_active)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                profile["full_name"],
                profile["employee_code"],
                profile["department_id"],
                profile["designation_id"],
                profile["is_active"],
            ),
        )
        connection.commit()
    teacher = get_teacher(cursor.lastrowid)
    if teacher is None:
        raise RuntimeError("Created teacher could not be retrieved")
    return teacher


def update_teacher_record(teacher_id: int, payload: dict[str, Any]) -> dict[str, Any]:
    current = get_teacher(teacher_id)
    if current is None:
        raise ValueError("Teacher not found")
    profile = _validated_profile(payload, current)
    with get_connection() as connection:
        connection.execute(
            """
            UPDATE teachers
            SET full_name = ?, employee_code = ?, department_id = ?,
                designation_id = ?, is_active = ?
            WHERE id = ?
            """,
            (
                profile["full_name"],
                profile["employee_code"],
                profile["department_id"],
                profile["designation_id"],
                profile["is_active"],
                teacher_id,
            ),
        )
        connection.commit()
    teacher = get_teacher(teacher_id)
    if teacher is None:
        raise RuntimeError("Updated teacher could not be retrieved")
    return teacher


def deactivate_teacher(teacher_id: int) -> dict[str, Any]:
    if get_teacher(teacher_id) is None:
        raise ValueError("Teacher not found")
    with get_connection() as connection:
        connection.execute("UPDATE teachers SET is_active = 0 WHERE id = ?", (teacher_id,))
        connection.commit()
    teacher = get_teacher(teacher_id)
    if teacher is None:
        raise RuntimeError("Deactivated teacher could not be retrieved")
    return teacher


def teacher_allocated_courses(teacher_id: int) -> list[dict[str, Any]]:
    if get_teacher(teacher_id) is None:
        raise ValueError("Teacher not found")
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT a.id AS allocation_id, a.workload_hours, a.created_at AS allocated_at,
                   c.id AS course_id, c.course_code, c.course_name,
                   s.id AS section_id, s.name AS section_name,
                   d.name AS department_name, at.name AS academic_term,
                   at.semester
            FROM course_allocations a
            INNER JOIN course_offerings o ON o.id = a.offering_id
            INNER JOIN courses c ON c.id = o.course_id
            INNER JOIN sections s ON s.id = o.section_id
            INNER JOIN departments d ON d.id = c.department_id
            INNER JOIN academic_terms at ON at.id = s.academic_term_id
            WHERE a.teacher_id = ?
            ORDER BY at.id DESC, s.name, c.course_code
            """,
            (teacher_id,),
        ).fetchall()
    return [_row_to_dict(row) for row in rows]
