"""Reusable helpers for request handling and API responses."""

import json
from typing import Any, Sequence

from fastapi import HTTPException, Request


def json_request_body(
    properties: dict[str, dict[str, Any]],
    required: Sequence[str] = (),
) -> dict[str, Any]:
    """Build OpenAPI metadata for JSON bodies handled through Request."""
    if properties.get("type") == "object":
        schema = dict(properties)
    else:
        schema = {"type": "object", "properties": properties}
    if required:
        schema["required"] = list(required)
    return {"content": {"application/json": {"schema": schema}}}


async def read_json_body(request: Request) -> dict[str, Any]:
    """Read and validate a JSON request body."""
    try:
        payload = await request.json()
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail="Request body must be valid JSON") from exc

    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="Request body must be a JSON object")

    return payload
