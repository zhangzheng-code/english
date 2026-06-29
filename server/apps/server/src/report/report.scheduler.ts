import { Injectable, Logger } from '@nestjs/common';
import { Cron } from '@nestjs/schedule';
import { InjectQueue } from '@nestjs/bullmq';
import { Queue } from 'bullmq';
import { PrismaService } from '@libs/shared/prisma/prisma.service';

export interface DailyReportJobData {
  userId: string;
  email: string;
}

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
          wordBookRecords: {
            some: {
              isMaster: false,
            },
          },
        },
      });

      const todayStr = new Date().toISOString().slice(0, 10);
      let dispatchedCount = 0;

      for (const user of users) {
        if (!user.email) continue;
        try {
          const jobData: DailyReportJobData = {
            userId: user.id,
            email: user.email,
          };
          await this.reportQueue.add(
            'send-daily-report',
            jobData,
            {
              jobId: `daily-report-${user.id}-${todayStr}`,
              attempts: 3,
              backoff: { type: 'exponential', delay: 5000 },
              removeOnComplete: true,
            },
          );
          dispatchedCount++;
        } catch (error) {
          this.logger.error(`❌ 向消息队列投递用户 ${user.id} (${user.email}) 日报任务失败`, error);
        }
      }
      this.logger.log(`✅ 调度完成，共向消息队列投递 ${dispatchedCount} 个用户的日报任务。`);
    } catch (error) {
      this.logger.error('❌ 每日零点错词日报调度失败', error);
    }
  }
}
