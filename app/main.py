"""FastAPI application entry point."""

from contextlib import asynccontextmanager
import logging
import sqlite3
from typing import AsyncIterator

from fastapi import FastAPI, HTTPException

from app.database.connection import get_connection, initialize_database
from app.routes.academic_terms import router as academic_terms_router
from app.routes.allocations import router as allocations_router
from app.routes.courses import router as courses_router
from app.routes.departments import router as departments_router
from app.routes.designations import router as designations_router
from app.routes.offerings import router as offerings_router
from app.routes.preferences import router as preferences_router
from app.routes.reports import router as reports_router
from app.routes.sections import router as sections_router
from app.routes.teachers import router as teachers_router
from app.routes.workload import router as workload_router

from pathlib import Path

from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles


logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    initialize_database()
    yield


app = FastAPI(
    title="University Course & Teacher Allocation Management System",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(departments_router)
app.include_router(academic_terms_router)
app.include_router(sections_router)
app.include_router(designations_router)
app.include_router(teachers_router)
app.include_router(courses_router)
app.include_router(preferences_router)
app.include_router(offerings_router)
app.include_router(workload_router)
app.include_router(allocations_router)
app.include_router(reports_router)


BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"

app.mount(
    "/static",
    StaticFiles(directory=STATIC_DIR),
    name="static",
)

@app.get("/", include_in_schema=False)
async def frontend():
    return FileResponse(STATIC_DIR / "index.html")

@app.get("/health")
def health_check() -> dict[str, str]:
    """Report that the API process is responsive."""
    return {"status": "ok"}


@app.get("/health/database")
def database_health_check() -> dict[str, str]:
    """Verify that the application can query its SQLite database."""
    try:
        with get_connection() as connection:
            connection.execute("SELECT 1").fetchone()
    except sqlite3.Error as error:
        logger.exception("SQLite health check failed")
        raise HTTPException(
            status_code=503,
            detail="Database unavailable",
        ) from error
    return {"status": "ok", "database": "connected"}

