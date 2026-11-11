"""Database operations for teacher designation and workload policies."""

import sqlite3
from typing import Any

from app.database.connection import get_connection
from app.utils.validators import normalize_bool, parse_integer, require_text


def _row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    return dict(row)


def list_designations() -> list[dict[str, Any]]:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT id, name, standard_workload, maximum_workload, is_active, created_at
            FROM designations
            ORDER BY name ASC
            """
        ).fetchall()
    return [_row_to_dict(row) for row in rows]


def get_designation(designation_id: int) -> dict[str, Any] | None:
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT id, name, standard_workload, maximum_workload, is_active, created_at
            FROM designations
            WHERE id = ?
            """,
            (designation_id,),
        ).fetchone()
    return None if row is None else _row_to_dict(row)


def create_designation_record(payload: dict[str, Any]) -> dict[str, Any]:
    name = require_text(payload.get("name"), "name")
    standard_workload = parse_integer(payload.get("standard_workload"), "standard_workload")
    maximum_workload = parse_integer(payload.get("maximum_workload"), "maximum_workload")
    is_active = normalize_bool(payload.get("is_active", True)) if "is_active" in payload else 1

    if standard_workload < 0:
        raise ValueError("standard_workload cannot be negative")
    if maximum_workload < standard_workload:
        raise ValueError("maximum_workload cannot be less than standard_workload")

    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO designations (name, standard_workload, maximum_workload, is_active)
            VALUES (?, ?, ?, ?)
            """,
            (name, standard_workload, maximum_workload, is_active),
        )
        connection.commit()
        row = connection.execute(
            """
            SELECT id, name, standard_workload, maximum_workload, is_active, created_at
            FROM designations
            WHERE id = ?
            """,
            (cursor.lastrowid,),
        ).fetchone()
    return _row_to_dict(row)


def update_designation_record(designation_id: int, payload: dict[str, Any]) -> dict[str, Any]:
    existing = get_designation(designation_id)
    if existing is None:
        raise ValueError("Designation not found")

    updates: list[str] = []
    values: list[Any] = []

    if "name" in payload:
        updates.append("name = ?")
        values.append(require_text(payload.get("name"), "name"))
    if "standard_workload" in payload:
        standard = parse_integer(payload.get("standard_workload"), "standard_workload")
        if standard < 0:
            raise ValueError("standard_workload cannot be negative")
        updates.append("standard_workload = ?")
        values.append(standard)
    if "maximum_workload" in payload:
        maximum = parse_integer(payload.get("maximum_workload"), "maximum_workload")
        updates.append("maximum_workload = ?")
        values.append(maximum)
    if "is_active" in payload:
        updates.append("is_active = ?")
        values.append(normalize_bool(payload.get("is_active")))

    if not updates:
        raise ValueError("No valid fields provided for update")

    with get_connection() as connection:
        current = connection.execute(
            "SELECT standard_workload, maximum_workload FROM designations WHERE id = ?",
            (designation_id,),
        ).fetchone()
        if current is None:
            raise ValueError("Designation not found")

        standard_value = parse_integer(payload.get("standard_workload"), "standard_workload") if "standard_workload" in payload else current["standard_workload"]
        maximum_value = parse_integer(payload.get("maximum_workload"), "maximum_workload") if "maximum_workload" in payload else current["maximum_workload"]

        if standard_value < 0:
            raise ValueError("standard_workload cannot be negative")
        if maximum_value < standard_value:
            raise ValueError("maximum_workload cannot be less than standard_workload")

        values.append(designation_id)
        connection.execute(
            f"UPDATE designations SET {', '.join(updates)} WHERE id = ?",
            tuple(values),
        )
        connection.commit()
        row = connection.execute(
            """
            SELECT id, name, standard_workload, maximum_workload, is_active, created_at
            FROM designations
            WHERE id = ?
            """,
            (designation_id,),
        ).fetchone()
    return _row_to_dict(row)


def delete_designation_record(designation_id: int) -> dict[str, Any]:
    if get_designation(designation_id) is None:
        raise ValueError("Designation not found")

    with get_connection() as connection:
        connection.execute(
            "UPDATE designations SET is_active = 0 WHERE id = ?",
            (designation_id,),
        )
        connection.commit()
        row = connection.execute(
            """
            SELECT id, name, standard_workload, maximum_workload, is_active, created_at
            FROM designations
            WHERE id = ?
            """,
            (designation_id,),
        ).fetchone()
    return _row_to_dict(row)
