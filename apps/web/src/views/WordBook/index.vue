<template>
    <div class="w-[1200px] mx-auto mt-10 rounded-[20px] p-20 shadow-lg" style="background: var(--color-surface);">
        <div class="h-20">
            <div class="flex items-center gap-2">
                <el-icon size="20" :style="{ color: 'var(--color-accent)' }">
                    <Reading />
                </el-icon>
                <span class="text-2xl font-bold" style="color: var(--color-text-primary);">词库列表</span>
            </div>
            <div class="text-sm" style="color: var(--color-text-secondary);">词典来源：牛津、柯林斯、BNC、FRQ、高考、中考、GRE、TOEFL、IELTS、大学英语六级、大学英语四级、考研</div>
        </div>
        <div class="flex items-center mb-10">
            <el-input @keyup.enter="searchWord" class="mr-10" v-model="query.word" placeholder="请输入单词"></el-input>
            <el-checkbox v-model="query.gk">高考</el-checkbox>
            <el-checkbox v-model="query.zk">中考</el-checkbox>
            <el-checkbox v-model="query.gre">GRE</el-checkbox>
            <el-checkbox v-model="query.toefl">TOEFL</el-checkbox>
            <el-checkbox v-model="query.ielts">IELTS</el-checkbox>
            <el-checkbox v-model="query.cet6">六级</el-checkbox>
            <el-checkbox v-model="query.cet4">四级</el-checkbox>
            <el-checkbox v-model="query.ky">考研</el-checkbox>
            <el-button @click="searchWord" class="ml-10" type="primary">搜索</el-button>
        </div>
        <div class="grid grid-cols-3 gap-2">
            <div class="rounded-[10px] p-4 cursor-pointer transition-all duration-200 shadow-sm hover:shadow-md h-[220px]"
                :style="{
                    background: 'var(--color-surface)',
                    border: '1px solid var(--color-surface-border)',
                    color: 'var(--color-text-primary)'
                }"
                @mouseenter="(e) => (e.currentTarget as HTMLElement).style.background = 'var(--color-surface-hover)'"
                @mouseleave="(e) => (e.currentTarget as HTMLElement).style.background = 'var(--color-surface)'"
                v-for="item in list" :key="item.id">
                <div class="">
                    <div class="text-sm font-semibold mb-1" style="color: var(--color-accent);">{{ item.word }}</div>
                    <div class="text-sm mb-1 flex items-center gap-2" style="color: var(--color-text-muted);">
                        {{ item.phonetic }}
                        <el-icon size="18" :style="{ color: 'var(--color-accent)' }" @click="playAudio(item.word)">
                            <VideoPlay />
                        </el-icon>
                    </div>
                    <div class="text-sm mb-1 overflow-hidden line-clamp-2" style="color: var(--color-text-primary);">{{ item.definition }}</div>
                    <div v-html="item.translation" class="text-sm mb-1 overflow-hidden line-clamp-2" style="color: var(--color-text-secondary);">
                    </div>
                    <div class="text-sm mt-3 flex items-center gap-2 flex-wrap">
                        <span v-if="item.gk" class="px-2 py-0.5 rounded-full text-xs" style="background: var(--color-accent-soft); color: var(--color-text-primary);">高考</span>
                        <span v-if="item.zk" class="px-2 py-0.5 rounded-full text-xs" style="background: var(--color-accent-soft); color: var(--color-text-primary);">中考</span>
                        <span v-if="item.gre" class="px-2 py-0.5 rounded-full text-xs" style="background: var(--color-accent-soft); color: var(--color-text-primary);">GRE</span>
                        <span v-if="item.toefl" class="px-2 py-0.5 rounded-full text-xs" style="background: var(--color-accent-soft); color: var(--color-text-primary);">TOEFL</span>
                        <span v-if="item.ielts" class="px-2 py-0.5 rounded-full text-xs" style="background: var(--color-accent-soft); color: var(--color-text-primary);">IELTS</span>
                        <span v-if="item.cet6" class="px-2 py-0.5 rounded-full text-xs" style="background: var(--color-accent-soft); color: var(--color-text-primary);">六级</span>
                        <span v-if="item.cet4" class="px-2 py-0.5 rounded-full text-xs" style="background: var(--color-accent-soft); color: var(--color-text-primary);">四级</span>
                        <span v-if="item.ky" class="px-2 py-0.5 rounded-full text-xs" style="background: var(--color-accent-soft); color: var(--color-text-primary);">考研</span>
                    </div>
                </div>
            </div>
            <el-pagination class="mt-10" background v-model:current-page="query.page" v-model:page-size="query.pageSize"
                :total="total" @current-change="getList" @size-change="getList" />
        </div>
    </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { getWordBookList } from '@/apis/word-book'
import type { WordQuery, WordList } from '@en/common/word'
import { Reading, VideoPlay } from '@element-plus/icons-vue'
import { useAudio } from '@/hooks/useAudio'
const { playAudio } = useAudio({})
const total = ref<WordList['total']>(0)
const list = ref<WordList['list']>([])
const query = ref<WordQuery>({
    page: 1,
    pageSize: 12,
    word: '',
    gk: false,
    zk: false,
    gre: false,
    toefl: false,
    ielts: false,
    cet6: false,
    cet4: false,
    ky: false,
})
const searchWord = () => {
    query.value.page = 1 //重置一下页数
    getList() //重新获取列表
}

const getList = async () => {
    const res = await getWordBookList(query.value)
    if (res.success) {
        total.value = res.data.total
        list.value = res.data.list
    }
}


onMounted(() => {
    getList()
})
</script>