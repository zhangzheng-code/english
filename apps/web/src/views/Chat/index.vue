<template>
    <div class="w-full max-w-[1440px] mx-auto px-6 mt-6 pb-8 flex gap-6 items-stretch h-[calc(100vh-80px)] relative">
        <!-- 左侧可折叠会话人格栏 -->
        <Conversations 
            :isCollapsed="isLeftCollapsed" 
            @toggleCollapse="isLeftCollapsed = !isLeftCollapsed" 
            @onGetRole="getRole" 
        />

        <!-- 中间气泡交互工作台 -->
        <div class="flex-1 flex flex-col min-w-0 transition-all duration-500 ease-out">
            <Bubble 
                ref="bubbleRef" 
                :list="list" 
                @onSendMessage="sendMessage" 
            />
        </div>

        <!-- 右侧可折叠 RAG 书架 -->
        <Bookshelf 
            :isCollapsed="isRightCollapsed" 
            @toggleCollapse="isRightCollapsed = !isRightCollapsed" 
            @selectBook="onSelectBook" 
        />

        <OralPracticeModal ref="oralModalRef" />

        <!-- 固定 FAB 口语连麦按钮 -->
        <div
            @click="openOralModal"
            class="fixed bottom-8 right-8 w-14 h-14 rounded-full flex items-center justify-center cursor-pointer shadow-2xl transition-all duration-300 hover:scale-110 active:scale-95 z-40 select-none oral-fab"
            :style="{ background: 'var(--color-accent-strong)', color: 'var(--color-nav-active-icon)' }"
            title="启动 AI 口语情境陪练"
        >
            <Mic :size="22" />
        </div>
    </div>
</template>

<script setup lang="ts">
import { Mic } from '@lucide/vue'
import Conversations from './components/Conversations.vue';
import Bubble from './components/Bubble.vue';
import Bookshelf from './components/Bookshelf.vue';
import OralPracticeModal from './components/OralPracticeModal.vue';
import { useUserStore } from '@/stores/user'
import { ref } from 'vue';
import { getChatHistory } from '@/apis/chat';
import type { ChatRoleType, ChatMessageList, ChatDto, ChatMessage } from '@en/common/chat';
import { sse, CHAT_URL } from '@/apis/sse';
import { ElMessage } from 'element-plus';

const isLeftCollapsed = ref(false)
const isRightCollapsed = ref(false)

const userStore = useUserStore()
const list = ref<ChatMessageList>([]) //存储历史记录的数组
const userId = userStore.user?.id
const role = ref<ChatRoleType>('normal') //存储角色
const bubbleRef = ref<any>(null)
const selectedBookId = ref<string | null>(null)
const oralModalRef = ref<any>(null)

const openOralModal = () => {
    if (oralModalRef.value) {
        oralModalRef.value.openModal();
    }
}

const getRole = async (params: ChatRoleType) => {
    role.value = params
    const res = await getChatHistory(userId!, params) //获取历史记录
    list.value = res.data //存储历史记录
}

const onSelectBook = (book: any) => {
    selectedBookId.value = book.id
    ElMessage.success(`已选中原著《${book.filename}》进行上下文学习`);
    if (bubbleRef.value) {
        bubbleRef.value.insertText(`请帮我解释在《${book.filename}》里，`);
    }
}

const sendMessage = (message: string, deepThink: boolean, webSearch: boolean, imageUrl?: string) => {
    list.value.push({role: 'human', content: message, type: 'chat', imageUrl: imageUrl || undefined} as any) //添加用户的消息
    list.value.push({role: 'ai', content: '',reasoning:'' ,type: 'chat'}) //添加AI的消息
    sse<ChatMessage, ChatDto>(CHAT_URL, "POST", {
        role: role.value,
        content: message,
        userId: userId!,
        deepThink,
        webSearch,
        imageUrl: imageUrl || undefined,
        fileId: selectedBookId.value || undefined
    }, (data) => {
        if(data.type === 'reasoning'){
            list.value[list.value.length - 1].reasoning += data.content
        }
        if(data.type === 'chat'){
            list.value[list.value.length - 1].content += data.content
        }
    })
}
</script>

<style scoped>
/* FAB 口语按钮呼吸动画 */
.oral-fab {
    animation: pulse-ring 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
}

@keyframes pulse-ring {
    0%, 100% {
        box-shadow: 0 0 0 0 rgba(13, 13, 13, 0.4);
    }
    50% {
        box-shadow: 0 0 0 12px rgba(13, 13, 13, 0);
    }
}

.dark .oral-fab {
    animation: pulse-ring-dark 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
}

@keyframes pulse-ring-dark {
    0%, 100% {
        box-shadow: 0 0 0 0 rgba(255, 255, 255, 0.4);
    }
    50% {
        box-shadow: 0 0 0 12px rgba(255, 255, 255, 0);
    }
}
</style>