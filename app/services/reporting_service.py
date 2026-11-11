"""Read-only report queries."""

from io import BytesIO
from typing import Any

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.worksheet.table import Table, TableStyleInfo

from app.database.connection import get_connection
from app.services.allocation_service import list_allocations
from app.services.offering_service import list_offerings
from app.services.workload_service import get_teacher_workload


def teacher_workload_workbook(teacher_id: int | None = None) -> bytes:
    with get_connection() as connection:
        teacher_filter = "WHERE t.id = ?" if teacher_id is not None else ""
        parameters = (teacher_id,) if teacher_id is not None else ()
        teachers = connection.execute(
            """
            SELECT t.id, t.full_name, t.employee_code, t.is_active,
                   d.name AS teacher_department, g.name AS designation
            FROM teachers t
            INNER JOIN departments d ON d.id = t.department_id
            INNER JOIN designations g ON g.id = t.designation_id
            """ + teacher_filter + " ORDER BY t.full_name COLLATE NOCASE, t.id",
            parameters,
        ).fetchall()
        if teacher_id is not None and not teachers:
            raise ValueError("Teacher not found")

        allocations = connection.execute(
            """
            SELECT a.teacher_id, c.course_code, c.course_name,
                   at.academic_year, at.name AS academic_term, at.semester,
                   s.name AS section_name, d.name AS assigned_department,
                   COALESCE(NULLIF(a.workload_hours, 0),
                            c.theory_hours + c.laboratory_hours) AS course_workload
            FROM course_allocations a
            INNER JOIN teachers t ON t.id = a.teacher_id
            INNER JOIN course_offerings o ON o.id = a.offering_id
            INNER JOIN courses c ON c.id = o.course_id
            INNER JOIN sections s ON s.id = o.section_id
            INNER JOIN departments d ON d.id = s.department_id
            INNER JOIN academic_terms at ON at.id = s.academic_term_id
            """ + ("WHERE a.teacher_id = ? " if teacher_id is not None else "")
            + """
            ORDER BY t.full_name COLLATE NOCASE, t.id,
                     at.academic_year DESC, at.id DESC,
                     c.course_name COLLATE NOCASE, s.name
            """,
            parameters,
        ).fetchall()

    allocations_by_teacher: dict[int, list[dict[str, Any]]] = {}
    totals_by_teacher: dict[int, int] = {}
    for allocation in allocations:
        row = dict(allocation)
        allocations_by_teacher.setdefault(row["teacher_id"], []).append(row)
        totals_by_teacher[row["teacher_id"]] = (
            totals_by_teacher.get(row["teacher_id"], 0) + int(row["course_workload"])
        )

    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = "Teacher Workload"
    headers = [
        "Sr. No.",
        "Teacher",
        "Employee Code",
        "Teacher Department",
        "Designation",
        "Course Code",
        "Course Name",
        "Academic Year",
        "Academic Term",
        "Semester",
        "Section",
        "Assigned Department",
        "Course Workload (Hours)",
        "Total Workload (All Terms)",
        "Teacher Status",
    ]
    worksheet.merge_cells(start_row=1, start_column=1, end_row=1, end_column=len(headers))
    title = worksheet.cell(row=1, column=1, value="Teacher Course & Workload Report")
    title.font = Font(bold=True, size=16, color="FFFFFF")
    title.fill = PatternFill("solid", fgColor="17365D")
    title.alignment = Alignment(vertical="center")
    worksheet.row_dimensions[1].height = 28
    worksheet.merge_cells(start_row=2, start_column=1, end_row=2, end_column=len(headers))
    subtitle = worksheet.cell(
        row=2,
        column=1,
        value="One row per assigned course. Teacher totals combine assigned workload across all academic terms.",
    )
    subtitle.font = Font(italic=True, color="666666")
    subtitle.alignment = Alignment(vertical="center")

    header_row = 4
    for column, header in enumerate(headers, start=1):
        cell = worksheet.cell(row=header_row, column=column, value=header)
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill("solid", fgColor="1F4E78")
        cell.alignment = Alignment(wrap_text=True, vertical="center")

    output_row = header_row + 1
    serial_number = 0
    for teacher in teachers:
        teacher_row = dict(teacher)
        teacher_allocations = allocations_by_teacher.get(teacher_row["id"], [])
        rows = teacher_allocations or [None]
        for allocation in rows:
            serial_number += 1
            values = [
                serial_number,
                teacher_row["full_name"],
                teacher_row["employee_code"] or "",
                teacher_row["teacher_department"],
                teacher_row["designation"],
                allocation["course_code"] if allocation else "",
                allocation["course_name"] if allocation else "No courses assigned",
                allocation["academic_year"] if allocation else "",
                allocation["academic_term"] if allocation else "",
                allocation["semester"] if allocation else "",
                allocation["section_name"] if allocation else "",
                allocation["assigned_department"] if allocation else "",
                allocation["course_workload"] if allocation else 0,
                totals_by_teacher.get(teacher_row["id"], 0),
                "Active" if teacher_row["is_active"] else "Inactive",
            ]
            for column, value in enumerate(values, start=1):
                cell = worksheet.cell(row=output_row, column=column, value=value)
                cell.alignment = Alignment(vertical="top", wrap_text=column in {7, 12})
            output_row += 1

    worksheet.freeze_panes = "A5"
    if output_row > header_row + 1:
        report_table = Table(
            displayName="TeacherWorkloadReport",
            ref=f"A{header_row}:O{output_row - 1}",
        )
        report_table.tableStyleInfo = TableStyleInfo(
            name="TableStyleMedium2",
            showFirstColumn=False,
            showLastColumn=False,
            showRowStripes=True,
            showColumnStripes=False,
        )
        worksheet.add_table(report_table)
    else:
        worksheet.auto_filter.ref = f"A{header_row}:O{header_row}"
    worksheet.row_dimensions[header_row].height = 32
    widths = {
        "A": 10, "B": 24, "C": 18, "D": 25, "E": 20, "F": 16, "G": 34,
        "H": 16, "I": 20, "J": 14, "K": 14, "L": 26, "M": 22, "N": 28, "O": 16,
    }
    for column, width in widths.items():
        worksheet.column_dimensions[column].width = width
    worksheet.sheet_view.showGridLines = False

    output = BytesIO()
    workbook.save(output)
    return output.getvalue()


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
