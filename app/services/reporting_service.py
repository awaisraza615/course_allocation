"""Read-only report queries."""

from typing import Any

from app.database.connection import get_connection
from app.services.allocation_service import list_allocations
from app.services.offering_service import list_offerings
from app.services.workload_service import get_teacher_workload


def teacher_report(teacher_id: int, term_id: int | None = None) -> dict[str, Any]:
    workload = get_teacher_workload(teacher_id, term_id)
    allocations = [
        row for row in list_allocations(
            term_id=workload["academic_term_id"],
            teacher_id=teacher_id,
        )
    ]
    return {"workload": workload, "allocations": allocations}


def section_report(section_id: int) -> dict[str, Any]:
    with get_connection() as connection:
        section = connection.execute(
            """
            SELECT s.id AS section_id, s.name AS section_name,
                   d.id AS department_id, d.name AS department_name,
                   at.id AS academic_term_id, at.name AS academic_term,
                   at.semester
            FROM sections s
            INNER JOIN departments d ON d.id = s.department_id
            INNER JOIN academic_terms at ON at.id = s.academic_term_id
            WHERE s.id = ?
            """,
            (section_id,),
        ).fetchone()
    if section is None:
        raise ValueError("Section not found")
    offerings = list_offerings(section_id=section_id)
    allocations = list_allocations(
        term_id=section["academic_term_id"],
        section_id=section_id,
    )
    return {"section": dict(section), "offerings": offerings, "allocations": allocations}


def department_report(
    department_id: int,
    term_id: int | None = None,
) -> dict[str, Any]:
    with get_connection() as connection:
        department = connection.execute(
            "SELECT id, name, code FROM departments WHERE id = ?",
            (department_id,),
        ).fetchone()
    if department is None:
        raise ValueError("Department not found")
    offerings = list_offerings(
        department_id=department_id,
        academic_term_id=term_id,
    )
    allocations = list_allocations(
        term_id=term_id,
        department_id=department_id,
    )
    return {
        "department": dict(department),
        "offerings": offerings,
        "allocations": allocations,
    }


def unallocated_report(term_id: int | None = None) -> list[dict[str, Any]]:
    if term_id is None:
        with get_connection() as connection:
            row = connection.execute(
                "SELECT id FROM academic_terms WHERE is_active = 1 ORDER BY id DESC LIMIT 1"
            ).fetchone()
            if row is None:
                raise ValueError("term_id is required when no academic term is active")
            term_id = int(row["id"])
    offerings = list_offerings(academic_term_id=term_id, pending_only=True)
    result: list[dict[str, Any]] = []
    with get_connection() as connection:
        for offering in offerings:
            candidate_count = connection.execute(
                """
                SELECT COUNT(*) AS count
                FROM teacher_course_preferences p
                INNER JOIN teachers t ON t.id = p.teacher_id
                WHERE p.course_id = ? AND t.is_active = 1
                """,
                (offering["course_id"],),
            ).fetchone()["count"]
            result.append(
                {
                    **offering,
                    "reason": (
                        "No active teacher has expressed interest"
                        if candidate_count == 0
                        else "No eligible allocation has been made"
                    ),
                }
            )
    return result
