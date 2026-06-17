# 英语学习平台 — 技术架构文档

> 本文档用于整理项目核心技术实现，供 PPT 制作参考。

---

## 一、项目架构：Monorepo + 微服务

### 1.1 整体架构图

```
┌─────────────────────────────────────────────────────────┐
│                    Nginx (前端静态资源)                     │
│              Vue 3 SPA + Three.js 3D                     │
└──────────┬──────────┬──────────┬─────────────────────────┘
           │          │          │
     /api/v1/*   /ai/v1/*   /socket.io/*
           │          │          │
┌──────────▼──┐ ┌─────▼──────┐ ┌▼────────────────┐
│  Server 服务  │ │  AI 服务    │ │  WebSocket 网关  │
│  (NestJS)   │ │  (NestJS)  │ │  (Socket.IO)    │
│  Port 3000  │ │  Port 3001 │ │                 │
└──────┬──────┘ └─────┬──────┘ └─────────────────┘
       │              │
┌──────▼──────────────▼──────────────────────────┐
│              共享基础设施层                        │
│  PostgreSQL │ Redis │ MinIO │ BullMQ            │
└─────────────────────────────────────────────────┘
```

### 1.2 Monorepo 结构

采用 **pnpm workspace** 管理的 Monorepo，包含以下子包：

| 子包 | 包名 | 职责 |
|------|------|------|
| `apps/web` | `@en/web` | Vue 3 前端应用（Vite + Element Plus + TailwindCSS） |
| `apps/tracker` | `@en/tracker` | 浏览器端埋点 SDK（独立构建的 Vite library） |
| `packages/common` | `@en/common` | 前后端共享的 TypeScript 类型定义 |
| `packages/config` | `@en/config` | 共享端口配置 |
| `server` | `@en/server` | NestJS 后端（内含 server + ai + shared 三个子项目） |
| `server-ai` | — | FastAPI Python AI 服务（灰度迁移目标） |

### 1.3 微服务拆分

项目在 NestJS 框架内实现了 **逻辑微服务** 拆分：

- **Server 服务**（端口 3000）：用户、认证、单词本、课程、学习、支付、埋点
- **AI 服务**（端口 3001）：AI 对话、Prompt 管理、邮件摘要

两个服务共享同一个 `libs/shared` 库，但作为 **独立进程** 运行，通过前端分别调用 `/api/v1/` 和 `/ai/v1/` 路由，不走内部 RPC。

### 1.4 技术栈总览

| 层级 | 技术选型 |
|------|---------|
| 前端 | Vue 3 + TypeScript + Vite + Element Plus + TailwindCSS + Pinia |
| 3D 渲染 | Three.js（GLTFLoader + OrbitControls） |
| 后端 | NestJS + Prisma ORM + PostgreSQL |
| AI 服务 | LangChain + LangGraph + DeepSeek API |
| 消息队列 | BullMQ（Redis 驱动） |
| 对象存储 | MinIO（S3 兼容） |
| 实时通信 | Socket.IO（WebSocket） |
| 部署 | Docker + Docker Compose + Nginx |

---

## 二、监控埋点系统

### 2.1 架构设计

采用 **自研轻量级 SDK** 方案，而非接入第三方平台（如百度统计、Google Analytics），以实现完全的数据自主可控。

```
浏览器端 SDK (@en/tracker)
    ├── UV 采集（FingerprintJS 指纹）
    ├── PV 采集（路由监听）
    ├── 事件采集（点击事件）
    ├── 性能采集（Web Vitals）
    └── 错误采集（全局错误捕获）
           │
           │ navigator.sendBeacon() / fetch(keepalive)
           ▼
    后端 API（/tracker/*）
           │
           ▼
    PostgreSQL 存储（5 张表）
```

### 2.2 五大采集模块

| 模块 | 采集内容 | 技术实现 |
|------|---------|---------|
| **UV（访客）** | 浏览器指纹、设备信息、用户标识 | FingerprintJS 生成唯一 visitorId，支持 `setUserId()` 关联登录用户 |
| **PV（页面浏览）** | 访问路径、时间戳 | 监听 `popstate`、`hashchange`，Monkey-patch `history.pushState/replaceState` |
| **事件（点击）** | 元素位置、文本内容、时间 | 监听 `BUTTON` 和 `SPAN` 的 click，获取 `getBoundingClientRect()` |
| **性能指标** | FP、FCP、LCP、INP、CLS | `PerformanceObserver` + `web-vitals` 库，在页面切到后台时上报 |
| **错误捕获** | JS 异常、Promise 异常、堆栈 | `window.onerror` + `unhandledrejection` |

### 2.3 上报策略

- **UV**：使用 `fetch(keepalive: true)`（需要服务端返回 visitorId）
- **其他**：使用 `navigator.sendBeacon()`（页面关闭时不丢失数据，fire-and-forget 模式）

### 2.4 数据库索引优化

```prisma
model Visitor       { @@index([userId]); @@index([anonymousId]) }
model PageView      { @@index([visitorId, createdAt]); @@index([path, createdAt]) }
model TrackEvent    { @@index([visitorId, createdAt]); @@index([event, createdAt]) }
model PerformanceEntry { @@index([fp, fcp, lcp, inp, cls, createdAt]) }  // 复合索引
model ErrorEntry    { @@index([visitorId, createdAt]); @@index([error, createdAt]) }
```

### 2.5 扩展方案：ClickHouse

已预置 ClickHouse 集成代码，使用 `ReplacingMergeTree`（访客去重）和 `MergeTree`（其他事件）引擎，按月分区。可用于后续的大数据分析场景。

---

## 三、项目部署：容器化 + Nginx 反向代理

### 3.1 容器化架构

```
┌──────────────────────────────────────────┐
│            Docker Compose 编排             │
├──────────┬──────────┬────────────────────┤
│ 前端容器  │ 后端容器  │    基础设施容器       │
│ Nginx    │ Node.js  │ Postgres ×2        │
│ (80端口) │ (3000)   │ Redis (6379)       │
│          │ (3001)   │ MinIO (9000/9001)  │
└──────────┴──────────┴────────────────────┘
```

### 3.2 Dockerfile 设计

采用 **多阶段构建** 优化镜像体积：

**后端 Dockerfile**（`server/Dockerfile`）：
```
Builder 阶段（Node 22 Alpine）:
  → pnpm install
  → prisma generate
  → pnpm build tracker
  → pnpm build server
  → pnpm build ai

Runner 阶段（Node 22 Alpine）:
  → 仅复制构建产物 + 运行时依赖
```

**前端 Dockerfile**（`apps/web/Dockerfile`）：
```
Builder 阶段: pnpm install → vite build
Runner 阶段: nginx:alpine + 自定义 nginx.conf
```

### 3.3 Nginx 路由规则

| 路径 | 转发目标 | 说明 |
|------|---------|------|
| `/api/*` | `backend:3000` | 后端 API |
| `/ai/*` | `ai:3001` | AI 服务 |
| `/socket.io/*` | `backend:3000` | WebSocket（支持 upgrade） |
| `/minio/*` | `minio:9000` | 对象存储代理 |
| `/` | 本地静态文件 | Vue SPA |

关键 Nginx 配置：
```nginx
# WebSocket 支持
proxy_http_version 1.1;
proxy_set_header Upgrade $http_upgrade;
proxy_set_header Connection "upgrade";

# SSE（Server-Sent Events）支持
proxy_buffering off;
proxy_read_timeout 300s;
```

### 3.4 灰度部署方案（NestJS → FastAPI 迁移）

通过 `docker-compose.fastapi-ai.yml` 实现新旧 AI 服务并行运行：

```
Nginx 路由分流:
  /ai/* → fastapi-ai:3002（新服务，Python FastAPI）
       → ai:3001（旧服务，NestJS，备用）
```

---

## 四、支付宝支付集成

### 4.1 支付流程

```
用户点击购买 → 前端调用 /pay/create
    → 后端创建 PaymentRecord（状态: NOT_PAY）
    → 调用支付宝 pageExecute 生成支付 URL
    → 前端跳转到支付宝收银台
    → 用户完成支付
    → 支付宝异步回调 /pay/notify
    → 后端验证签名、更新状态为 TRADE_SUCCESS
    → 创建 CourseRecord（购买记录）
    → WebSocket 推送 paymentSuccess 事件
    → 前端弹出购买成功提示
```

### 4.2 核心实现

**支付宝 SDK 配置**：
```typescript
const alipaySdk = new AlipaySdk({
  appId: process.env.ALIPAY_APP_ID,
  privateKey: process.env.ALIPAY_PRIVATE_KEY,
  alipayPublicKey: process.env.ALIPAY_PUBLIC_KEY,
  gateway: process.env.ALIPAY_GATEWAY,  // 沙箱网关地址
});
```

**防重复购买**：创建订单前查询是否已存在 `TRADE_SUCCESS` 的 `CourseRecord`。

**事务保证**：在 Prisma 事务中完成「创建支付记录 → 更新状态 → 创建课程记录」，确保数据一致性。

**订单号生成**：`XM-{nanoid(12)}`，保证全局唯一。

### 4.3 四个 API 接口

| 接口 | 方法 | 认证 | 功能 |
|------|------|------|------|
| `/pay/create` | POST | 需要 | 创建支付订单，返回支付宝 URL |
| `/pay/notify` | ALL | 不需要 | 支付宝异步回调（服务端对服务端） |
| `/pay/verify` | POST | 需要 | 查询用户是否已购买某课程 |
| `/pay/manual-complete` | POST | 需要 | 手动完成购买（测试/管理用途） |

---

## 五、消息队列 + 定时任务

### 5.1 技术选型

采用 **BullMQ**（基于 Redis）作为消息队列，配合 `@nestjs/bullmq` 集成到 NestJS。

### 5.2 邮件摘要系统

**场景**：每天凌晨自动为开启定时任务的用户发送单词学习日报。

```
定时触发（Cron: 0 0 * * *）
    │
    ▼
查询符合条件的用户:
  - isTimingTask = true
  - email 不为空
  - 今日有学习记录
    │
    ▼
为每个用户创建 LangChain Agent:
  - 调用 queryTool 查询用户学习数据
  - 生成个性化 HTML 学习报告
    │
    ▼
将邮件发送任务加入队列（延迟到用户设定的 timingTaskTime）
    │
    ▼
Worker 消费任务 → EmailService 发送邮件
```

### 5.3 队列设计

```typescript
// 队列名: DIGEST_QUEUE
// 任务类型:
EMAIL_DIGEST_TASK    // 发送单封邮件
EVERY_DAY_DIGEST_TASK // 触发每日摘要生成
```

**BullMQ 定时任务配置**：
```typescript
await digestQueue.add(EVERY_DAY_DIGEST_TASK, {}, {
  repeat: { pattern: '0 0 * * *' }  // 每天 00:00
});
```

### 5.4 FastAPI 替代方案

Python 版使用 **APScheduler** 的 `AsyncIOScheduler` + `CronTrigger`，直接在进程内调度，不依赖 Redis 队列。

---

## 六、双 Token 认证机制

### 6.1 设计思路

采用 **Access Token + Refresh Token** 双令牌方案，解决「安全性」与「用户体验」的矛盾：

| Token | 有效期 | 用途 | 存储位置 |
|-------|--------|------|---------|
| Access Token | 10 秒（开发）/ 生产可调 | API 请求认证 | Pinia Store → localStorage |
| Refresh Token | 7 天 | 静默刷新 Access Token | Pinia Store → localStorage |

### 6.2 安全设计

**TokenType 防护**：两个 Token 的 payload 中都包含 `tokenType` 字段（`'access'` 或 `'refresh'`），Guard 校验时严格匹配，防止 Access Token 被当作 Refresh Token 使用，反之亦然。

**Refresh 时验证用户存在**：刷新 Token 时不仅验证签名，还查询数据库确认用户仍然存在，防止已删除用户的 Token 被利用。

### 6.3 前端无感刷新流程

```
请求 API → 返回 401
    │
    ▼
是否正在刷新中？
    ├── 是 → 将请求加入队列，等待刷新完成
    └── 否 → 调用 /user/refresh-token
              │
              ├── 成功 → 更新 Pinia Store → 重发原请求 + 队列中的请求
              └── 失败 → 清空用户状态 → 跳转首页 → 提示"登录已过期"
```

**关键实现**：
- 使用独立的 axios 实例 `refreshServer` 调用刷新接口，避免无限循环
- 请求队列机制确保并发请求不会触发多次刷新

---

## 七、语音转文字

### 7.1 技术实现

采用 **Web Speech API**（浏览器原生），无需后端支持：

```typescript
// 语音转文字（STT）
const recognition = new SpeechRecognition() || new webkitSpeechRecognition();
recognition.lang = 'zh-CN';
recognition.continuous = false;
recognition.interimResults = false;
recognition.onresult = (event) => {
  const transcript = event.results[0][0].transcript;
  // 识别结果回调
};

// 文字转语音（TTS）
const utterance = new SpeechSynthesisUtterance(word);
utterance.lang = 'en-US';
utterance.rate = 0.7;
speechSynthesis.speak(utterance);
```

### 7.2 封装为 Vue Hook

| Hook | 功能 | 方法 |
|------|------|------|
| `useVoiceToText()` | 语音识别 | `start(callback)` / `stop()` |
| `useAudio()` | 语音朗读 | `playAudio(word)` |

采用 **单例模式**，全局复用同一个 `SpeechRecognition` 实例。

### 7.3 国内替代方案分析

Web Speech API 的限制：
- Chrome 内核支持较好，但 Safari/Firefox 支持有限
- 依赖 Google 服务器（国内访问不稳定）

**推荐替代方案**：

| 方案 | 优势 | 接入方式 |
|------|------|---------|
| **讯飞语音 SDK** | 中文识别率最高，有 Web SDK | REST API + WebSocket 流式 |
| **百度语音识别** | 免费额度大，支持离线 | REST API |
| **腾讯云 ASR** | 微信生态集成好 | REST API |
| **阿里云 NLS** | 支持实时流式识别 | WebSocket |

**推荐**：讯飞语音 SDK（中文场景最优）或百度语音（免费额度大），通过 WebSocket 流式传输实现实时识别。

---

## 八、数据库性能优化（77 万条词汇数据）

### 8.1 挑战

WordBook 表包含 **770,611** 条记录，需要实现毫秒级的单词查询和筛选。

### 8.2 索引策略

```prisma
model WordBook {
  @@index([word])          // 单词精确/模糊搜索
  @@index([tag])           // 按考试类型筛选
  @@index([word, tag])     // 复合查询：搜索单词 + 筛选类型
}
```

### 8.3 查询优化

**分页查询**（`skip` + `take`）：
```typescript
const [total, list] = await Promise.all([
  prisma.wordBook.count({ where }),
  prisma.wordBook.findMany({ where, skip, take: 20, orderBy: { frq: 'desc' } })
]);
```
- `Promise.all` 并行执行 count 和 findMany
- 按 `frq`（词频）降序排列，高频词优先

**学习模块优化**（NOT EXISTS 子查询）：
```typescript
// 获取用户未掌握的单词，排除已学过的
prisma.wordBook.findMany({
  where: {
    [courseType]: true,
    wordBookRecords: { none: { userId } }  // NOT EXISTS 子查询
  },
  take: 10
});
```

**批量写入**：
```typescript
await prisma.wordBook.createMany({ data: batch, skipDuplicates: true });
```
每 2000 条一批写入，使用 `skipDuplicates` 避免冲突。

### 8.4 进一步优化建议

| 优化方向 | 具体方案 | 预期效果 |
|---------|---------|---------|
| **前缀索引** | 对 `word` 字段建立 B-Tree 索引 + `text_pattern_ops` | 加速 LIKE 'abc%' 查询 |
| **读写分离** | PostgreSQL 主从复制，查询走从库 | 降低主库压力 |
| **缓存层** | Redis 缓存热门单词（Top 1000） | 热点查询 < 1ms |
| **GIN 索引** | 对 `definition`/`translation` 使用 pg_trgm 扩展 | 支持中文模糊搜索 |
| **分区表** | 按首字母分区（a-z + 其他） | 减少单次扫描行数 |

---

## 九、Three.js 3D 渲染

### 9.1 应用场景

| 场景 | 组件 | 模型文件 |
|------|------|---------|
| 登录页 3D 展示 | `ModelViewer.vue` | `login/scene.gltf`、`register/scene.gltf` |
| 首页全息投影效果 | `Hologram.vue` | `hologram/scene.gltf` |

### 9.2 技术实现

```
初始化流程:
  Scene（场景）
    → PerspectiveCamera（透视相机，FOV 60）
    → WebGLRenderer（抗锯齿、高性能、透明背景）
    → OrbitControls（用户交互：拖拽、缩放、旋转）
    → GLTFLoader（加载 .gltf 模型）
    → AnimationMixer（播放模型动画）
    → requestAnimationFrame 循环（自动旋转 + 动画更新）
```

**核心特性**：
- **动态模型切换**：登录/注册切换时，移除旧模型、加载新模型
- **自动旋转**：`scene.rotation.y += 0.002` 每帧旋转
- **动画播放**：通过 `AnimationMixer` 播放 GLTF 内嵌动画
- **响应式**：监听 `resize` 事件更新相机和渲染器尺寸
- **内存管理**：切换模型时调用 `model.traverse()` 遍历销毁几何体和材质

### 9.3 性能优化

- `WebGLRenderer` 设置 `antialias: true`（抗锯齿）和 `powerPreference: 'high-performance'`
- 透明背景（`alpha: true`）与页面融合
- 使用 `Timer` 类控制动画帧率

---

## 十、其他技术亮点

### 10.1 SSE 流式 AI 对话

AI 对话采用 **Server-Sent Events**（SSE）实现流式输出：

```
前端: @microsoft/fetch-event-source
后端: Content-Type: text/event-stream
```

支持两种内容类型：
- `type: 'content'`：普通回答
- `type: 'reasoning'`：深度思考（推理过程）

### 10.2 LangChain + LangGraph Agent

```typescript
const agent = createReactAgent({
  llm: new ChatDeepSeek({ model: 'deepseek-v4-flash' }),
  tools: [queryTool, bochaSearchTool],
  checkpointSaver: new PostgresSaver(),  // 对话历史持久化
});
```

- **queryTool**：查询用户单词学习记录
- **BochaSearchTool**：实时联网搜索（博查搜索 API）
- **PostgresSaver**：对话历史存入独立的 `langchain` 数据库

### 10.3 统一响应格式

```json
{
  "timestamp": "2026-06-16T10:00:00Z",
  "path": "/api/v1/user/login",
  "message": "success",
  "code": 200,
  "success": true,
  "data": { ... }
}
```

通过 NestJS **Interceptor** 统一包装，**ExceptionFilter** 统一错误格式。BigInt 自动转为字符串避免 JSON 序列化问题。

### 10.4 对象存储（MinIO）

- 两个 Bucket：`avatar`（用户头像）、`course`（课程资源）
- 启动时自动创建 Bucket 并设置公共读策略
- 头像上传限制 5MB

---

## 附录：项目关键文件索引

| 模块 | 关键文件路径 |
|------|------------|
| 前端入口 | `apps/web/src/main.ts` |
| 前端路由 | `apps/web/src/router/` |
| 前端 API 层 | `apps/web/src/apis/` |
| 埋点 SDK | `apps/tracker/index.ts` |
| 后端主入口 | `server/apps/server/src/main.ts` |
| AI 服务入口 | `server/apps/ai/src/main.ts` |
| Prisma Schema | `server/prisma/schema.prisma` |
| 支付模块 | `server/apps/server/src/pay/` |
| 认证模块 | `server/apps/server/src/auth/` |
| 消息队列 | `server/apps/ai/src/digest/` |
| Docker Compose | `docker-compose.yml` |
| Nginx 配置 | `apps/web/nginx.conf` |
| 双 Token 逻辑 | `apps/web/src/apis/index.ts`（前端刷新） |
| 语音识别 | `apps/web/src/hooks/useVoiceToText.ts` |
| Three.js 3D | `apps/web/src/components/Login/ModelViewer.vue` |
