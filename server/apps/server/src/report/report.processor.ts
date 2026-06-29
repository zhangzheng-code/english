import { Processor, WorkerHost } from '@nestjs/bullmq';

@Processor('daily-report')
export class ReportProcessor extends WorkerHost {
  async process(): Promise<any> {}
}
