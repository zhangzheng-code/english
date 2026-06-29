import { Controller, Post, UseGuards, Req } from '@nestjs/common';
import { AuthGuard } from '@libs/shared/auth/auth.guard';
import { InjectQueue } from '@nestjs/bullmq';
import { Queue } from 'bullmq';
import { PrismaService } from '@libs/shared/prisma/prisma.service';
import { ResponseService } from '@libs/shared/response/response.service';
import type { Request } from 'express';
import type { DailyReportJobData } from './report.processor';

@Controller('learn/report')
export class ReportController {
  constructor(
    @InjectQueue('daily-report') private readonly reportQueue: Queue<DailyReportJobData>,
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

    return this.response.success({ message: `已成功向消息队列投递测试发信任务至 ${user.email}，请稍候查收邮箱` });
  }
}
