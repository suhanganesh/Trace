from __future__ import annotations

from datetime import date
from typing import Any

from fastapi import HTTPException


def parse_optional_date(value: str | None, param_name: str) -> date | None:
    if value is None or value.strip() == "":
        return None
    try:
        return date.fromisoformat(value.strip())
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid {param_name}. Use ISO format YYYY-MM-DD.",
        ) from exc


def build_date_match(start: date | None, end: date | None) -> dict[str, Any]:
    if start is None and end is None:
        return {}
    date_filter: dict[str, str] = {}
    if start is not None:
        date_filter["$gte"] = start.isoformat()
    if end is not None:
        date_filter["$lte"] = end.isoformat()
    return {"date": date_filter}


def safe_divide(numerator: float, denominator: float) -> float:
    if denominator == 0:
        return 0.0
    return numerator / denominator


def pct(part: float, whole: float) -> float:
    return round(safe_divide(part, whole) * 100, 4)
