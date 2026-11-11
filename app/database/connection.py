"""Centralized SQLite connection and initialization helpers."""

from contextlib import contextmanager
from pathlib import Path
import os
import sqlite3
from typing import Iterator


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = Path(__file__).with_name("schema.sql")


def get_database_path() -> Path:
    """Return the configured database path or the project-local default."""
    configured_path = os.environ.get("DATABASE_PATH")
    if configured_path:
        return Path(configured_path).expanduser().resolve()
    return PROJECT_ROOT / "university.db"


def create_connection(database_path: Path | None = None) -> sqlite3.Connection:
    """Create a SQLite connection with row access and foreign keys enabled."""
    path = database_path or get_database_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


@contextmanager
def get_connection(database_path: Path | None = None) -> Iterator[sqlite3.Connection]:
    """Yield a connection and always close it after use."""
    connection = create_connection(database_path)
    try:
        yield connection
    finally:
        connection.close()


def initialize_database(database_path: Path | None = None) -> None:
    """Create the database tables from the packaged SQL schema."""
    schema = SCHEMA_PATH.read_text(encoding="utf-8")
    with get_connection(database_path) as connection:
        connection.executescript(schema)
        _add_column_if_missing(
            connection,
            "academic_terms",
            "academic_year",
            "TEXT NOT NULL DEFAULT ''",
        )
        _add_column_if_missing(
            connection,
            "academic_terms",
            "is_active",
            "INTEGER NOT NULL DEFAULT 0 CHECK (is_active IN (0, 1))",
        )
        _add_column_if_missing(
            connection,
            "academic_terms",
            "created_at",
            "TEXT",
        )
        _add_column_if_missing(
            connection,
            "course_allocations",
            "workload_hours",
            "INTEGER NOT NULL DEFAULT 0 CHECK (workload_hours >= 0)",
        )
        _add_column_if_missing(
            connection,
            "course_allocations",
            "standard_workload_snapshot",
            "INTEGER",
        )
        _add_column_if_missing(
            connection,
            "course_allocations",
            "maximum_workload_snapshot",
            "INTEGER",
        )
        _add_column_if_missing(
            connection,
            "course_allocations",
            "preference_priority",
            "INTEGER",
        )
        _add_column_if_missing(
            connection,
            "allocation_history",
            "workload_hours",
            "INTEGER",
        )
        _add_column_if_missing(
            connection,
            "allocation_history",
            "standard_workload_snapshot",
            "INTEGER",
        )
        _add_column_if_missing(
            connection,
            "allocation_history",
            "maximum_workload_snapshot",
            "INTEGER",
        )
        connection.execute(
            "UPDATE academic_terms SET academic_year = name "
            "WHERE academic_year = ''"
        )
        connection.execute(
            "UPDATE academic_terms SET created_at = CURRENT_TIMESTAMP "
            "WHERE created_at IS NULL"
        )
        connection.execute(
            """
            INSERT OR IGNORE INTO course_departments (course_id, department_id)
            SELECT id, department_id FROM courses
            """
        )
        connection.commit()


def _add_column_if_missing(
    connection: sqlite3.Connection,
    table_name: str,
    column_name: str,
    column_definition: str,
) -> None:
    columns = {
        row["name"]
        for row in connection.execute(f"PRAGMA table_info({table_name})")
    }
    if column_name not in columns:
        connection.execute(
            f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_definition}"
        )
