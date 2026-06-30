<template>
    <div class="flex-1 h-full p-6 bg-white/75 backdrop-blur-2xl flex flex-col rounded-3xl shadow-xl border border-purple-100/80 overflow-hidden transition-all duration-500">
        <div class="flex-1 overflow-y-auto pr-2 custom-scrollbar">
            <!-- 欢迎/空状态插画 -->
            <div v-if="!list || list.length === 0" class="h-full flex flex-col items-center justify-center text-slate-400 select-none py-16 animate-fade-in">
                <div class="w-20 h-20 rounded-3xl bg-gradient-to-tr from-indigo-600 via-purple-600 to-pink-500 flex items-center justify-center text-4xl mb-4 shadow-xl shadow-purple-500/30 text-white transform hover:scale-105 transition-all duration-500">
                    ✨
                </div>
                <h3 class="text-base font-black text-neutral-800 mb-1">多模态智能英语学习助手已就绪</h3>
                <p class="text-xs text-neutral-500 max-w-sm text-center leading-relaxed">
                    您可以点击右下方“口语陪练”进行情境对话，或直接发送英文生词启动翻译与语法深度解析！
                </p>
            </div>
            <div v-for="(item, index) in list" :key="index">
                <div class="flex justify-end items-start gap-3.5 mt-5 mb-5 mr-3" v-if="item.role === 'human'">
                    <div class="text-sm text-white max-w-[80%] rounded-2xl p-3.5 bg-gradient-to-r from-neutral-900 to-indigo-950 shadow-md flex flex-col gap-2.5 border border-neutral-700/50">
                        <img v-if="(item as any).imageUrl" :src="(item as any).imageUrl" class="max-w-[240px] max-h-[240px] rounded-xl object-contain bg-black/20 border border-white/20" />
                        <span class="leading-relaxed">{{ item.content }}</span>
                    </div>
                    <div>
                        <el-avatar :size="38" class="!bg-indigo-600 !text-white !font-bold shadow-sm">U</el-avatar>
                    </div>
                </div>
                <div class="flex justify-start items-start gap-3.5 mt-5 mb-5" v-else>
                    <div> <el-avatar :size="38" class="!bg-gradient-to-tr !from-purple-600 !to-indigo-600 !text-white !font-black shadow-sm">AI</el-avatar></div>
                    <div class="flex-1 min-w-0">
                        <div v-if="item.role === 'ai' && !item.reasoning && !item.content"
                            class="text-xs text-purple-700 bg-purple-50/90 px-4 py-3 rounded-2xl shadow-xs border border-purple-200/70 inline-flex items-center gap-2.5 animate-pulse mt-1">
                            <span class="w-2.5 h-2.5 bg-purple-600 rounded-full animate-ping"></span>
                            <span class="font-bold">AI 正在深度推理与多模态解析...</span>
                        </div>
                        <div v-if="item.role === 'ai' && item.reasoning" class="text-xs text-neutral-600 max-w-[85%] p-3.5 bg-gradient-to-br from-purple-50/90 via-indigo-50/50 to-white/90 rounded-2xl border border-purple-200/70 shadow-xs mb-3 backdrop-blur-md transition-all hover:shadow-sm">
                            <div class="font-extrabold text-purple-900 mb-1.5 flex items-center gap-1.5">
                                <span class="animate-bounce">🧠</span>
                                <span>思维链深度推理过程:</span>
                            </div>
                            <div class="leading-relaxed whitespace-pre-wrap font-mono text-[11px] text-neutral-600 bg-white/70 p-3 rounded-xl border border-purple-100/70 max-h-48 overflow-y-auto custom-scrollbar">{{ item.reasoning }}</div>
                        </div>
                        <div v-if="item.role === 'ai' && item.content !== ''"
                            class="text-sm text-neutral-800 max-w-[85%] bg-white/95 p-4 rounded-2xl mt-1 shadow-md deepseek-markdown border border-purple-100/80 backdrop-blur-sm transition-all hover:shadow-lg hover:shadow-purple-500/5"
                            v-html="parseMarkdown(item.content)" />
                    </div>
                </div>
            </div>
            <div ref="chatRef"></div>
        </div>
        <div class="flex pt-4 border-t border-purple-100/60 box-border flex-col gap-3 mt-2">
            <!-- 功能选项卡 -->
            <div class="flex items-center justify-between">
                <div class="flex items-center gap-2.5">
                    <div class="flex items-center gap-1.5 px-3.5 py-1 rounded-full text-xs cursor-pointer transition-all border font-bold select-none"
                        :class="deepThink
                            ? 'bg-purple-100/90 border-purple-400 text-purple-800 shadow-2xs scale-102'
                            : 'bg-neutral-100/80 border-neutral-200/80 text-neutral-500 hover:bg-neutral-200/70'"
                        @click="deepThink = !deepThink">
                        <span>🧠</span>
                        <span>深度思考 (DeepSeek)</span>
                    </div>
                    <div class="flex items-center gap-1.5 px-3.5 py-1 rounded-full text-xs cursor-pointer transition-all border font-bold select-none"
                        :class="webSearch
                            ? 'bg-blue-100/90 border-blue-400 text-blue-800 shadow-2xs scale-102'
                            : 'bg-neutral-100/80 border-neutral-200/80 text-neutral-500 hover:bg-neutral-200/70'"
                        @click="webSearch = !webSearch">
                        <span>🌐</span>
                        <span>联网增强搜索</span>
                    </div>
                </div>
            </div>
            <!-- 图片预览 -->
            <div v-if="imageUrl" class="relative w-16 h-16 border border-purple-200 rounded-xl bg-white flex items-center justify-center p-1 group mb-1 shadow-sm transition-all duration-300">
                <img :src="imageUrl" class="max-w-full max-h-full object-contain rounded-lg" />
                <div class="absolute -top-2 -right-2 bg-red-500 hover:bg-red-600 text-white rounded-full w-4 h-4 flex items-center justify-center text-[10px] cursor-pointer shadow transition-colors" @click="clearImage">✕</div>
            </div>
            <!-- 输入交互面板与下沉的口语陪练控制中枢 -->
            <div class="flex items-end gap-2">
                <input type="file" ref="imageInputRef" class="hidden" accept="image/*" @change="onImageSelected" />
                <el-input @keyup.enter="sendMessage" type="textarea" :rows="2" v-model="message" placeholder="输入生词解析词根、探讨原著或自由对话..." class="!rounded-2xl" />
                
                <el-tooltip content="上传图片进行多模态 OCR 与视觉对话" placement="top">
                    <el-button class="!rounded-2xl !h-10 !w-10 !p-0 border-purple-200 text-purple-700 hover:bg-purple-50 shadow-2xs shrink-0" :icon="Picture" type="default" @click="triggerImageUpload"></el-button>
                </el-tooltip>
                <el-button class="!rounded-2xl !h-10 !px-4 !bg-gradient-to-r !from-indigo-600 !to-purple-600 !border-none !font-bold shadow-md hover:shadow-indigo-500/30 shrink-0" :icon="Position" type="primary" @click="sendMessage">发送</el-button>
                <el-button v-if="!isRecording" class="!rounded-2xl !h-10 !w-10 !p-0 !bg-purple-600 !border-none shadow-md hover:shadow-purple-500/30 shrink-0" :icon="Mic" type="primary" @click="startRecording"></el-button>
                <el-button v-else class="!rounded-2xl !h-10 !w-10 !p-0 !bg-red-500 animate-pulse shrink-0" :icon="VideoPause" type="primary" @click="stopRecording"></el-button>

                <el-tooltip content="启动 AI 多模态情境口语对练 (PCM实时连麦)" placement="top">
                    <div @click="emits('openOralModal')" class="ml-1 px-4 h-10 bg-gradient-to-r from-purple-600 via-indigo-600 to-pink-500 hover:from-purple-500 hover:to-pink-400 text-white text-xs font-black rounded-2xl cursor-pointer shadow-md shadow-purple-500/30 flex items-center gap-1.5 transition-all hover:scale-105 select-none shrink-0">
                        <span class="animate-pulse">🎙️</span>
                        <span>口语连麦</span>
                    </div>
                </el-tooltip>
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