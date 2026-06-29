import { serverApi, type Response } from '..';
import type { ResultLearn } from '@en/common/learn';
import type { Word } from '@en/common/word';
export const getWordList = (courseId: string) => serverApi.get(`/learn/word/${courseId}`) as Promise<Response<Word[]>>;
export const saveWordMaster = (wordIds: string[]) => serverApi.post(`/learn/word/master`, { wordIds }) as Promise<Response<ResultLearn>>;
export const recordMistake = (wordId: string) => serverApi.post('/learn/word/mistake', { wordId }) as Promise<Response<any>>;
export const getMistakeList = () => serverApi.get('/learn/word/mistakes') as Promise<Response<Word[]>>;
export const resolveMistake = (wordId: string) => serverApi.post('/learn/word/mistake-resolve', { wordId }) as Promise<Response<any>>;
export const triggerTestReport = () => serverApi.post('/learn/report/test-trigger') as Promise<Response<any>>;