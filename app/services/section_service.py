
"""Database operations for section management."""

import sqlite3
from typing import Any

from app.database.connection import get_connection
from app.services.academic_term_service import get_academic_term
from app.services.department_service import get_department
from app.utils.validators import (
    normalize_bool,
    parse_integer,
    require_text,
)


def _row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    return dict(row)


def _section_query():
    return """
        SELECT
            s.id,
            s.name,
            s.department_id,
            s.academic_term_id,
            s.is_active,
            d.name AS department_name,
            d.code AS department_code,
            at.name AS academic_term_name,
            at.semester,
            s.created_at
        FROM sections s
        INNER JOIN departments d
            ON d.id = s.department_id
        INNER JOIN academic_terms at
            ON at.id = s.academic_term_id
    """


def list_sections() -> list[dict[str, Any]]:
    with get_connection() as connection:
        rows = connection.execute(
            _section_query() + """
            ORDER BY
                d.name ASC,
                at.name ASC,
                s.name ASC
            """
        ).fetchall()

    return [_row_to_dict(row) for row in rows]


def get_section(section_id: int) -> dict[str, Any] | None:
    with get_connection() as connection:
        row = connection.execute(
            _section_query() + """
            WHERE s.id = ?
            """,
            (section_id,)
        ).fetchone()

    return None if row is None else _row_to_dict(row)


def create_section_record(
    payload: dict[str, Any]
) -> dict[str, Any]:

    name = require_text(payload.get("name"), "name")
    department_id = parse_integer(
        payload.get("department_id"),
        "department_id"
    )
    academic_term_id = parse_integer(
        payload.get("academic_term_id"),
        "academic_term_id"
    )

    is_active = (
        normalize_bool(payload.get("is_active"))
        if "is_active" in payload
        else 1
    )

    if get_department(department_id) is None:
        raise ValueError("Department not found")

    if get_academic_term(academic_term_id) is None:
        raise ValueError("Academic term not found")

    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO sections (
                name,
                department_id,
                academic_term_id,
                is_active
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                name,
                department_id,
                academic_term_id,
                is_active
            )
        )

        section_id = cursor.lastrowid
        connection.commit()

        row = connection.execute(
            _section_query() + """
            WHERE s.id = ?
            """,
            (section_id,)
        ).fetchone()

    return _row_to_dict(row)


def update_section_record(
    section_id: int,
    payload: dict[str, Any]
) -> dict[str, Any]:

    existing = get_section(section_id)

    if existing is None:
        raise ValueError("Section not found")

    updates: list[str] = []
    values: list[Any] = []

    if "name" in payload:
        updates.append("name = ?")
        values.append(
            require_text(payload.get("name"), "name")
        )

    if "department_id" in payload:
        department_id = parse_integer(
            payload.get("department_id"),
            "department_id"
        )

        if get_department(department_id) is None:
            raise ValueError("Department not found")

        updates.append("department_id = ?")
        values.append(department_id)

    if "academic_term_id" in payload:
        academic_term_id = parse_integer(
            payload.get("academic_term_id"),
            "academic_term_id"
        )

        if get_academic_term(academic_term_id) is None:
            raise ValueError("Academic term not found")

        updates.append("academic_term_id = ?")
        values.append(academic_term_id)

    if "is_active" in payload:
        updates.append("is_active = ?")
        values.append(
            normalize_bool(payload.get("is_active"))
        )

    if not updates:
        raise ValueError("No valid fields provided for update")

    values.append(section_id)

    with get_connection() as connection:
        connection.execute(
            f"""
            UPDATE sections
            SET {", ".join(updates)}
            WHERE id = ?
            """,
            tuple(values)
        )

        connection.commit()

        row = connection.execute(
            _section_query() + """
            WHERE s.id = ?
            """,
            (section_id,)
        ).fetchone()

    return _row_to_dict(row)


def delete_section_record(
    section_id: int
) -> dict[str, Any]:

    existing = get_section(section_id)

    if existing is None:
        raise ValueError("Section not found")

    with get_connection() as connection:
        connection.execute(
            """
            UPDATE sections
            SET is_active = 0
            WHERE id = ?
            """,
            (section_id,)
        )

        connection.commit()

        row = connection.execute(
            _section_query() + """
            WHERE s.id = ?
            """,
            (section_id,)
        ).fetchone()

    return _row_to_dict(row)


def permanently_delete_section_record(section_id: int) -> dict[str, Any]:
    with get_connection() as connection:
        connection.execute("BEGIN IMMEDIATE")
        section = connection.execute(
            _section_query() + " WHERE s.id = ?",
            (section_id,),
        ).fetchone()
        if section is None:
            raise ValueError("Section not found")

        offering_count = connection.execute(
            "SELECT COUNT(*) AS count FROM course_offerings WHERE section_id = ?",
            (section_id,),
        ).fetchone()["count"]
        allocation_count = connection.execute(
            """
            SELECT COUNT(*) AS count
            FROM course_allocations a
            INNER JOIN course_offerings o ON o.id = a.offering_id
            WHERE o.section_id = ?
            """,
            (section_id,),
        ).fetchone()["count"]
        history_count = connection.execute(
            """
            SELECT COUNT(*) AS count
            FROM allocation_history h
            INNER JOIN course_offerings o ON o.id = h.offering_id
            WHERE o.section_id = ?
            """,
            (section_id,),
        ).fetchone()["count"]

        connection.execute(
            """
            DELETE FROM allocation_history
            WHERE offering_id IN (
                SELECT id FROM course_offerings WHERE section_id = ?
            )
            """,
            (section_id,),
        )
        connection.execute(
            """
            DELETE FROM course_allocations
            WHERE offering_id IN (
                SELECT id FROM course_offerings WHERE section_id = ?
            )
            """,
            (section_id,),
        )
        connection.execute(
            "DELETE FROM course_offerings WHERE section_id = ?",
            (section_id,),
        )
        connection.execute("DELETE FROM sections WHERE id = ?", (section_id,))
        connection.commit()

    return {
        "section": dict(section),
        "deleted_offerings": offering_count,
        "deleted_allocations": allocation_count,
        "deleted_allocation_history": history_count,
    }
