"""支付相关 Pydantic Schema"""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class CreatePayDto(BaseModel):
    """创建支付订单请求"""
    subject: str          # 订单标题
    body: str             # 附加信息
    total_amount: str = Field(alias="total_amount")  # 订单金额
    course_id: str = Field(alias="courseId")          # 课程ID

    model_config = {"populate_by_name": True}
