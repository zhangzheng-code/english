<template>
  <div
    class="flex h-screen w-screen overflow-hidden"
    :style="{ background: 'linear-gradient(135deg, var(--color-canvas-from), var(--color-canvas-to))' }"
  >
    <NavRail />
    <main class="flex-1 ml-16 overflow-y-auto h-full">
      <RouterView />
      <Search />
      <Login />
    </main>
  </div>
</template>

<script setup lang="ts">
import NavRail from './NavRail/index.vue'
import { RouterView } from 'vue-router'
import Search from '../components/Search/index.vue'
import Login from '../components/Login/index.vue'
import { provide, ref } from 'vue'
import { IS_SHOW_LOGIN } from '../components/Login/type'
provide(IS_SHOW_LOGIN, ref(false))
</script>