<template>
    <div class="w-[1320px] mx-auto flex mt-10 gap-4 items-start relative">
        <Conversations @onGetRole="getRole" />
        <div class="flex-1 flex flex-col gap-4">
            <div class="flex justify-between items-center px-4 bg-gradient-to-r from-purple-900/15 via-indigo-900/10 to-purple-500/10 py-3 rounded-2xl border border-purple-300/60 shadow-md backdrop-blur-sm">
                <div class="flex items-center gap-2.5">
                    <span class="animate-pulse flex h-3 w-3 relative">
                      <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-purple-400 opacity-75"></span>
                      <span class="relative inline-flex rounded-full h-3 w-3 bg-purple-600"></span>
                    </span>
                    <span class="text-xs font-extrabold text-purple-950 tracking-wide">多模态情境化口语引擎准备就绪 (PCM / 阿里云 SenseVoice / 音素诊断)</span>
                </div>
                <el-button type="primary" size="default" class="!bg-gradient-to-r from-purple-600 via-indigo-600 to-purple-700 border-none shadow-lg hover:shadow-purple-500/50 hover:scale-102 active:scale-98 transition-all text-white font-bold px-4 py-2 rounded-xl" @click="openOralModal()">
                    🎙️ 启动 AI 多模态口语情境陪练
                </el-button>
            </div>
            <Bubble ref="bubbleRef" :list="list" @onSendMessage="sendMessage" />
        </div>
        <Bookshelf @selectBook="onSelectBook" />
        <OralPracticeModal ref="oralModalRef" />
    </div>
</template>
<script setup lang="ts">
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