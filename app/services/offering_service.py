"""Database operations for semester course offerings."""

import sqlite3
from typing import Any

from app.database.connection import get_connection


def _row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    return dict(row)


OFFERING_SELECT = """
    SELECT o.id, o.course_id, o.section_id, o.created_at,
           c.course_code, c.course_name, c.theory_hours, c.laboratory_hours,
           c.theory_hours + c.laboratory_hours AS workload_hours,
           a.id AS allocation_id, a.teacher_id AS allocated_teacher_id,
           t.full_name AS allocated_teacher_name,
           s.name AS section_name, s.department_id, d.name AS department_name,
           at.id AS academic_term_id, at.name AS academic_term, at.semester
    FROM course_offerings o
    INNER JOIN courses c ON c.id = o.course_id
    INNER JOIN sections s ON s.id = o.section_id
    INNER JOIN departments d ON d.id = s.department_id
    INNER JOIN academic_terms at ON at.id = s.academic_term_id
    LEFT JOIN course_allocations a ON a.offering_id = o.id
    LEFT JOIN teachers t ON t.id = a.teacher_id
"""


def list_offerings(
    section_id: int | None = None,
    department_id: int | None = None,
    academic_term_id: int | None = None,
    pending_only: bool = False,
) -> list[dict[str, Any]]:
    conditions: list[str] = []
    values: list[Any] = []
    if section_id is not None:
        conditions.append("o.section_id = ?")
        values.append(section_id)
    if department_id is not None:
        conditions.append("s.department_id = ?")
        values.append(department_id)
    if academic_term_id is not None:
        conditions.append("s.academic_term_id = ?")
        values.append(academic_term_id)
    if pending_only:
        conditions.append("a.id IS NULL")
    where = f" WHERE {' AND '.join(conditions)}" if conditions else ""
    query = OFFERING_SELECT
    query += where + " ORDER BY at.id DESC, s.name, c.course_code"
    with get_connection() as connection:
        rows = connection.execute(query, tuple(values)).fetchall()
    return [_row_to_dict(row) for row in rows]


def create_offering(payload: dict[str, Any]) -> dict[str, Any]:
    try:
        course_id = int(payload["course_id"])
        section_id = int(payload["section_id"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("course_id and section_id must be integers") from exc
    with get_connection() as connection:
        course = connection.execute(
            "SELECT is_active FROM courses WHERE id = ?",
            (course_id,),
        ).fetchone()
        if course is None or not course["is_active"]:
            raise ValueError("Active course not found")
        section = connection.execute(
            """
            SELECT s.is_active, s.department_id
            FROM sections s
            INNER JOIN academic_terms at ON at.id = s.academic_term_id
            WHERE s.id = ?
            """,
            (section_id,),
        ).fetchone()
        if section is None or not section["is_active"]:
            raise ValueError("Active section not found")
        course_department = connection.execute(
            """
            SELECT 1
            FROM course_departments
            WHERE course_id = ? AND department_id = ?
            """,
            (course_id, section["department_id"]),
        ).fetchone()
        if course_department is None:
            raise ValueError("Course is not associated with the section's department")
        cursor = connection.execute(
            """
            INSERT INTO course_offerings (course_id, section_id)
            VALUES (?, ?)
            """,
            (course_id, section_id),
        )
        connection.commit()
        row = connection.execute(
            OFFERING_SELECT + " WHERE o.id = ?",
            (cursor.lastrowid,),
        ).fetchone()
    return _row_to_dict(row)


def delete_pending_offering(offering_id: int) -> dict[str, Any]:
    with get_connection() as connection:
        row = connection.execute(
            OFFERING_SELECT + " WHERE o.id = ?",
            (offering_id,),
        ).fetchone()
        if row is None:
            raise ValueError("Offering not found")
        allocation = connection.execute(
            "SELECT id FROM course_allocations WHERE offering_id = ?",
            (offering_id,),
        ).fetchone()
        if allocation is not None:
            raise ValueError("Allocated offerings cannot be deleted")
        connection.execute(
            "DELETE FROM allocation_history WHERE offering_id = ?",
            (offering_id,),
        )
        connection.execute("DELETE FROM course_offerings WHERE id = ?", (offering_id,))
        connection.commit()
    return _row_to_dict(row)
