"""Tests for SQLite initialization and integrity settings."""

from pathlib import Path
import sqlite3
import tempfile
import unittest

from app.database.connection import get_connection, initialize_database


class DatabaseInitializationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.database_path = Path(self.temporary_directory.name) / "test.db"
        initialize_database(self.database_path)

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def test_initialization_creates_core_tables(self) -> None:
        expected_tables = {
            "departments",
            "academic_terms",
            "sections",
            "designations",
            "teachers",
            "courses",
            "teacher_course_preferences",
            "course_offerings",
            "course_allocations",
            "allocation_history",
        }
        with get_connection(self.database_path) as connection:
            actual_tables = {
                row["name"]
                for row in connection.execute(
                    "SELECT name FROM sqlite_master WHERE type = ?",
                    ("table",),
                )
            }
        self.assertTrue(expected_tables.issubset(actual_tables))

    def test_initialization_is_idempotent(self) -> None:
        initialize_database(self.database_path)
        with get_connection(self.database_path) as connection:
            count = connection.execute(
                "SELECT COUNT(*) AS count FROM sqlite_master "
                "WHERE type = ? AND name = ?",
                ("table", "departments"),
            ).fetchone()["count"]
        self.assertEqual(count, 1)

    def test_foreign_key_constraints_are_enabled_per_connection(self) -> None:
        with get_connection(self.database_path) as connection:
            enabled = connection.execute("PRAGMA foreign_keys").fetchone()[0]
        self.assertEqual(enabled, 1)

    def test_foreign_key_violation_is_rejected(self) -> None:
        with get_connection(self.database_path) as connection:
            with self.assertRaises(sqlite3.IntegrityError):
                connection.execute(
                    "INSERT INTO sections (department_id, academic_term_id, name) "
                    "VALUES (?, ?, ?)",
                    (999, 999, "A"),
                )

    def test_invalid_course_credit_hours_are_rejected(self) -> None:
        with get_connection(self.database_path) as connection:
            department = connection.execute(
                "INSERT INTO departments (name, code) VALUES (?, ?)",
                ("Computer Science", "CS"),
            )
            with self.assertRaises(sqlite3.IntegrityError):
                connection.execute(
                    "INSERT INTO courses "
                    "(course_code, course_name, theory_hours, laboratory_hours, department_id) "
                    "VALUES (?, ?, ?, ?, ?)",
                    ("CS101", "Invalid Course", 4, 2, department.lastrowid),
                )


if __name__ == "__main__":
    unittest.main()
