# 自定义翻译与复合双语解析 MCP 服务实现计划

> **面向 AI 代理的工作者：** 必需子技能：使用 superpowers:subagent-driven-development（推荐）或 superpowers:executing-plans 逐任务实现此计划。步骤使用复选框（`- [ ]`）语法来跟踪进度。

**目标：** 构建并集成基于 fastmcp 和 DeepSeek API 的自定义翻译与复合双语解析 MCP 服务（支持基础翻译、词根词缀拆解、语法结构分析及场景例句），并无缝挂载到 server-ai 的 LangChain 聊天助教中。

**架构：** 在 `server-ai` 根目录创建独立的 `translate_mcp_server.py`（基于 fastmcp 框架提供 stdio 通信服务，内部调用 DeepSeek 生成结构化 JSON）。在 `app/llm/tools.py` 中使用 `MultiServerMCPClient` 连接该 MCP Server 获取工具，并在 `app/services/chat.py` 中将工具注入到 LangChain Agent 的工具列表中。

**技术栈：** Python 3.12+, FastMCP, langchain-mcp-adapters, LangChain, DeepSeek API

---

### 任务 1：安装依赖与构建 MCP Server 核心解析服务

**文件：**
- 修改：`server-ai/pyproject.toml:5-33`
- 创建：`server-ai/translate_mcp_server.py`
- 创建：`server-ai/tests/test_translate_mcp.py`

- [ ] **步骤 1：编写失败的单元测试**

创建 `server-ai/tests/test_translate_mcp.py`，测试核心解析函数的逻辑与结构化返回值：

```python
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
```

- [ ] **步骤 2：运行测试验证失败**

运行：`cd server-ai && .\.venv\Scripts\python.exe -m pytest tests/test_translate_mcp.py -v`
预期：FAIL，报错 `ModuleNotFoundError: No module named 'translate_mcp_server'`

- [ ] **步骤 3：安装 fastmcp 与 langchain-mcp-adapters 依赖**

运行：`cd server-ai && .\.venv\Scripts\pip.exe install fastmcp langchain-mcp-adapters`
预期：成功安装 fastmcp 与 langchain-mcp-adapters 及其相关依赖。

- [ ] **步骤 4：编写 MCP Server 完整实现**

创建 `server-ai/translate_mcp_server.py`：

```python
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
```

- [ ] **步骤 5：运行测试验证通过**

运行：`cd server-ai && .\.venv\Scripts\python.exe -m pytest tests/test_translate_mcp.py -v`
预期：PASS

- [ ] **步骤 6：Commit 提交代码**

```bash
git add server-ai/translate_mcp_server.py server-ai/tests/test_translate_mcp.py
git commit -m "feat: build custom translation and dual-parsing MCP server"
```

---

### 任务 2：将翻译 MCP 集成到 LangChain 助教服务中

**文件：**
- 修改：`server-ai/app/llm/tools.py:105-135`
- 修改：`server-ai/app/services/chat.py:85-100`

- [ ] **步骤 1：在 `tools.py` 中编写 MCP 客户端连接与获取函数**

修改 `server-ai/app/llm/tools.py`，在文件末尾追加以下代码：

```python
async def get_translation_mcp_tools():
    """
    连接本地 translate_mcp_server.py MCP 服务，获取解析工具。
    """
    import os
    from langchain_mcp_adapters.client import MultiServerMCPClient
    
    server_script = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "translate_mcp_server.py")
    python_exe = sys.executable if "sys" in globals() else "python"
    import sys
    
    client = MultiServerMCPClient({
        "english_parser": {
            "transport": "stdio",
            "command": sys.executable,
            "args": [server_script]
        }
    })
    return await client.get_tools()
```

- [ ] **步骤 2：在 `chat.py` 中挂载工具并优化系统提示词**

修改 `server-ai/app/services/chat.py` 中的 `stream_chat` 函数（约第 88-98 行）：

定位原有代码：
```python
    # 创建用户的专属 RAG 检索工具
    from app.llm.tools import create_search_tool
    search_tool = create_search_tool(user_id, file_id)

    # 构建 agent
    agent = build_agent(
        model=model,
        system_prompt=system_prompt,
        checkpointer=checkpointer,
        tools=[search_tool],
    )
```

替换为：
```python
    # 创建用户的专属 RAG 检索工具与翻译解析 MCP 工具
    from app.llm.tools import create_search_tool, get_translation_mcp_tools
    search_tool = create_search_tool(user_id, file_id)
    
    try:
        mcp_tools = await get_translation_mcp_tools()
    except Exception as e:
        print(f"[WARN] 加载翻译 MCP 工具失败，将仅使用基础检索: {e}")
        mcp_tools = []

    # 提示词增强：指引 AI 人格优先使用 MCP 工具
    system_prompt += (
        "\n当你需要帮用户翻译长句、解析生词、拆解语法或提供造句时，"
        "请主动调用 `smart_english_parser` 工具获取精细化的结构化数据，"
        "并结合你的人格设定（如女仆、英语大师、麒麟哥等）生动呈现给用户！"
    )

    # 构建 agent
    agent = build_agent(
        model=model,
        system_prompt=system_prompt,
        checkpointer=checkpointer,
        tools=[search_tool] + mcp_tools,
    )
```

- [ ] **步骤 3：运行语法与模块检查**

运行：`cd server-ai && .\.venv\Scripts\python.exe -c "from app.services.chat import stream_chat; print('Import OK')"`
预期：输出 `Import OK`，无语法报错。

- [ ] **步骤 4：Commit 提交代码**

```bash
git add server-ai/app/llm/tools.py server-ai/app/services/chat.py
git commit -m "feat: integrate translation MCP tools into LangChain chat agent"
```

---

### 自检检查表
- [x] 所有文件路径均为绝对或准确相对路径
- [x] 所有步骤包含完整命令与预期代码块
- [x] 无任何占位符（TODO / 待定 / 后续处理）
- [x] 遵守 DRY / YAGNI / TDD 原则
