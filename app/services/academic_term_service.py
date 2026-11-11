
"""Database operations for academic term management."""

import sqlite3
from typing import Any

from app.database.connection import get_connection
from app.utils.validators import normalize_bool, require_text


def _row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    return dict(row)


def list_academic_terms() -> list[dict[str, Any]]:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT id, name, academic_year, semester, is_active, created_at
            FROM academic_terms
            ORDER BY academic_year DESC, semester DESC, id DESC
            """
        ).fetchall()

    return [_row_to_dict(row) for row in rows]


def get_academic_term(term_id: int) -> dict[str, Any] | None:
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT id, name, academic_year, semester, is_active, created_at
            FROM academic_terms
            WHERE id = ?
            """,
            (term_id,)
        ).fetchone()

    return None if row is None else _row_to_dict(row)


def create_academic_term_record(
    payload: dict[str, Any]
) -> dict[str, Any]:

    name = require_text(payload.get("name"), "name")
    semester = require_text(payload.get("semester"), "semester")
    academic_year = require_text(payload.get("academic_year", name), "academic_year")
    is_active = normalize_bool(payload.get("is_active", False))

    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO academic_terms (name, academic_year, semester, is_active)
            VALUES (?, ?, ?, ?)
            """,
            (name, academic_year, semester, is_active)
        )

        connection.commit()

        row = connection.execute(
            """
            SELECT id, name, academic_year, semester, is_active, created_at
            FROM academic_terms
            WHERE id = ?
            """,
            (cursor.lastrowid,)
        ).fetchone()

    return _row_to_dict(row)


def update_academic_term_record(
    term_id: int,
    payload: dict[str, Any]
) -> dict[str, Any]:

    existing = get_academic_term(term_id)

    if existing is None:
        raise ValueError("Academic term not found")

    name = require_text(payload.get("name", existing["name"]), "name")
    semester = require_text(payload.get("semester", existing["semester"]), "semester")
    academic_year = require_text(
        payload.get("academic_year", existing["academic_year"]),
        "academic_year",
    )

    with get_connection() as connection:
        connection.execute(
            """
            UPDATE academic_terms
            SET name = ?, academic_year = ?, semester = ?, is_active = ?
            WHERE id = ?
            """,
            (
                name,
                academic_year,
                semester,
                normalize_bool(payload.get("is_active", existing["is_active"])),
                term_id,
            )
        )

        connection.commit()

        row = connection.execute(
            """
            SELECT id, name, academic_year, semester, is_active, created_at
            FROM academic_terms
            WHERE id = ?
            """,
            (term_id,)
        ).fetchone()

    return _row_to_dict(row)


def set_academic_term_active(term_id: int, is_active: bool) -> dict[str, Any]:
    if get_academic_term(term_id) is None:
        raise ValueError("Academic term not found")
    with get_connection() as connection:
        connection.execute(
            "UPDATE academic_terms SET is_active = ? WHERE id = ?",
            (int(is_active), term_id),
        )
        connection.commit()
        row = connection.execute(
            """
            SELECT id, name, academic_year, semester, is_active, created_at
            FROM academic_terms
            WHERE id = ?
            """,
            (term_id,),
        ).fetchone()
    return _row_to_dict(row)


def activate_academic_term(term_id: int) -> dict[str, Any]:
    return set_academic_term_active(term_id, True)
