<template>
    <div class="min-h-[60vh]">
        <div class="w-[1200px] mx-auto px-4 pt-12 pb-24">
            <!-- 标题 -->
            <header class="mb-10 text-center">
                <p class="text-sm font-medium tracking-wide uppercase mb-2" style="color: var(--color-accent);">Vocabulary Courses</p>
                <h1 class="text-3xl font-bold tracking-tight sm:text-4xl" style="color: var(--color-text-primary);">精选课程</h1>
                <p class="mt-3 text-sm max-w-md mx-auto" style="color: var(--color-text-secondary);">一次购买，长期有效 · 覆盖高考、考研、四六级、托福雅思等</p>
            </header>

            <!-- ClickHouse 遥测驱动 AI 智能个性化推荐 -->
            <div class="rounded-3xl p-6 sm:p-8 mb-10 shadow-xl relative overflow-hidden backdrop-blur-2xl"
                style="background: var(--color-accent-strong); border: 1px solid var(--color-surface-border);">
                <!-- 装饰光晕 -->
                <div class="absolute -right-12 -top-12 w-48 h-48 rounded-full blur-3xl pointer-events-none"
                    style="background: var(--color-accent-soft); opacity: 0.2;"></div>
                <div class="absolute right-1/3 -bottom-12 w-48 h-48 rounded-full blur-3xl pointer-events-none"
                    style="background: var(--color-accent); opacity: 0.2;"></div>

                <div class="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-6">
                    <div>
                        <div class="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-medium mb-3"
                            style="background: rgba(184,176,232,0.2); border: 1px solid rgba(184,176,232,0.3); color: var(--color-accent-soft);">
                            <span class="w-2 h-2 rounded-full bg-green-400 animate-pulse"></span>
                            ClickHouse 实时遥测引擎
                        </div>
                        <h2 class="text-2xl font-bold tracking-tight flex items-center gap-2" style="color: var(--color-accent-strong) === '#0D0D0D' ? 'white' : 'var(--color-text-primary)';">
                            <span>✨ 大模型个性化课程推荐</span>
                        </h2>
                        <p class="text-sm mt-1 max-w-xl leading-relaxed" style="color: var(--color-accent-soft); opacity: 0.9;">
                            基于您在平台内的生词点击、发音评测与浏览埋点，DeepSeek 智能引擎为您量身定制学习提升链路。
                        </p>
                    </div>
                    <div>
                        <button type="button" @click="fetchRecommendations" :disabled="loadingRecs"
                            class="px-6 py-3 rounded-2xl font-semibold text-sm shadow-lg active:scale-95 transition-all duration-200 flex items-center gap-2 cursor-pointer disabled:opacity-60 disabled:cursor-not-allowed shrink-0"
                            style="background: var(--color-surface); color: var(--color-text-primary);">
                            <svg v-if="loadingRecs" class="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" style="color: var(--color-text-primary);">
                                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                            </svg>
                            <span>{{ loadingRecs ? '分析近期遥测轨迹中...' : '🧠 生成我的专属推荐' }}</span>
                        </button>
                    </div>
                </div>

                <!-- 推荐结果展示列表 -->
                <div v-if="recommendations.length > 0" class="mt-6 pt-6 grid grid-cols-1 md:grid-cols-2 gap-4" style="border-top: 1px solid rgba(255,255,255,0.1);">
                    <div v-for="(rec, idx) in recommendations" :key="idx"
                        class="backdrop-blur-md rounded-2xl p-4 transition-all flex flex-col justify-between"
                        style="background: rgba(255,255,255,0.1); border: 1px solid rgba(255,255,255,0.1);"
                        @mouseenter="(e) => ((e.currentTarget as HTMLElement).style.background = 'rgba(255,255,255,0.15)')"
                        @mouseleave="(e) => ((e.currentTarget as HTMLElement).style.background = 'rgba(255,255,255,0.1)')">
                        <div>
                            <div class="flex items-center justify-between gap-2 mb-2">
                                <h3 class="font-bold text-lg truncate" style="color: white;">{{ rec.title }}</h3>
                                <span class="px-2.5 py-0.5 rounded-full text-xs font-semibold shrink-0"
                                    style="background: rgba(184,176,232,0.2); color: var(--color-accent-soft);">
                                    匹配度 {{ (rec.confidence * 100).toFixed(0) }}%
                                </span>
                            </div>
                            <p class="text-sm leading-relaxed" style="color: rgba(244,164,176,0.9);">{{ rec.reason }}</p>
                        </div>
                        <div class="mt-4 pt-3 flex justify-end" style="border-top: 1px solid rgba(255,255,255,0.1);">
                            <button type="button" @click="handleRecClick(rec)"
                                class="text-xs font-semibold px-4 py-1.5 rounded-xl transition-colors cursor-pointer"
                                style="background: var(--color-accent); color: white;">
                                立即查看课程 →
                            </button>
                        </div>
                    </div>
                </div>
            </div>

            <el-tabs type="card" v-model="currentTab" @tab-change="getList">
                <el-tab-pane name="list" label="精选课程"></el-tab-pane>
                <el-tab-pane v-if="userStore.user?.id" name="my" label="我的课程"></el-tab-pane>
                <el-tab-pane v-if="userStore.user?.id" name="mistakes" label="📖 专属错题本"></el-tab-pane>
            </el-tabs>

            <div v-if="currentTab === 'mistakes'" class="mt-4">
                <MistakeChallenge @resolved="getList" />
            </div>
            <template v-else>
                <!-- 课程卡片 3 列 -->
                <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
                    <article v-for="item in list" :key="item.id"
                        class="group rounded-2xl overflow-hidden shadow-sm hover:shadow-lg transition-all duration-300 flex flex-col"
                        :style="{
                            background: 'var(--color-surface)',
                            border: '1px solid var(--color-surface-border)'
                        }"
                        @mouseenter="(e) => ((e.currentTarget as HTMLElement).style.borderColor = 'var(--color-accent)')"
                        @mouseleave="(e) => ((e.currentTarget as HTMLElement).style.borderColor = 'var(--color-surface-border)')">
                        <div class="relative aspect-4/3 overflow-hidden" style="background: var(--color-surface-hover);">
                            <img :src="imageSrc(item.url)" :alt="item.name"
                                class="absolute inset-0 w-full h-full object-cover group-hover:scale-105 transition-transform duration-500 ease-out" />
                            <div
                                class="absolute top-3 left-3 px-2.5 py-1 rounded-lg backdrop-blur text-xs font-medium shadow-sm"
                                style="background: rgba(255,255,255,0.9); color: var(--color-text-secondary);">
                                词汇</div>
                        </div>
                        <div class="p-5 flex-1 flex flex-col">
                            <h2 class="text-base font-semibold line-clamp-1" style="color: var(--color-text-primary);">{{ item.name }}</h2>
                            <p class="mt-2 text-sm line-clamp-2 leading-relaxed flex-1" style="color: var(--color-text-secondary);">{{ item.description }}
                            </p>
                            <div class="mt-4 pt-4 flex items-center justify-between gap-3" style="border-top: 1px solid var(--color-surface-border);">
                                <span class="text-xs truncate" style="color: var(--color-text-muted);">讲师 {{ item.teacher }}</span>
                                <span class="text-lg font-bold shrink-0" style="color: var(--color-accent);">¥{{ item.price }}</span>
                            </div>
                            <button type="button" @click="openPay(item)"
                                class="mt-4 w-full py-2.5 rounded-xl text-sm font-medium transition-colors cursor-pointer"
                                :style="{
                                    color: 'var(--color-accent)',
                                    border: '1px solid var(--color-accent)',
                                    background: 'var(--color-surface)'
                                }"
                                @mouseenter="(e) => ((e.currentTarget as HTMLElement).style.background = 'var(--color-surface-hover)')"
                                @mouseleave="(e) => ((e.currentTarget as HTMLElement).style.background = 'var(--color-surface)')">
                                {{ currentTab === 'list' ? '购买课程' : '学习课程' }}
                            </button>
                        </div>
                    </article>
                </div>
                <el-empty v-if="list.length === 0" description="暂无课程" />
            </template>
        </div>
        <CoursePay v-model="payVisible" :course="selectedCourse" @paid="onPaid" />
    </div>
</template>
<script setup lang="ts">
import { ref, onMounted } from 'vue';
import type { CourseList } from '@en/common/course';
import { getCourseList, getMyCourse, getCourseRecommendations, type CourseRecommendation } from '@/apis/course';
import { getFileUrl } from '@/apis';
import CoursePay from './components/Pay.vue';
import MistakeChallenge from './components/MistakeChallenge.vue';
import type { Course } from '@en/common/course';
import { useLogin } from '@/hooks/useLogin';
import { useUserStore } from '@/stores/user';
import { useRouter } from 'vue-router';
import { ElMessage } from 'element-plus';

const router = useRouter();
const userStore = useUserStore();
const currentTab = ref('list');
const { login } = useLogin();
const list = ref<CourseList>([]);
const payVisible = ref(false); //控制弹框的显示
const selectedCourse = ref<Course | null>(null); //选中的课程

const loadingRecs = ref(false);
const recommendations = ref<CourseRecommendation[]>([]);

const fetchRecommendations = async () => {
    await login();
    if (!userStore.user?.id) return;
    loadingRecs.value = true;
    try {
        const res = await getCourseRecommendations();
        if (res && res.recommendations) {
            recommendations.value = res.recommendations;
            ElMessage.success('个性化推荐已生成！');
        } else {
            ElMessage.warning('未能获取推荐内容，请稍后再试');
        }
    } catch (e: any) {
        ElMessage.error(e.message || '生成推荐失败');
    } finally {
        loadingRecs.value = false;
    }
};

const handleRecClick = (rec: CourseRecommendation) => {
    const matched = list.value.find(c => c.id === rec.course_id || c.name === rec.title);
    if (matched) {
        openPay(matched);
    } else if (list.value.length > 0) {
        openPay(list.value[0]);
    }
};

const getList = async () => {
    if (currentTab.value === 'list') {
        const res = await getCourseList();
        list.value = res.data;
    } else if (currentTab.value === 'my') {
        const res = await getMyCourse();
        list.value = res.data;
    }
}
//打开支付弹框
const openPay = async (course: Course) => {
    await login();
    if (currentTab.value === 'list') {
        payVisible.value = true;
        selectedCourse.value = course;
    } else {
        router.push(`/courses/learn/${course.id}/${course.name}`);
    }
}
const imageSrc = (url: string) => getFileUrl(url)
const onPaid = () => {
    payVisible.value = false;
    if (currentTab.value === 'my') getList();
}
onMounted(() => {
    getList();
})
</script>