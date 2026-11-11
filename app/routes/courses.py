"""Course catalog HTTP endpoints."""

import sqlite3
from typing import Any

from fastapi import APIRouter, HTTPException, Request

from app.services.course_service import (
    create_course_record,
    deactivate_course,
    get_course,
    list_courses,
    update_course_record,
)
from app.utils.response import json_request_body, read_json_body


router = APIRouter(tags=["Courses"])
COURSE_BODY = {
    "type": "object",
    "properties": {
        "course_code": {"type": "string", "example": "CSC111"},
        "course_name": {"type": "string", "example": "Object Oriented Programming"},
        "theory_hours": {"type": "integer", "enum": [2, 3]},
        "laboratory_hours": {"type": "integer", "enum": [0, 1]},
        "department_ids": {
            "type": "array",
            "items": {"type": "integer"},
            "minItems": 1,
            "uniqueItems": True,
            "example": [1, 2],
        },
        "department_id": {
            "type": "integer",
            "deprecated": True,
            "description": "Legacy single-department field; use department_ids.",
        },
        "is_active": {"type": "boolean", "default": True},
    },
    "required": [
        "course_code",
        "course_name",
        "theory_hours",
        "laboratory_hours",
        "department_ids",
    ],
}


def _handle_error(error: Exception) -> HTTPException:
    if isinstance(error, sqlite3.IntegrityError):
        return HTTPException(status_code=409, detail="Course code already exists")
    if isinstance(error, ValueError):
        status = 404 if "not found" in str(error).lower() else 400
        return HTTPException(status_code=status, detail=str(error))
    raise error


@router.get("/courses")
async def list_courses_route(
    department_id: int | None = None,
    is_active: bool | None = None,
    search: str | None = None,
    theory_hours: int | None = None,
    laboratory_hours: int | None = None,
) -> list[dict[str, Any]]:
    return list_courses(
        department_id,
        is_active,
        search,
        theory_hours,
        laboratory_hours,
    )


@router.post(
    "/courses",
    openapi_extra={"requestBody": json_request_body(COURSE_BODY)},
)
async def create_course_route(request: Request) -> dict[str, Any]:
    try:
        return create_course_record(await read_json_body(request))
    except (ValueError, sqlite3.IntegrityError) as exc:
        raise _handle_error(exc) from exc


@router.get("/courses/{course_id}")
async def get_course_route(course_id: int) -> dict[str, Any]:
    course = get_course(course_id)
    if course is None:
        raise HTTPException(status_code=404, detail="Course not found")
    return course


@router.put(
    "/courses/{course_id}",
    openapi_extra={"requestBody": json_request_body(COURSE_BODY)},
)
async def update_course_route(request: Request, course_id: int) -> dict[str, Any]:
    try:
        return update_course_record(course_id, await read_json_body(request))
    except (ValueError, sqlite3.IntegrityError) as exc:
        raise _handle_error(exc) from exc


@router.delete("/courses/{course_id}")
async def deactivate_course_route(course_id: int) -> dict[str, Any]:
    try:
        return deactivate_course(course_id)
    except ValueError as exc:
        raise _handle_error(exc) from exc
