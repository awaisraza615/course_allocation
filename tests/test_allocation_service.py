"""Tests for allocation planning and manual allocation."""

from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from app.database.connection import get_connection, initialize_database
from app.services.allocation_service import (
    create_manual_allocation,
    execute_automatic_allocations,
    list_allocations,
    reassign_allocation,
    _pending_plans,
)


class AllocationServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        database_path = Path(self.temporary_directory.name) / "test.db"
        self.database_path = database_path
        initialize_database(database_path)
        self.connection_patch = patch(
            "app.services.allocation_service.get_connection",
            lambda: get_connection(database_path),
        )
        self.connection_patch.start()
        self.addCleanup(self.connection_patch.stop)

        with get_connection(database_path) as connection:
            primary_department = connection.execute(
                "INSERT INTO departments (name, code) VALUES (?, ?)",
                ("Primary Department", "PRI"),
            )
            self.primary_department_id = primary_department.lastrowid
            section_department = connection.execute(
                "INSERT INTO departments (name, code) VALUES (?, ?)",
                ("Offering Department", "OFF"),
            )
            self.section_department_id = section_department.lastrowid
            term = connection.execute(
                "INSERT INTO academic_terms (name, semester) VALUES (?, ?)",
                ("2026", "Fall"),
            )
            self.term_id = term.lastrowid
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
                    (full_name, department_id, designation_id)
                VALUES (?, ?, ?)
                """,
                (
                    "Test Teacher",
                    self.section_department_id,
                    designation.lastrowid,
                ),
            )
            self.teacher_id = teacher.lastrowid
            second_teacher = connection.execute(
                """
                INSERT INTO teachers
                    (full_name, department_id, designation_id)
                VALUES (?, ?, ?)
                """,
                (
                    "Second Teacher",
                    self.section_department_id,
                    designation.lastrowid,
                ),
            )
            self.second_teacher_id = second_teacher.lastrowid
            connection.commit()

        self.offering_ids: list[int] = []

    def add_offering(self, index: int) -> int:
        with get_connection(self.database_path) as connection:
            section = connection.execute(
                """
                INSERT INTO sections (department_id, academic_term_id, name)
                VALUES (?, ?, ?)
                """,
                (self.section_department_id, self.term_id, f"S{index}"),
            )
            course = connection.execute(
                """
                INSERT INTO courses
                    (course_code, course_name, theory_hours, laboratory_hours, department_id)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    f"PRI{index:03d}",
                    f"Cross-listed Course {index}",
                    3,
                    0,
                    self.primary_department_id,
                ),
            )
            connection.executemany(
                """
                INSERT INTO course_departments (course_id, department_id)
                VALUES (?, ?)
                """,
                [
                    (course.lastrowid, self.primary_department_id),
                    (course.lastrowid, self.section_department_id),
                ],
            )
            connection.execute(
                """
                INSERT INTO teacher_course_preferences (teacher_id, course_id, priority)
                VALUES (?, ?, ?)
                """,
                (self.teacher_id, course.lastrowid, index),
            )
            offering = connection.execute(
                """
                INSERT INTO course_offerings (course_id, section_id)
                VALUES (?, ?)
                """,
                (course.lastrowid, section.lastrowid),
            )
            connection.commit()
        offering_id = int(offering.lastrowid)
        self.offering_ids.append(offering_id)
        return offering_id

    def test_cross_department_offering_uses_section_department(self) -> None:
        offering_id = self.add_offering(1)

        with get_connection(self.database_path) as connection:
            allocations, unallocated = _pending_plans(connection, self.term_id)

        self.assertEqual(unallocated, [])
        self.assertEqual(len(allocations), 1)
        self.assertEqual(
            allocations[0]["department_name"],
            "Offering Department",
        )

        with get_connection(self.database_path) as connection:
            connection.execute(
                """
                INSERT INTO course_allocations
                    (offering_id, teacher_id, workload_hours)
                VALUES (?, ?, ?)
                """,
                (offering_id, self.teacher_id, 3),
            )
            connection.commit()

        current_allocations = list_allocations()
        self.assertEqual(len(current_allocations), 1)
        self.assertEqual(
            current_allocations[0]["course_department"],
            "Offering Department",
        )

    def test_automatic_allocation_stops_at_12_and_manual_can_exceed_it(self) -> None:
        for index in range(1, 7):
            self.add_offering(index)

        result = execute_automatic_allocations(self.term_id)

        self.assertEqual(len(result["allocations"]), 4)
        self.assertEqual(len(result["unallocated"]), 2)
        self.assertIn("12-hour automatic allocation limit", result["unallocated"][0]["reason"])

        manual_allocation = create_manual_allocation(
            {
                "offering_id": self.offering_ids[4],
                "teacher_id": self.teacher_id,
            }
        )
        self.assertEqual(manual_allocation["teacher_id"], self.teacher_id)

        allocation_for_second_teacher = create_manual_allocation(
            {
                "offering_id": self.offering_ids[5],
                "teacher_id": self.second_teacher_id,
                "override_preference": True,
            }
        )
        reassigned = reassign_allocation(
            allocation_for_second_teacher["allocation_id"],
            {
                "teacher_id": self.teacher_id,
                "override_preference": True,
            },
        )
        self.assertEqual(reassigned["teacher_id"], self.teacher_id)
        self.assertEqual(len(list_allocations()), 6)

    def test_automatic_allocation_balances_load_before_preference_rank(self) -> None:
        for index in range(1, 5):
            offering_id = self.add_offering(index)
            with get_connection(self.database_path) as connection:
                course_id = connection.execute(
                    "SELECT course_id FROM course_offerings WHERE id = ?",
                    (offering_id,),
                ).fetchone()["course_id"]
                connection.execute(
                    """
                    INSERT INTO teacher_course_preferences
                        (teacher_id, course_id, priority)
                    VALUES (?, ?, ?)
                    """,
                    (self.second_teacher_id, course_id, index),
                )
                connection.commit()

        result = execute_automatic_allocations(self.term_id)

        self.assertEqual(len(result["allocations"]), 4)
        workload_by_teacher: dict[int, int] = {}
        for allocation in result["allocations"]:
            teacher_id = allocation["teacher_id"]
            workload_by_teacher[teacher_id] = (
                workload_by_teacher.get(teacher_id, 0)
                + allocation["workload_hours"]
            )
        self.assertEqual(
            workload_by_teacher,
            {self.teacher_id: 6, self.second_teacher_id: 6},
        )
        self.assertTrue(all(hours <= 12 for hours in workload_by_teacher.values()))


if __name__ == "__main__":
    unittest.main()
