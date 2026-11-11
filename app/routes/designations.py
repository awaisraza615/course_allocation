
"""Designation HTTP endpoints."""

import sqlite3

from fastapi import APIRouter, HTTPException, Request

from app.services.designation_service import (
    create_designation_record,
    delete_designation_record,
    get_designation,
    list_designations,
    update_designation_record,
)
from app.utils.response import json_request_body, read_json_body


router = APIRouter(tags=["Designations"])


def designation_schema():
    return {
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "example": "Lecturer"
            },
            "standard_workload": {
                "type": "integer",
                "minimum": 0,
                "example": 12
            },
            "maximum_workload": {
                "type": "integer",
                "minimum": 0,
                "example": 12
            },
            "is_active": {
                "type": "boolean",
                "default": True,
                "example": True
            }
        },
        "required": [
            "name",
            "standard_workload",
            "maximum_workload"
        ]
    }


@router.get("/designations")
async def list_designations_route():
    return list_designations()


@router.get("/designations/{designation_id}")
async def get_designation_route(designation_id: int):
    designation = get_designation(designation_id)

    if designation is None:
        raise HTTPException(
            status_code=404,
            detail="Designation not found"
        )

    return designation


@router.post(
    "/designations",
    openapi_extra={
        "requestBody": json_request_body(
            designation_schema(),
            required=(
                "name",
                "standard_workload",
                "maximum_workload"
            )
        )
    }
)
async def create_designation_route(request: Request):

    try:
        payload = await read_json_body(request)

        return create_designation_record(payload)

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc)
        ) from exc

    except sqlite3.IntegrityError as exc:
        raise HTTPException(
            status_code=409,
            detail="Designation name already exists"
        ) from exc


@router.put(
    "/designations/{designation_id}",
    openapi_extra={
        "requestBody": json_request_body(
            {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "standard_workload": {
                        "type": "integer",
                        "minimum": 0
                    },
                    "maximum_workload": {
                        "type": "integer",
                        "minimum": 0
                    },
                    "is_active": {"type": "boolean"}
                }
            }
        )
    }
)
async def update_designation_route(
    request: Request,
    designation_id: int
):

    try:
        payload = await read_json_body(request)

        return update_designation_record(
            designation_id,
            payload
        )

    except ValueError as exc:
        status_code = (
            404 if "not found" in str(exc).lower() else 400
        )

        raise HTTPException(
            status_code=status_code,
            detail=str(exc)
        ) from exc

    except sqlite3.IntegrityError as exc:
        raise HTTPException(
            status_code=409,
            detail="Designation name already exists"
        ) from exc


@router.delete("/designations/{designation_id}")
async def delete_designation_route(designation_id: int):

    try:
        return delete_designation_record(designation_id)

    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc)
        ) from exc
