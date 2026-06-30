# AI 服务路由与动态模型切换重构执行计划 (Migration Plan)

本文件详细规划了前端 AI 流量分流开关与后端基于 LangChain `@wrap_model_call` 的动态模型参数重构的实施步骤。

---

## 📋 任务列表与细分步骤

### 1. 前端多 AI 服务自由分流切换
通过环境变量控制前端代理，在 Python AI 服务与 NestJS AI 服务之间无缝切换。

- [x] **1.1 配置开发与生产环境环境变量**
  - [x] 在 `apps/web/.env.development` 中新增环境变量 `VITE_USE_PYTHON_AI=false`（默认指向 NestJS AI 端口）。
  - [ ] 在 `apps/web/.env.production` 中新增对应变量说明，供容器化部署时动态注入。
  
- [x] **1.2 修改 Vite 代理配置**
  - [x] 编辑 [`apps/web/vite.config.ts`](file:///D:/english/apps/web/vite.config.ts)。
  - [x] 使用 `loadEnv` 方法在 `defineConfig` 内安全获取当前环境变量（防止直接访问 `process.env` 在不同环境下失效）。
  - [x] 动态设定代理的目标端口：
    - `VITE_USE_PYTHON_AI === 'true'` 时：将 `/ai` 和 `/socket.io` 代理到 **`http://localhost:3001`**（Python FastAPI 服务）。
    - `VITE_USE_PYTHON_AI !== 'true'` 时：将 `/ai` 和 `/socket.io` 代理到 **`http://localhost:3002`**（NestJS AI 服务）。
    > *注：端口 3001 与 3002 对应的分流规则需在配置文件中显式注明，防止端口冲突。*

- [x] **1.3 联调测试验证**
  - [x] 分别在启动和关闭 `VITE_USE_PYTHON_AI` 的情况下启动前端，观察浏览器 Network 面板，验证 `/ai/v1/chat` 接口是否被正确反向代理至对应的后端服务。

---

### 2. 后端基于 LangChain `@wrap_model_call` 的动态请求参数修改重构
利用 LangChain 内部的中间件机制，实现请求级别的模型动态选择与重写。

- [x] **2.1 设计并实现 `ChatContext` 上下文管理器**
  - [x] 在 [`server-ai/app/llm/`](file:///D:/english/server-ai/app/llm) 中新建 `context.py`。
  - [x] 引入 `contextvars.ContextVar`，声明一个线程/协程安全的 `chat_model_var`（用于暂存当前会话中用户选择的模型类型，例如 `flash` 或 `pro` / `reasoner`）。
  - [x] 提供设置 `set_model_type` 和获取 `get_model_type` 的上下文辅助函数。
  
- [x] **2.2 编写 `dynamic_model_selector` 中间件**
  - [x] 在 [`server-ai/app/llm/`](file:///D:/english/server-ai/app/llm) 目录下新建 `middleware.py`。
  - [x] 导入依赖：`from langchain.agents.middleware import wrap_model_call`。
  - [x] 编写被装饰的函数 `dynamic_model_selector`：
    ```python
    @wrap_model_call
    def dynamic_model_selector(request, handler):
        # 1. 从 ChatContext 获取用户当前请求的模型选择
        model_type = get_model_type()
        
        # 2. 根据 model_type 决定使用的实际 ChatModel 实例
        #    例如选用 create_deepseek() 或 create_deepseek_reasoner()
        from app.llm.models import create_deepseek, create_deepseek_reasoner
        target_model = create_deepseek_reasoner() if model_type == "reasoner" else create_deepseek()
        
        # 3. 使用 request.override 进行不可变参数重写
        overridden_request = request.override(model=target_model)
        
        # 4. 执行链条，并将最终的 ModelResponse 返回
        return handler(overridden_request)
    ```

- [x] **2.3 将中间件织入 Agent 编译流程**
  - [x] 重构 [`server-ai/app/llm/agents.py`](file:///D:/english/server-ai/app/llm/agents.py) 中的 `build_agent` 函数。
  - [x] 废弃原 `langgraph.prebuilt.create_react_agent`（不支持 middleware 参数），改用 `langchain.agents.create_agent` 进行 Agent 编译。
  - [x] 导入 `dynamic_model_selector`，将其作为 `middleware=[dynamic_model_selector]` 传递给 `create_agent`  （注：如果是 create_react_agent 则是 `middleware` 传入）。

- [x] **2.4 在 FastAPI 请求周期中拦截并注入 Context**
  - [x] 修改聊天接口路由器 [`server-ai/app/routers/chat.py`](file:///D:/english/server-ai/app/routers/chat.py)。
  - [x] 在处理对话请求（如 WebSocket 消息接收、HTTP POST 接收）的第一时间，读取前端传入 `model` 字段参数。
  - [x] 在调用 Agent 之前，使用 `chat_model_var.set(user_selected_model)` 将模型参数绑定到当前请求上下文生命周期中。

- [x] **2.5 系统集成测试**
  - [x] 编写测试脚本，模拟同一个 Agent 发送两次请求：一次指定使用普通对话模型（Flash），另一次指定使用推理模型（Reasoner/Pro）。
  - [x] 验证系统是否无缝通过 `@wrap_model_call` 中间件重构了请求，且底层准确调用了不同的 DeepSeek 接口。
