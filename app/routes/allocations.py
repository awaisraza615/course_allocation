"""Automatic and manual allocation HTTP endpoints."""

from typing import Any

from fastapi import APIRouter, HTTPException, Request

from app.services.allocation_service import (
    create_manual_allocation,
    execute_automatic_allocations,
    list_allocation_history,
    list_allocations,
    preview_automatic_allocations,
    reassign_allocation,
    remove_allocation,
)
from app.utils.response import json_request_body, read_json_body


router = APIRouter(tags=["Allocations"])
TERM_BODY = {
    "type": "object",
    "properties": {"term_id": {"type": "integer", "nullable": True}},
}
MANUAL_BODY = {
    "type": "object",
    "properties": {
        "offering_id": {"type": "integer"},
        "teacher_id": {"type": "integer"},
        "override_preference": {"type": "boolean", "default": False},
        "reason": {"type": "string"},
    },
    "required": ["offering_id", "teacher_id"],
}


def _error(error: ValueError) -> HTTPException:
    message = str(error)
    status = 404 if "not found" in message.lower() else (
        409 if any(word in message.lower() for word in ("already", "exceeds", "cannot")) else 400
    )
    return HTTPException(status_code=status, detail=message)


@router.post(
    "/allocations/auto/preview",
    openapi_extra={"requestBody": json_request_body(TERM_BODY)},
)
async def preview_auto_route(request: Request) -> dict[str, Any]:
    try:
        payload = await read_json_body(request)
        return preview_automatic_allocations(payload.get("term_id"))
    except ValueError as exc:
        raise _error(exc) from exc


@router.post(
    "/allocations/auto/execute",
    openapi_extra={"requestBody": json_request_body(TERM_BODY)},
)
async def execute_auto_route(request: Request) -> dict[str, Any]:
    try:
        payload = await read_json_body(request)
        return execute_automatic_allocations(payload.get("term_id"))
    except ValueError as exc:
        raise _error(exc) from exc


@router.post(
    "/allocations/manual",
    openapi_extra={"requestBody": json_request_body(MANUAL_BODY)},
)
async def manual_allocation_route(request: Request) -> dict[str, Any]:
    try:
        return create_manual_allocation(await read_json_body(request))
    except ValueError as exc:
        raise _error(exc) from exc


@router.get("/allocations")
async def list_allocations_route(
    term_id: int | None = None,
    teacher_id: int | None = None,
    department_id: int | None = None,
    section_id: int | None = None,
) -> list[dict[str, Any]]:
    return list_allocations(term_id, teacher_id, department_id, section_id)


@router.put(
    "/allocations/{allocation_id}",
    openapi_extra={
        "requestBody": json_request_body(
            {
                "type": "object",
                "properties": {
                    "teacher_id": {"type": "integer"},
                    "override_preference": {"type": "boolean", "default": False},
                    "reason": {"type": "string"},
                },
                "required": ["teacher_id"],
            }
        )
    },
)
async def reassign_allocation_route(
    request: Request,
    allocation_id: int,
) -> dict[str, Any]:
    try:
        return reassign_allocation(allocation_id, await read_json_body(request))
    except ValueError as exc:
        raise _error(exc) from exc


@router.delete("/allocations/{allocation_id}")
async def remove_allocation_route(allocation_id: int, reason: str | None = None) -> dict[str, Any]:
    try:
        return remove_allocation(allocation_id, reason)
    except ValueError as exc:
        raise _error(exc) from exc


@router.get("/allocations/history")
async def allocation_history_route(term_id: int | None = None) -> list[dict[str, Any]]:
    return list_allocation_history(term_id)
