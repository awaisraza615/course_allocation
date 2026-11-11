"""Database operations for department management."""

import sqlite3
from typing import Any

from app.database.connection import get_connection
from app.utils.validators import normalize_bool, require_text


def _row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    return dict(row)


def list_departments() -> list[dict[str, Any]]:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT id, name, code, is_active, created_at
            FROM departments
            ORDER BY name ASC
            """
        ).fetchall()
    return [_row_to_dict(row) for row in rows]


def get_department(department_id: int) -> dict[str, Any] | None:
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT id, name, code, is_active, created_at
            FROM departments
            WHERE id = ?
            """,
            (department_id,),
        ).fetchone()
    return None if row is None else _row_to_dict(row)


def create_department_record(payload: dict[str, Any]) -> dict[str, Any]:
    name = require_text(payload.get("name"), "name")
    code = require_text(payload.get("code"), "code").upper()
    is_active = normalize_bool(payload.get("is_active", True)) if "is_active" in payload else 1

    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO departments (name, code, is_active)
            VALUES (?, ?, ?)
            """,
            (name, code, is_active),
        )
        connection.commit()
        row = connection.execute(
            "SELECT id, name, code, is_active, created_at FROM departments WHERE id = ?",
            (cursor.lastrowid,),
        ).fetchone()
    return _row_to_dict(row)


def update_department_record(department_id: int, payload: dict[str, Any]) -> dict[str, Any]:
    existing = get_department(department_id)
    if existing is None:
        raise ValueError("Department not found")

    updates: list[str] = []
    values: list[Any] = []

    if "name" in payload:
        updates.append("name = ?")
        values.append(require_text(payload.get("name"), "name"))
    if "code" in payload:
        updates.append("code = ?")
        values.append(require_text(payload.get("code"), "code").upper())
    if "is_active" in payload:
        updates.append("is_active = ?")
        values.append(normalize_bool(payload.get("is_active")))

    if not updates:
        raise ValueError("No valid fields provided for update")

    values.append(department_id)

    with get_connection() as connection:
        connection.execute(
            f"UPDATE departments SET {', '.join(updates)} WHERE id = ?",
            tuple(values),
        )
        connection.commit()
        row = connection.execute(
            "SELECT id, name, code, is_active, created_at FROM departments WHERE id = ?",
            (department_id,),
        ).fetchone()
    return _row_to_dict(row)


def delete_department_record(department_id: int) -> dict[str, Any]:
    if get_department(department_id) is None:
        raise ValueError("Department not found")

    with get_connection() as connection:
        connection.execute(
            "UPDATE departments SET is_active = 0 WHERE id = ?",
            (department_id,),
        )
        connection.commit()
        row = connection.execute(
            "SELECT id, name, code, is_active, created_at FROM departments WHERE id = ?",
            (department_id,),
        ).fetchone()
    return _row_to_dict(row)


def list_department_sections(department_id: int) -> list[dict[str, Any]]:
    if get_department(department_id) is None:
        raise ValueError("Department not found")

    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT s.id, s.department_id, s.academic_term_id, s.name, s.is_active,
                   at.academic_year, at.semester, s.created_at
            FROM sections s
            INNER JOIN academic_terms at ON at.id = s.academic_term_id
            WHERE s.department_id = ?
            ORDER BY at.academic_year DESC, at.semester ASC, s.name ASC
            """,
            (department_id,),
        ).fetchall()
    return [_row_to_dict(row) for row in rows]
