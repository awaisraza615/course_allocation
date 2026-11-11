"""Course offering HTTP endpoints."""

import sqlite3
from typing import Any

from fastapi import APIRouter, HTTPException, Request

from app.services.offering_service import (
    create_offering,
    delete_pending_offering,
    list_offerings,
)
from app.utils.response import json_request_body, read_json_body


router = APIRouter(tags=["Course Offerings"])


@router.get("/offerings")
async def list_offerings_route(
    section_id: int | None = None,
    department_id: int | None = None,
    academic_term_id: int | None = None,
    pending_only: bool = False,
) -> list[dict[str, Any]]:
    return list_offerings(section_id, department_id, academic_term_id, pending_only)


@router.post(
    "/offerings",
    openapi_extra={
        "requestBody": json_request_body(
            {
                "type": "object",
                "properties": {
                    "course_id": {"type": "integer"},
                    "section_id": {"type": "integer"},
                },
                "required": ["course_id", "section_id"],
            }
        )
    },
)
async def create_offering_route(request: Request) -> dict[str, Any]:
    try:
        return create_offering(await read_json_body(request))
    except ValueError as exc:
        status = 404 if "not found" in str(exc).lower() else 400
        raise HTTPException(status_code=status, detail=str(exc)) from exc
    except sqlite3.IntegrityError as exc:
        raise HTTPException(status_code=409, detail="Course is already offered to this section") from exc


@router.get("/sections/{section_id}/offerings")
async def list_section_offerings_route(section_id: int) -> list[dict[str, Any]]:
    return list_offerings(section_id=section_id)


@router.get("/departments/{department_id}/offerings")
async def list_department_offerings_route(
    department_id: int,
    academic_term_id: int | None = None,
) -> list[dict[str, Any]]:
    return list_offerings(
        department_id=department_id,
        academic_term_id=academic_term_id,
    )


@router.delete("/offerings/{offering_id}")
async def delete_offering_route(offering_id: int) -> dict[str, Any]:
    try:
        return delete_pending_offering(offering_id)
    except ValueError as exc:
        status = 404 if "not found" in str(exc).lower() else 409
        raise HTTPException(status_code=status, detail=str(exc)) from exc
