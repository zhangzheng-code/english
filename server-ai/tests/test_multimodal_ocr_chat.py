import pytest
import io, base64
from PIL import Image, ImageDraw
from unittest.mock import patch
from langchain_core.tools import tool
from app.services.chat import stream_chat
from app.llm.context import set_image_url, set_model_type

@tool
def mock_search_tool(query: str) -> str:
    """Mock search tool"""
    return "mock result"

def create_sample_image_base64():
    img = Image.new('RGB', (400, 150), color=(255, 255, 255))
    d = ImageDraw.Draw(img)
    d.text((20, 40), "STOP Ahead\nRoad construction ahead 500m", fill=(255, 0, 0))
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()

@pytest.mark.asyncio
@patch("app.services.chat.get_checkpoint")
@patch("app.llm.tools.create_search_tool")
async def test_repro_multimodal(mock_create_search, mock_get_checkpoint):
    mock_get_checkpoint.return_value = None
    mock_create_search.return_value = mock_search_tool

    sample_img_url = create_sample_image_base64()
    body = {
        "role": "normal",
        "content": "帮我翻译并分析一下这张图片里的内容。",
        "userId": "test_user_123",
        "deepThink": False,
        "webSearch": False,
        "imageUrl": sample_img_url
    }
    
    set_model_type("flash")
    set_image_url(body["imageUrl"])

    chunks = []
    full_reply = ""
    try:
        async for chunk in stream_chat(body):
            chunks.append(chunk)
            content = chunk.get("content", "")
            full_reply += content
            print("Received chunk:", content, end="", flush=True)
        print("\n\nFull AI Reply:", full_reply)
        assert len(full_reply) > 0
        # 确保 AI 识别并翻译了图片中 OCR 提取出的 STOP Ahead 内容
        assert "STOP" in full_reply or "停止" in full_reply or "前方" in full_reply or "道路" in full_reply or "施工" in full_reply
    except Exception as e:
        print("\nEXCEPTION IN STREAM_CHAT:", type(e), str(e))
        raise e
