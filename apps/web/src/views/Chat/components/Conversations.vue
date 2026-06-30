<template>
    <div :class="isCollapsed ? 'w-[68px]' : 'w-[240px]'" class="bg-white/80 backdrop-blur-2xl rounded-3xl p-3 border border-purple-100/80 shadow-md transition-all duration-500 ease-out flex flex-col h-full shrink-0">
        <!-- 头部导航与折叠开关 -->
        <div class="flex items-center justify-between pb-3 mb-2 border-b border-purple-100/60 px-2" :class="{ 'justify-center': isCollapsed }">
            <div v-if="!isCollapsed" class="flex items-center gap-2 overflow-hidden">
                <span class="text-base">🎭</span>
                <span class="text-xs font-black bg-gradient-to-r from-purple-900 to-indigo-800 bg-clip-text text-transparent tracking-wide">AI 情境角色</span>
            </div>
            <div @click="emits('toggleCollapse')" class="w-7 h-7 rounded-full bg-purple-50 hover:bg-purple-100 text-purple-700 flex items-center justify-center cursor-pointer transition-transform duration-300 hover:scale-110 shadow-2xs select-none" :title="isCollapsed ? '展开角色栏' : '收起角色栏'">
                <span class="text-[10px] font-bold">{{ isCollapsed ? '▶' : '◀' }}</span>
            </div>
        </div>

        <!-- 角色列表 -->
        <div class="flex-1 overflow-y-auto space-y-1.5 pr-0.5 custom-scrollbar">
            <template v-for="value in chatMode" :key="value.id">
                <el-tooltip :content="value.label" placement="right" :disabled="!isCollapsed">
                    <div @click="changeActive(value)" 
                        :class="[
                            active === value.id 
                                ? 'bg-gradient-to-r from-purple-600 via-indigo-600 to-purple-700 text-white font-bold shadow-md shadow-purple-500/25 scale-[1.02]' 
                                : 'text-neutral-700 hover:bg-purple-50/80 hover:text-purple-900',
                            isCollapsed ? 'p-2.5 justify-center' : 'p-3 px-3.5 gap-3'
                        ]"
                        class="rounded-2xl transition-all duration-300 cursor-pointer select-none flex items-center">
                        
                        <div class="w-7 h-7 rounded-xl flex items-center justify-center text-xs font-black shrink-0 transition-transform"
                            :class="active === value.id ? 'bg-white/20 text-white' : 'bg-purple-100/70 text-purple-700'">
                            {{ value.label.slice(0, 1) }}
                        </div>

                        <div v-if="!isCollapsed" class="text-xs truncate flex-1 tracking-tight">
                            {{ value.label }}
                        </div>
                    </div>
                </el-tooltip>
            </template>
        </div>
    </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import type { ChatModeList, ChatMode } from '@en/common/chat';
import { getChatMode } from '@/apis/chat';

defineProps<{ isCollapsed?: boolean }>()
const emits = defineEmits(['onGetRole', 'toggleCollapse'])

const chatMode = ref<ChatModeList>([]) //消息模式列表
const active = ref<string | null>(null) //当前激活的id

//切换消息模式
const changeActive = (value: ChatMode) => {
    active.value = value.id
    emits('onGetRole', value.role) //派发role
}

//获取消息模式列表
const getChatModeList = async () => {
    const res = await getChatMode()
    chatMode.value = res.data
    if (res.data && res.data.length > 0) {
        active.value = res.data[0].id //默认选中第一个
        emits('onGetRole', res.data[0].role) //派发role
    }
}

onMounted(() => {
    getChatModeList()
})
</script>