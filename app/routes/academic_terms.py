
"""Academic term HTTP endpoints."""

import sqlite3

from fastapi import APIRouter, HTTPException, Request

from app.services.academic_term_service import (
    activate_academic_term,
    create_academic_term_record,
    get_academic_term,
    list_academic_terms,
    set_academic_term_active,
    update_academic_term_record,
)
from app.utils.response import json_request_body, read_json_body


router = APIRouter(tags=["Academic Terms"])


def academic_term_schema():
    return {
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "example": "Fall 26"
            },
            "semester": {
                "type": "string",
                "example": "3rd"
            },
            "academic_year": {
                "type": "string",
                "example": "2026-2027"
            },
            "is_active": {
                "type": "boolean",
                "default": False
            },
        },
        "required": ["name", "semester"],
        "additionalProperties": False
    }


@router.get("/academic-terms")
async def list_academic_terms_route() -> list[dict]:
    return list_academic_terms()


@router.get("/academic-terms/{term_id}")
async def get_academic_term_route(term_id: int) -> dict:
    term = get_academic_term(term_id)

    if term is None:
        raise HTTPException(
            status_code=404,
            detail="Academic term not found"
        )

    return term


@router.post(
    "/academic-terms",
    openapi_extra={
        "requestBody": json_request_body(academic_term_schema())
    }
)
async def create_academic_term_route(request: Request) -> dict:
    try:
        payload = await read_json_body(request)
        return create_academic_term_record(payload)

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc)
        ) from exc

    except sqlite3.IntegrityError as exc:
        raise HTTPException(
            status_code=409,
            detail="Academic term already exists"
        ) from exc


@router.put(
    "/academic-terms/{term_id}",
    openapi_extra={
        "requestBody": json_request_body(academic_term_schema())
    }
)
async def update_academic_term_route(
    request: Request,
    term_id: int
) -> dict:
    try:
        payload = await read_json_body(request)
        return update_academic_term_record(term_id, payload)

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
            detail="Academic term already exists"
        ) from exc


@router.put("/academic-terms/{term_id}/activate")
async def activate_academic_term_route(term_id: int) -> dict:
    try:
        return activate_academic_term(term_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.put("/academic-terms/{term_id}/deactivate")
async def deactivate_academic_term_route(term_id: int) -> dict:
    try:
        return set_academic_term_active(term_id, False)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
