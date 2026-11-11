"""Tests for teacher workload Excel reporting."""

from io import BytesIO
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from openpyxl import load_workbook

from app.database.connection import get_connection, initialize_database
from app.services.reporting_service import teacher_workload_workbook


class TeacherWorkloadWorkbookTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.database_path = Path(self.temporary_directory.name) / "test.db"
        initialize_database(self.database_path)
        self.connection_patch = patch(
            "app.services.reporting_service.get_connection",
            lambda: get_connection(self.database_path),
        )
        self.connection_patch.start()
        self.addCleanup(self.connection_patch.stop)

        with get_connection(self.database_path) as connection:
            department = connection.execute(
                "INSERT INTO departments (name, code) VALUES (?, ?)",
                ("Computer Science", "CS"),
            )
            term = connection.execute(
                """
                INSERT INTO academic_terms (name, academic_year, semester)
                VALUES (?, ?, ?)
                """,
                ("Fall 2026", "2026-2027", "Fall"),
            )
            section = connection.execute(
                """
                INSERT INTO sections (department_id, academic_term_id, name)
                VALUES (?, ?, ?)
                """,
                (department.lastrowid, term.lastrowid, "A"),
            )
            designation = connection.execute(
                """
                INSERT INTO designations
                    (name, standard_workload, maximum_workload)
                VALUES (?, ?, ?)
                """,
                ("Lecturer", 6, 12),
            )
            teacher = connection.execute(
                """
                INSERT INTO teachers
                    (full_name, employee_code, department_id, designation_id)
                VALUES (?, ?, ?, ?)
                """,
                ("Alice Example", "EMP001", department.lastrowid, designation.lastrowid),
            )
            self.teacher_id = teacher.lastrowid
            no_course_teacher = connection.execute(
                """
                INSERT INTO teachers
                    (full_name, employee_code, department_id, designation_id)
                VALUES (?, ?, ?, ?)
                """,
                ("Bob Example", "EMP002", department.lastrowid, designation.lastrowid),
            )
            course = connection.execute(
                """
                INSERT INTO courses
                    (course_code, course_name, theory_hours, laboratory_hours, department_id)
                VALUES (?, ?, ?, ?, ?)
                """,
                ("CS101", "Introduction to Computing", 3, 0, department.lastrowid),
            )
            offering = connection.execute(
                "INSERT INTO course_offerings (course_id, section_id) VALUES (?, ?)",
                (course.lastrowid, section.lastrowid),
            )
            connection.execute(
                """
                INSERT INTO course_allocations (offering_id, teacher_id, workload_hours)
                VALUES (?, ?, ?)
                """,
                (offering.lastrowid, teacher.lastrowid, 3),
            )
            connection.commit()

    def test_default_workbook_includes_all_teachers_and_allocation_details(self) -> None:
        workbook_bytes = teacher_workload_workbook()
        worksheet = load_workbook(BytesIO(workbook_bytes), read_only=True).active
        rows = list(worksheet.iter_rows(values_only=True))

        self.assertEqual(rows[0][0], "Teacher Course & Workload Report")
        self.assertEqual(rows[3][0:2], ("Sr. No.", "Teacher"))
        self.assertEqual(rows[4][1], "Alice Example")
        self.assertEqual(rows[4][5:12], (
            "CS101",
            "Introduction to Computing",
            "2026-2027",
            "Fall 2026",
            "Fall",
            "A",
            "Computer Science",
        ))
        self.assertEqual(rows[4][12], 3)
        self.assertEqual(rows[4][13], 3)
        self.assertEqual(rows[4][14], "Active")
        self.assertEqual(rows[5][1], "Bob Example")
        self.assertEqual(rows[5][6], "No courses assigned")
        self.assertEqual(rows[5][13], 0)

    def test_workbook_can_be_filtered_to_one_teacher(self) -> None:
        workbook_bytes = teacher_workload_workbook(self.teacher_id)
        worksheet = load_workbook(BytesIO(workbook_bytes), read_only=True).active
        rows = list(worksheet.iter_rows(values_only=True))

        self.assertEqual(len(rows), 5)
        self.assertEqual(rows[4][1], "Alice Example")
        self.assertNotIn("Bob Example", [row[1] for row in rows[4:]])

    def test_missing_teacher_is_reported(self) -> None:
        with self.assertRaisesRegex(ValueError, "Teacher not found"):
            teacher_workload_workbook(999)


if __name__ == "__main__":
    unittest.main()
