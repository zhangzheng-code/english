# 每日零点异步错词日报发送实现计划

> **面向 AI 代理的工作者：** 必需子技能：使用 superpowers:subagent-driven-development（推荐）或 superpowers:executing-plans 逐任务实现此计划。步骤使用复选框（`- [ ]`）语法来跟踪进度。

**目标：** 构建一个基于 NestJS `@nestjs/schedule` 定时器与 `BullMQ` 异步消费队列的每日零点错词日报发送系统，并提供可自测的手动触发接口。

**架构：** 零点由 `ReportScheduler` 定时查询符合条件（开启定时任务、有邮箱、有错题）的用户，将发信任务异步投递到 BullMQ `daily-report` 队列；由 `ReportProcessor` 消费者拉取并渲染精美 HTML 邮件模板后调用 `EmailService` 发送。

**技术栈：** NestJS 11, Prisma, BullMQ, @nestjs/schedule, Nodemailer

---

### 任务 1：安装依赖与模块声明 (`ReportModule`)

**文件：**
- 创建：`server/apps/server/src/report/report.module.ts`
- 修改：`server/apps/server/src/app.module.ts:14-18`

- [ ] **步骤 1：安装 `@nestjs/schedule`**

运行命令安装定时任务模块：
```bash
cd D:\english\server && pnpm add @nestjs/schedule
```

- [ ] **步骤 2：创建 `report.module.ts`**

创建文件 `server/apps/server/src/report/report.module.ts`：
```typescript
import { Module } from '@nestjs/common';
import { BullModule } from '@nestjs/bullmq';
import { ReportScheduler } from './report.scheduler';
import { ReportProcessor } from './report.processor';
import { ReportController } from './report.controller';

@Module({
  imports: [
    BullModule.registerQueue({
      name: 'daily-report',
    }),
  ],
  controllers: [ReportController],
  providers: [ReportScheduler, ReportProcessor],
})
export class ReportModule {}
```

- [ ] **步骤 3：在 `AppModule` 中注册模块**

修改 `server/apps/server/src/app.module.ts`，引入 `ScheduleModule.forRoot()` 与 `ReportModule`：
```typescript
import { Module } from '@nestjs/common';
import { ScheduleModule } from '@nestjs/schedule';
import { AppController } from './app.controller';
import { AppService } from './app.service';
import { SharedModule } from '@libs/shared';
import { WordBookModule } from './word-book/word-book.module';
import { UserModule } from './user/user.module';
import { AuthService } from './auth/auth.service';
import { AuthModule } from './auth/auth.module';
import { CourseModule } from './course/course.module';
import { PayModule } from './pay/pay.module';
import { SocketModule } from './socket/socket.module';
import { LearnModule } from './learn/learn.module';
import { TrackerModule } from './tracker/tracker.module';
import { ReportModule } from './report/report.module';

@Module({
  imports: [
    ScheduleModule.forRoot(),
    UserModule,
    SharedModule,
    WordBookModule,
    AuthModule,
    CourseModule,
    PayModule,
    SocketModule,
    LearnModule,
    TrackerModule,
    ReportModule,
  ],
  controllers: [AppController],
  providers: [AppService, AuthService],
})
export class AppModule {}
```

---

### 任务 2：创建日报调度器与队列消费处理器 (`ReportScheduler` & `ReportProcessor`)

**文件：**
- 创建：`server/apps/server/src/report/report.scheduler.ts`
- 创建：`server/apps/server/src/report/report.processor.ts`

- [ ] **步骤 1：创建 `report.scheduler.ts` 零点调度器**

创建文件 `server/apps/server/src/report/report.scheduler.ts`：
```typescript
import { Injectable, Logger } from '@nestjs/common';
import { Cron } from '@nestjs/schedule';
import { InjectQueue } from '@nestjs/bullmq';
import { Queue } from 'bullmq';
import { PrismaService } from '@libs/shared/prisma/prisma.service';

@Injectable()
export class ReportScheduler {
  private readonly logger = new Logger(ReportScheduler.name);

  constructor(
    @InjectQueue('daily-report') private readonly reportQueue: Queue,
    private readonly prisma: PrismaService,
  ) {}

  @Cron('0 0 0 * * *')
  async scheduleDailyReports() {
    this.logger.log('⏰ 开始触发每日零点错词日报调度...');
    try {
      const users = await this.prisma.user.findMany({
        where: {
          isTimingTask: true,
          email: { not: null },
        },
      });

      let dispatchedCount = 0;
      for (const user of users) {
        if (!user.email) continue;
        const mistakeCount = await this.prisma.wordBookRecord.count({
          where: { userId: user.id, isMaster: false },
        });

        if (mistakeCount > 0) {
          await this.reportQueue.add(
            'send-daily-report',
            { userId: user.id, email: user.email },
            {
              attempts: 3,
              backoff: { type: 'exponential', delay: 5000 },
              removeOnComplete: true,
            },
          );
          dispatchedCount++;
        }
      }
      this.logger.log(`✅ 调度完成，共向消息队列投递 ${dispatchedCount} 个用户的日报任务。`);
    } catch (error) {
      this.logger.error('❌ 每日零点错词日报调度失败', error);
    }
  }
}
```

- [ ] **步骤 2：创建 `report.processor.ts` 队列消费者**

创建文件 `server/apps/server/src/report/report.processor.ts`：
```typescript
import { Processor, WorkerHost } from '@nestjs/bullmq';
import { Logger } from '@nestjs/common';
import { Job } from 'bullmq';
import { PrismaService } from '@libs/shared/prisma/prisma.service';
import { EmailService } from '@libs/shared/email/email.service';

@Processor('daily-report')
export class ReportProcessor extends WorkerHost {
  private readonly logger = new Logger(ReportProcessor.name);

  constructor(
    private readonly prisma: PrismaService,
    private readonly emailService: EmailService,
  ) {
    super();
  }

  async process(job: Job<{ userId: string; email: string }>): Promise<any> {
    const { userId, email } = job.data;
    this.logger.log(`⚙️ 正在处理用户 ${userId} (${email}) 的错词日报...`);

    const unmasteredCount = await this.prisma.wordBookRecord.count({
      where: { userId, isMaster: false },
    });
    const masteredCount = await this.prisma.wordBookRecord.count({
      where: { userId, isMaster: true },
    });

    if (unmasteredCount === 0) {
      this.logger.log(`用户 ${userId} 当前错题已清零，取消发送。`);
      return;
    }

    const topMistakes = await this.prisma.wordBookRecord.findMany({
      where: { userId, isMaster: false },
      orderBy: { updatedAt: 'desc' },
      take: 10,
      include: { word: true },
    });

    const rowsHtml = topMistakes
      .map((record) => {
        const w = record.word;
        const phonetic = w.phonetic ? `[${w.phonetic}]` : '';
        const trans = w.translation || w.definition || '暂无释义';
        return `
          <tr style="border-bottom: 1px solid #f1f5f9;">
            <td style="padding: 12px 16px; font-weight: bold; color: #1e293b; font-size: 15px;">${w.word}</td>
            <td style="padding: 12px 16px; color: #64748b; font-family: monospace;">${phonetic}</td>
            <td style="padding: 12px 16px; color: #334155;">${trans}</td>
          </tr>
        `;
      })
      .join('');

    const htmlContent = `
      <div style="max-width: 600px; margin: 0 auto; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);">
        <div style="background: linear-gradient(135deg, #4f46e5 0%, #3b82f6 100%); padding: 32px 24px; text-align: center; color: #ffffff;">
          <h1 style="margin: 0; font-size: 24px; font-weight: 700;">📚 每日英语错词攻克日报</h1>
          <p style="margin: 8px 0 0; opacity: 0.9; font-size: 14px;">坚持每日复习，让每一个生词都化为掌握！</p>
        </div>
        
        <div style="padding: 24px;">
          <div style="display: flex; background-color: #f8fafc; border-radius: 8px; padding: 16px; margin-bottom: 24px;">
            <div style="flex: 1; text-align: center; border-right: 1px solid #e2e8f0;">
              <div style="font-size: 12px; color: #64748b; text-transform: uppercase;">🔥 待攻克错题</div>
              <div style="font-size: 24px; font-weight: bold; color: #ef4444; margin-top: 4px;">${unmasteredCount}</div>
            </div>
            <div style="flex: 1; text-align: center;">
              <div style="font-size: 12px; color: #64748b; text-transform: uppercase;">✅ 累计已掌握</div>
              <div style="font-size: 24px; font-weight: bold; color: #10b981; margin-top: 4px;">${masteredCount}</div>
            </div>
          </div>

          <h3 style="margin: 0 0 12px; color: #1e293b; font-size: 16px; border-left: 4px solid #4f46e5; padding-left: 8px;">🔥 重点复习清单 (Top 10)</h3>
          <table style="width: 100%; border-collapse: collapse; text-align: left; background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 8px; overflow: hidden;">
            <thead>
              <tr style="background-color: #f8fafc; color: #475569; font-size: 13px; border-bottom: 1px solid #e2e8f0;">
                <th style="padding: 10px 16px;">单词</th>
                <th style="padding: 10px 16px;">音标</th>
                <th style="padding: 10px 16px;">释义</th>
              </tr>
            </thead>
            <tbody>
              ${rowsHtml}
            </tbody>
          </table>
          <p style="font-size: 12px; color: #94a3b8; text-align: center; margin-top: 12px;">（仅展示近期最需要巩固的 10 个核心词汇，完整错题库请登录网页查看）</p>

          <div style="text-align: center; margin-top: 32px; padding-top: 24px; border-top: 1px solid #f1f5f9;">
            <p style="color: #475569; font-size: 14px; margin-bottom: 16px;">今天只需花 5 分钟，立刻登录平台【专属错题本】进行特训消杀吧！</p>
          </div>
        </div>
      </div>
    `;

    const success = await this.emailService.sendEmail(
      email,
      '📚 每日英语错词攻克日报 - 助您轻松背单词',
      htmlContent,
    );

    if (!success) {
      throw new Error(`邮件发送至 ${email} 失败`);
    }
    this.logger.log(`✅ 成功发送错词日报至 ${email}`);
  }
}
```

---

### 任务 3：创建测试触发器接口与验证 (`ReportController`)

**文件：**
- 创建：`server/apps/server/src/report/report.controller.ts`

- [ ] **步骤 1：创建 `report.controller.ts` 手动测试触发器**

创建文件 `server/apps/server/src/report/report.controller.ts`：
```typescript
import { Controller, Post, UseGuards, Req } from '@nestjs/common';
import { AuthGuard } from '@libs/shared/auth/auth.guard';
import { InjectQueue } from '@nestjs/bullmq';
import { Queue } from 'bullmq';
import { PrismaService } from '@libs/shared/prisma/prisma.service';
import { ResponseService } from '@libs/shared/response/response.service';
import type { Request } from 'express';

@Controller('learn/report')
export class ReportController {
  constructor(
    @InjectQueue('daily-report') private readonly reportQueue: Queue,
    private readonly prisma: PrismaService,
    private readonly response: ResponseService,
  ) {}

  @UseGuards(AuthGuard)
  @Post('test-trigger')
  async triggerTestReport(@Req() req: Request) {
    const userId = req.user.userId;
    const user = await this.prisma.user.findUnique({ where: { id: userId } });

    if (!user || !user.email) {
      return this.response.error(null, '当前登录用户未绑定邮箱，无法触发测试发信');
    }

    const mistakeCount = await this.prisma.wordBookRecord.count({
      where: { userId, isMaster: false },
    });

    if (mistakeCount === 0) {
      return this.response.error(null, '当前错题本为空，无需发送日报');
    }

    await this.reportQueue.add(
      'send-daily-report',
      { userId: user.id, email: user.email },
      { attempts: 1 },
    );

    return this.response.success(null, `已成功向消息队列投递测试发信任务至 ${user.email}，请稍候查收邮箱`);
  }
}
```

- [ ] **步骤 2：验证后端编译构建**

在 `server` 目录下运行编译验证：
```bash
cd D:\english\server && pnpm build
```
预期：构建通过，零类型报错。
