import os
import json
import httpx
from fastmcp import FastMCP
from dotenv import load_dotenv

load_dotenv()

mcp = FastMCP("EnglishParser")

async def parse_english_text(text: str, parse_type: str = "auto") -> str:
    api_key = os.getenv("DEEPSEEK_API_KEY", "")
    if not api_key:
        return json.dumps({
            "original": text,
            "translation": "系统未配置 DEEPSEEK_API_KEY，无法进行深度解析",
            "phonetic": "",
            "root_affix": "",
            "grammar_breakdown": "",
            "example_sentences": []
        }, ensure_ascii=False)

    prompt = f"""请对以下英文或中文内容进行深度复合解析与互译。
内容："{text}"
解析模式：{parse_type} (word=单词解析, sentence=长句语法拆解, auto=智能识别)

你必须返回且仅返回一个合法的 JSON 字符串，格式严谨如下：
{{
  "original": "{text}",
  "translation": "准确地道的中文或英文翻译",
  "phonetic": "美英双音标（仅单词提供，长句填空字符串）",
  "root_affix": "词根词缀拆解与记忆法（单词必填，长句说明核心短语）",
  "grammar_breakdown": "长难句主谓宾定状补层级拆解（单词说明词性与固定搭配）",
  "example_sentences": [
    {{"context": "💼 商务职场", "en": "...", "zh": "..."}},
    {{"context": "☕ 日常生活", "en": "...", "zh": "..."}},
    {{"context": "🎓 考试学术", "en": "...", "zh": "..."}}
  ]
}}"""

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                "https://api.deepseek.com/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "deepseek-chat",
                    "messages": [{"role": "user", "content": prompt}],
                    "response_format": {"type": "json_object"},
                    "temperature": 0.3
                }
            )
            if resp.status_code == 200:
                content = resp.json()["choices"][0]["message"]["content"]
                return content
            else:
                raise Exception(f"HTTP {resp.status_code}: {resp.text}")
    except Exception as e:
        return json.dumps({
            "original": text,
            "translation": f"基础翻译查询。解析服务暂不可用 ({str(e)})",
            "phonetic": "",
            "root_affix": "暂无",
            "grammar_breakdown": "暂无",
            "example_sentences": []
        }, ensure_ascii=False)

@mcp.tool()
async def smart_english_parser(text: str, parse_type: str = "auto") -> str:
    """
    对英文单词、短语或长难句进行深度复合解析与中英互译。
    当用户在对话中要求翻译、解析生词、拆解语法或查询英文造句时调用此工具。
    :param text: 需要翻译或解析的英文/中文文本内容
    :param parse_type: 解析模式，可选 "word"(单词深度解析) / "sentence"(长难句语法拆解) / "auto"(智能识别)
    """
    return await parse_english_text(text, parse_type)

if __name__ == "__main__":
    mcp.run(transport="stdio")
