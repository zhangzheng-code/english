<template>
  <div class="w-[320px] h-[750px] p-5 bg-white border border-zinc-100 rounded-2xl flex flex-col shadow-sm">
    <!-- Header -->
    <div class="flex items-center justify-between pb-4 border-b border-zinc-100">
      <div class="flex items-center gap-2">
        <span class="text-xl">📚</span>
        <h2 class="text-md font-bold text-zinc-800">专属精读电子书架</h2>
      </div>
      <el-tooltip content="仅支持 .txt 或 .pdf 格式原著电子书" placement="top">
        <span class="text-xs text-zinc-400 cursor-help">ℹ️</span>
      </el-tooltip>
    </div>

    <!-- Upload Section -->
    <div class="mt-4">
      <input
        type="file"
        ref="fileInputRef"
        class="hidden"
        accept=".txt,.pdf"
        @change="handleFileChange"
      />
      <div
        class="border border-dashed border-zinc-300 rounded-xl p-4 flex flex-col items-center justify-center bg-zinc-50 hover:bg-indigo-50/30 hover:border-indigo-400 transition-all duration-300 cursor-pointer group"
        @click="triggerFileInput"
      >
        <span class="text-2xl group-hover:scale-110 transition-transform duration-300">📤</span>
        <span class="text-xs font-semibold text-zinc-600 mt-2">点击或拖拽上传精读电子书</span>
        <span class="text-[10px] text-zinc-400 mt-1">支持 TXT / PDF 格式</span>
      </div>
    </div>

    <!-- Upload Progress -->
    <div v-if="uploadState.isUploading" class="mt-4 p-3 bg-indigo-50/50 rounded-xl border border-indigo-100">
      <div class="flex items-center justify-between text-xs mb-1">
        <span class="font-medium text-indigo-700 truncate max-w-[150px]">{{ uploadState.filename }}</span>
        <span class="text-indigo-600 font-bold">{{ uploadState.progress }}%</span>
      </div>
      <el-progress :percentage="uploadState.progress" :show-text="false" status="success" />
      <div class="text-[10px] text-indigo-500 mt-1">{{ uploadState.statusText }}</div>
    </div>

    <!-- Book List -->
    <div class="flex-1 overflow-y-auto mt-4 pr-1 custom-scrollbar">
      <div v-if="loading" class="flex flex-col items-center justify-center h-48 gap-2">
        <el-icon class="is-loading text-zinc-400" :size="24"><Loading /></el-icon>
        <span class="text-xs text-zinc-400">正在载入书架...</span>
      </div>
      <div v-else-if="books.length === 0" class="flex flex-col items-center justify-center h-48 gap-2">
        <span class="text-3xl grayscale opacity-60">📖</span>
        <span class="text-xs text-zinc-400">您的书架空空如也</span>
        <span class="text-[10px] text-zinc-300">上传精读材料以开启 RAG 检索对练</span>
      </div>
      <div v-else class="flex flex-col gap-3">
        <div
          v-for="book in books"
          :key="book.id"
          class="group p-3 border rounded-xl transition-all duration-300 flex gap-3 relative overflow-hidden"
          :class="[
            book.status === 'processing'
              ? 'border-amber-100 bg-amber-50/10 cursor-not-allowed hover:bg-amber-50/20'
              : book.status === 'failed'
              ? 'border-red-100 bg-red-50/10 cursor-not-allowed hover:bg-red-50/20'
              : 'border-zinc-100 bg-emerald-50/5 hover:border-emerald-200 hover:shadow-md hover:shadow-indigo-500/5 cursor-pointer'
          ]"
          @click="handleBookClick(book)"
        >
          <!-- Delete button -->
          <div
            class="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity duration-200 z-10"
            @click.stop="handleDeleteBook(book)"
          >
            <el-tooltip content="从书架彻底移除此资料" placement="top">
              <span class="w-5 h-5 rounded-full bg-red-50 hover:bg-red-100 flex items-center justify-center text-[10px] text-red-500 shadow-sm cursor-pointer select-none transition-colors">🗑️</span>
            </el-tooltip>
          </div>

          <!-- Book Cover Icon Placeholder -->
          <div
            class="w-10 h-12 rounded flex items-center justify-center text-white text-md font-bold shadow-sm select-none"
            :class="[
              book.status === 'processing'
                ? 'bg-gradient-to-tr from-amber-400 to-orange-400'
                : book.status === 'failed'
                ? 'bg-gradient-to-tr from-red-400 to-rose-500'
                : 'bg-gradient-to-tr from-indigo-500 to-purple-500'
            ]"
          >
            {{ book.filename.slice(0, 1).toUpperCase() }}
          </div>
          <!-- Details -->
          <div class="flex-1 min-w-0 pr-4">
            <h4
              class="text-xs font-bold truncate transition-colors"
              :class="[
                book.status === 'processing'
                  ? 'text-amber-800'
                  : book.status === 'failed'
                  ? 'text-red-800'
                  : 'text-zinc-800 group-hover:text-indigo-600'
              ]"
              :title="book.filename"
            >
              {{ book.filename }}
            </h4>
            <div class="flex items-center gap-2 mt-0.5 text-[10px] text-zinc-400">
              <span>{{ formatSize(book.size) }}</span>
              <span>•</span>
              <span>{{ formatDate(book.createdAt) }}</span>
            </div>

            <!-- Status Indicator messages -->
            <div v-if="book.status === 'processing'" class="flex items-center gap-1.5 mt-1 text-[10px] text-amber-600 font-medium">
              <el-icon class="is-loading"><Loading /></el-icon>
              <span>正在进行语义向量化解析...</span>
            </div>
            <div v-else-if="book.status === 'failed'" class="flex items-center gap-1 mt-1 text-[10px] text-red-500 font-semibold">
              <span>❌ 向量化解析失败，请重新上传</span>
            </div>
            <div v-else class="flex items-center gap-1 mt-1 text-[10px] text-emerald-600 font-medium">
              <span>✨ 精读资料已上架，可随时在聊天中引用</span>
            </div>
          </div>
          <!-- Selection highlight line -->
          <div
            class="absolute left-0 top-0 bottom-0 w-[3px] transition-transform origin-top duration-300"
            :class="[
              book.status === 'processing'
                ? 'bg-amber-400 scale-y-100'
                : book.status === 'failed'
                ? 'bg-red-400 scale-y-100'
                : 'bg-emerald-500 scale-y-0 group-hover:scale-y-100'
            ]"
          ></div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, reactive } from 'vue'
import { Loading } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import SparkMD5 from 'spark-md5'
import { aiApi } from '@/apis'

interface BookFile {
  id: string
  filename: string
  size: number
  md5: string
  url: string
  status: string
  createdAt: string
}

const emits = defineEmits(['selectBook'])

const fileInputRef = ref<HTMLInputElement | null>(null)
const loading = ref(false)
const books = ref<BookFile[]>([])
let pollingTimer: number | null = null

const uploadState = reactive({
  isUploading: false,
  filename: '',
  progress: 0,
  statusText: ''
})

// Trigger Hidden File Dialog
const triggerFileInput = () => {
  if (uploadState.isUploading) {
    ElMessage.warning('已有任务正在上传中')
    return
  }
  fileInputRef.value?.click()
}

// Format File Size
const formatSize = (bytes: number) => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i]
}

// Format Date
const formatDate = (dateStr: string) => {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  return `${d.getMonth() + 1}/${d.getDate()}`
}

// Get Book List (Active loading)
const fetchBooks = async () => {
  loading.value = true
  try {
    const res: any = await aiApi.get('/upload/list')
    if (res.success) {
      books.value = res.data
      checkAndControlPolling()
    }
  } catch (e) {
    console.error('Fetch books failed:', e)
  } finally {
    loading.value = false
  }
}

// Silent get book list (For polling updates without flickering)
let pollingErrorsCount = 0

const fetchBooksSilent = async () => {
  try {
    const res: any = await aiApi.get('/upload/list')
    if (res.success) {
      books.value = res.data
      pollingErrorsCount = 0
      checkAndControlPolling()
    } else {
      handlePollingError()
    }
  } catch (e) {
    console.error('Fetch books silent failed:', e)
    handlePollingError()
  }
}

const handlePollingError = () => {
  pollingErrorsCount++
  if (pollingErrorsCount >= 3) {
    console.warn('轮询连续失败3次，强制注销定时器以防无限循环请求')
    stopPolling()
    pollingErrorsCount = 0
  }
}

// Control Polling Loop
const checkAndControlPolling = () => {
  const hasProcessing = books.value.some(b => b.status === 'processing')
  if (hasProcessing) {
    startPolling()
  } else {
    stopPolling()
  }
}

let pollingTickCount = 0
const MAX_POLLING_TICKS = 60 // 60 × 4s = 4 分钟，兼容 79MB 大文件批量写入耗时

const startPolling = () => {
  if (pollingTimer) return
  pollingTickCount = 0
  pollingTimer = window.setInterval(async () => {
    pollingTickCount++

    // 硬熔断：超过 15 次强制自毁，防雪崩死循环
    if (pollingTickCount >= MAX_POLLING_TICKS) {
      console.warn(`[POLLING] 已达硬上限 ${MAX_POLLING_TICKS} 次轮询，强制自毁定时器！`)
      stopPolling()
      return
    }

    await fetchBooksSilent()

    // 动态二次检查：如果此刻列表中已无任何 processing，立即干净注销
    const hasProcessing = books.value.some(f => f.status === 'processing')
    if (!hasProcessing) {
      console.log('[POLLING] 专属书架已全部就绪，依法干净注销清除定时器！')
      stopPolling()
    }
  }, 4000)
}

const stopPolling = () => {
  if (pollingTimer) {
    clearInterval(pollingTimer)
    pollingTimer = null
  }
}

// Book Click Handler
const handleBookClick = (book: BookFile) => {
  if (book.status === 'processing') {
    ElMessage.warning('该原著仍在进行后台语义分块和向量库注册，请稍候...')
    return
  }
  if (book.status === 'failed') {
    ElMessage.error('该原著向量化解析失败，无法加载。请尝试重新上传！')
    return
  }
  emits('selectBook', book)
}

// Book Delete Handler
const handleDeleteBook = (book: BookFile) => {
  ElMessageBox.confirm(
    `确定要从您的专属精读书架中彻底移除此英文资料 《${book.filename}》 吗？此操作将同步清除该文档在 MinIO 及向量库中的全部解析数据。`,
    '提示',
    {
      confirmButtonText: '确定移除',
      cancelButtonText: '取消',
      confirmButtonClass: 'el-button--danger',
      type: 'warning'
    }
  ).then(async () => {
    try {
      const res: any = await aiApi.delete(`/upload/${book.id}`)
      if (res.success) {
        ElMessage.success('精读资料移除成功！')
        books.value = books.value.filter(b => b.id !== book.id)
      } else {
        ElMessage.error(res.message || '移除失败')
      }
    } catch (e) {
      console.error('Delete book error:', e)
      ElMessage.error('服务连接异常，删除失败')
    }
  }).catch(() => {})
}

// Compute File MD5 Hash
const calculateMD5 = (file: File): Promise<string> => {
  return new Promise((resolve, reject) => {
    const chunkSize = 2 * 1024 * 1024 // 2MB
    const chunks = Math.ceil(file.size / chunkSize)
    let currentChunk = 0
    const spark = new SparkMD5.ArrayBuffer()
    const fileReader = new FileReader()

    fileReader.onload = (e) => {
      spark.append(e.target?.result as ArrayBuffer)
      currentChunk++
      if (currentChunk < chunks) {
        uploadState.progress = Math.min(Math.round((currentChunk / chunks) * 20), 20)
        loadNext()
      } else {
        resolve(spark.end())
      }
    }

    fileReader.onerror = () => reject('文件校验失败')

    const loadNext = () => {
      const start = currentChunk * chunkSize
      const end = Math.min(start + chunkSize, file.size)
      fileReader.readAsArrayBuffer(file.slice(start, end))
    }

    loadNext()
  })
}

// Handle File Selection and Upload
const handleFileChange = async (e: Event) => {
  const file = (e.target as HTMLInputElement).files?.[0]
  if (!file) return

  // Format Check
  const ext = file.name.substring(file.name.lastIndexOf('.')).toLowerCase()
  if (ext !== '.txt' && ext !== '.pdf') {
    ElMessage.error('仅支持上传 .txt 或 .pdf 格式电子书原著')
    return
  }

  uploadState.isUploading = true
  uploadState.filename = file.name
  uploadState.progress = 0
  uploadState.statusText = '正在计算数字指纹 (MD5)...'

  try {
    // 1. 计算文件 MD5
    const md5 = await calculateMD5(file)
    uploadState.statusText = '已完成指纹校验，正在检查秒传状态...'

    // 2. 检查秒传状态
    const checkRes: any = await aiApi.get(`/upload/check?md5=${md5}`)
    if (!checkRes.success) {
      throw new Error(checkRes.message || '秒传状态查询失败')
    }

    if (checkRes.data.exists) {
      uploadState.progress = 100
      uploadState.statusText = '秒传成功！电子书已自动收纳！'
      ElMessage.success('文档秒传收纳成功！')
      await fetchBooks()
      return
    }

    // 3. 执行分片上传
    const uploadedChunks = checkRes.data.uploadedChunks || []
    const chunkSize = 2 * 1024 * 1024 // 2MB
    const totalChunks = Math.ceil(file.size / chunkSize)
    uploadState.statusText = `指纹核实完毕，共需传送 ${totalChunks} 分片...`

    // 并发控制器，限制并发数为 3
    const maxConcurrency = 3
    const queue: number[] = []
    for (let i = 0; i < totalChunks; i++) {
      if (!uploadedChunks.includes(i)) {
        queue.push(i)
      }
    }

    let finishedChunks = totalChunks - queue.length

    const uploadChunkTask = async (chunkIndex: number) => {
      const start = chunkIndex * chunkSize
      const end = Math.min(start + chunkSize, file.size)
      const chunkFile = file.slice(start, end)

      const formData = new FormData()
      formData.append('md5', md5)
      formData.append('chunkIndex', String(chunkIndex))
      formData.append('totalChunks', String(totalChunks))
      formData.append('file', chunkFile)

      try {
        await aiApi.post('/upload/chunk', formData, {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        })
        finishedChunks++
        uploadState.progress = Math.round(20 + (finishedChunks / totalChunks) * 70)
        uploadState.statusText = `分片传输中 (${finishedChunks}/${totalChunks})`
      } catch (err) {
        throw new Error(`分片 ${chunkIndex} 上传失败`)
      }
    }

    // 执行并发队列
    const runWorker = async () => {
      while (queue.length > 0) {
        const chunkIndex = queue.shift()
        if (chunkIndex !== undefined) {
          await uploadChunkTask(chunkIndex)
        }
      }
    }

    const workers = Array.from({ length: Math.min(maxConcurrency, queue.length) }, runWorker)
    await Promise.all(workers)

    // 4. 合并分片
    uploadState.statusText = '已完成所有分片上传，正在服务端合并...'
    uploadState.progress = 95

    const mergeRes: any = await aiApi.post('/upload/merge', {
      md5,
      filename: file.name,
      totalChunks,
      size: file.size
    })

    if (mergeRes.success) {
      uploadState.progress = 100
      uploadState.statusText = '合并完毕，正在启动后台语义向量化索引...'
      ElMessage.success('文档已提交！后台正在解析排架中...')
      await fetchBooks()
    } else {
      throw new Error(mergeRes.message || '文件合并失败')
    }
  } catch (err: any) {
    ElMessage.error(err.message || '上传异常')
    uploadState.statusText = '传送异常中止'
  } finally {
    setTimeout(() => {
      uploadState.isUploading = false
      if (fileInputRef.value) {
        fileInputRef.value.value = ''
      }
    }, 3000)
  }
}

onMounted(() => {
  fetchBooks()
})

onUnmounted(() => {
  stopPolling()
})
</script>

<style scoped>
.custom-scrollbar::-webkit-scrollbar {
  width: 4px;
}
.custom-scrollbar::-webkit-scrollbar-track {
  background: transparent;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background: #e4e4e7;
  border-radius: 4px;
}
.custom-scrollbar::-webkit-scrollbar-thumb:hover {
  background: #d4d4d8;
}
</style>
