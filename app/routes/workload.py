"""Workload lookup endpoints."""

from typing import Any

from fastapi import APIRouter, HTTPException

from app.services.workload_service import (
    get_all_teacher_workloads,
    get_teacher_workload,
)


router = APIRouter(tags=["Workload"])


@router.get("/workload")
async def list_workloads_route(
    term_id: int | None = None,
    department_id: int | None = None,
) -> list[dict[str, Any]]:
    try:
        return get_all_teacher_workloads(term_id, department_id)
    except ValueError as exc:
        status = 404 if "not found" in str(exc).lower() else 400
        raise HTTPException(status_code=status, detail=str(exc)) from exc


@router.get("/workload/limits")
async def workload_limits_route() -> list[dict[str, Any]]:
    from app.database.connection import get_connection

    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT id AS designation_id, name AS designation,
                   standard_workload, maximum_workload
            FROM designations
            WHERE is_active = 1
            ORDER BY name
            """
        ).fetchall()
    return [dict(row) for row in rows]


@router.get("/workload/department/{department_id}")
async def department_workload_route(
    department_id: int,
    term_id: int | None = None,
) -> list[dict[str, Any]]:
    try:
        return get_all_teacher_workloads(term_id, department_id)
    except ValueError as exc:
        status = 404 if "not found" in str(exc).lower() else 400
        raise HTTPException(status_code=status, detail=str(exc)) from exc


@router.get("/workload/{teacher_id}")
async def teacher_workload_route(
    teacher_id: int,
    term_id: int | None = None,
) -> dict[str, Any]:
    try:
        return get_teacher_workload(teacher_id, term_id)
    except ValueError as exc:
        status = 404 if "not found" in str(exc).lower() else 400
        raise HTTPException(status_code=status, detail=str(exc)) from exc
