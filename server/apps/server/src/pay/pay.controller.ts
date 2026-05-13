import { Controller, Post, Body,UseGuards ,Req,All} from '@nestjs/common';
import { PayService } from './pay.service';
import type { CreatePayDto } from '@en/common/pay';
import { AuthGuard } from '@libs/shared/auth/auth.guard';
import type { Request } from 'express';
@Controller('pay')
export class PayController {
  constructor(private readonly payService: PayService) {}

  @UseGuards(AuthGuard)
  @Post('create')
  create(@Body() createPayDto: CreatePayDto, @Req() req: Request) {
    const user = req.user;
    return this.payService.create(createPayDto,user);
  }

  @All('notify')
  notify(@Req() req: Request) {
    return this.payService.notify(req);
  }

  @UseGuards(AuthGuard)
  @Post('verify')
  verify(@Body('courseId') courseId: string, @Req() req: Request) {
    return this.payService.verify(courseId, req.user.userId);
  }

  @UseGuards(AuthGuard)
  @Post('manual-complete')
  manualComplete(@Body('courseId') courseId: string, @Req() req: Request) {
    return this.payService.manualComplete(courseId, req.user.userId);
  }

}
