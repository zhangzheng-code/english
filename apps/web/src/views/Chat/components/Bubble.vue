<template>
    <div class="flex-1 h-full p-6 flex flex-col rounded-3xl overflow-hidden transition-all duration-500"
        style="background: rgba(255,255,255,0.75); backdrop-filter: blur(24px); -webkit-backdrop-filter: blur(24px); border: 1px solid var(--color-surface-border); box-shadow: 0 8px 32px rgba(0,0,0,0.04);">
        <div class="flex-1 overflow-y-auto pr-2 custom-scrollbar">
            <div v-if="!list || list.length === 0" class="h-full flex flex-col items-center justify-center select-none py-16 animate-fade-in">
                <div class="w-20 h-20 rounded-3xl flex items-center justify-center text-4xl mb-6 transform hover:scale-105 transition-all duration-500"
                    style="background: linear-gradient(135deg, #B8B0E8, #F4A4B0); box-shadow: 0 12px 32px rgba(184,176,232,0.35)">
                    ✨
                </div>
                <h3 class="text-base font-black mb-2" style="color: var(--color-text-primary)">多模态智能英语学习助手已就绪</h3>
                <p class="text-xs max-w-sm text-center leading-relaxed" style="color: var(--color-text-secondary)">
                    点击右下角 🎙️ 启动口语情境陪练，或输入英文生词开启深度解析！
                </p>
            </div>
            <div v-for="(item, index) in list" :key="index">
                <div class="flex justify-end items-start gap-3.5 mt-5 mb-5 mr-3" v-if="item.role === 'human'">
                    <div class="text-sm max-w-[80%] rounded-2xl p-4 flex flex-col gap-2.5 transition-all duration-200"
                            style="background: var(--color-accent-strong); color: var(--color-nav-active-icon); box-shadow: 0 4px 16px rgba(0,0,0,0.12)">
                        <img v-if="(item as any).imageUrl" :src="(item as any).imageUrl" class="max-w-[240px] max-h-[240px] rounded-xl object-contain bg-white/10 border border-white/20" />
                        <span class="leading-relaxed">{{ item.content }}</span>
                    </div>
                    <div>
                        <el-avatar :size="38" style="background: var(--color-accent); color: white; font-weight: 700">U</el-avatar>
                    </div>
                </div>
                <div class="flex justify-start items-start gap-3.5 mt-5 mb-5" v-else>
                    <div><el-avatar :size="38" style="background: linear-gradient(135deg, #B8B0E8, #F4A4B0); color: white; font-weight: 900">AI</el-avatar></div>
                    <div class="flex-1 min-w-0">
                        <div v-if="item.role === 'ai' && !item.reasoning && !item.content"
                            class="text-xs px-4 py-3 rounded-2xl inline-flex items-center gap-2.5 animate-pulse mt-1"
                            style="background: rgba(184,176,232,0.12); color: var(--color-accent); border: 1px solid var(--color-accent); backdrop-filter: blur(8px)">
                            <span class="w-2.5 h-2.5 rounded-full animate-ping" style="background: var(--color-accent)"></span>
                            <span class="font-bold">AI 正在深度推理与多模态解析...</span>
                        </div>
                        <div v-if="item.role === 'ai' && item.reasoning"
                            class="text-xs max-w-[85%] p-4 rounded-2xl mb-3 transition-all duration-300"
                            style="background: rgba(184,176,232,0.08); border: 1px solid var(--color-accent); backdrop-filter: blur(12px); color: var(--color-text-secondary)">
                            <div class="font-extrabold mb-2 flex items-center gap-1.5" style="color: var(--color-text-primary)">
                                <span class="animate-bounce">🧠</span>
                                <span>思维链深度推理过程</span>
                            </div>
                            <div class="leading-relaxed whitespace-pre-wrap font-mono text-[11px] p-3 rounded-xl max-h-48 overflow-y-auto custom-scrollbar"
                                style="background: var(--color-surface); border: 1px solid var(--color-surface-border); color: var(--color-text-muted)">{{ item.reasoning }}</div>
                        </div>
                        <div v-if="item.role === 'ai' && item.content !== ''"
                            class="text-sm max-w-[85%] p-4 rounded-2xl mt-1 deepseek-markdown ai-bubble transition-all duration-300"
                            v-html="parseMarkdown(item.content)" />
                    </div>
                </div>
            </div>
            <div ref="chatRef"></div>
        </div>
        <div class="flex pt-4 box-border flex-col gap-3 mt-2" :style="{ borderTop: '1px solid var(--color-surface-border)' }">
            <div class="flex items-center gap-2">
                <div class="flex items-center gap-1.5 px-3.5 py-1.5 rounded-full text-xs cursor-pointer transition-all font-semibold select-none"
                    :style="deepThink ? { background: 'var(--color-accent-strong)', color: 'var(--color-nav-active-icon)', border: '1px solid var(--color-accent-strong)' } : { background: 'var(--color-surface-hover)', color: 'var(--color-text-muted)', border: '1px solid var(--color-surface-border)' }"
                    @click="deepThink = !deepThink">
                    <span>🧠</span><span>深度思考</span>
                </div>
                <div class="flex items-center gap-1.5 px-3.5 py-1.5 rounded-full text-xs cursor-pointer transition-all font-semibold select-none"
                    :style="webSearch ? { background: 'var(--color-accent-strong)', color: 'var(--color-nav-active-icon)', border: '1px solid var(--color-accent-strong)' } : { background: 'var(--color-surface-hover)', color: 'var(--color-text-muted)', border: '1px solid var(--color-surface-border)' }"
                    @click="webSearch = !webSearch">
                    <span>🌐</span><span>联网搜索</span>
                </div>
                <div class="flex items-center gap-1.5 px-3.5 py-1.5 rounded-full text-xs cursor-pointer transition-all font-semibold select-none"
                    :style="imageUrl ? { background: 'var(--color-accent-strong)', color: 'var(--color-nav-active-icon)', border: '1px solid var(--color-accent-strong)' } : { background: 'var(--color-surface-hover)', color: 'var(--color-text-muted)', border: '1px solid var(--color-surface-border)' }"
                    @click="triggerImageUpload">
                    <span>📷</span><span>图片</span>
                </div>
            </div>
            <div v-if="imageUrl" class="relative w-16 h-16 rounded-xl flex items-center justify-center p-1 mb-1 shadow-sm"
                :style="{ background: 'var(--color-surface)', border: '1px solid var(--color-surface-border)' }">
                <img :src="imageUrl" class="max-w-full max-h-full object-contain rounded-lg" />
                <div class="absolute -top-2 -right-2 bg-red-500 hover:bg-red-600 text-white rounded-full w-4 h-4 flex items-center justify-center text-[10px] cursor-pointer shadow" @click="clearImage">✕</div>
            </div>
            <div class="flex items-end gap-2">
                <input type="file" ref="imageInputRef" class="hidden" accept="image/*" @change="onImageSelected" />
                <el-input @keyup.enter="sendMessage" type="textarea" :rows="2" v-model="message" placeholder="输入生词、长句或问题..." class="!rounded-2xl" />
                <el-button class="!rounded-2xl !h-10 !px-4 !border-none !font-bold shadow-sm shrink-0"
                    :style="{ background: 'var(--color-accent-strong)', color: 'var(--color-nav-active-icon)' }"
                    :icon="Position" @click="sendMessage">发送</el-button>
                <el-button v-if="!isRecording" class="!rounded-2xl !h-10 !w-10 !p-0 !border-none shadow-sm shrink-0"
                    :style="{ background: 'var(--color-accent)', color: 'white' }"
                    :icon="Mic" @click="startRecording"></el-button>
                <el-button v-else class="!rounded-2xl !h-10 !w-10 !p-0 !bg-red-500 !border-none animate-pulse shrink-0"
                    :icon="VideoPause" type="danger" @click="stopRecording"></el-button>
            </div>
        </div>
    </div>
</template>

<script setup lang="ts">
import { ref, useTemplateRef, watch, nextTick } from 'vue'
import { Position, Mic, VideoPause, Picture } from '@element-plus/icons-vue';
import type { ChatMessageList } from '@en/common/chat';
import { marked } from 'marked'
import '@/assets/css/deep-seek.css'
import { useVoiceToText } from '@/hooks/useVoiceToText'

const { isRecording, start, stop } = useVoiceToText({
    lang: 'zh-CN',
    continuous: true,
})
const deepThink = ref(false) //深度思考
const webSearch = ref(false) //联网搜索
const emits = defineEmits(['onSendMessage', 'openOralModal'])
const chatRef = useTemplateRef<HTMLDivElement>('chatRef') //读取DOM元素
const props = defineProps<{
    list?: ChatMessageList //消息列表
}>()

const message = ref<string>('') //发送的内容
const imageUrl = ref<string>('') //选中的图片 base64
const imageInputRef = ref<HTMLInputElement | null>(null)

// 触发图片文件选择
const triggerImageUpload = () => {
    imageInputRef.value?.click()
}

// 选中图片并转换 base64
const onImageSelected = (e: Event) => {
    const file = (e.target as HTMLInputElement).files?.[0]
    if (file) {
        const reader = new FileReader()
        reader.onload = (event) => {
            imageUrl.value = event.target?.result as string
        }
        reader.readAsDataURL(file)
    }
}

// 清理选中图片
const clearImage = () => {
    imageUrl.value = ''
    if (imageInputRef.value) {
        imageInputRef.value.value = ''
    }
}

// 发送消息
const sendMessage = () => {
    if (!message.value && !imageUrl.value) return
    emits('onSendMessage', message.value, deepThink.value, webSearch.value, imageUrl.value)
    message.value = ''
    clearImage()
}

// 向输入框中插入文本方法 (由父组件调用)
const insertText = (text: string) => {
    message.value = text + message.value
}

// 暴露方法给父组件
defineExpose({
    insertText
})

//markdown解析HTML
const parseMarkdown = (content: string) => {
    if (!content) return ''
    return marked.parse(content)
}
//开始录音
const startRecording = () => {
    start((result) => {
        message.value = result
    })
}
//停止录音
const stopRecording = () => {
    stop()
    sendMessage()
}
//监听消息列表，滚动到最底部
watch(() => props.list, () => {
    nextTick(() => {
        chatRef.value?.scrollIntoView({ behavior: 'smooth' })
    })
}, {
    immediate: true,
    deep: true
})
</script>

<style scoped>
/* AI 气泡样式：暗色模式隔离 */
.ai-bubble {
    background: var(--color-surface);
    border: 1px solid var(--color-surface-border);
    color: var(--color-text-primary);
    backdrop-filter: blur(8px);
    box-shadow: 0 2px 12px rgba(0,0,0,0.04);
}

.dark .ai-bubble {
    background: rgba(26, 22, 40, 0.6);
    border: 1px solid rgba(255, 255, 255, 0.12);
    color: #F5F5F5;
    backdrop-filter: blur(24px);
    box-shadow: 0 4px 24px rgba(0, 0, 0, 0.3);
}
</style>