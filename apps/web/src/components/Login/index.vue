<template>
    <div v-if="isShowLogin" class="fixed inset-0 opacity-30 filter blur-sm z-40" style="background: var(--color-accent-strong);"></div>
    <Transition name="fade">
        <div v-if="isShowLogin" class="fixed inset-30  flex items-center justify-center z-50">
            <div class="w-[1200px] h-[700px] rounded-[20px] shadow-2xl overflow-hidden flex" style="background: var(--color-surface);">
                <!-- 左侧 3D 模型区域 -->
                <ModelViewer @changeType="changeType" ref="modelViewerRef" />

                <!-- 右侧登录表单区域 -->
                <div class="flex-1 flex flex-col justify-center px-12 py-10 login-form-container">
                    <LoginForm v-if="loginType === 'login'" />
                    <RegisterForm v-if="loginType === 'register'" />
                    <div class="mt-6 text-center">
                        <div class="flex items-center justify-center gap-4 text-sm" style="color: var(--color-text-muted);">
                            <span class="cursor-pointer transition-colors" style="color: var(--color-text-muted);"
                                @mouseenter="(e) => ((e.currentTarget as HTMLElement).style.color = 'var(--color-accent)')"
                                @mouseleave="(e) => ((e.currentTarget as HTMLElement).style.color = 'var(--color-text-muted)')">忘记密码？</span>
                            <span style="color: var(--color-surface-border);">|</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </Transition>
</template>

<script setup lang="ts">
import ModelViewer from './ModelViewer.vue'
import LoginForm from './LoginForm.vue'
import RegisterForm from './RegisterForm.vue'
import { ref, inject } from 'vue'
import { IS_SHOW_LOGIN } from './type'
import type { LoginType } from './type'
const isShowLogin = inject(IS_SHOW_LOGIN, ref(false))
const loginType = ref<LoginType>('login')
//1. pinia
//2. event bus
//3. provide/inject
const changeType = (url: LoginType) => {
    loginType.value = url
}
window.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        isShowLogin.value = false
    }
})
</script>

<style scoped>
.fade-enter-active,
.fade-leave-active {
    transition: opacity 0.3s ease;
}
.fade-enter-from,
.fade-leave-to {
    opacity: 0;
}

/* 登录表单容器：暗色模式强制不透明 */
.login-form-container {
    background: var(--color-surface);
}

.dark .login-form-container {
    background: #1A1628;
}
</style>