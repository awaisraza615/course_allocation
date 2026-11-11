"""Teacher course preference HTTP endpoints."""

import sqlite3
from typing import Any

from fastapi import APIRouter, HTTPException, Request

from app.services.preference_service import (
    add_teacher_preferences,
    list_course_interested_teachers,
    list_teacher_preferences,
    remove_preference,
    update_preference_priority,
)
from app.services.teacher_service import get_teacher
from app.utils.response import json_request_body, read_json_body


router = APIRouter(tags=["Preferences"])
PREFERENCE_BODY = {
    "type": "object",
    "properties": {
        "course_id": {"type": "integer"},
        "priority": {"type": "integer", "minimum": 1},
        "preferences": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "course_id": {"type": "integer"},
                    "priority": {"type": "integer", "minimum": 1},
                },
                "required": ["course_id"],
            },
        },
    },
}


@router.post(
    "/teachers/{teacher_id}/preferences",
    openapi_extra={"requestBody": json_request_body(PREFERENCE_BODY)},
)
async def add_preferences_route(request: Request, teacher_id: int) -> list[dict[str, Any]]:
    if get_teacher(teacher_id) is None:
        raise HTTPException(status_code=404, detail="Teacher not found")
    try:
        payload = await read_json_body(request)
        preferences = payload.get("preferences")
        if preferences is None:
            preferences = [payload]
        if not isinstance(preferences, list) or not all(
            isinstance(item, dict) for item in preferences
        ):
            raise ValueError("preferences must be a list of objects")
        return add_teacher_preferences(teacher_id, preferences)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except sqlite3.IntegrityError as exc:
        raise HTTPException(status_code=409, detail="Duplicate course or preference priority") from exc


@router.get("/teachers/{teacher_id}/preferences")
async def get_teacher_preferences_route(teacher_id: int) -> list[dict[str, Any]]:
    if get_teacher(teacher_id) is None:
        raise HTTPException(status_code=404, detail="Teacher not found")
    return list_teacher_preferences(teacher_id)


@router.get("/courses/{course_id}/interested-teachers")
async def get_interested_teachers_route(course_id: int) -> list[dict[str, Any]]:
    return list_course_interested_teachers(course_id)


@router.put(
    "/preferences/{preference_id}",
    openapi_extra={
        "requestBody": json_request_body(
            {"type": "object", "properties": {"priority": {"type": "integer", "minimum": 1}},
             "required": ["priority"]}
        )
    },
)
async def update_preference_route(
    request: Request,
    preference_id: int,
) -> dict[str, Any]:
    try:
        payload = await read_json_body(request)
        priority = int(payload["priority"])
        return update_preference_priority(preference_id, priority)
    except (ValueError, KeyError, TypeError) as exc:
        if isinstance(exc, ValueError) and "not found" in str(exc).lower():
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        raise HTTPException(status_code=400, detail="A positive integer priority is required") from exc


@router.delete("/preferences/{preference_id}")
async def delete_preference_route(preference_id: int) -> dict[str, Any]:
    try:
        return remove_preference(preference_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
