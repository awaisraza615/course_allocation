
"""Department HTTP endpoints."""

import sqlite3

from fastapi import APIRouter, HTTPException, Request

from app.services.department_service import (
    create_department_record,
    delete_department_record,
    get_department,
    list_department_sections,
    list_departments,
    update_department_record,
)
from app.utils.response import json_request_body, read_json_body


router = APIRouter(tags=["Departments"])


def department_schema():
    return {
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "example": "Artificial Intelligence"
            },
            "code": {
                "type": "string",
                "example": "AI"
            },
            "description": {
                "type": "string",
                "example": "Department of Artificial Intelligence"
            },
            "is_active": {
                "type": "boolean",
                "default": True,
                "example": True
            }
        },
        "required": ["name", "code"]
    }


@router.get("/departments")
async def list_department_routes() -> list[dict]:
    return list_departments()


@router.get("/departments/{department_id}")
async def get_department_route(department_id: int) -> dict:
    department = get_department(department_id)

    if department is None:
        raise HTTPException(
            status_code=404,
            detail="Department not found"
        )

    return department
@router.post(
    "/departments",
    openapi_extra={
        "requestBody": json_request_body(
            department_schema()
        )
    }
)
async def create_department_route(request: Request) -> dict:
    try:
        payload = await read_json_body(request)
        return create_department_record(payload)

    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    except sqlite3.IntegrityError as exc:
        raise HTTPException(
            status_code=409,
            detail="Department code already exists"
        ) from exc


@router.put(
    "/departments/{department_id}",
    openapi_extra={
        "requestBody": json_request_body({
            "type": "object",
            "properties": department_schema()["properties"]
        })
    }
)
async def update_department_route(
    request: Request,
    department_id: int
) -> dict:
    try:
        payload = await read_json_body(request)
        return update_department_record(department_id, payload)

    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    except sqlite3.IntegrityError as exc:
        raise HTTPException(
            status_code=409,
            detail="Department code already exists"
        ) from exc

@router.delete("/departments/{department_id}")
async def delete_department_route(department_id: int) -> dict:
    try:
        return delete_department_record(department_id)

    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc)
        ) from exc


@router.get("/departments/{department_id}/sections")
async def get_department_sections_route(
    department_id: int
) -> list[dict]:
    try:
        return list_department_sections(department_id)

    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc)
        ) from exc
