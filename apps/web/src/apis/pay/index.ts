import { serverApi, type Response } from '..';
import type { CreatePayDto, ResultPay } from '@en/common/pay';

export const createPay = (data: CreatePayDto) => serverApi.post('/pay/create', data) as Promise<Response<ResultPay>>;

export const verifyPay = (courseId: string) => serverApi.post('/pay/verify', { courseId }) as Promise<Response<{ purchased: boolean }>>;

export const manualCompletePay = (courseId: string) => serverApi.post('/pay/manual-complete', { courseId }) as Promise<Response<null>>;