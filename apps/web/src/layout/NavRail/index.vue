<template>
  <nav
    class="fixed left-0 top-0 h-screen w-16 flex flex-col items-center py-5 gap-1.5 z-50"
    :style="{ background: 'var(--color-nav-bg)', borderRight: '1px solid var(--color-nav-border)' }"
  >
    <!-- Logo -->
    <div
      class="w-10 h-10 rounded-2xl flex items-center justify-center text-white font-black text-lg mb-5 shrink-0"
      style="background: linear-gradient(135deg, #B8B0E8, #F4A4B0)"
    >
      E
    </div>

    <!-- Nav Items -->
    <template v-for="item in navItems" :key="item.path">
      <el-tooltip :content="item.label" placement="right" :show-after="300">
        <div
          @click="gotoPath(item.path)"
          class="w-11 h-11 flex items-center justify-center cursor-pointer transition-all duration-200 rounded-2xl"
          :style="isActive(item.path)
            ? { background: 'var(--color-nav-active-bg)', color: 'var(--color-nav-active-icon)' }
            : { color: 'var(--color-nav-icon)' }"
          :class="!isActive(item.path) ? 'hover:bg-[var(--color-surface-hover)]' : ''"
        >
          <component :is="item.icon" :size="20" />
        </div>
      </el-tooltip>
    </template>

    <div class="flex-1" />

    <!-- Theme Toggle -->
    <el-tooltip :content="isDark ? '切换为亮色' : '切换为暗色'" placement="right">
      <div
        @click="toggle"
        class="w-11 h-11 rounded-2xl flex items-center justify-center cursor-pointer transition-all duration-200 hover:bg-[var(--color-surface-hover)]"
        :style="{ color: 'var(--color-nav-icon)' }"
      >
        <Moon v-if="!isDark" :size="18" />
        <Sun v-else :size="18" />
      </div>
    </el-tooltip>

    <!-- User Avatar -->
    <el-popover placement="right-end" :width="340" trigger="click">
      <template #reference>
        <img
          :src="avatar"
          class="w-10 h-10 rounded-2xl object-cover cursor-pointer mt-1 shrink-0"
          style="border: 2px solid var(--color-surface-border)"
        />
      </template>
      <Profile />
    </el-popover>
  </nav>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { LayoutDashboard, MessageSquare, BookOpen, Star, Settings, Moon, Sun } from '@lucide/vue'
import { useUserStore } from '@/stores/user'
import { useTheme } from '@/composables/useTheme'
import { useAvatar } from '@/hooks/useAvatar'
import { useLogin } from '@/hooks/useLogin'
import Profile from '../Profile/index.vue'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()
const { mode, toggle } = useTheme()
const { avatar } = useAvatar()
const { login } = useLogin()
const isDark = computed(() => mode.value === 'dark')

const navItems = [
  { path: '/', label: '首页', icon: LayoutDashboard, isAuth: false },
  { path: '/chat/index', label: 'AI 助教', icon: MessageSquare, isAuth: true },
  { path: '/word-book/index', label: '单词本', icon: Star, isAuth: false },
  { path: '/courses/index', label: '课程', icon: BookOpen, isAuth: false },
  { path: '/setting/index', label: '设置', icon: Settings, isAuth: true },
]

const isActive = (path: string) => {
  if (path === '/') return route.path === '/'
  return route.path.startsWith(path.split('/').slice(0, -1).join('/') || path)
}

const gotoPath = async (path: string) => {
  const isAuth = navItems.find(item => item.path === path)?.isAuth ?? false
  if (isAuth) {
    await login()
    if (userStore.getUser) {
      router.push(path)
    }
  } else {
    router.push(path)
  }
}
</script>
