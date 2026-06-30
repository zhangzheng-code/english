<template>
  <el-dialog
    v-model="visible"
    title="🎙️ AI 多模态情境化口语陪练 (Oral Speaking Practice)"
    width="720px"
    destroy-on-close
    class="custom-oral-dialog overflow-hidden rounded-2xl shadow-2xl border border-purple-200/50"
  >
    <!-- 顶栏情境卡片 -->
    <div class="bg-gradient-to-r from-purple-900 via-indigo-900 to-slate-900 p-6 rounded-xl text-white mb-6 shadow-inner relative overflow-hidden">
      <div class="absolute -right-10 -bottom-10 w-40 h-40 bg-purple-500/20 rounded-full blur-2xl pointer-events-none"></div>
      <div class="flex items-center justify-between relative z-10">
        <div>
          <span class="text-xs font-bold uppercase tracking-wider bg-purple-500/30 text-purple-200 px-3 py-1 rounded-full border border-purple-400/30">
            Current Scenario
          </span>
          <h3 class="text-xl font-extrabold mt-2 tracking-tight flex items-center gap-2">
            <span>{{ topic || 'Daily English Practice' }}</span>
          </h3>
        </div>
        <div class="text-right">
          <div class="text-xs text-purple-300">Your Role</div>
          <div class="text-lg font-bold text-amber-300 flex items-center justify-end gap-1 mt-1">
            <span>🎭</span><span>{{ role || 'English Learner' }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 练习目标与输入栏 -->
    <div class="bg-slate-50 p-5 rounded-xl border border-slate-200/80 mb-6 shadow-sm">
      <label class="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">
        🎯 练习发音目标词 / 核心句式 (Target Vocabulary / Sentence)
      </label>
      <div class="flex gap-3">
        <el-input
          v-model="targetWord"
          placeholder="例如: allowance 或 pronunciation"
          class="flex-1 font-medium text-slate-700"
          size="large"
          clearable
        />
        <el-button type="primary" plain size="large" @click="setSample('allowance')">示例: allowance</el-button>
        <el-button type="success" plain size="large" @click="setSample('pronunciation')">示例: pronunciation</el-button>
      </div>
    </div>

    <!-- 录音控制区域 -->
    <div class="flex flex-col items-center justify-center py-8 bg-gradient-to-b from-white to-purple-50/50 rounded-2xl border border-dashed border-purple-300 mb-6 relative">
      <!-- 录音波形动画指示器 -->
      <div v-if="isRecording" class="flex items-center gap-1.5 h-12 mb-4">
        <span class="w-1.5 bg-red-500 rounded-full animate-[bounce_0.8s_infinite_100ms] h-6"></span>
        <span class="w-1.5 bg-red-500 rounded-full animate-[bounce_0.8s_infinite_300ms] h-10"></span>
        <span class="w-1.5 bg-red-500 rounded-full animate-[bounce_0.8s_infinite_200ms] h-8"></span>
        <span class="w-1.5 bg-red-500 rounded-full animate-[bounce_0.8s_infinite_400ms] h-12"></span>
        <span class="w-1.5 bg-red-500 rounded-full animate-[bounce_0.8s_infinite_150ms] h-7"></span>
        <span class="w-1.5 bg-red-500 rounded-full animate-[bounce_0.8s_infinite_350ms] h-9"></span>
      </div>
      <div v-else class="h-12 flex items-center text-slate-400 text-sm mb-4">
        点击下方麦克风开始朗读上方目标词
      </div>

      <!-- 核心麦克风按钮 -->
      <button
        @click="toggleRecord"
        :class="[
          'w-20 h-20 rounded-full flex items-center justify-center transition-all duration-300 shadow-xl cursor-pointer transform hover:scale-105 active:scale-95 border-4 outline-none',
          isRecording 
            ? 'bg-red-500 border-red-200 text-white animate-pulse shadow-red-500/50' 
            : 'bg-gradient-to-tr from-purple-600 to-indigo-600 border-purple-100 text-white hover:shadow-purple-500/40'
        ]"
      >
        <span class="text-3xl">{{ isRecording ? '⏹️' : '🎙️' }}</span>
      </button>

      <div class="mt-3 font-semibold text-sm" :class="isRecording ? 'text-red-600 animate-pulse' : 'text-slate-600'">
        {{ isRecording ? '正在实时录制 PCM 语音流... (点击停止并送检)' : '点击录制语音' }}
      </div>
    </div>

    <!-- AI 识别与分析加载状态 -->
    <div v-if="isAnalyzing" class="p-6 bg-purple-50/80 rounded-xl border border-purple-200 flex flex-col items-center justify-center gap-3 text-purple-700 my-4 animate-pulse">
      <div class="flex items-center gap-2 font-bold text-base">
        <span class="inline-block w-3 h-3 bg-purple-600 rounded-full animate-ping"></span>
        <span>Whisper ASR 语音识别与 Levenshtein 音素纠音中...</span>
      </div>
      <span class="text-xs text-purple-500">正在对比发音矩阵，生成音素级诊断报告</span>
    </div>

    <!-- ASR 识别结果与纠音报告渲染面板 -->
    <transition name="el-fade-in-linear">
      <div v-if="asrText || evaluation" class="bg-white rounded-2xl p-6 border border-slate-200 shadow-lg mt-4">
        <div class="flex items-center justify-between border-b border-slate-100 pb-4 mb-4">
          <div>
            <span class="text-xs font-bold text-slate-400 uppercase tracking-wider">Whisper ASR Transcription</span>
            <div class="text-lg font-bold text-slate-800 mt-1 flex items-center gap-2">
              <span>🗣️ 识别文本：</span>
              <span class="px-3 py-1 bg-slate-100 rounded-lg text-indigo-600 font-mono">{{ asrText }}</span>
            </div>
          </div>

          <!-- 发音得分卡片 -->
          <div v-if="evaluation" class="text-right flex items-center gap-3 bg-slate-50 px-4 py-2 rounded-xl border border-slate-100">
            <span class="text-xs font-bold text-slate-500 uppercase">发音准确度</span>
            <span 
              :class="[
                'text-3xl font-black px-3 py-1 rounded-lg shadow-sm',
                evaluation.score >= 80 ? 'bg-emerald-500 text-white' :
                evaluation.score >= 60 ? 'bg-amber-500 text-white' : 'bg-rose-500 text-white'
              ]"
            >
              {{ evaluation.score }}<span class="text-sm font-normal">%</span>
            </span>
          </div>
        </div>

        <!-- 音素纠音图谱渲染 -->
        <div v-if="evaluation && evaluation.details && evaluation.details.length > 0">
          <div class="text-xs font-bold text-slate-500 uppercase tracking-wider mb-3 flex items-center justify-between">
            <span>🔬 Levenshtein 音素级发音诊断图谱 (Phoneme Breakdown)</span>
            <div class="flex items-center gap-3 text-xs font-normal">
              <span class="flex items-center gap-1"><span class="w-2.5 h-2.5 bg-emerald-500 rounded-full"></span>准确 (Correct)</span>
              <span class="flex items-center gap-1"><span class="w-2.5 h-2.5 bg-rose-500 rounded-full"></span>错读 (Mispronounced)</span>
              <span class="flex items-center gap-1"><span class="w-2.5 h-2.5 bg-amber-500 rounded-full"></span>漏读 (Missing)</span>
              <span class="flex items-center gap-1"><span class="w-2.5 h-2.5 bg-purple-500 rounded-full"></span>多读 (Extra)</span>
            </div>
          </div>

          <div class="flex flex-wrap gap-2.5 p-4 bg-slate-50 rounded-xl border border-slate-200/60">
            <div
              v-for="(item, idx) in evaluation.details"
              :key="idx"
              :class="[
                'flex flex-col items-center justify-center px-3.5 py-2 rounded-xl border font-mono text-sm shadow-sm transition-all hover:scale-105',
                item.status === 'correct' ? 'bg-emerald-50 border-emerald-300 text-emerald-800' :
                item.status === 'mispronounced' ? 'bg-rose-50 border-rose-300 text-rose-800 animate-pulse' :
                item.status === 'missing' ? 'bg-amber-50 border-amber-300 text-amber-800 opacity-80' :
                'bg-purple-50 border-purple-300 text-purple-800'
              ]"
            >
              <div class="font-bold text-base">{{ item.phoneme }}</div>
              <div class="text-[10px] uppercase font-sans mt-0.5 tracking-tighter opacity-75">
                {{ item.status === 'mispronounced' ? `读作 ${item.user_phoneme || '?'}` : item.status }}
              </div>
            </div>
          </div>
        </div>
      </div>
    </transition>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue';
import { useSocket } from '@/hooks/useSocket';
import { ElMessage } from 'element-plus';

const { getSocket, connect } = useSocket();

const visible = ref(false);
const topic = ref('Airport customs clearance');
const role = ref('Customs Officer');
const targetWord = ref('allowance');
const isRecording = ref(false);
const isAnalyzing = ref(false);
const asrText = ref('');
const evaluation = ref<any>(null);

let mediaRecorder: MediaRecorder | null = null;
let audioStream: MediaStream | null = null;

const setSample = (word: string) => {
  targetWord.value = word;
};

// 打开面板外部调用方法
const openModal = (customTopic?: string, customRole?: string) => {
  if (customTopic) topic.value = customTopic;
  if (customRole) role.value = customRole;
  visible.value = true;
};

defineExpose({ openModal });

const setupSocketListeners = () => {
  connect();
  const socket = getSocket();
  if (!socket) return;

  socket.on('practiceInvitation', (data: any) => {
    topic.value = data?.topic || 'Daily English Practice';
    role.value = data?.role || 'English Learner';
    visible.value = true;
    ElMessage.success('🎉 收到 AI 发来的实时口语对练邀请！');
  });

  socket.on('audio_transcribed', (data: any) => {
    isAnalyzing.value = false;
    asrText.value = data?.text || '';
    evaluation.value = data?.evaluation || null;
    ElMessage.success('🎯 语音识别与纠音评测完成！');
  });
};

const removeSocketListeners = () => {
  const socket = getSocket();
  if (!socket) return;
  socket.off('practiceInvitation');
  socket.off('audio_transcribed');
};

const startRecording = async () => {
  try {
    asrText.value = '';
    evaluation.value = null;
    audioStream = await navigator.mediaDevices.getUserMedia({ audio: true });
    
    // 连接 socket
    connect();
    const socket = getSocket();
    
    mediaRecorder = new MediaRecorder(audioStream);
    
    mediaRecorder.ondataavailable = (event) => {
      if (event.data && event.data.size > 0 && socket) {
        socket.emit('audio_chunk', event.data);
      }
    };

    mediaRecorder.onstop = () => {
      if (socket) {
        socket.emit('audio_end', { targetWord: targetWord.value });
        isAnalyzing.value = true;
      }
      if (audioStream) {
        audioStream.getTracks().forEach(track => track.stop());
        audioStream = null;
      }
    };

    // 每 250ms 切片上报一次音频流
    mediaRecorder.start(250);
    isRecording.value = true;
  } catch (err: any) {
    console.error('麦克风权限启动失败:', err);
    ElMessage.error('无法启动麦克风录音，请检查浏览器麦克风授权！');
  }
};

const stopRecording = () => {
  if (mediaRecorder && mediaRecorder.state !== 'inactive') {
    mediaRecorder.stop();
  }
  isRecording.value = false;
};

const toggleRecord = () => {
  if (isRecording.value) {
    stopRecording();
  } else {
    startRecording();
  }
};

onMounted(() => {
  setupSocketListeners();
});

onUnmounted(() => {
  stopRecording();
  removeSocketListeners();
});
</script>
