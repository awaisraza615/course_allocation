"""Term-scoped teacher workload calculations."""

import sqlite3
from typing import Any

from app.database.connection import get_connection


def resolve_term_id(
    connection: sqlite3.Connection,
    term_id: int | None,
) -> int:
    if term_id is None:
        row = connection.execute(
            "SELECT id FROM academic_terms WHERE is_active = 1 ORDER BY id DESC LIMIT 1"
        ).fetchone()
        if row is None:
            raise ValueError("term_id is required when no academic term is active")
        return int(row["id"])
    row = connection.execute(
        "SELECT id FROM academic_terms WHERE id = ?",
        (term_id,),
    ).fetchone()
    if row is None:
        raise ValueError("Academic term not found")
    return int(row["id"])


def workload_total(
    connection: sqlite3.Connection,
    teacher_id: int,
    term_id: int,
    exclude_allocation_id: int | None = None,
) -> int:
    exclusion = ""
    values: list[Any] = [teacher_id, term_id]
    if exclude_allocation_id is not None:
        exclusion = " AND a.id != ?"
        values.append(exclude_allocation_id)
    row = connection.execute(
        """
        SELECT COALESCE(
            SUM(CASE WHEN a.workload_hours > 0
                     THEN a.workload_hours
                     ELSE c.theory_hours + c.laboratory_hours END),
            0
        ) AS total
        FROM course_allocations a
        INNER JOIN course_offerings o ON o.id = a.offering_id
        INNER JOIN courses c ON c.id = o.course_id
        INNER JOIN sections s ON s.id = o.section_id
        WHERE a.teacher_id = ? AND s.academic_term_id = ?
        """ + exclusion,
        tuple(values),
    ).fetchone()
    return int(row["total"])


def _teacher_workload(
    connection: sqlite3.Connection,
    teacher_id: int,
    term_id: int,
) -> dict[str, Any]:
    teacher = connection.execute(
        """
        SELECT t.id AS teacher_id, t.full_name AS teacher_name,
               t.employee_code, t.department_id, d.name AS department_name,
               g.id AS designation_id, g.name AS designation,
               g.standard_workload, g.maximum_workload
        FROM teachers t
        INNER JOIN departments d ON d.id = t.department_id
        INNER JOIN designations g ON g.id = t.designation_id
        WHERE t.id = ?
        """,
        (teacher_id,),
    ).fetchone()
    if teacher is None:
        raise ValueError("Teacher not found")

    allocated = workload_total(connection, teacher_id, term_id)
    standard = int(teacher["standard_workload"])
    maximum = int(teacher["maximum_workload"])
    status = "SAFE" if allocated <= standard else (
        "EXTENDED" if allocated <= maximum else "EXCEEDED"
    )
    return {
        **dict(teacher),
        "academic_term_id": term_id,
        "allocated_hours": allocated,
        "remaining_standard_hours": standard - allocated,
        "remaining_maximum_hours": maximum - allocated,
        "status": status,
    }


def get_teacher_workload(
    teacher_id: int,
    term_id: int | None = None,
) -> dict[str, Any]:
    with get_connection() as connection:
        resolved_term = resolve_term_id(connection, term_id)
        return _teacher_workload(connection, teacher_id, resolved_term)


def get_all_teacher_workloads(
    term_id: int | None = None,
    department_id: int | None = None,
) -> list[dict[str, Any]]:
    with get_connection() as connection:
        resolved_term = resolve_term_id(connection, term_id)
        query = "SELECT id FROM teachers WHERE is_active = 1"
        values: tuple[Any, ...] = ()
        if department_id is not None:
            query += " AND department_id = ?"
            values = (department_id,)
        query += " ORDER BY full_name, id"
        teacher_ids = connection.execute(query, values).fetchall()
        return [
            _teacher_workload(connection, row["id"], resolved_term)
            for row in teacher_ids
        ]
