import { Processor, WorkerHost, OnWorkerEvent } from '@nestjs/bullmq';
import { Logger } from '@nestjs/common';
import { Job } from 'bullmq';
import { PrismaService } from '@libs/shared/prisma/prisma.service';
import { EmailService } from '@libs/shared/email/email.service';

export interface DailyReportJobData {
  userId: string;
  email: string;
}

@Processor('daily-report')
export class ReportProcessor extends WorkerHost {
  private readonly logger = new Logger(ReportProcessor.name);

  constructor(
    private readonly prisma: PrismaService,
    private readonly emailService: EmailService,
  ) {
    super();
  }

  async process(job: Job<DailyReportJobData>): Promise<void> {
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
        const w = record?.word;
        if (!w) return '';
        const wordText = w?.word || '未知单词';
        const phonetic = w?.phonetic ? `[${w.phonetic}]` : '';
        const trans = w?.translation || w?.definition || '暂无释义';
        return `
          <tr style="border-bottom: 1px solid #f1f5f9;">
            <td style="padding: 12px 16px; font-weight: bold; color: #1e293b; font-size: 15px;">${wordText}</td>
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

  @OnWorkerEvent('failed')
  onFailed(job: Job<DailyReportJobData> | undefined, error: Error) {
    this.logger.error(
      `❌ 处理错词日报任务失败: Job ID: ${job?.id}, User ID: ${job?.data?.userId}, Email: ${job?.data?.email}`,
      error?.stack || error,
    );
  }
}
