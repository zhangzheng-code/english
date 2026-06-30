"""支付宝支付服务（复刻原 NestJS PayService）"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta

from cuid import cuid
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.schemas import error, success
from app.socketio import emit_payment_success

logger = logging.getLogger(__name__)


def _create_trade_no() -> str:
    """生成订单编号（前缀 XM + 12位随机）"""
    import nanoid
    return f"XM-{nanoid.generate(size=12)}"


def _get_alipay_client():
    """延迟初始化 AlipaySdk 客户端"""
    from alipay_sdk_python.alipay import Alipay
    return Alipay(
        appid=settings.alipay_app_id,
        app_private_key=settings.alipay_private_key,
        alipay_public_key=settings.alipay_public_key,
        gateway=settings.alipay_gateway,
    )


async def create_pay_order(db: AsyncSession, body: dict, user_id: str) -> dict:
    """
    创建支付订单：
    1. 检查是否已购买
    2. 创建 PaymentRecord（未支付）
    3. 调用支付宝 SDK 生成支付 URL
    """
    course_id = body.get("courseId")
    subject = body.get("subject", "课程购买")
    total_amount = body.get("total_amount", "0.01")
    pay_body = body.get("body", "")

    # 检查是否已购买（使用原生 SQL 避免模型依赖）
    from sqlalchemy import text
    result = await db.execute(
        text('SELECT id FROM "CourseRecord" WHERE "userId" = :uid AND "courseId" = :cid'),
        {"uid": user_id, "cid": course_id},
    )
    if result.first():
        return error(message="您已经购买过该课程")

    # 创建订单
    out_trade_no = _create_trade_no()
    now = datetime.utcnow()
    expire_time = now + timedelta(minutes=30)

    await db.execute(
        text("""
            INSERT INTO "PaymentRecord" (id, "userId", "outTradeNo", amount, subject, body, "tradeStatus", "createdAt", "updatedAt")
            VALUES (:id, :uid, :out_trade_no, :amount, :subject, :body, 'NOT_PAY', :now, :now)
        """),
        {
            "id": cuid(),
            "uid": user_id,
            "out_trade_no": out_trade_no,
            "amount": total_amount,
            "subject": subject,
            "body": pay_body,
            "now": now,
        },
    )
    await db.commit()

    # 生成支付宝支付 URL
    try:
        alipay = _get_alipay_client()
        pay_url = alipay.api_alipay_trade_page_pay(
            out_trade_no=out_trade_no,
            total_amount=total_amount,
            subject=subject,
            body=json.dumps({"courseId": course_id, "userId": user_id}),
            product_code="FAST_INSTANT_TRADE_PAY",
            time_expire=expire_time.strftime("%Y-%m-%d %H:%M:%S"),
            return_url=settings.alipay_notify_url,
            notify_url=f"{settings.alipay_notify_url}/api/v1/pay/notify",
        )
    except Exception as e:
        logger.error(f"支付宝 SDK 调用失败: {e}")
        # SDK 不可用时返回模拟 URL（开发环境）
        pay_url = f"https://openapi.alipay.com/gateway.do?out_trade_no={out_trade_no}"

    return success({
        "payUrl": pay_url,
        "timeExpire": int(expire_time.timestamp() * 1000),
    })


async def handle_pay_notify(db: AsyncSession, form_data: dict) -> str:
    """
    支付宝异步回调：
    1. 验签
    2. 更新 PaymentRecord 状态
    3. 创建 CourseRecord
    4. Socket.IO 广播支付成功
    """
    try:
        # 验签
        alipay = _get_alipay_client()
        sign = form_data.get("sign", "")
        sign_type = form_data.get("sign_type", "RSA2")

        # 移除 sign 和 sign_type 后验签
        verify_data = {k: v for k, v in form_data.items() if k not in ("sign", "sign_type")}
        is_valid = alipay.verify(verify_data, sign)

        if not is_valid:
            logger.warning("支付宝回调验签失败")
            return "fail"

        # 检查交易状态
        trade_status = form_data.get("trade_status", "")
        if trade_status not in ("TRADE_SUCCESS", "TRADE_FINISHED"):
            return "success"

        out_trade_no = form_data.get("out_trade_no", "")
        trade_no = form_data.get("trade_no", "")
        gmt_payment = form_data.get("gmt_payment", "")

        # 解析 body 中的 courseId 和 userId
        body_str = form_data.get("body", "{}")
        try:
            body_data = json.loads(body_str)
        except json.JSONDecodeError:
            body_data = {}

        course_id = body_data.get("courseId", "")
        user_id = body_data.get("userId", "")

        if not out_trade_no or not user_id:
            logger.warning("支付宝回调缺少必要参数")
            return "fail"

        # 更新 PaymentRecord
        from sqlalchemy import text
        pay_time = datetime.strptime(gmt_payment, "%Y-%m-%d %H:%M:%S") if gmt_payment else datetime.utcnow()

        await db.execute(
            text("""
                UPDATE "PaymentRecord"
                SET "tradeNo" = :trade_no, "tradeStatus" = 'TRADE_SUCCESS', "sendPayTime" = :pay_time, "updatedAt" = :now
                WHERE "outTradeNo" = :out_trade_no
            """),
            {
                "trade_no": trade_no,
                "pay_time": pay_time,
                "now": datetime.utcnow(),
                "out_trade_no": out_trade_no,
            },
        )

        # 获取 PaymentRecord id
        result = await db.execute(
            text('SELECT id FROM "PaymentRecord" WHERE "outTradeNo" = :out_trade_no'),
            {"out_trade_no": out_trade_no},
        )
        payment_record = result.first()

        if payment_record and course_id:
            # 创建 CourseRecord
            await db.execute(
                text("""
                    INSERT INTO "CourseRecord" (id, "userId", "courseId", "isPurchased", "paymentRecordId", "createdAt", "updatedAt")
                    VALUES (:id, :uid, :cid, true, :pid, :now, :now)
                    ON CONFLICT ("userId", "courseId") DO NOTHING
                """),
                {
                    "id": cuid(),
                    "uid": user_id,
                    "cid": course_id,
                    "pid": payment_record[0],
                    "now": datetime.utcnow(),
                },
            )

        await db.commit()

        # Socket.IO 广播支付成功
        await emit_payment_success(user_id)

        logger.info(f"支付成功: out_trade_no={out_trade_no}, user={user_id}")
        return "success"

    except Exception as e:
        logger.error(f"支付回调处理失败: {e}")
        return "fail"


async def verify_purchase(db: AsyncSession, course_id: str, user_id: str) -> dict:
    """验证用户是否已购买课程"""
    from sqlalchemy import text
    result = await db.execute(
        text("""
            SELECT cr.id FROM "CourseRecord" cr
            JOIN "PaymentRecord" pr ON cr."paymentRecordId" = pr.id
            WHERE cr."userId" = :uid AND cr."courseId" = :cid AND pr."tradeStatus" = 'TRADE_SUCCESS'
        """),
        {"uid": user_id, "cid": course_id},
    )
    return success({"purchased": result.first() is not None})
