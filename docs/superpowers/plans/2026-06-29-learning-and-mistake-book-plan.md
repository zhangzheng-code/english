# 单词学习与错题本闭环系统 实现计划

> **面向 AI 代理的工作者：** 必需子技能：使用 superpowers:subagent-driven-development（推荐）或 superpowers:executing-plans 逐任务实现此计划。步骤使用复选框（`- [ ]`）语法来跟踪进度。

**目标：** 实现背词切题自动朗读、拼写正确延迟 600ms 平滑跳转、一键错题收录，以及双端闯关消杀错题本。

**架构：** 复用 `WordBookRecord` 的 `isMaster` 布尔字段区分状态（`false`=错题未掌握，`true`=已掌握销账）。前端 Vue 3 构建沉浸式背词卡与消杀闯关弹窗。

**技术栈：** Vue 3, TypeScript, TailwindCSS, Element Plus, NestJS, Prisma

---

### 文件结构

- **创建**：
  - `apps/web/src/views/Course/components/MistakeChallenge.vue` —— 沉浸式错题闯关消杀抽认卡组件
- **修改**：
  - `server/apps/server/src/learn/learn.controller.ts` —— 新增错题收录、列表、销账路由
  - `server/apps/server/src/learn/learn.service.ts` —— 实现错题业务操作逻辑
  - `apps/web/src/apis/learn/index.ts` —— 新增前端错题相关 API 封装
  - `apps/web/src/views/Course/Learn/index.vue` —— 改造背词主页（自动读音、延迟跳转、一键记错、错题角标）
  - `apps/web/src/views/Course/index.vue` —— 课程大厅新增“专属错题本”标签页

---

### 任务 1：后端 NestJS 错题 API 拓展

**文件：**
- 修改：`server/apps/server/src/learn/learn.controller.ts`
- 修改：`server/apps/server/src/learn/learn.service.ts`

- [ ] **步骤 1：修改 `learn.service.ts` 添加错题服务方法**

在 `server/apps/server/src/learn/learn.service.ts` 底部新增 `recordMistake`, `getMistakeList`, `resolveMistake` 方法：

```typescript
  // 记录错题 isMaster: false
  async recordMistake(wordId: string, userId: string) {
    const record = await this.prisma.wordBookRecord.upsert({
      where: {
        userId_wordId: { userId, wordId }
      },
      update: { isMaster: false },
      create: { userId, wordId, isMaster: false }
    });
    return this.response.success(record);
  }

  // 获取错题列表
  async getMistakeList(userId: string) {
    const records = await this.prisma.wordBookRecord.findMany({
      where: { userId, isMaster: false },
      include: { word: true },
      orderBy: { updatedAt: 'desc' }
    });
    const words = records.map(r => r.word);
    return this.response.success(words);
  }

  // 错题闯关销账 isMaster: true
  async resolveMistake(wordId: string, userId: string) {
    await this.prisma.wordBookRecord.updateMany({
      where: { userId, wordId },
      data: { isMaster: true }
    });
    return this.response.success(null);
  }
```

- [ ] **步骤 2：修改 `learn.controller.ts` 暴露路由**

在 `server/apps/server/src/learn/learn.controller.ts` 中添加注解接口：

```typescript
  @UseGuards(AuthGuard)
  @Post('word/mistake')
  recordMistake(@Body('wordId') wordId: string, @Req() req: Request) {
    return this.learnService.recordMistake(wordId, req.user.userId);
  }

  @UseGuards(AuthGuard)
  @Get('word/mistakes')
  getMistakes(@Req() req: Request) {
    return this.learnService.getMistakeList(req.user.userId);
  }

  @UseGuards(AuthGuard)
  @Post('word/mistake-resolve')
  resolveMistake(@Body('wordId') wordId: string, @Req() req: Request) {
    return this.learnService.resolveMistake(wordId, req.user.userId);
  }
```

- [ ] **步骤 3：编译验证服务方**

运行：`cd server && pnpm build` 或 `pnpm tsc --noEmit`  
预期：编译顺利通过，无 TS 语法报错。

---

### 任务 2：前端 API 客户端定义

**文件：**
- 修改：`apps/web/src/apis/learn/index.ts`

- [ ] **步骤 1：添加错题 API 方法**

在 `apps/web/src/apis/learn/index.ts` 中增加导出：

```typescript
export const recordMistake = (wordId: string) => serverApi.post('/learn/word/mistake', { wordId }) as Promise<Response<any>>;
export const getMistakeList = () => serverApi.get('/learn/word/mistakes') as Promise<Response<Word[]>>;
export const resolveMistake = (wordId: string) => serverApi.post('/learn/word/mistake-resolve', { wordId }) as Promise<Response<any>>;
```

---

### 任务 3：单词学习主页紧凑化与自动进阶 (`Course/Learn/index.vue`)

**文件：**
- 修改：`apps/web/src/views/Course/Learn/index.vue`

- [ ] **步骤 1：新增自动读音、延时跳转逻辑与错题状态**

在 `script setup` 引入错题接口与自动进阶：
```typescript
import { recordMistake, getMistakeList } from '@/apis/learn';
import MistakeChallenge from '../components/MistakeChallenge.vue';

const mistakeCount = ref(0);
const showMistakeModal = ref(false);

const loadMistakes = async () => {
    const res = await getMistakeList();
    if (res.success) mistakeCount.value = res.data.length;
};

// 监听切词自动朗读
watch(currentWord, (newWord) => {
    if (newWord?.word) {
        setTimeout(() => playAudio(newWord.word), 150);
    }
});

// 一键加入错题本
const captureMistake = async () => {
    if (!currentWord.value) return;
    // 填充答案
    Array.from(currentWord.value.word).forEach((char, idx) => {
        if (wordList.value[idx]) {
            wordList.value[idx].input = char;
            wordList.value[idx].isTrue = true;
        }
    });
    await recordMistake(currentWord.value.id);
    ElMessage.warning('已显示正确答案并收录入错题本！');
    mistakeCount.value++;
    setTimeout(() => pageNext(), 1200);
};
```

在 `onInput` / `onKeyDown` 校验完全正确处补充平滑跳转：
```typescript
// 校验若全对，延时 600ms 自动下一个
const checkAllCorrect = () => {
    if (wordList.value.length > 0 && wordList.value.every(i => i.isTrue === true)) {
        playAudio(currentWord.value!.word);
        setTimeout(() => {
            if (currentIndex.value < list.value.length) {
                pageNext();
            }
        }, 600);
    }
};
```

- [ ] **步骤 2：在模板中增加右上角错题角标与快捷收录栏**

在头部右上角加入按钮：
```html
<button type="button" @click="showMistakeModal = true"
    class="absolute top-8 right-8 px-4 py-2 rounded-full bg-amber-500/10 border border-amber-500/30 text-amber-600 font-semibold text-sm hover:bg-amber-500/20 transition-all flex items-center gap-2 cursor-pointer shadow-sm">
    <span>📖 待攻克错题</span>
    <span class="px-2 py-0.5 rounded-full bg-amber-500 text-white text-xs font-bold">{{ mistakeCount }}</span>
</button>
```

在拼写输入框下方加入：
```html
<div class="mt-4 text-center">
    <button type="button" @click="captureMistake"
        class="text-xs text-amber-600 hover:text-amber-700 underline font-medium cursor-pointer py-1 px-3 rounded hover:bg-amber-50 transition-colors">
        💡 不会拼？按 Tab 或点此显示答案并记入错题本
    </button>
</div>
```

---

### 任务 4：沉浸式闯关消杀组件与大厅挂载

**文件：**
- 创建：`apps/web/src/views/Course/components/MistakeChallenge.vue`
- 修改：`apps/web/src/views/Course/index.vue`

- [ ] **步骤 1：新建 `MistakeChallenge.vue` 闯关卡片**

支持全屏遮罩，卡片单张翻页听音拼写。每通过一词调用 `resolveMistake(word.id)`，直到列表清零展现庆祝。

- [ ] **步骤 2：在课程大厅挂载**

在 `Course/index.vue` 的 `el-tabs` 新增：
```html
<el-tab-pane v-if="userStore.user?.id" name="mistakes" label="📖 专属错题本"></el-tab-pane>
```
当 `currentTab === 'mistakes'` 时，渲染 `<MistakeChallenge @resolved="getList" />`。

- [ ] **步骤 3：构建前端类型检查**

运行：`cd apps/web && npm run build`  
预期：成功构建通过无编译错误。

---
