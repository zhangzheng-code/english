"""Socket.IO 实时通信（复刻原 NestJS SocketGateway）"""
from __future__ import annotations

import logging
import io

import socketio

logger = logging.getLogger(__name__)

# 创建 AsyncServer，与 FastAPI 共享同一端口
sio = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins="*",
    logger=False,
)


@sio.event
async def connect(sid, environ, auth):
    """
    客户端连接时，从 auth 载荷或 query string 中解析 userId 并加入专属房间。
    前端连接方式一: io.connect('http://host', { auth: { token: 'xxx' } })
    前端连接方式二（开发兼容）: io.connect('http://host', { query: { userId: 'xxx' } })
    """
    from app.security import decode_token
    import jwt
    import socketio

    token = None
    userId = None

    # 1. 优先尝试从 auth 中提取 JWT Token 进行身份验证
    if isinstance(auth, dict):
        token = auth.get("token") or auth.get("Authorization")
    
    if token:
        if token.startswith("Bearer "):
            token = token[7:]
        try:
            payload = decode_token(token)
            userId = payload.get("userId")
            logger.info(f"Socket.IO: JWT auth successful for sid={sid}, userId={userId}")
        except (jwt.ExpiredSignatureError, jwt.InvalidTokenError) as e:
            logger.warning(f"Socket.IO: JWT validation failed: {e}")

    # 2. 如果无 token 或校验失败，检测 URL Query string 中是否含有 userId (开发环境容灾放行)
    if not userId:
        from urllib.parse import parse_qsl
        query_string = environ.get("QUERY_STRING", "")
        if isinstance(query_string, bytes):
            query_string = query_string.decode("utf-8", errors="ignore")
        params = dict(parse_qsl(query_string))
        userId = params.get("userId", "")
        if userId:
            logger.warning(f"Socket.IO: Bypassed JWT validation, using fallback query userId={userId} for sid={sid}")

    # 3. 进入对应房间或拒绝连接
    if userId:
        await sio.enter_room(sid, f"user_{userId}")
        logger.info(f"Socket.IO: sid={sid} joined room user_{userId}")
    else:
        logger.error(f"Socket.IO: Connection refused for sid={sid}. Missing valid JWT token or query userId.")
        raise socketio.exceptions.ConnectionRefusedError("Authentication failed")



@sio.event
async def disconnect(sid):
    logger.info(f"Socket.IO: sid={sid} disconnected")


async def emit_payment_success(userId: str):
    """支付成功后，向对应用户的房间广播事件（支持 NestJS 与新版 API 双重协议）"""
    await sio.emit("paymentSuccess", userId, room=f"user_{userId}")
    await sio.emit("pay_success", {"success": True}, room=f"user_{userId}")
    logger.info(f"Socket.IO: emitted paymentSuccess and pay_success to user_{userId}")


# 存放各个连接会话的音频字节缓冲
audio_buffers: dict[str, io.BytesIO] = {}


@sio.on("audio_chunk")
async def handle_audio_chunk(sid, chunk: bytes):
    """追加接收到的 PCM / WebM 二进制音频切片"""
    import io
    if sid not in audio_buffers:
        audio_buffers[sid] = io.BytesIO()
    audio_buffers[sid].write(chunk)


@sio.on("audio_end")
async def handle_audio_end(sid, payload: dict = None):
    """音频输入结束，执行 Whisper ASR 与音素发音纠音分析"""
    import io
    if sid not in audio_buffers:
        logger.warning(f"Socket.IO: sid={sid} sent audio_end but no buffer found")
        return

    # 提取音频缓冲并释放
    audio_stream = audio_buffers.pop(sid)
    audio_bytes = audio_stream.getvalue()

    from app.services.audio import transcribe_audio, evaluate_pronunciation

    # 1. 语音转文字 (ASR)
    asr_text = await transcribe_audio(audio_bytes)

    # 2. 如果携带了评测标准目标词，执行发音纠偏评估
    evaluation = None
    target_word = (payload or {}).get("targetWord")
    if target_word:
        evaluation = evaluate_pronunciation(target_word, asr_text)

    # 3. 将 ASR 识别结果和纠音报告返回客户端
    await sio.emit(
        "audio_transcribed",
        {
            "text": asr_text,
            "evaluation": evaluation
        },
        room=sid
    )
    logger.info(f"Socket.IO: sent audio_transcribed to sid={sid}, text={asr_text}")

