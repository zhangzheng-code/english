import pytest
import json
import asyncio
from translate_mcp_server import parse_english_text

@pytest.mark.asyncio
async def test_parse_english_text():
    result_str = await parse_english_text("Unprecedented", "word")
    data = json.loads(result_str)
    assert "original" in data
    assert "translation" in data
    assert "root_affix" in data
    assert "example_sentences" in data
    assert isinstance(data["example_sentences"], list)
