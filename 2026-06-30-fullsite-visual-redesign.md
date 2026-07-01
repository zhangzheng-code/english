# 全站视觉换血重构规格说明
> 版本：v1.0 | 日期：2026-06-30 | 参考图：.agents/references/1.webp & 2.webp

---

## 一、设计总纲

### 核心原则
- **绝对禁区**：彻底清洗 `purple-*`、`indigo-*` 系列所有高饱和度 Tailwind class
- **审美锚点**：低饱和度莫兰迪粉 + 薰衣草渐变 + 大面积高明度中性白灰
- **业务红线**：所有后端接口调用、SSE 流式响应、Pinia store、业务 hooks 零修改
- **验收标准**：`pnpm run type-check` + `pnpm run build` 双重绿色通过

---

## 二、全局 Design Token 体系

### CSS 变量（注入到 `apps/web/src/assets/base.css`）

```css
:root {
  --color-canvas-from:    #FDF0F0;   /* 粉藕色 */
  --color-canvas-to:      #F0EEF8;   /* 薰衣草淡紫 */
  --color-surface:        #FFFFFF;
  --color-surface-border: #F0EEF8;
  --color-surface-hover:  #FAFAFA;
  --color-accent:         #B8B0E8;   /* 低饱和薰衣草紫 */
  --color-accent-strong:  #0D0D0D;   /* 近黑，激活按钮 */
  --color-accent-soft:    #F4A4B0;   /* 玫瑰粉，图表/徽章 */
  --color-text-primary:   #111111;
  --color-text-secondary: #666666;
  --color-text-muted:     #AAAAAA;
  --color-nav-bg:         #FFFFFF;
  --color-nav-border:     #F0EEF8;
  --color-nav-active-bg:  #0D0D0D;
  --color-nav-active-icon:#FFFFFF;
  --color-nav-icon:       #666666;
  --el-color-primary:     #0D0D0D;
  --el-border-radius-base: 12px;
}

.dark {
  --color-canvas-from:    #0F0E17;
  --color-canvas-to:      #1A1628;
  --color-surface:        rgba(255,255,255,0.05);
  --color-surface-border: rgba(255,255,255,0.08);
  --color-accent:         #C4BCE8;
  --color-accent-strong:  #FFFFFF;
  --color-accent-soft:    #E8A0AF;
  --color-text-primary:   #F5F5F5;
  --color-text-secondary: #999999;
  --color-text-muted:     #555555;
  --color-nav-bg:         rgba(255,255,255,0.04);
  --color-nav-border:     rgba(255,255,255,0.08);
  --color-nav-active-bg:  #FFFFFF;
  --color-nav-active-icon:#0D0D0D;
  --color-nav-icon:       #888888;
  --el-color-primary:     #FFFFFF;
  --el-bg-color:          #1A1628;
  --el-bg-color-page:     #0F0E17;
  --el-text-color-primary:#F5F5F5;
  --el-border-color:      rgba(255,255,255,0.10);
  --el-fill-color-blank:  rgba(255,255,255,0.05);
}
```

---

## 三、全局布局架构重构

**彻底移除 `layout/Header/index.vue`**，由新建的 64px `NavRail` 接管导航职责。

### `layout/index.vue` 新结构
```html
<div class="flex h-screen overflow-hidden" style="background: linear-gradient(135deg, var(--color-canvas-from), var(--color-canvas-to))">
  <NavRail />
  <main class="flex-1 ml-16 overflow-y-auto">
    <RouterView />
  </main>
</div>
```

### NavRail 组件（新建 `layout/NavRail/index.vue`）
- 固定左侧：`fixed left-0 top-0 h-screen w-16`
- 背景：`bg-[var(--color-nav-bg)] border-r border-[var(--color-nav-border)]`
- 路由图标列表（使用 lucide-vue-next）：
  - Home → `<LayoutDashboard />`
  - Chat → `<MessageSquare />`
  - Course → `<BookOpen />`
  - WordBook → `<Star />`
  - Setting → `<Settings />`
- 激活态：`w-11 h-11 rounded-2xl bg-[var(--color-nav-active-bg)] text-[var(--color-nav-active-icon)]`
- Tooltip：`el-tooltip` placement="right"，显示中文模块名
- 底部：
  1. 主题切换胶囊（`useColorMode` from `@vueuse/core`）
  2. 用户头像 + `el-popover` 挂载 Profile 组件（保留现有 Profile 组件零修改）

---

## 四、首页 Dashboard 重构规格

### 布局（`views/Home/index.vue`）
```
max-w-[1300px] mx-auto px-8 py-10
grid grid-cols-3 gap-6

left (col-span-2):
  ① 问候语区：Good morning, [name]  text-4xl font-black text-[var(--color-text-primary)]
  ② 统计徽章区：词汇量卡 + 坚持天数卡（白色大数字卡并排）
  ③ 学习折线图卡（Chart.js Line，Mock 最近 7 天数据）
  ④ 核心能力 3 卡（升级现有 abouts 卡片）

right (col-span-1):
  ⑤ 课程推荐卡列表（3 张，静态 Mock，含底色差异：粉/紫/白）
```

### 图表规格
- 库：`vue-chartjs` + `Chart.js`
- 数据：Mock 7 天词汇量 `[12, 24, 18, 35, 42, 28, 56]`
- 颜色：线条 `#B8B0E8`，填充 `rgba(184,176,232,0.15)`
- 无需任何新接口

---

## 五、Chat 工作台改造规格

### Bubble.vue 输入控制条
```
上方 Toggle 行：
  [🧠 深思] [🌐 联网] [📷 图片]
  激活态：bg-[var(--color-accent-strong)] text-white rounded-full px-3 py-1 text-xs
  非激活：bg-[var(--color-surface)] border border-[var(--color-surface-border)] text-[var(--color-text-secondary)]

输入行：
  textarea rounded-2xl + 发送按钮
  麦克风按钮保留（语音转文字，非口语连麦）
```

### 口语 FAB 按钮（Bubble.vue 或 Chat/index.vue）
```css
position: fixed;
bottom: 2rem; right: 2rem;
width: 3.5rem; height: 3.5rem;
border-radius: 9999px;
background: var(--color-accent-strong);
color: var(--color-nav-active-icon);
box-shadow: 0 8px 32px rgba(0,0,0,0.18);
animation: pulse 2s infinite; /* idle 状态 */
```
点击触发：现有 `openOralModal()` 方法，**业务逻辑零修改**。

---

## 六、新增依赖

```
chart.js@^4
vue-chartjs@^5
lucide-vue-next@^0.x
```
`@vueuse/core` 已存在，直接使用 `useColorMode`。

---

## 七、改动文件清单

| 文件 | 操作 | 备注 |
|------|------|------|
| `apps/web/src/assets/base.css` | 修改 | 注入 Token 变量 |
| `apps/web/src/layout/index.vue` | 修改 | NavRail + main |
| `apps/web/src/layout/NavRail/index.vue` | 新建 | 64px 图标导航 |
| `apps/web/src/layout/Header/index.vue` | 弃用 | 停止在 layout 中引用 |
| `apps/web/src/composables/useTheme.ts` | 新建 | 日夜模式 hook |
| `apps/web/src/views/Home/index.vue` | 重构 | 仪表盘化 |
| `apps/web/src/views/Chat/index.vue` | 修改 | 传递 openOralModal |
| `apps/web/src/views/Chat/components/Bubble.vue` | 修改 | 控制条 + FAB |
| `apps/web/src/views/Chat/components/Conversations.vue` | 修改 | Token 替换 |
| `apps/web/src/views/Chat/components/Bookshelf.vue` | 修改 | Token 替换 |
| `apps/web/src/views/WordBook/**` | 修改 | Token 清洗 |
| `apps/web/src/views/Course/**` | 修改 | Token 清洗 |
| `apps/web/src/views/Setting/**` | 修改 | Token 清洗 |
| `apps/web/src/components/Search/` | 修改 | Token 清洗 |
| `apps/web/src/components/Login/` | 修改 | Token 清洗 |
| `apps/web/package.json` | 修改 | 新增 3 依赖 |

---

## 八、业务红线（绝对禁止修改）

- ❌ `apps/web/src/apis/` — 所有接口函数
- ❌ `apps/web/src/stores/` — Pinia store 逻辑
- ❌ `apps/web/src/hooks/` — useVoiceToText / useSocket / useLogin
- ❌ `apps/web/src/apis/sse.ts` — SSE 流式响应
- ❌ 所有组件现有 emit / props 类型签名（只可增加，不可删改）
- ❌ 后端接口 URL、请求参数、响应类型
