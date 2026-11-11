"""Small validation helpers for request payloads."""

from typing import Any


def require_text(value: Any, field_name: str) -> str:
    """Require a non-empty string value."""
    if value is None:
        raise ValueError(f"{field_name} is required")
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string")
    cleaned = value.strip()
    if not cleaned:
        raise ValueError(f"{field_name} cannot be empty")
    return cleaned


def normalize_bool(value: Any) -> int:
    """Convert boolean-like values into SQLite-friendly integers."""
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        if value in (0, 1):
            return value
    raise ValueError("Boolean value must be true or false")


def parse_integer(value: Any, field_name: str) -> int:
    """Require an integer value for IDs and numeric fields."""
    if value is None:
        raise ValueError(f"{field_name} is required")
    if isinstance(value, bool):
        raise ValueError(f"{field_name} must be an integer")
    try:
        number = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must be an integer") from exc
    return number
