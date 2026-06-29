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
