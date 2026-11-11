"""Transactional automatic and manual course allocation operations."""

import sqlite3
from typing import Any

from app.database.connection import get_connection
from app.services.workload_service import resolve_term_id

AUTOMATIC_ALLOCATION_MAX_HOURS = 12


def _offering_query(where: str = "") -> str:
    return """
        SELECT o.id AS offering_id, o.course_id, o.section_id,
               c.course_code, c.course_name, c.theory_hours,
               c.laboratory_hours,
               c.theory_hours + c.laboratory_hours AS workload_hours,
               s.name AS section_name, s.academic_term_id,
               d.name AS department_name
        FROM course_offerings o
        INNER JOIN courses c ON c.id = o.course_id
        INNER JOIN sections s ON s.id = o.section_id
        INNER JOIN departments d ON d.id = s.department_id
    """ + where


def _candidate_rows(
    connection: sqlite3.Connection,
    course_id: int,
) -> list[sqlite3.Row]:
    return connection.execute(
        """
        SELECT p.teacher_id, p.priority, t.full_name, t.designation_id,
               g.standard_workload, g.maximum_workload
        FROM teacher_course_preferences p
        INNER JOIN teachers t ON t.id = p.teacher_id
        INNER JOIN designations g ON g.id = t.designation_id
        WHERE p.course_id = ? AND t.is_active = 1 AND g.is_active = 1
        ORDER BY p.priority, t.full_name, t.id
        """,
        (course_id,),
    ).fetchall()


def _pending_plans(
    connection: sqlite3.Connection,
    term_id: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    offerings = connection.execute(
        _offering_query(
            """
            LEFT JOIN course_allocations a ON a.offering_id = o.id
            WHERE s.academic_term_id = ? AND a.id IS NULL
            ORDER BY o.id
            """
        ),
        (term_id,),
    ).fetchall()
    assigned = connection.execute(
        """
        SELECT a.teacher_id,
               COALESCE(SUM(CASE WHEN a.workload_hours > 0
                                 THEN a.workload_hours
                                 ELSE c.theory_hours + c.laboratory_hours END), 0) AS hours
        FROM course_allocations a
        INNER JOIN course_offerings o ON o.id = a.offering_id
        INNER JOIN courses c ON c.id = o.course_id
        INNER JOIN sections s ON s.id = o.section_id
        WHERE s.academic_term_id = ?
        GROUP BY a.teacher_id
        """,
        (term_id,),
    ).fetchall()
    totals = {row["teacher_id"]: int(row["hours"]) for row in assigned}
    plans: list[dict[str, Any]] = []
    unallocated: list[dict[str, Any]] = []

    for row in offerings:
        offering = dict(row)
        workload = int(offering["workload_hours"])
        candidates = _candidate_rows(connection, offering["course_id"])
        eligible = [
            candidate for candidate in candidates
            if totals.get(candidate["teacher_id"], 0) + workload
            <= min(candidate["maximum_workload"], AUTOMATIC_ALLOCATION_MAX_HOURS)
        ]
        if not eligible:
            reason = (
                "No active teacher has expressed interest"
                if not candidates
                else (
                    "All interested teachers would exceed the 12-hour automatic "
                    "allocation limit or their designation maximum"
                )
            )
            unallocated.append({**offering, "reason": reason})
            continue
        chosen = min(
            eligible,
            key=lambda candidate: (
                totals.get(candidate["teacher_id"], 0),
                candidate["priority"],
                candidate["full_name"].casefold(),
            ),
        )
        projected = totals.get(chosen["teacher_id"], 0) + workload
        plans.append(
            {
                **offering,
                "teacher_id": chosen["teacher_id"],
                "teacher_name": chosen["full_name"],
                "preference_priority": chosen["priority"],
                "current_workload": totals.get(chosen["teacher_id"], 0),
                "projected_workload": projected,
                "standard_workload": chosen["standard_workload"],
                "maximum_workload": chosen["maximum_workload"],
                "status": (
                    "SAFE" if projected <= chosen["standard_workload"]
                    else "EXTENDED"
                ),
            }
        )
        totals[chosen["teacher_id"]] = projected
    return plans, unallocated


def _insert_allocation(
    connection: sqlite3.Connection,
    offering_id: int,
    teacher_id: int,
    workload_hours: int,
    standard_limit: int,
    maximum_limit: int,
    preference_priority: int | None,
    action: str,
    previous_teacher_id: int | None = None,
    reason: str | None = None,
) -> dict[str, Any]:
    cursor = connection.execute(
        """
        INSERT INTO course_allocations
            (offering_id, teacher_id, workload_hours,
             standard_workload_snapshot, maximum_workload_snapshot,
             preference_priority)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            offering_id,
            teacher_id,
            workload_hours,
            standard_limit,
            maximum_limit,
            preference_priority,
        ),
    )
    allocation_id = cursor.lastrowid
    connection.execute(
        """
        INSERT INTO allocation_history
            (offering_id, allocation_id, action, previous_teacher_id,
             new_teacher_id, workload_hours, standard_workload_snapshot,
             maximum_workload_snapshot, reason)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            offering_id,
            allocation_id,
            action,
            previous_teacher_id,
            teacher_id,
            workload_hours,
            standard_limit,
            maximum_limit,
            reason,
        ),
    )
    return _get_allocation(connection, allocation_id)


def _get_allocation(
    connection: sqlite3.Connection,
    allocation_id: int,
) -> dict[str, Any]:
    row = connection.execute(
        """
        SELECT a.id AS allocation_id, a.offering_id, a.teacher_id,
               t.full_name AS teacher_name, c.course_code, c.course_name,
               a.workload_hours, a.standard_workload_snapshot,
               a.maximum_workload_snapshot, a.preference_priority,
               s.id AS section_id, s.name AS section_name,
               at.id AS academic_term_id, at.name AS academic_term,
               a.created_at
        FROM course_allocations a
        INNER JOIN teachers t ON t.id = a.teacher_id
        INNER JOIN course_offerings o ON o.id = a.offering_id
        INNER JOIN courses c ON c.id = o.course_id
        INNER JOIN sections s ON s.id = o.section_id
        INNER JOIN academic_terms at ON at.id = s.academic_term_id
        WHERE a.id = ?
        """,
        (allocation_id,),
    ).fetchone()
    if row is None:
        raise RuntimeError("Allocation could not be retrieved")
    return dict(row)


def preview_automatic_allocations(term_id: int | None = None) -> dict[str, Any]:
    with get_connection() as connection:
        resolved_term = resolve_term_id(connection, term_id)
        plans, unallocated = _pending_plans(connection, resolved_term)
    return {
        "academic_term_id": resolved_term,
        "allocations": plans,
        "unallocated": unallocated,
    }


def execute_automatic_allocations(term_id: int | None = None) -> dict[str, Any]:
    with get_connection() as connection:
        connection.execute("BEGIN IMMEDIATE")
        resolved_term = resolve_term_id(connection, term_id)
        plans, unallocated = _pending_plans(connection, resolved_term)
        created: list[dict[str, Any]] = []
        for plan in plans:
            created.append(
                _insert_allocation(
                    connection,
                    plan["offering_id"],
                    plan["teacher_id"],
                    plan["workload_hours"],
                    plan["standard_workload"],
                    plan["maximum_workload"],
                    plan["preference_priority"],
                    "assigned",
                    reason="Automatic allocation",
                )
            )
        connection.commit()
    return {
        "academic_term_id": resolved_term,
        "allocations": created,
        "unallocated": unallocated,
    }


def _preference_for_teacher(
    connection: sqlite3.Connection,
    teacher_id: int,
    course_id: int,
) -> sqlite3.Row | None:
    return connection.execute(
        """
        SELECT priority FROM teacher_course_preferences
        WHERE teacher_id = ? AND course_id = ?
        """,
        (teacher_id, course_id),
    ).fetchone()


def create_manual_allocation(payload: dict[str, Any]) -> dict[str, Any]:
    try:
        offering_id = int(payload["offering_id"])
        teacher_id = int(payload["teacher_id"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("offering_id and teacher_id must be integers") from exc
    override = payload.get("override_preference", False) is True
    reason = payload.get("reason")
    with get_connection() as connection:
        connection.execute("BEGIN IMMEDIATE")
        offering = connection.execute(
            _offering_query("WHERE o.id = ?"),
            (offering_id,),
        ).fetchone()
        if offering is None:
            raise ValueError("Offering not found")
        current = connection.execute(
            "SELECT id FROM course_allocations WHERE offering_id = ?",
            (offering_id,),
        ).fetchone()
        if current is not None:
            raise ValueError("Offering already has an allocation")
        teacher = connection.execute(
            """
            SELECT t.id, t.is_active, g.standard_workload,
                   g.maximum_workload, g.is_active AS designation_is_active
            FROM teachers t
            INNER JOIN designations g ON g.id = t.designation_id
            WHERE t.id = ?
            """,
            (teacher_id,),
        ).fetchone()
        if teacher is None or not teacher["is_active"] or not teacher["designation_is_active"]:
            raise ValueError("Active teacher with active designation not found")
        preference = _preference_for_teacher(connection, teacher_id, offering["course_id"])
        if preference is None and not override:
            raise ValueError("Teacher has no course preference; set override_preference to true")
        workload = int(offering["workload_hours"])
        maximum = int(teacher["maximum_workload"])
        allocation = _insert_allocation(
            connection,
            offering_id,
            teacher_id,
            workload,
            int(teacher["standard_workload"]),
            maximum,
            None if preference is None else preference["priority"],
            "assigned",
            reason=reason or "Manual allocation",
        )
        connection.commit()
    return allocation


def reassign_allocation(
    allocation_id: int,
    payload: dict[str, Any],
) -> dict[str, Any]:
    try:
        new_teacher_id = int(payload["teacher_id"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("teacher_id must be an integer") from exc
    override = payload.get("override_preference", False) is True
    with get_connection() as connection:
        connection.execute("BEGIN IMMEDIATE")
        old = connection.execute(
            """
            SELECT a.*, o.course_id, s.academic_term_id,
                   c.theory_hours + c.laboratory_hours AS course_workload
            FROM course_allocations a
            INNER JOIN course_offerings o ON o.id = a.offering_id
            INNER JOIN sections s ON s.id = o.section_id
            INNER JOIN courses c ON c.id = o.course_id
            WHERE a.id = ?
            """,
            (allocation_id,),
        ).fetchone()
        if old is None:
            raise ValueError("Allocation not found")
        teacher = connection.execute(
            """
            SELECT t.is_active, g.standard_workload, g.maximum_workload,
                   g.is_active AS designation_is_active
            FROM teachers t
            INNER JOIN designations g ON g.id = t.designation_id
            WHERE t.id = ?
            """,
            (new_teacher_id,),
        ).fetchone()
        if teacher is None or not teacher["is_active"] or not teacher["designation_is_active"]:
            raise ValueError("Active teacher with active designation not found")
        preference = _preference_for_teacher(connection, new_teacher_id, old["course_id"])
        if preference is None and not override:
            raise ValueError("Teacher has no course preference; set override_preference to true")
        if new_teacher_id == old["teacher_id"]:
            connection.rollback()
            return _get_allocation(connection, allocation_id)
        workload = int(old["workload_hours"] or old["course_workload"])
        maximum = int(teacher["maximum_workload"])
        old_teacher_id = int(old["teacher_id"])
        connection.execute(
            "DELETE FROM course_allocations WHERE id = ?",
            (allocation_id,),
        )
        result = _insert_allocation(
            connection,
            int(old["offering_id"]),
            new_teacher_id,
            workload,
            int(teacher["standard_workload"]),
            maximum,
            None if preference is None else preference["priority"],
            "reassigned",
            previous_teacher_id=old_teacher_id,
            reason=payload.get("reason") or "Manual reassignment",
        )
        connection.commit()
    return result


def remove_allocation(allocation_id: int, reason: str | None = None) -> dict[str, Any]:
    with get_connection() as connection:
        connection.execute("BEGIN IMMEDIATE")
        row = connection.execute(
            """
            SELECT a.id, a.offering_id, a.teacher_id, a.workload_hours,
                   a.standard_workload_snapshot, a.maximum_workload_snapshot
            FROM course_allocations a WHERE a.id = ?
            """,
            (allocation_id,),
        ).fetchone()
        if row is None:
            raise ValueError("Allocation not found")
        result = dict(row)
        connection.execute(
            """
            INSERT INTO allocation_history
                (offering_id, allocation_id, action, previous_teacher_id,
                 workload_hours, standard_workload_snapshot,
                 maximum_workload_snapshot, reason)
            VALUES (?, ?, 'removed', ?, ?, ?, ?, ?)
            """,
            (
                row["offering_id"],
                row["id"],
                row["teacher_id"],
                row["workload_hours"],
                row["standard_workload_snapshot"],
                row["maximum_workload_snapshot"],
                reason or "Allocation removed",
            ),
        )
        connection.execute("DELETE FROM course_allocations WHERE id = ?", (allocation_id,))
        connection.commit()
    return result


def list_allocations(
    term_id: int | None = None,
    teacher_id: int | None = None,
    department_id: int | None = None,
    section_id: int | None = None,
) -> list[dict[str, Any]]:
    conditions: list[str] = []
    values: list[Any] = []
    if term_id is not None:
        conditions.append("s.academic_term_id = ?")
        values.append(term_id)
    if teacher_id is not None:
        conditions.append("a.teacher_id = ?")
        values.append(teacher_id)
    if department_id is not None:
        conditions.append("s.department_id = ?")
        values.append(department_id)
    if section_id is not None:
        conditions.append("s.id = ?")
        values.append(section_id)
    where = f" WHERE {' AND '.join(conditions)}" if conditions else ""
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT a.id AS allocation_id, a.offering_id, a.teacher_id,
                   t.full_name AS teacher_name, t.department_id AS teacher_department_id,
                   c.course_code, c.course_name, c.department_id AS course_department_id,
                   d.name AS course_department, s.id AS section_id,
                   s.name AS section_name, s.academic_term_id,
                   at.name AS academic_term,
                   COALESCE(NULLIF(a.workload_hours, 0),
                            c.theory_hours + c.laboratory_hours) AS workload_hours,
                   a.standard_workload_snapshot, a.maximum_workload_snapshot,
                   a.preference_priority, a.created_at
            FROM course_allocations a
            INNER JOIN teachers t ON t.id = a.teacher_id
            INNER JOIN course_offerings o ON o.id = a.offering_id
            INNER JOIN courses c ON c.id = o.course_id
            INNER JOIN sections s ON s.id = o.section_id
            INNER JOIN departments d ON d.id = s.department_id
            INNER JOIN academic_terms at ON at.id = s.academic_term_id
            """ + where + " ORDER BY at.id DESC, s.name, c.course_code",
            tuple(values),
        ).fetchall()
    return [dict(row) for row in rows]


def list_allocation_history(term_id: int | None = None) -> list[dict[str, Any]]:
    where = " WHERE s.academic_term_id = ?" if term_id is not None else ""
    values: tuple[Any, ...] = (term_id,) if term_id is not None else ()
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT h.id AS history_id, h.offering_id, h.allocation_id,
                   h.action, h.previous_teacher_id, old_t.full_name AS previous_teacher,
                   h.new_teacher_id, new_t.full_name AS new_teacher,
                   h.workload_hours, h.standard_workload_snapshot,
                   h.maximum_workload_snapshot, h.reason, h.changed_at,
                   c.course_code, c.course_name, s.name AS section_name,
                   at.id AS academic_term_id, at.name AS academic_term
            FROM allocation_history h
            INNER JOIN course_offerings o ON o.id = h.offering_id
            INNER JOIN courses c ON c.id = o.course_id
            INNER JOIN sections s ON s.id = o.section_id
            INNER JOIN academic_terms at ON at.id = s.academic_term_id
            LEFT JOIN teachers old_t ON old_t.id = h.previous_teacher_id
            LEFT JOIN teachers new_t ON new_t.id = h.new_teacher_id
            """ + where + " ORDER BY h.changed_at DESC, h.id DESC",
            values,
        ).fetchall()
    return [dict(row) for row in rows]
