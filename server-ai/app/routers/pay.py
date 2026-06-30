"""支付宝支付路由（与原 NestJS /api/v1/pay 路径对齐）"""
from __future__ import annotations

from fastapi import APIRouter, Request

from app.deps import CurrentUser, SessionDep
from app.pay_schemas import CreatePayDto
from app.services.pay import create_pay_order, handle_pay_notify, verify_purchase

router = APIRouter(prefix="/pay", tags=["pay"])


@router.post("/create")
async def pay_create(
    body: CreatePayDto,
    db: SessionDep,
    current_user: CurrentUser,
):
    """创建支付订单"""
    return await create_pay_order(db, body.model_dump(by_alias=True), current_user["userId"])


@router.post("/notify")
async def pay_notify(request: Request, db: SessionDep):
    """支付宝异步回调（验签 + 更新状态 + Socket.IO 广播）"""
    form_data = await request.form()
    form_dict = dict(form_data)
    result = await handle_pay_notify(db, form_dict)
    return result


@router.get("/verify")
async def pay_verify(
    course_id: str,
    db: SessionDep,
    current_user: CurrentUser,
):
    """验证用户是否已购买课程"""
    return await verify_purchase(db, course_id, current_user["userId"])
