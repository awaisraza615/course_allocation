"""Reporting endpoints."""

from typing import Any

from fastapi import APIRouter, HTTPException

from app.services.allocation_service import list_allocation_history
from app.services.reporting_service import (
    department_report,
    section_report,
    teacher_report,
    unallocated_report,
)


router = APIRouter(prefix="/reports", tags=["Reports"])


def _not_found_or_bad_request(error: ValueError) -> HTTPException:
    status = 404 if "not found" in str(error).lower() else 400
    return HTTPException(status_code=status, detail=str(error))


@router.get("/teacher/{teacher_id}")
async def teacher_report_route(
    teacher_id: int,
    term_id: int | None = None,
) -> dict[str, Any]:
    try:
        return teacher_report(teacher_id, term_id)
    except ValueError as exc:
        raise _not_found_or_bad_request(exc) from exc


@router.get("/department/{department_id}")
async def department_report_route(
    department_id: int,
    term_id: int | None = None,
) -> dict[str, Any]:
    try:
        return department_report(department_id, term_id)
    except ValueError as exc:
        raise _not_found_or_bad_request(exc) from exc


@router.get("/section/{section_id}")
async def section_report_route(section_id: int) -> dict[str, Any]:
    try:
        return section_report(section_id)
    except ValueError as exc:
        raise _not_found_or_bad_request(exc) from exc


@router.get("/unallocated")
async def unallocated_report_route(term_id: int | None = None) -> list[dict[str, Any]]:
    try:
        return unallocated_report(term_id)
    except ValueError as exc:
        raise _not_found_or_bad_request(exc) from exc


@router.get("/history")
async def history_report_route(term_id: int | None = None) -> list[dict[str, Any]]:
    return list_allocation_history(term_id)
