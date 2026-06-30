<template>
    <div class="min-h-screen bg-gradient-to-br from-slate-50 via-purple-50/40 to-pink-50/50 text-neutral-800 font-sans selection:bg-purple-500 selection:text-white flex flex-col">
        <Header />
        <main class="flex-1 flex flex-col relative">
            <Content />
        </main>
    </div>
</template>
<script setup lang="ts">
import Header from './Header/index.vue'
import Content from './Content/index.vue'
</script>