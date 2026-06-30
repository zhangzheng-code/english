import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from langchain_core.messages import HumanMessage, AIMessage

from app.llm.context import chat_image_url_var, set_image_url, get_image_url
from app.llm.middleware import dynamic_model_selector

def test_context_vars():
    """测试图片上下文变量设置与读取"""
    set_image_url(None)
    assert get_image_url() is None
    
    set_image_url("data:image/png;base64,123")
    assert get_image_url() == "data:image/png;base64,123"
    
    set_image_url(None)


@pytest.mark.asyncio
async def test_middleware_rewrites_multimodal_request():
    """测试中间件检测到图片 URL 时，重写用户消息为多模态内容契约"""
    # 模拟 LangChain ModelCallRequest
    mock_request = MagicMock()
    # 原始单文本消息
    original_message = HumanMessage(content="Describe this road sign")
    mock_request.messages = [original_message]
    
    # 模拟 handler 逻辑，用于验证最终收到的 request 是否已被重写
    async def mock_handler(req):
        last_msg = req.messages[-1]
        # 验证消息已被重写为多模态 List 结构
        assert isinstance(last_msg.content, list)
        assert len(last_msg.content) == 2
        assert last_msg.content[0] == {"type": "text", "text": "Describe this road sign"}
        assert last_msg.content[1] == {
            "type": "image_url",
            "image_url": {"url": "http://minio/test.png"}
        }
        return "success"

    # 设置当前协程上下文的图片变量
    set_image_url("http://minio/test.png")
    
    try:
        # 运行中间件
        # 拦截 request.override 以便于传递改动过的 messages
        def mock_override(**kwargs):
            mock_req = MagicMock()
            mock_req.messages = kwargs.get("messages", mock_request.messages)
            return mock_req
        mock_request.override = mock_override
        
        # 调用 LangChain middleware 的 awrap_model_call 方法
        await dynamic_model_selector.awrap_model_call(mock_request, mock_handler)
    finally:
        set_image_url(None)


@pytest.mark.asyncio
@patch("app.socketio.sio")
async def test_start_oral_practice_tool(mock_sio):
    """测试 start_oral_practice 工具能正确发送 Socket.IO 邀请"""
    from app.llm.tools import create_oral_practice_tool
    
    user_id = "user_456"
    topic = "Airport check-in"
    role = "Officer"
    
    # 创建工具
    oral_tool = create_oral_practice_tool(user_id)
    assert oral_tool.name == "start_oral_practice"
    
    # 模拟 Socket.IO emit
    mock_sio.emit = AsyncMock()
    
    # 运行工具
    res = await oral_tool.ainvoke({"topic": topic, "role": role})
    
    # 验证返回值与事件广播
    assert "成功" in res
    mock_sio.emit.assert_called_once_with(
        "practiceInvitation",
        {"topic": topic, "role": role},
        room=f"user_{user_id}"
    )
