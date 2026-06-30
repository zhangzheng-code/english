<template>
    <header class="flex items-center h-20 justify-center sticky top-0 z-50 backdrop-blur-2xl bg-white/75 border-b border-purple-100/60 shadow-xs transition-all duration-300">
        <div class="w-full max-w-[1400px] px-6 mx-auto flex items-center justify-between">
            <!-- Brand Logo -->
            <div class="flex items-center gap-3 cursor-pointer group" @click="gotoPath('/')">
                <div class="text-xl font-black bg-gradient-to-tr from-indigo-600 via-purple-600 to-pink-500 text-white rounded-2xl w-10 h-10 flex items-center justify-center shadow-lg shadow-indigo-500/25 group-hover:scale-105 transition-all duration-300">
                    E
                </div>
                <div class="flex flex-col">
                    <span class="text-lg font-black bg-gradient-to-r from-neutral-800 via-purple-950 to-indigo-900 bg-clip-text text-transparent tracking-tight">Antigravity English</span>
                    <span class="text-[10px] font-semibold text-purple-500/80 tracking-widest uppercase -mt-1">Multimodal AI Workspace</span>
                </div>
            </div>

            <!-- Pill Navigation Tabs -->
            <nav class="flex items-center gap-1.5 bg-purple-50/70 p-1.5 rounded-full border border-purple-100/80 shadow-inner backdrop-blur-md">
                <template v-for="route in routes" :key="route.path">
                    <div @click="gotoPath(route.path)"
                        :class="currentPath === route.path 
                            ? 'bg-white text-purple-900 shadow-sm font-bold scale-102 border border-purple-100/60' 
                            : 'text-neutral-600 hover:text-purple-900 hover:bg-white/50 font-medium'"
                        class="flex items-center gap-2 cursor-pointer rounded-full px-4 py-2 text-xs transition-all duration-300 select-none">
                        <el-icon :size="15" class="transition-transform duration-300 group-hover:scale-110">
                            <component :is="route.icon" />
                        </el-icon>
                        <span>{{ route.name }}</span>
                    </div>
                </template>
            </nav>

            <!-- User Stats & Profile Widget -->
            <div class="flex items-center gap-3">
                <div class="flex items-center gap-1.5 bg-gradient-to-r from-blue-50 to-indigo-50/80 text-indigo-700 border border-blue-200/60 rounded-full px-3 py-1.5 shadow-2xs hover:shadow-sm transition-all" title="掌握词汇量">
                    <el-icon class="text-amber-500"><Sunny /></el-icon>
                    <span class="font-extrabold text-xs">{{ userStore.getUser?.wordNumber ?? 0 }}</span>
                    <span class="text-[10px] text-indigo-400 font-medium">词</span>
                </div>
                <div class="flex items-center gap-1.5 bg-gradient-to-r from-amber-50 to-orange-50/80 text-amber-700 border border-amber-200/60 rounded-full px-3 py-1.5 shadow-2xs hover:shadow-sm transition-all" title="连续坚持天数">
                    <el-icon class="text-orange-500"><Star /></el-icon>
                    <span class="font-extrabold text-xs">{{ userStore.getUser?.dayNumber ?? 0 }}</span>
                    <span class="text-[10px] text-amber-500 font-medium">天</span>
                </div>

                <el-popover :width="340" placement="bottom-end" trigger="click">
                    <template #reference>
                        <div class="flex items-center gap-2.5 bg-neutral-100/80 hover:bg-purple-50/80 border border-neutral-200/80 hover:border-purple-300/60 rounded-full p-1.5 pr-4 cursor-pointer transition-all duration-300 shadow-2xs">
                            <img class="w-8 h-8 rounded-full object-cover border border-white shadow-xs" :src="avatar" />
                            <span class="text-xs font-bold text-neutral-800 truncate max-w-[90px]">{{ userStore.getUser?.name ?? '游客' }}</span>
                        </div>
                    </template>
                    <Profile />
                </el-popover>
            </div>
        </div>
    </header>
</template>


<script setup lang="ts">
import { Sunny, Star, HomeFilled, Notebook, MagicStick, Reading, Setting } from '@element-plus/icons-vue'
import { useRouter } from 'vue-router';
import { watch, ref } from 'vue'
import { useUserStore } from '@/stores/user';
import Profile from '../Profile/index.vue'
import { useAvatar } from '@/hooks/useAvatar'
import { useLogin } from '@/hooks/useLogin'
const { avatar } = useAvatar()
const { login } = useLogin()
const userStore = useUserStore()
const router = useRouter()
const currentPath = ref('')
const routes = [
    { path: '/', name: '主页', icon: HomeFilled, isAuth: false },  //不需要登录
    { path: '/chat/index', name: '聊天', icon: MagicStick, isAuth: true },  //需要登录
    { path: '/word-book/index', name: '词库', icon: Notebook, isAuth: false },  //不需要登录
    { path: '/courses/index', name: '课程', icon: Reading, isAuth: false },  //不需要登录
    { path: '/setting/index', name: '设置', icon: Setting, isAuth: true },  //需要登录
]
const isActive = (path: string) => {
    return currentPath.value === path ? 'bg-blue-200 text-blue-700' : 'text-gray-500 hover:bg-blue-200 hover:text-blue-700'
}
watch(() => router.currentRoute.value, (newVal) => {
    currentPath.value = newVal.path
}, {
    immediate: true,
})
const gotoPath = async (path: string) => {
    const isAuth = routes.find(route => route.path === path)?.isAuth ?? false
    //如果是true表示必须登录
    if (isAuth) {
        await login()
        //如果登录了下面的代码才会走
        if (userStore.getUser) {
            router.push(path)
        }
    } else {
        router.push(path)
    }
}
</script>