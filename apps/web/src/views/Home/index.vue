<template>
  <div class="max-w-[1300px] mx-auto px-8 py-10 min-h-full">
    <div class="grid grid-cols-3 gap-6 items-start">
      <div class="col-span-2 flex flex-col gap-6">
        <div>
          <div class="text-xs font-semibold mb-2 uppercase tracking-widest" style="color: var(--color-text-muted)">{{ greetingLabel }}</div>
          <h1 class="text-4xl font-black tracking-tight" style="color: var(--color-text-primary)">
            Good morning, <span style="color: var(--color-accent-strong)">{{ username }}</span>
          </h1>
          <p class="mt-2 text-sm" style="color: var(--color-text-secondary)">坚持是最好的老师，你已连续学习 {{ userStore.getUser?.dayNumber ?? 0 }} 天了！</p>
        </div>
        <div class="grid grid-cols-2 gap-4">
          <div class="rounded-3xl p-6" style="background: var(--color-surface); border: 1px solid var(--color-surface-border)">
            <div class="text-xs font-semibold uppercase tracking-widest mb-1" style="color: var(--color-text-muted)">掌握词汇量</div>
            <div class="text-5xl font-black mt-1" style="color: var(--color-accent-strong)">{{ userStore.getUser?.wordNumber ?? 0 }}</div>
            <div class="text-sm mt-1" style="color: var(--color-text-secondary)">个单词</div>
            <div class="mt-3 h-1.5 rounded-full" style="background: var(--color-surface-border)">
              <div class="h-full rounded-full" style="width: 65%; background: var(--color-accent)"></div>
            </div>
          </div>
          <div class="rounded-3xl p-6" style="background: var(--color-surface); border: 1px solid var(--color-surface-border)">
            <div class="text-xs font-semibold uppercase tracking-widest mb-1" style="color: var(--color-text-muted)">连续坚持</div>
            <div class="text-5xl font-black mt-1" style="color: var(--color-accent-soft)">{{ userStore.getUser?.dayNumber ?? 0 }}</div>
            <div class="text-sm mt-1" style="color: var(--color-text-secondary)">天打卡</div>
            <div class="mt-3 h-1.5 rounded-full" style="background: var(--color-surface-border)">
              <div class="h-full rounded-full" style="width: 45%; background: var(--color-accent-soft)"></div>
            </div>
          </div>
        </div>
        <div class="rounded-3xl p-6" style="background: var(--color-surface); border: 1px solid var(--color-surface-border)">
          <div class="flex items-center justify-between mb-4">
            <div>
              <div class="text-base font-black" style="color: var(--color-text-primary)">学习进度追踪</div>
              <div class="text-xs mt-0.5" style="color: var(--color-text-muted)">近 7 天每日学词量</div>
            </div>
            <span class="text-xs px-3 py-1 rounded-full font-semibold" style="background: var(--color-surface-border); color: var(--color-accent-strong)">本周</span>
          </div>
          <div class="h-44">
            <Line :data="chartData" :options="chartOptions" />
          </div>
        </div>
        <div class="grid grid-cols-3 gap-4 cards-container">
          <div v-for="(item, index) in abouts" :key="item.title"
            class="about-card rounded-3xl p-6 cursor-pointer transition-all duration-300 hover:-translate-y-1"
            style="background: var(--color-surface); border: 1px solid var(--color-surface-border)"
            :style="{ animationDelay: `${index * 80}ms` }">
            <div class="text-2xl mb-4">{{ item.icon }}</div>
            <div class="text-sm font-black mb-2" style="color: var(--color-text-primary)">{{ item.title }}</div>
            <div class="text-xs leading-relaxed" style="color: var(--color-text-secondary)">{{ item.content }}</div>
          </div>
        </div>
      </div>
      <div class="col-span-1 flex flex-col gap-4 sticky top-6">
        <div class="text-sm font-black mb-2" style="color: var(--color-text-primary)">精选课程</div>
        <div v-for="course in courses" :key="course.title"
          class="rounded-3xl p-5 cursor-pointer transition-all duration-300 hover:-translate-y-1"
          :style="{ background: course.bg, border: `1px solid var(--color-surface-border)` }">
          <div class="flex items-start justify-between mb-2">
            <div class="text-sm font-black leading-snug" style="color: var(--color-text-primary)">{{ course.title }}</div>
            <span class="text-lg">{{ course.icon }}</span>
          </div>
          <div class="text-xs mb-4" style="color: var(--color-text-secondary)">{{ course.desc }}</div>
          <div class="flex items-center justify-between">
            <div class="text-[10px]" style="color: var(--color-text-muted)">{{ course.date }}</div>
            <button class="text-xs font-black px-3 py-1.5 rounded-full transition-all duration-200 hover:scale-105"
              style="background: var(--color-accent-strong); color: var(--color-nav-active-icon)">立即加入 →</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, computed } from "vue"
import { Line } from "vue-chartjs"
import { Chart as ChartJS, CategoryScale, LinearScale, PointElement, LineElement, Tooltip, Filler } from "chart.js"
import { gsap } from "gsap"
import { ScrollTrigger } from "gsap/ScrollTrigger"
import { useUserStore } from "@/stores/user"

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Tooltip, Filler)
gsap.registerPlugin(ScrollTrigger)

const userStore = useUserStore()
const username = computed(() => userStore.getUser?.name ?? "同学")
const hour = new Date().getHours()
const greetingLabel = computed(() => hour < 12 ? "GOOD MORNING" : hour < 18 ? "GOOD AFTERNOON" : "GOOD EVENING")

const chartData = {
  labels: ["周一", "周二", "周三", "周四", "周五", "周六", "周日"],
  datasets: [{
    label: "学词数",
    data: [12, 24, 18, 35, 42, 28, 56],
    borderColor: "#B8B0E8",
    backgroundColor: "rgba(184, 176, 232, 0.12)",
    borderWidth: 2,
    fill: true,
    tension: 0.4,
    pointBackgroundColor: "#B8B0E8",
    pointBorderColor: "#ffffff",
    pointBorderWidth: 2,
    pointRadius: 4,
  }]
}
const chartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: { legend: { display: false }, tooltip: { backgroundColor: "#0D0D0D", titleColor: "#fff", bodyColor: "#ccc", cornerRadius: 12 } },
  scales: {
    x: { grid: { display: false }, border: { display: false }, ticks: { color: "#AAAAAA", font: { size: 11 } } },
    y: { grid: { color: "rgba(0,0,0,0.04)" }, border: { display: false }, ticks: { color: "#AAAAAA", font: { size: 11 } } }
  }
}

const abouts = [
  { icon: "🖼️", title: "AI 情境学习", content: "沉浸式场景模拟，在真实语境中自然习得英语，告别枯燥死记硬背。" },
  { icon: "🧠", title: "智能对话练习", content: "AI 实时纠错，个性化对话训练，24 小时随时练习口语表达。" },
  { icon: "🎤", title: "科学词汇记忆", content: "基于艾宾浩斯遗忘曲线，智能安排复习计划，让单词真正记住。" },
]

const courses = [
  { title: "拓展英语词汇量", desc: "Learn new useful words", bg: "#FDF0F0", date: "Nov 22, 2024", icon: "📖" },
  { title: "构建强大语法体系", desc: "Clear rules with examples", bg: "#F0EEF8", date: "Nov 12, 2024", icon: "✏️" },
  { title: "掌握日常口语表达", desc: "Practice real-life dialogues", bg: "#FAFAFA", date: "Nov 30, 2024", icon: "🗣️" },
]

onMounted(() => {
  const cards = gsap.utils.toArray(".about-card") as HTMLElement[]
  cards.forEach((card, index) => {
    gsap.fromTo(card,
      { opacity: 0, y: 32, scale: 0.97 },
      { opacity: 1, y: 0, scale: 1, duration: 0.5, delay: index * 0.08, ease: "power2.out",
        scrollTrigger: { trigger: ".cards-container", start: "top 80%" } }
    )
  })
})
</script>
