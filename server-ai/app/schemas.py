from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class ApiResponse(BaseModel):
    data: Any
    code: int = 200
    message: str = "success"
    success: bool = True


def success(data: Any) -> dict:
    return {"data": data, "code": 200, "message": "success", "success": True}


def error(data: Any = None, message: str = "error", code: int = 500) -> dict:
    return {"data": data, "code": code, "message": message, "success": False}
