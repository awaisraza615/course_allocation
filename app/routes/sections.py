
"""Section HTTP endpoints."""

import sqlite3

from fastapi import APIRouter, HTTPException, Request

from app.services.section_service import (
    create_section_record,
    delete_section_record,
    get_section,
    list_sections,
    permanently_delete_section_record,
    update_section_record,
)
from app.utils.response import json_request_body, read_json_body


router = APIRouter(tags=["Sections"])


def section_schema():
    return {
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "example": "A"
            },
            "department_id": {
                "type": "integer",
                "example": 1
            },
            "academic_term_id": {
                "type": "integer",
                "example": 1
            },
            "is_active": {
                "type": "boolean",
                "default": True,
                "example": True
            }
        },
        "required": [
            "name",
            "department_id",
            "academic_term_id"
        ],
        "additionalProperties": False
    }


@router.get("/sections")
async def list_sections_route() -> list[dict]:
    return list_sections()


@router.get("/sections/{section_id}")
async def get_section_route(section_id: int) -> dict:
    section = get_section(section_id)

    if section is None:
        raise HTTPException(
            status_code=404,
            detail="Section not found"
        )

    return section


@router.post(
    "/sections",
    openapi_extra={
        "requestBody": json_request_body(section_schema())
    }
)
async def create_section_route(request: Request) -> dict:
    try:
        payload = await read_json_body(request)
        return create_section_record(payload)

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc)
        ) from exc

    except sqlite3.IntegrityError as exc:
        raise HTTPException(
            status_code=409,
            detail="Section already exists in this department and term"
        ) from exc


@router.put(
    "/sections/{section_id}",
    openapi_extra={
        "requestBody": json_request_body(section_schema())
    }
)
async def update_section_route(
    request: Request,
    section_id: int
) -> dict:
    try:
        payload = await read_json_body(request)
        return update_section_record(section_id, payload)

    except ValueError as exc:
        if "not found" in str(exc).lower():
            raise HTTPException(
                status_code=404,
                detail=str(exc)
            ) from exc

        raise HTTPException(
            status_code=400,
            detail=str(exc)
        ) from exc

    except sqlite3.IntegrityError as exc:
        raise HTTPException(
            status_code=409,
            detail="Section already exists in this department and term"
        ) from exc


@router.delete("/sections/{section_id}")
async def delete_section_route(section_id: int) -> dict:
    try:
        return delete_section_record(section_id)

    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc)
        ) from exc


@router.delete("/sections/{section_id}/permanent")
async def permanently_delete_section_route(section_id: int) -> dict:
    try:
        return permanently_delete_section_record(section_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except sqlite3.IntegrityError as exc:
        raise HTTPException(
            status_code=409,
            detail="Section could not be permanently deleted because it has related records",
        ) from exc
