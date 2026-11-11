"""Teacher profile HTTP endpoints."""

import sqlite3
from typing import Any

from fastapi import APIRouter, HTTPException, Query, Request

from app.services.teacher_service import (
    create_teacher_record,
    deactivate_teacher,
    get_teacher,
    list_teachers,
    teacher_allocated_courses,
    update_teacher_record,
)
from app.utils.response import json_request_body, read_json_body


router = APIRouter(tags=["Teachers"])
TEACHER_BODY = {
    "type": "object",
    "properties": {
        "full_name": {"type": "string", "example": "Awais Raza"},
        "employee_code": {"type": "string", "nullable": True, "example": "EMP001"},
        "department_id": {"type": "integer", "example": 1},
        "designation_id": {"type": "integer", "example": 1},
        "is_active": {"type": "boolean", "default": True},
    },
    "required": ["full_name", "department_id", "designation_id"],
}


def _handle_error(error: Exception) -> HTTPException:
    if isinstance(error, sqlite3.IntegrityError):
        return HTTPException(status_code=409, detail="Employee code already exists")
    if isinstance(error, ValueError):
        status = 404 if "not found" in str(error).lower() else 400
        return HTTPException(status_code=status, detail=str(error))
    raise error


@router.get("/teachers")
async def list_teachers_route(
    department_id: int | None = None,
    is_active: bool | None = None,
) -> list[dict[str, Any]]:
    return list_teachers(department_id, is_active)


@router.post(
    "/teachers",
    openapi_extra={"requestBody": json_request_body(TEACHER_BODY)},
)
async def create_teacher_route(request: Request) -> dict[str, Any]:
    try:
        return create_teacher_record(await read_json_body(request))
    except (ValueError, sqlite3.IntegrityError) as exc:
        raise _handle_error(exc) from exc


@router.get("/teachers/{teacher_id}")
async def get_teacher_route(teacher_id: int) -> dict[str, Any]:
    teacher = get_teacher(teacher_id)
    if teacher is None:
        raise HTTPException(status_code=404, detail="Teacher not found")
    return teacher


@router.put(
    "/teachers/{teacher_id}",
    openapi_extra={"requestBody": json_request_body(TEACHER_BODY)},
)
async def update_teacher_route(request: Request, teacher_id: int) -> dict[str, Any]:
    try:
        return update_teacher_record(teacher_id, await read_json_body(request))
    except (ValueError, sqlite3.IntegrityError) as exc:
        raise _handle_error(exc) from exc


@router.delete("/teachers/{teacher_id}")
async def deactivate_teacher_route(teacher_id: int) -> dict[str, Any]:
    try:
        return deactivate_teacher(teacher_id)
    except ValueError as exc:
        raise _handle_error(exc) from exc


@router.get("/teachers/{teacher_id}/allocated-courses")
async def teacher_allocated_courses_route(teacher_id: int) -> list[dict[str, Any]]:
    try:
        return teacher_allocated_courses(teacher_id)
    except ValueError as exc:
        raise _handle_error(exc) from exc
