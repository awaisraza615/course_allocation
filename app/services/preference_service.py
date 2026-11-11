"""Database operations for teacher course preferences."""

import sqlite3
from typing import Any

from app.database.connection import get_connection


def _row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    return dict(row)


def list_teacher_preferences(teacher_id: int) -> list[dict[str, Any]]:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT p.id, p.teacher_id, p.course_id, p.priority, p.created_at,
                   c.course_code, c.course_name, c.theory_hours, c.laboratory_hours,
                   c.department_id, d.name AS department_name
            FROM teacher_course_preferences p
            INNER JOIN courses c ON c.id = p.course_id
            INNER JOIN departments d ON d.id = c.department_id
            WHERE p.teacher_id = ?
            ORDER BY p.priority, p.id
            """,
            (teacher_id,),
        ).fetchall()
    return [_row_to_dict(row) for row in rows]


def list_course_interested_teachers(course_id: int) -> list[dict[str, Any]]:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT p.id AS preference_id, p.priority, t.id AS teacher_id,
                   t.full_name, t.employee_code, t.department_id,
                   d.name AS department_name, g.name AS designation_name
            FROM teacher_course_preferences p
            INNER JOIN teachers t ON t.id = p.teacher_id
            INNER JOIN departments d ON d.id = t.department_id
            INNER JOIN designations g ON g.id = t.designation_id
            WHERE p.course_id = ?
            ORDER BY p.priority, t.full_name
            """,
            (course_id,),
        ).fetchall()
    return [_row_to_dict(row) for row in rows]


def _validate_references(connection: sqlite3.Connection, teacher_id: int, course_id: int) -> None:
    teacher = connection.execute(
        "SELECT is_active FROM teachers WHERE id = ?",
        (teacher_id,),
    ).fetchone()
    if teacher is None or not teacher["is_active"]:
        raise ValueError("Active teacher not found")
    course = connection.execute(
        "SELECT is_active FROM courses WHERE id = ?",
        (course_id,),
    ).fetchone()
    if course is None or not course["is_active"]:
        raise ValueError("Active course not found")


def add_teacher_preferences(
    teacher_id: int,
    preferences: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    if not preferences:
        raise ValueError("At least one preference is required")
    with get_connection() as connection:
        connection.execute("BEGIN IMMEDIATE")
        for preference in preferences:
            course_id = int(preference["course_id"])
            _validate_references(connection, teacher_id, course_id)
            existing = connection.execute(
                """
                SELECT COALESCE(MAX(priority), 0) AS max_priority
                FROM teacher_course_preferences
                WHERE teacher_id = ?
                """,
                (teacher_id,),
            ).fetchone()["max_priority"]
            priority = int(preference.get("priority", existing + 1))
            if priority < 1:
                raise ValueError("priority must be a positive integer")
            connection.execute(
                """
                INSERT INTO teacher_course_preferences (teacher_id, course_id, priority)
                VALUES (?, ?, ?)
                """,
                (teacher_id, course_id, priority),
            )
        connection.commit()
    return list_teacher_preferences(teacher_id)


def _set_priorities(
    connection: sqlite3.Connection,
    ordered_ids: list[int],
) -> None:
    if not ordered_ids:
        return
    max_priority = connection.execute(
        "SELECT COALESCE(MAX(priority), 0) FROM teacher_course_preferences"
    ).fetchone()[0]
    offset = max_priority + len(ordered_ids) + 1
    for position, preference_id in enumerate(ordered_ids, start=1):
        connection.execute(
            "UPDATE teacher_course_preferences SET priority = ? WHERE id = ?",
            (offset + position, preference_id),
        )
    for position, preference_id in enumerate(ordered_ids, start=1):
        connection.execute(
            "UPDATE teacher_course_preferences SET priority = ? WHERE id = ?",
            (position, preference_id),
        )


def update_preference_priority(preference_id: int, priority: int) -> dict[str, Any]:
    if priority < 1:
        raise ValueError("priority must be a positive integer")
    with get_connection() as connection:
        connection.execute("BEGIN IMMEDIATE")
        preference = connection.execute(
            "SELECT id, teacher_id FROM teacher_course_preferences WHERE id = ?",
            (preference_id,),
        ).fetchone()
        if preference is None:
            raise ValueError("Preference not found")
        rows = connection.execute(
            """
            SELECT id FROM teacher_course_preferences
            WHERE teacher_id = ? ORDER BY priority, id
            """,
            (preference["teacher_id"],),
        ).fetchall()
        ids = [row["id"] for row in rows if row["id"] != preference_id]
        if priority > len(ids) + 1:
            raise ValueError("priority cannot exceed the next available position")
        ids.insert(priority - 1, preference_id)
        _set_priorities(connection, ids)
        connection.commit()
        updated = connection.execute(
            """
            SELECT id, teacher_id, course_id, priority, created_at
            FROM teacher_course_preferences WHERE id = ?
            """,
            (preference_id,),
        ).fetchone()
    return _row_to_dict(updated)


def remove_preference(preference_id: int) -> dict[str, Any]:
    with get_connection() as connection:
        connection.execute("BEGIN IMMEDIATE")
        preference = connection.execute(
            "SELECT id, teacher_id, course_id, priority FROM teacher_course_preferences WHERE id = ?",
            (preference_id,),
        ).fetchone()
        if preference is None:
            raise ValueError("Preference not found")
        result = _row_to_dict(preference)
        connection.execute(
            "DELETE FROM teacher_course_preferences WHERE id = ?",
            (preference_id,),
        )
        remaining = connection.execute(
            """
            SELECT id FROM teacher_course_preferences
            WHERE teacher_id = ? ORDER BY priority, id
            """,
            (preference["teacher_id"],),
        ).fetchall()
        _set_priorities(connection, [row["id"] for row in remaining])
        connection.commit()
    return result
