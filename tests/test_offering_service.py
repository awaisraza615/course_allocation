"""Tests for course offering operations."""

from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from app.database.connection import get_connection, initialize_database
from app.services.offering_service import delete_pending_offering


class DeletePendingOfferingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.database_path = Path(self.temporary_directory.name) / "test.db"
        initialize_database(self.database_path)
        self.connection_patch = patch(
            "app.services.offering_service.get_connection",
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
                "INSERT INTO academic_terms (name, semester) VALUES (?, ?)",
                ("2026", "Fall"),
            )
            section = connection.execute(
                "INSERT INTO sections (department_id, academic_term_id, name) "
                "VALUES (?, ?, ?)",
                (department.lastrowid, term.lastrowid, "A"),
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
            self.offering_id = offering.lastrowid
            connection.commit()

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def test_deletion_removes_offering_and_its_allocation_history(self) -> None:
        with get_connection(self.database_path) as connection:
            connection.execute(
                """
                INSERT INTO allocation_history (offering_id, action)
                VALUES (?, 'removed')
                """,
                (self.offering_id,),
            )
            connection.commit()

        deleted = delete_pending_offering(self.offering_id)
        self.assertEqual(deleted["id"], self.offering_id)

        with get_connection(self.database_path) as connection:
            offering_count = connection.execute(
                "SELECT COUNT(*) FROM course_offerings WHERE id = ?",
                (self.offering_id,),
            ).fetchone()[0]
            history_count = connection.execute(
                "SELECT COUNT(*) FROM allocation_history WHERE offering_id = ?",
                (self.offering_id,),
            ).fetchone()[0]

        self.assertEqual(offering_count, 0)
        self.assertEqual(history_count, 0)

    def test_pending_offering_without_history_can_be_deleted(self) -> None:
        deleted = delete_pending_offering(self.offering_id)

        self.assertEqual(deleted["id"], self.offering_id)
        with get_connection(self.database_path) as connection:
            offering_count = connection.execute(
                "SELECT COUNT(*) FROM course_offerings WHERE id = ?",
                (self.offering_id,),
            ).fetchone()[0]
        self.assertEqual(offering_count, 0)


if __name__ == "__main__":
    unittest.main()
