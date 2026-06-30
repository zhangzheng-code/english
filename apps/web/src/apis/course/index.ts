import { serverApi, aiApi, type Response } from '..';
import type { CourseList } from '@en/common/course';

export interface CourseRecommendation {
    course_id: string;
    title: string;
    reason: string;
    confidence: number;
}

export interface RecommendationResponse {
    recommendations: CourseRecommendation[];
}

export const getCourseList = () => serverApi.get('/course/list') as Promise<Response<CourseList>>;

export const getMyCourse = () => serverApi.get('/course/my') as Promise<Response<CourseList>>;

export const getCourseRecommendations = () => aiApi.get('/recommend') as Promise<RecommendationResponse>;