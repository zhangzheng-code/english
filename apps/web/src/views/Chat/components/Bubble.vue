<template>
    <div class="flex-1 h-[750px] p-6 bg-gradient-to-b from-purple-50/70 to-white flex flex-col rounded-2xl shadow-xl border border-purple-200/80 overflow-hidden">
        <div class="flex-1 overflow-y-auto pr-2">
            <!-- 欢迎/空状态插画 -->
            <div v-if="!list || list.length === 0" class="h-full flex flex-col items-center justify-center text-slate-400 select-none py-16 animate-fade-in">
                <div class="w-20 h-20 rounded-2xl bg-gradient-to-tr from-purple-500 to-indigo-500 flex items-center justify-center text-4xl mb-4 shadow-lg shadow-purple-500/30 text-white transform hover:scale-105 transition-all">
                    ✨
                </div>
                <h3 class="text-base font-bold text-slate-700 mb-1">多模态智能英语学习助手已就绪</h3>
                <p class="text-xs text-slate-500 max-w-sm text-center leading-relaxed">
                    您可以点击上方按钮进行“语音纠音对练”，或在下方上传图片、输入英文进行全方位智能问答！
                </p>
            </div>
            <div v-for="(item, index) in list" :key="index">
                <div class="flex justify-end items-start gap-4 mt-5 mb-5 mr-5" v-if="item.role === 'human'">
                    <div class="text-sm text-white max-w-[80%] rounded-lg p-3 bg-blue-500 shadow-md flex flex-col gap-2">
                        <img v-if="(item as any).imageUrl" :src="(item as any).imageUrl" class="max-w-[240px] max-h-[240px] rounded object-contain bg-black/10 border border-white/20" />
                        <span>{{ item.content }}</span>
                    </div>
                    <div>
                        <el-avatar :size="35">user</el-avatar>
                    </div>
                </div>
                <div class="flex justify-start items-start gap-4 mt-5 mb-5" v-else>
                    <div> <el-avatar :size="35">AI</el-avatar></div>
                    <div class="flex-1">
                        <div v-if="item.role === 'ai' && !item.reasoning && !item.content"
                            class="text-xs text-gray-500 bg-white px-4 py-2.5 rounded-lg shadow-sm border border-gray-100 inline-flex items-center gap-2 animate-pulse mt-1">
                            <span class="w-2 h-2 bg-purple-500 rounded-full animate-ping"></span>
                            <span>AI 正在识别多模态视觉内容与思考中...</span>
                        </div>
                        <div v-if="item.role === 'ai' && item.reasoning" class="text-[12px] text-gray-500 max-w-[80%] p-2 bg-gray-100/60 rounded border border-gray-200 mb-2">
                            <div class="font-bold text-gray-600 mb-1 flex items-center gap-1"><span>🧠</span><span>思考过程:</span></div>
                            {{ item.reasoning }}
                        </div>
                        <div v-if="item.role === 'ai' && item.content !== ''"
                            class="text-sm text-gray-700 max-w-[80%] bg-white p-3 rounded-lg mt-1 shadow-sm deepseek-markdown border border-gray-100"
                            v-html="parseMarkdown(item.content)" />
                    </div>
                </div>
            </div>
            <div ref="chatRef"></div>
        </div>
        <div class="flex p-5 border-t border-gray-200 box-border flex-col gap-3">
            <!-- 功能选项 -->
            <div class="flex items-center gap-3">
                <div class="flex items-center gap-1 px-3 py-1 rounded-full text-xs cursor-pointer transition-all border"
                    :class="deepThink
                        ? 'bg-purple-100 border-purple-400 text-purple-700'
                        : 'bg-gray-100 border-gray-200 text-gray-500 hover:bg-gray-200'"
                    @click="deepThink = !deepThink">
                    <span>🧠</span>
                    <span>深度思考</span>
                </div>
                <div class="flex items-center gap-1 px-3 py-1 rounded-full text-xs cursor-pointer transition-all border"
                    :class="webSearch
                        ? 'bg-blue-100 border-blue-400 text-blue-700'
                        : 'bg-gray-100 border-gray-200 text-gray-500 hover:bg-gray-200'"
                    @click="webSearch = !webSearch">
                    <span>🌐</span>
                    <span>联网搜索</span>
                </div>
            </div>
            <!-- 图片预览 -->
            <div v-if="imageUrl" class="relative w-16 h-16 border border-zinc-200 rounded-lg bg-white flex items-center justify-center p-1 group mb-2 shadow-sm transition-all duration-300">
                <img :src="imageUrl" class="max-w-full max-h-full object-contain rounded" />
                <div class="absolute -top-2 -right-2 bg-red-500 hover:bg-red-600 text-white rounded-full w-4 h-4 flex items-center justify-center text-[10px] cursor-pointer shadow transition-colors" @click="clearImage">✕</div>
            </div>
            <!-- 输入框 -->
            <div class="flex items-end">
                <input type="file" ref="imageInputRef" class="hidden" accept="image/*" @change="onImageSelected" />
                <el-input @keyup.enter="sendMessage" type="textarea" :rows="2" v-model="message" placeholder="请输入内容..." />
                <el-tooltip content="上传图片以进行多模态交互对练" placement="top">
                    <el-button class="ml-2" :icon="Picture" type="default" @click="triggerImageUpload"></el-button>
                </el-tooltip>
                <el-button class="ml-2" :icon="Position" type="primary" @click="sendMessage"></el-button>
                <el-button v-if="!isRecording" class="ml-2" :icon="Mic" type="primary" @click="startRecording"></el-button>
                <el-button v-else class="ml-2" :icon="VideoPause" type="primary" @click="stopRecording"></el-button>
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
const emits = defineEmits(['onSendMessage'])
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