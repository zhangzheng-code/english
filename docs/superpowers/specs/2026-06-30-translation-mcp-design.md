# 自定义翻译与复合双语解析 MCP 服务设计规格 (Design Spec)

**日期**: 2026-06-30  
**状态**: 已批准  
**方案**: 方案 C（LLM 提示词增强型复合智能双语解析 MCP）  

---

## 1. 需求与目标 (Requirements & Goals)

### 1.1 业务背景
在“英语背单词系统”的 AI 伴学对话（`server-ai`）及资料库对练中，用户经常遇到生词、长难句以及日常翻译需求。传统的纯对话式翻译存在格式不统一、缺乏深度记忆扩展（如词根拆解、例句场景）以及不同 AI 人格助教重复定义工具的问题。

### 1.2 核心目标
1. **标准化构建 MCP Server**：遵循 MCP (Model Context Protocol) 协议，使用 `fastmcp` 构建独立的本地服务 `translate_mcp_server.py`。
2. **复合智能双语解析**：对外提供统一工具 `smart_english_parser`，支持基础中英翻译，并自动扩展词根词缀拆解、语法结构句法分析、3 大典型场景例句。
3. **复用现有底层模型**：直接复用后端 `server-ai/.env` 已配置的 `DEEPSEEK_API_KEY`，无需申请额外密钥。
4. **即插即用无缝挂载**：通过 `MultiServerMCPClient` 以 `stdio` 进程通信方式挂载到 LangChain Agent（如女仆、英语大师、商务英语助教等），实现所有对话场景中的智能化查词与翻译响应。

---

## 2. 架构与技术选型 (Architecture & Tech Stack)

### 2.1 技术栈
- **协议框架**：FastMCP (`fastmcp` Python 包)
- **通信传输协议**：`stdio` (标准输入输出，进程级通信，零网络端口占用)
- **AI 引擎**：LangChain / DeepSeek API（直接复用项目的 DeepSeek 接口配置，约束输出结构化 JSON Schema）

### 2.2 系统交互拓扑
```
[ 用户端 Vue3 Web ]
        │ (发送聊天提问：e.g., "帮我解析和翻译: Unprecedented")
        ▼
[ FastAPI server-ai (chat.py) ]
        │ (激活对应的 AI 人格 Agent)
        ▼
[ LangChain Agent (MCP Host) ]
        │ (通过 MultiServerMCPClient stdio 发起 RPC 工具调用)
        ▼
[ translate_mcp_server.py (MCP Server) ]
        │ (调用 DeepSeek 生成结构化解析数据)
        ▼
[ 返回 JSON 复合数据 -> Agent 渲染精美回复 ]
```

---

## 3. 详细接口与数据定义 (Detailed Interfaces)

### 3.1 MCP Server 定义 (`server-ai/translate_mcp_server.py`)
初始化 `FastMCP("EnglishParser")`，定义核心工具：

```python
@mcp.tool()
async def smart_english_parser(text: str, parse_type: str = "auto") -> str:
    """
    对英文单词、短语或长难句进行深度复合解析与中英互译。
    当用户在对话中要求翻译、解析生词、拆解语法或查询英文造句时调用此工具。
    :param text: 需要翻译或解析的英文/中文文本内容
    :param parse_type: 解析模式，可选 "word"(单词深度解析) / "sentence"(长难句语法拆解) / "auto"(智能识别)
    """
```

### 3.2 数据出参规范 (JSON Schema Response)
内部大模型生成完毕后，返回严格序列化的 JSON 字符串：
```json
{
  "original": "用户查询的原词或句子",
  "translation": "准确地道的中文翻译（或中译英结果）",
  "phonetic": "美英双音标（若为单词，如 /ʌnˈpres.ə.den.tɪd/；若为长句则为空）",
  "root_affix": "词根词缀深度拆解与记忆法（如 un-否定 + precedent-先例 + -ed形容词 -> 史无前例的）",
  "grammar_breakdown": "长难句主谓宾定状补从句层级拆解（若为单词则描述词性及常用短语搭配）",
  "example_sentences": [
    {"context": "💼 商务职场", "en": "...", "zh": "..."},
    {"context": "☕ 日常生活", "en": "...", "zh": "..."},
    {"context": "🎓 考试学术", "en": "...", "zh": "..."}
  ]
}
```

---

## 4. LangChain 宿主集成方案 (Host Integration)

### 4.1 MCP Client 挂载 (`server-ai/app/llm/tools.py` 或单独初始化模块)
通过 `MultiServerMCPClient` 连接本地 Python 子进程：
```python
from langchain_mcp_adapters.client import MultiServerMCPClient
import os

async def get_translation_mcp_tools():
    server_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "translate_mcp_server.py")
    client = MultiServerMCPClient({
        "english_parser": {
            "transport": "stdio",
            "command": "python",
            "args": [server_path]
        }
    })
    return await client.get_tools()
```

### 4.2 对接聊天助教 (`server-ai/app/services/chat.py`)
在 `stream_chat` 流式响应处理前，注入 MCP 工具：
- 将获取到的 MCP tools 与现有的 `search_tool` 合并为完整的 `tools` 列表传入 `build_agent`。
- 在 `ROLE_PROMPTS` 提示词中补充系统级指导，确保 AI 助教遇到生词解析和翻译时优先调用 `smart_english_parser` 工具。

---

## 5. 错误处理与容错 (Error Handling)
1. **API 调用超时容错**：若 DeepSeek 解析响应超时或失败，捕获异常并返回降级基础字典结构，防止整个对话流程抛错中断。
2. **进程管理**：利用 `MultiServerMCPClient` 内置的 stdio 子进程生命周期管理，确保 HTTP 协程结束或应用关闭时安全释放子进程资源。

---

## 6. 验证与测试标准 (Verification & Success Criteria)
1. **语法与依赖自测**：确认 `fastmcp` 安装无误，运行脚本测试无语法报错。
2. **集成联调验证**：向端侧聊天接口发送提问：“请帮我翻译并解析生词 Procrastination”，验证日志中 Agent 成功调用 `smart_english_parser`，且最终对话流式输出包含词根拆解和 3 场景例句。
