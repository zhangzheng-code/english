<template>
    <div class="min-h-[60vh] bg-zinc-50/80">
        <div class="w-[1200px] mx-auto px-4 pt-12 pb-24">
            <!-- 标题 -->
            <header class="mb-10 text-center">
                <p class="text-sm font-medium text-indigo-600 tracking-wide uppercase mb-2">Vocabulary Courses</p>
                <h1 class="text-3xl font-bold text-zinc-900 tracking-tight sm:text-4xl">精选课程</h1>
                <p class="mt-3 text-zinc-500 text-sm max-w-md mx-auto">一次购买，长期有效 · 覆盖高考、考研、四六级、托福雅思等</p>
            </header>

            <!-- ClickHouse 遥测驱动 AI 智能个性化推荐 -->
            <div class="bg-gradient-to-r from-indigo-900 via-purple-900 to-slate-900 rounded-3xl p-6 sm:p-8 mb-10 text-white shadow-xl relative overflow-hidden border border-purple-500/20">
                <!-- 装饰光晕 -->
                <div class="absolute -right-12 -top-12 w-48 h-48 bg-purple-500/20 rounded-full blur-3xl pointer-events-none"></div>
                <div class="absolute right-1/3 -bottom-12 w-48 h-48 bg-indigo-500/20 rounded-full blur-3xl pointer-events-none"></div>

                <div class="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-6">
                    <div>
                        <div class="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-purple-500/20 border border-purple-400/30 text-purple-200 text-xs font-medium mb-3">
                            <span class="w-2 h-2 rounded-full bg-green-400 animate-pulse"></span>
                            ClickHouse 实时遥测引擎
                        </div>
                        <h2 class="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
                            <span>✨ 大模型个性化课程推荐</span>
                        </h2>
                        <p class="text-purple-200/80 text-sm mt-1 max-w-xl leading-relaxed">
                            基于您在平台内的生词点击、发音评测与浏览埋点，DeepSeek 智能引擎为您量身定制学习提升链路。
                        </p>
                    </div>
                    <div>
                        <button type="button" @click="fetchRecommendations" :disabled="loadingRecs"
                            class="px-6 py-3 rounded-2xl bg-white text-indigo-900 font-semibold text-sm shadow-lg shadow-white/10 hover:bg-purple-50 active:scale-95 transition-all duration-200 flex items-center gap-2 cursor-pointer disabled:opacity-60 disabled:cursor-not-allowed shrink-0">
                            <svg v-if="loadingRecs" class="animate-spin h-4 w-4 text-indigo-900" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                            </svg>
                            <span>{{ loadingRecs ? '分析近期遥测轨迹中...' : '🧠 生成我的专属推荐' }}</span>
                        </button>
                    </div>
                </div>

                <!-- 推荐结果展示列表 -->
                <div v-if="recommendations.length > 0" class="mt-6 pt-6 border-t border-white/10 grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div v-for="(rec, idx) in recommendations" :key="idx" 
                        class="bg-white/10 backdrop-blur-md rounded-2xl p-4 border border-white/10 hover:bg-white/15 transition-all flex flex-col justify-between">
                        <div>
                            <div class="flex items-center justify-between gap-2 mb-2">
                                <h3 class="font-bold text-lg text-white truncate">{{ rec.title }}</h3>
                                <span class="px-2.5 py-0.5 rounded-full bg-purple-400/20 text-purple-200 text-xs font-semibold shrink-0">
                                    匹配度 {{ (rec.confidence * 100).toFixed(0) }}%
                                </span>
                            </div>
                            <p class="text-sm text-purple-100/90 leading-relaxed">{{ rec.reason }}</p>
                        </div>
                        <div class="mt-4 pt-3 border-t border-white/10 flex justify-end">
                            <button type="button" @click="handleRecClick(rec)"
                                class="text-xs font-semibold px-4 py-1.5 rounded-xl bg-indigo-500 hover:bg-indigo-600 text-white transition-colors cursor-pointer">
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
                        class="group bg-white rounded-2xl overflow-hidden border border-zinc-100 shadow-sm hover:shadow-lg hover:shadow-indigo-500/5 hover:border-indigo-100 transition-all duration-300 flex flex-col">
                        <div class="relative aspect-4/3 bg-zinc-100 overflow-hidden">
                            <img :src="imageSrc(item.url)" :alt="item.name"
                                class="absolute inset-0 w-full h-full object-cover group-hover:scale-105 transition-transform duration-500 ease-out" />
                            <div
                                class="absolute top-3 left-3 px-2.5 py-1 rounded-lg bg-white/90 backdrop-blur text-xs font-medium text-zinc-600 shadow-sm">
                                词汇</div>
                        </div>
                        <div class="p-5 flex-1 flex flex-col">
                            <h2 class="text-base font-semibold text-zinc-900 line-clamp-1">{{ item.name }}</h2>
                            <p class="mt-2 text-sm text-zinc-500 line-clamp-2 leading-relaxed flex-1">{{ item.description }}
                            </p>
                            <div class="mt-4 pt-4 border-t border-zinc-100 flex items-center justify-between gap-3">
                                <span class="text-xs text-zinc-400 truncate">讲师 {{ item.teacher }}</span>
                                <span class="text-lg font-bold text-indigo-600 shrink-0">¥{{ item.price }}</span>
                            </div>
                            <button type="button" @click="openPay(item)"
                                class="mt-4 w-full py-2.5 rounded-xl text-sm font-medium text-indigo-600 border border-indigo-200 bg-white hover:bg-indigo-50 transition-colors cursor-pointer">
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