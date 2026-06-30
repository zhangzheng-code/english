<template>
    <div class="min-h-[60vh] bg-zinc-50/80">
        <div class="w-[1200px] mx-auto px-4 pt-12 pb-24">
            <header class="mb-10 text-center relative">
                <div class="flex justify-end mb-2 sm:absolute sm:right-0 sm:top-0 sm:mb-0">
                    <el-button type="danger" plain round @click="showMistakeDrawer = true">
                        📖 待攻克错题 ({{ mistakeCount }})
                    </el-button>
                </div>
                <h1 class="text-3xl font-bold text-zinc-900 tracking-tight sm:text-4xl">{{ title }}</h1>
                <p class="mt-3 text-zinc-500 text-sm">请根据释义和翻译拼写单词</p>
            </header>

            <el-skeleton v-if="isLoading" :rows="10" animated />

            <div v-if="list.length === 0" class="flex justify-center py-20">
                <el-empty description="暂无单词或您尚未购买该课程" />
            </div>

            <template v-else>
                <!-- 本组已学完 -->
                <div v-if="currentIndex >= list.length"
                    class="text-center py-16 px-6 bg-white rounded-2xl border border-zinc-100 shadow-sm">
                    <p class="text-zinc-600 mb-6">本组 10 个词已学完</p>
                    <el-button type="primary" size="large" @click="saveWordMaster">
                        再练一组
                    </el-button>
                </div>

                <!-- 当前单词卡片 -->
                <div v-else>
                    <div class="mb-4 flex items-center justify-between text-sm text-zinc-500">
                        <span>第 {{ currentIndex + 1 }} / {{ list.length }} 个</span>
                    </div>
                    <article class="bg-white rounded-2xl border border-zinc-100 shadow-sm overflow-hidden">
                        <div class="p-8 sm:p-10 relative">
                            <div class="flex justify-center mb-6">
                                <div :class="{ 'filter blur-md select-none': isWordBlurred }"
                                    class="transition-all duration-300 min-h-10 flex flex-col items-center text-center">
                                    <div class="text-2xl sm:text-3xl font-bold text-indigo-600 tracking-tight">
                                        {{ currentWord?.word }}
                                    </div>
                                    <div class="flex items-center justify-center gap-2 mt-1">
                                        <span v-if="currentWord?.phonetic" class="text-base text-zinc-500 font-mono">
                                            {{ currentWord.phonetic }}
                                        </span>
                                        <el-icon v-if="currentWord?.word"
                                            class="shrink-0 cursor-pointer text-slate-400 hover:text-indigo-400 transition-colors"
                                            :size="18" title="发音" @click="playAudio(currentWord!.word)">
                                            <VideoPlay />
                                        </el-icon>
                                    </div>
                                </div>
                                <el-icon
                                    class="absolute! right-10 top-10 cursor-pointer text-slate-400 hover:text-indigo-400 transition-colors"
                                    :size="18" :title="isWordBlurred ? '点击显示单词' : '点击隐藏单词'"
                                    @click="isWordBlurred = !isWordBlurred">
                                    <View v-if="isWordBlurred" />
                                    <Hide v-else />
                                </el-icon>
                            </div>
                            <!-- 释义 -->
                            <div class="mb-4 rounded-lg bg-zinc-50/80 border border-zinc-100 p-4">
                                <p class="text-xs font-medium text-zinc-400 uppercase tracking-wide mb-2">释义</p>
                                <div class="text-zinc-700 leading-relaxed prose prose-sm max-w-none"
                                    v-html="currentWord?.definition" />
                            </div>
                            <!-- 翻译 -->
                            <div class="rounded-lg bg-zinc-50/80 border border-zinc-100 p-4">
                                <p class="text-xs font-medium text-zinc-400 uppercase tracking-wide mb-2">翻译</p>
                                <div class="text-zinc-600 leading-relaxed whitespace-pre-line prose prose-sm max-w-none"
                                    v-html="currentWord?.translation" />
                            </div>
                            <!--拼写练习-->
                            <div class="rounded-lg bg-zinc-50/80 border border-zinc-100 p-4">
                                <p class="text-xs font-medium text-zinc-400 uppercase tracking-wide mb-2">拼写</p>
                                <div class="flex items-center gap-2 justify-center">
                                    <input :maxlength="1" ref="inputRefs" @input="onInput(index)"
                                        v-for="(item, index) in wordList" @keydown="onKeyDown(index, $event)"
                                        :key="index" type="text" v-model="item.input"
                                        :class="{ 'border-indigo-500!': item.isTrue === true, 'border-red-500!': item.isTrue === false }"
                                        class="border-0 border-b-2 border-zinc-300 focus:border-indigo-500 bg-transparent outline-none w-10 text-center text-2xl font-bold" />
                                </div>
                                <div class="mt-4 flex justify-center">
                                    <el-button type="warning" link @click="captureMistake">
                                        💡 不会拼？按 Tab 或点此显示答案并记入错题本
                                    </el-button>
                                </div>
                            </div>
                            <!--控制按钮-->
                            <div class="flex justify-end gap-2">
                                <el-button type="primary" :disabled="isAutoAdvancing" @click="pagePrev">
                                    上一个
                                </el-button>
                                <el-button type="primary" :disabled="isAutoAdvancing" @click="pageNext">
                                    下一个
                                </el-button>
                            </div>
                        </div>
                    </article>
                </div>
            </template>
        </div>
        <el-drawer v-model="showMistakeDrawer" title="待攻克错题本" size="500px" destroy-on-close>
            <MistakeChallenge @resolved="loadMistakes" />
        </el-drawer>
    </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, nextTick, computed, useTemplateRef } from 'vue';
import { useRoute } from 'vue-router';
import type { Word } from '@en/common/word';
import { useAudio } from '@/hooks/useAudio';
import { View, Hide, VideoPlay } from '@element-plus/icons-vue';
import { getWordList, saveWordMaster as saveWordMasterApi, recordMistake, getMistakeList } from '@/apis/learn';
import { ElMessage } from 'element-plus';
import { useUserStore } from '@/stores/user';
import MistakeChallenge from '../components/MistakeChallenge.vue';
const userStore = useUserStore();
const inputRefs = useTemplateRef<HTMLInputElement[]>('inputRefs');
interface WordItem {
    word: string;
    input: string;
    isTrue: boolean | undefined;
}
const { playAudio } = useAudio({}); //发音的api
const route = useRoute();
const title = route.params.title || '我的课程'
const isLoading = ref(false); //默认不加载
const list = ref<Word[]>([]) //单词列表 [{},{},....] list[currentIndex.value]
const currentIndex = ref(0); //当前单词索引
const isWordBlurred = ref(true); //是否模糊显示单词 默认是模糊的
const currentWord = computed<Word | undefined>(() => list.value[currentIndex.value]); //当前的单词
const wordList = ref<WordItem[]>([]); //拼写列表
const mistakeCount = ref(0);
const showMistakeDrawer = ref(false);
const isAutoAdvancing = ref(false);

const timerIds: number[] = [];
const addTimer = (fn: () => void, delay: number) => {
    const id = window.setTimeout(() => {
        fn();
        const idx = timerIds.indexOf(id);
        if (idx !== -1) timerIds.splice(idx, 1);
    }, delay);
    timerIds.push(id);
    return id;
};

const loadMistakes = async () => {
    try {
        const res = await getMistakeList();
        if (res.success && res.data) {
            mistakeCount.value = res.data.length;
        }
    } catch (e) {
        console.error(e);
    }
};

watch(currentWord, (newWord) => {
    isWordBlurred.value = true;
    isAutoAdvancing.value = false;
    const current = newWord?.word || '';
    wordList.value = Array.from(current).map((item) => ({
        word: item,
        input: '',
        isTrue: undefined,
    }));
    if (newWord?.word) {
        addTimer(() => playAudio(newWord.word), 150);
    }
    nextTick(() => {
        if (inputRefs.value && inputRefs.value.length > 0) {
            inputRefs.value[0].focus();
        }
    });
}, { immediate: true });

//上一个
const pagePrev = () => {
    if (isAutoAdvancing.value) return;
    if (currentIndex.value <= 0) return;
    currentIndex.value--
}
//下一个
const pageNext = () => {
    if (isAutoAdvancing.value) return;
    if(wordList.value.some(item => !item.isTrue)) {
        ElMessage.error('请先完成拼写')
        return;
    }
    currentIndex.value++
}

//保存的方法
const saveWordMaster = async () => {
    //找到单词所有的id并且是一个数组
    const wordIds = list.value.map(item => item.id);
    const res = await saveWordMasterApi(wordIds);
    if (res.success) {
        currentIndex.value = 0;
        getWordListData();
        loadMistakes();
        userStore.updateUserWordNumber(res.data.wordNumber);
        ElMessage.success(res.message);
    } else {
        ElMessage.error(res.message);
    }
}

const captureMistake = async () => {
    if (!currentWord.value || isAutoAdvancing.value) return;
    if (currentIndex.value >= list.value.length) return;
    isAutoAdvancing.value = true;
    wordList.value.forEach(item => {
        item.input = item.word;
        item.isTrue = true;
    });
    mistakeCount.value++;
    const res = await recordMistake(currentWord.value.id);
    if (!res || !res.success) {
        mistakeCount.value--;
        ElMessage.error((res && res.message) || '加入错题本失败');
        isAutoAdvancing.value = false;
        return;
    }
    ElMessage.warning('已显示正确答案并收录入错题本！');
    addTimer(() => {
        isAutoAdvancing.value = false;
        if (currentIndex.value < list.value.length) {
            pageNext();
        }
    }, 1200);
};

const checkAllCorrect = () => {
    if (isAutoAdvancing.value) return;
    if (wordList.value.length > 0 && wordList.value.every(i => i.isTrue === true)) {
        isAutoAdvancing.value = true;
        if (currentWord.value?.word) {
            playAudio(currentWord.value.word);
        }
        addTimer(() => {
            isAutoAdvancing.value = false;
            if (currentIndex.value < list.value.length) {
                pageNext();
            }
        }, 600);
    }
};

//输入的方法
const onInput = (index: number) => {
    const current = wordList.value[index];
    current.isTrue = current.word.toLowerCase() === current.input.toLowerCase();
    nextTick(() => {
        const inputs = inputRefs.value as HTMLInputElement[]
        if (index < inputs.length - 1) { //不是最后一个输入框
            inputs[index + 1].focus() //下一个输入框聚焦
        }
    });
    checkAllCorrect();
}
//按键的方法
const onKeyDown = (index: number, event: KeyboardEvent) => {
    if (event.key === 'Tab') {
        event.preventDefault();
        captureMistake();
        return;
    }
    if (event.key === 'Backspace') {
        event.preventDefault();
        const current = wordList.value[index];
        current.input = '';
        current.isTrue = undefined;
        nextTick(() => {
            const inputs = inputRefs.value as HTMLInputElement[]
            if (index > 0) { //不是第一个输入框
                inputs[index - 1].focus()
            }
        })
    }
    //按下了一个键盘的某个字符 不是ctrl、不是windows win Mac command、不是alt键
    if (event.key.length == 1 && !event.ctrlKey && !event.metaKey && !event.altKey) {
        const current = wordList.value[index];
        if (current.input && index < wordList.value.length - 1) {
            event.preventDefault();
            wordList.value[index + 1].input = event.key;
            wordList.value[index + 1].isTrue = wordList.value[index + 1].word.toLowerCase() === event.key.toLowerCase();
            nextTick(() => {
                const inputs = inputRefs.value as HTMLInputElement[]
                inputs[index + 1].focus();
            })
        }
    }
    checkAllCorrect();
}

const getWordListData = async () => {
    isLoading.value = true;
    const res = await getWordList(route.params.courseId as string);
    isLoading.value = false;
    if (res.success) {
        list.value = res.data;
    } else {
        ElMessage.error(res.message);
    }
}

onMounted(() => {
    getWordListData();
    loadMistakes();
})

onUnmounted(() => {
    timerIds.forEach(id => clearTimeout(id));
})
</script>