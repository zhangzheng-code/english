<template>
    <div class="mistake-challenge p-2 sm:p-4">
        <!-- 顶部通栏/闯关模式切换 -->
        <div class="mb-6 rounded-2xl p-6 text-white shadow-lg relative overflow-hidden mistake-banner">
            <div class="absolute -right-6 -bottom-6 w-32 h-32 rounded-full blur-xl pointer-events-none" style="background: rgba(184,176,232,0.2);"></div>
            <div class="relative z-10 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
                <div>
                    <div class="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-white/20 backdrop-blur text-xs font-semibold mb-2">
                        <span>🔥 AI 智能特训场</span>
                    </div>
                    <h2 class="text-xl sm:text-2xl font-extrabold tracking-tight">沉浸式错题闯关消杀</h2>
                    <p class="text-xs sm:text-sm mt-1" style="color: rgba(244,164,176,0.9);">攻克弱点，化茧成蝶，每消杀一个错题都是进步</p>
                </div>
                <div class="flex items-center gap-2 self-end sm:self-auto flex-wrap">
                    <el-button size="small" type="warning" class="!rounded-full !px-3 font-bold shadow-sm" :loading="sendingReport" @click="handleSendReport">
                        📧 肉测发错词日报
                    </el-button>
                    <el-radio-group v-model="mode" size="small">
                        <el-radio-button value="challenge">🎮 闯关模式</el-radio-button>
                        <el-radio-button value="list">📋 列表概览</el-radio-button>
                    </el-radio-group>
                </div>
            </div>
        </div>

        <el-skeleton v-if="loading" :rows="6" animated />
        <div v-else-if="mistakes.length === 0" class="py-16 text-center bg-white rounded-2xl border border-zinc-100 shadow-sm">
            <div class="text-5xl mb-4 animate-bounce">🎉</div>
            <h3 class="text-lg font-bold text-zinc-800 mb-1">太棒了！错题本已清空</h3>
            <p class="text-sm text-zinc-500">您已经攻克了所有错题，继续保持！</p>
        </div>

        <!-- 闯关模式 -->
        <div v-else-if="mode === 'challenge'" class="max-w-xl mx-auto">
            <div class="flex items-center justify-between mb-3 px-1 text-sm font-medium text-zinc-600">
                <span>剩余关卡: <strong class="font-bold" style="color: var(--color-accent);">{{ mistakes.length }}</strong> 题</span>
                <span>第 {{ currentChallengeIndex + 1 }} / {{ mistakes.length }} 关</span>
            </div>
            <!-- 进度条 -->
            <div class="w-full bg-zinc-200 h-2 rounded-full mb-6 overflow-hidden">
                <div class="h-full transition-all duration-300 mistake-progress"
                     :style="{ width: `${((currentChallengeIndex) / mistakes.length) * 100}%` }"></div>
            </div>

            <div class="bg-white rounded-3xl shadow-xl p-6 sm:p-8 relative overflow-hidden text-center transition-all mistake-card">
                <div class="absolute top-4 right-4 text-xs font-bold px-3 py-1 rounded-full mistake-badge">
                    BOSS 挑战
                </div>
                
                <div class="my-8">
                    <div :class="{ 'filter blur-md select-none': isAnswerHidden }"
                         class="transition-all duration-300 min-h-16 flex flex-col items-center justify-center cursor-pointer"
                         @click="isAnswerHidden = !isAnswerHidden"
                         :title="isAnswerHidden ? '点击显示单词' : '点击隐藏单词'">
                        <span class="text-3xl sm:text-4xl font-black text-indigo-900 tracking-tight">{{ currentWord?.word }}</span>
                        <span v-if="currentWord?.phonetic" class="text-sm text-zinc-400 font-mono mt-1">{{ currentWord.phonetic }}</span>
                    </div>
                    <div class="mt-3 flex items-center justify-center gap-4 text-xs text-zinc-400">
                        <button type="button" @click="isAnswerHidden = !isAnswerHidden" class="transition-colors flex items-center gap-1 cursor-pointer mistake-action-btn">
                            <span>{{ isAnswerHidden ? '👁️ 点击查看答案' : '🙈 隐藏答案' }}</span>
                        </button>
                        <button v-if="currentWord?.word" type="button" @click="playAudio(currentWord.word)" class="transition-colors flex items-center gap-1 cursor-pointer mistake-action-btn">
                            <el-icon :size="14"><VideoPlay /></el-icon>
                            <span>播放发音</span>
                        </button>
                    </div>
                </div>

                <!-- 释义提示 -->
                <div class="bg-zinc-50 rounded-2xl p-5 mb-8 text-left border border-zinc-100 space-y-3">
                    <div>
                        <span class="text-xs font-bold text-zinc-400 uppercase tracking-wider">中文释义</span>
                        <div v-if="currentWord?.translation" class="text-base font-semibold text-zinc-800 mt-1 whitespace-pre-line leading-relaxed" v-html="currentWord.translation" />
                    </div>
                    <div v-if="currentWord?.definition" class="pt-2 border-t border-zinc-200/60">
                        <span class="text-xs font-bold text-zinc-400 uppercase tracking-wider">英文释义</span>
                        <div class="text-sm text-zinc-600 mt-1 leading-relaxed" v-html="currentWord.definition" />
                    </div>
                </div>

                <!-- 闯关操作按钮 -->
                <div class="flex items-center gap-4">
                    <button type="button" @click="nextChallengeWord" class="flex-1 py-3.5 px-4 rounded-2xl border border-zinc-200 bg-zinc-50 hover:bg-zinc-100 text-zinc-700 font-semibold text-sm transition-all cursor-pointer">
                        跳过，下次再练
                    </button>
                    <button type="button" @click="handleResolve(currentWord!.id)" :disabled="resolvingId === currentWord?.id" class="flex-1 py-3.5 px-4 rounded-2xl bg-gradient-to-r from-emerald-500 to-teal-600 hover:from-emerald-600 hover:to-teal-700 text-white font-bold text-sm shadow-lg shadow-emerald-500/25 active:scale-95 transition-all flex items-center justify-center gap-2 cursor-pointer disabled:opacity-50">
                        <span>⚡ 斩杀！攻克掌握</span>
                    </button>
                </div>
            </div>
        </div>

        <!-- 列表模式 -->
        <div v-else class="space-y-4">
            <div class="flex items-center justify-between mb-2 pb-2 border-b border-zinc-100">
                <span class="text-sm font-medium text-zinc-600">共 {{ mistakes.length }} 个错题待攻克</span>
                <el-button type="primary" link @click="fetchMistakes">刷新数据</el-button>
            </div>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div
                    v-for="word in mistakes"
                    :key="word.id"
                    class="p-5 bg-white rounded-2xl border border-zinc-200/80 shadow-xs hover:border-indigo-300 hover:shadow-md transition-all flex flex-col justify-between gap-4"
                >
                    <div>
                        <div class="flex items-start justify-between gap-2 mb-3">
                            <div class="flex items-center gap-2">
                                <span class="text-xl font-extrabold text-indigo-900">{{ word.word }}</span>
                                <span v-if="word.phonetic" class="text-xs text-zinc-400 font-mono">{{ word.phonetic }}</span>
                                <el-icon
                                    class="cursor-pointer text-slate-400 hover:text-indigo-600 transition-colors"
                                    :size="18"
                                    title="发音"
                                    @click="playAudio(word.word)"
                                >
                                    <VideoPlay />
                                </el-icon>
                            </div>
                            <el-button
                                type="success"
                                size="small"
                                round
                                :loading="resolvingId === word.id"
                                @click="handleResolve(word.id)"
                            >
                                ⚡ 攻克掌握
                            </el-button>
                        </div>
                        <div v-if="word.translation" class="text-sm font-medium text-zinc-700 bg-zinc-50 p-2.5 rounded-xl leading-relaxed whitespace-pre-line" v-html="word.translation" />
                        <div v-if="word.definition" class="text-xs text-zinc-400 mt-2 leading-relaxed line-clamp-2" v-html="word.definition" />
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue';
import type { Word } from '@en/common/word';
import { getMistakeList, resolveMistake, triggerTestReport } from '@/apis/learn';
import { useAudio } from '@/hooks/useAudio';
import { ElMessage } from 'element-plus';
import { VideoPlay } from '@element-plus/icons-vue';

const emit = defineEmits<{
    (e: 'resolved'): void;
}>();

const mode = ref<'challenge' | 'list'>('challenge');
const mistakes = ref<Word[]>([]);
const loading = ref(false);
const sendingReport = ref(false);
const resolvingId = ref<string | null>(null);
const currentChallengeIndex = ref(0);
const isAnswerHidden = ref(true);
const { playAudio } = useAudio({});

const handleSendReport = async () => {
    try {
        sendingReport.value = true;
        const res = await triggerTestReport();
        if (res.code === 200) {
            ElMessage.success(res.message || '测试日报投递成功！请稍候查收邮箱。');
        } else {
            ElMessage.error(res.message || '发送失败');
        }
    } catch (e: any) {
        ElMessage.error(e?.message || '请求发信失败');
    } finally {
        sendingReport.value = false;
    }
};

const currentWord = computed<Word | undefined>(() => mistakes.value[currentChallengeIndex.value]);

watch(currentChallengeIndex, () => {
    isAnswerHidden.value = true;
});

// 庆祝音效生成器 (Web Audio API)
const playCelebrationSound = () => {
    try {
        const AudioContext = window.AudioContext || (window as any).webkitAudioContext;
        if (!AudioContext) return;
        const ctx = new AudioContext();
        const now = ctx.currentTime;
        const freqs = [523.25, 659.25, 783.99, 1046.50]; // C5, E5, G5, C6 琶音
        freqs.forEach((freq, index) => {
            const osc = ctx.createOscillator();
            const gain = ctx.createGain();
            osc.type = 'triangle';
            osc.frequency.setValueAtTime(freq, now + index * 0.08);
            gain.gain.setValueAtTime(0.2, now + index * 0.08);
            gain.gain.exponentialRampToValueAtTime(0.001, now + index * 0.08 + 0.35);
            osc.connect(gain);
            gain.connect(ctx.destination);
            osc.start(now + index * 0.08);
            osc.stop(now + index * 0.08 + 0.35);
        });
    } catch (e) {
        console.error('AudioContext error:', e);
    }
};

const fetchMistakes = async () => {
    loading.value = true;
    try {
        const res = await getMistakeList();
        if (res.success && res.data) {
            mistakes.value = res.data;
            if (currentChallengeIndex.value >= mistakes.value.length) {
                currentChallengeIndex.value = Math.max(0, mistakes.value.length - 1);
            }
        } else {
            ElMessage.error(res.message || '获取错题失败');
        }
    } catch (e) {
        console.error(e);
    } finally {
        loading.value = false;
    }
};

const nextChallengeWord = () => {
    if (mistakes.value.length === 0) return;
    currentChallengeIndex.value = (currentChallengeIndex.value + 1) % mistakes.value.length;
};

const handleResolve = async (wordId: string) => {
    if (!wordId) return;
    resolvingId.value = wordId;
    try {
        const wordObj = mistakes.value.find(item => item.id === wordId);
        const res = await resolveMistake(wordId);
        if (res.success) {
            playCelebrationSound();
            if (wordObj?.word) {
                setTimeout(() => playAudio(wordObj.word), 300);
            }
            ElMessage({
                message: '🎉 恭喜斩杀错题！消杀成功！',
                type: 'success',
                duration: 2000
            });
            mistakes.value = mistakes.value.filter(item => item.id !== wordId);
            if (currentChallengeIndex.value >= mistakes.value.length) {
                currentChallengeIndex.value = Math.max(0, mistakes.value.length - 1);
            }
            isAnswerHidden.value = true;
            emit('resolved');
        } else {
            ElMessage.error(res.message || '操作失败');
        }
    } catch (e) {
        console.error(e);
        ElMessage.error('网络请求失败');
    } finally {
        resolvingId.value = null;
    }
};

onMounted(() => {
    fetchMistakes();
});
</script>

<style scoped>
/* 错题本莫兰迪配色 */
.mistake-banner {
    background: linear-gradient(135deg, #B8B0E8, #F4A4B0);
}

.mistake-progress {
    background: linear-gradient(90deg, #B8B0E8, #F4A4B0);
}

.mistake-card {
    border: 2px solid rgba(184, 176, 232, 0.2);
}

.mistake-badge {
    background: rgba(184, 176, 232, 0.1);
    color: #B8B0E8;
    border: 1px solid rgba(184, 176, 232, 0.3);
}

.mistake-action-btn {
    color: #AAAAAA;
}

.mistake-action-btn:hover {
    color: #B8B0E8;
}
</style>
