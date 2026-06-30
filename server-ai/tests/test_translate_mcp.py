import pytest
import json
from unittest.mock import patch, AsyncMock, MagicMock
from translate_mcp_server import parse_english_text

@pytest.mark.asyncio
async def test_parse_english_text_success():
    mock_response_json = {
        "choices": [
            {
                "message": {
                    "content": json.dumps({
                        "original": "Unprecedented",
                        "translation": "史无前例的",
                        "phonetic": "/ʌnˈpresɪdentɪd/",
                        "root_affix": "un-(否定) + pre-(前) + ced(走) + -ent + -ed",
                        "grammar_breakdown": "形容词",
                        "example_sentences": [
                            {"context": "💼 商务职场", "en": "An unprecedented opportunity.", "zh": "前所未有的机遇。"}
                        ]
                    })
                }
            }
        ]
    }
    
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = mock_response_json

    with patch("os.getenv", return_value="dummy_api_key"), \
         patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=mock_resp) as mock_post:
        result_str = await parse_english_text("Unprecedented", "word")
        data = json.loads(result_str)
        assert data["original"] == "Unprecedented"
        assert data["translation"] == "史无前例的"
        assert len(data["example_sentences"]) == 1
        mock_post.assert_called_once()

@pytest.mark.asyncio
async def test_parse_english_text_no_api_key():
    with patch("os.getenv", return_value=""):
        result_str = await parse_english_text("hello", "word")
        data = json.loads(result_str)
        assert "系统未配置 DEEPSEEK_API_KEY" in data["translation"]

@pytest.mark.asyncio
async def test_parse_english_text_network_error():
    with patch("os.getenv", return_value="dummy_api_key"), \
         patch("httpx.AsyncClient.post", new_callable=AsyncMock, side_effect=Exception("Network Timeout")):
        result_str = await parse_english_text("hello", "word")
        data = json.loads(result_str)
        assert "基础翻译查询" in data["translation"]
        assert "Network Timeout" in data["translation"]

@pytest.mark.asyncio
async def test_parse_english_text_boundary():
    # 测试空文本
    res_empty = await parse_english_text("   ")
    assert "输入文本不能为空" in json.loads(res_empty)["translation"]

    # 测试超长文本
    res_long = await parse_english_text("a" * 3001)
    assert "输入文本过长" in json.loads(res_long)["translation"]

    # 测试非法 parse_type 置为 auto
    with patch("os.getenv", return_value=""), patch("translate_mcp_server.json.dumps", side_effect=json.dumps) as mock_dumps:
        await parse_english_text("test", "invalid_type")
