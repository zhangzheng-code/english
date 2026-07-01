<template>
    <div :class="isCollapsed ? 'w-[68px]' : 'w-[240px]'"
        class="rounded-3xl p-4 transition-all duration-500 ease-out flex flex-col h-full shrink-0"
        style="background: rgba(255,255,255,0.70); backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px); border: 1px solid var(--color-surface-border); box-shadow: 0 4px 24px rgba(0,0,0,0.04);">

        <div class="flex items-center justify-between pb-4 mb-3 px-1"
            :class="{ 'justify-center': isCollapsed }"
            :style="{ borderBottom: '1px solid var(--color-surface-border)' }">
            <div v-if="!isCollapsed" class="flex items-center gap-2 overflow-hidden">
                <span class="text-base">🎭</span>
                <span class="text-xs font-black tracking-wide" style="color: var(--color-text-primary)">AI 情境角色</span>
            </div>
            <div @click="emits('toggleCollapse')"
                class="w-7 h-7 rounded-full flex items-center justify-center cursor-pointer transition-all duration-300 hover:scale-110 select-none"
                :style="{ background: 'var(--color-surface-hover)', color: 'var(--color-text-muted)' }"
                :title="isCollapsed ? '展开角色栏' : '收起角色栏'">
                <span class="text-[10px] font-bold">{{ isCollapsed ? '▶' : '◀' }}</span>
            </div>
        </div>

        <div class="flex-1 overflow-y-auto space-y-2 pr-0.5 custom-scrollbar">
            <template v-for="value in chatMode" :key="value.id">
                <el-tooltip :content="value.label" placement="right" :disabled="!isCollapsed">
                    <div @click="changeActive(value)"
                        :class="[isCollapsed ? 'p-2.5 justify-center' : 'p-3.5 px-4 gap-3', { 'hover:bg-[var(--color-surface-hover)]': active !== value.id }]"
                        :style="active === value.id
                            ? { background: 'var(--color-nav-active-bg)', color: 'var(--color-nav-active-icon)', boxShadow: '0 4px 12px rgba(0,0,0,0.12)' }
                            : { color: 'var(--color-text-secondary)' }"
                        class="rounded-2xl transition-all duration-300 cursor-pointer select-none flex items-center">

                        <div class="w-7 h-7 rounded-xl flex items-center justify-center text-xs font-black shrink-0"
                            :style="active === value.id
                                ? { background: 'rgba(255,255,255,0.2)', color: 'var(--color-nav-active-icon)' }
                                : { background: 'var(--color-surface-hover)', color: 'var(--color-accent-strong)' }">
                            {{ value.label.slice(0, 1) }}
                        </div>
                        <div v-if="!isCollapsed" class="text-xs truncate flex-1 tracking-tight font-semibold">
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

const chatMode = ref<ChatModeList>([])
const active = ref<string | null>(null)

const changeActive = (value: ChatMode) => {
    active.value = value.id
    emits('onGetRole', value.role)
}

const getChatModeList = async () => {
    const res = await getChatMode()
    chatMode.value = res.data
    if (res.data && res.data.length > 0) {
        active.value = res.data[0].id
        emits('onGetRole', res.data[0].role)
    }
}

onMounted(() => {
    getChatModeList()
})
</script>
