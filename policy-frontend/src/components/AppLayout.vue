<template>
  <el-container direction="vertical" class="pp-app flex min-h-screen flex-col">
    <el-header height="auto" class="pp-header shrink-0 border-b border-stone-200/80 bg-white/85 px-4 py-3 shadow-sm backdrop-blur-md sm:px-6">
      <div class="mx-auto flex max-w-6xl flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div class="flex flex-col gap-3 sm:flex-row sm:items-center sm:gap-8">
          <router-link to="/" class="pp-brand group flex shrink-0 items-baseline gap-2 no-underline">
            <span class="text-2xl font-bold tracking-tight text-teal-800 sm:text-[1.65rem]">PolicyPlain</span>
            <span class="hidden text-sm font-medium text-stone-500 sm:inline sm:max-w-[14rem] sm:truncate sm:text-[0.95rem]">
              社保 · 医保 · 养老 — 政策白话助手
            </span>
          </router-link>
          <nav class="flex flex-wrap items-center gap-2">
            <el-button
              :type="isExplain ? 'primary' : 'default'"
              size="large"
              round
              class="pp-nav-btn !px-5 !text-base"
              @click="$router.push('/')"
            >
              白话解读
            </el-button>
            <el-button
              :type="isHistory ? 'primary' : 'default'"
              size="large"
              round
              plain
              class="pp-nav-btn !px-5 !text-base"
              @click="$router.push('/history')"
            >
              历史记录
            </el-button>
          </nav>
        </div>
        <div class="flex items-center gap-3 rounded-2xl border border-stone-200/90 bg-stone-50/90 px-4 py-2.5 shadow-inner">
          <span class="max-w-[14rem] truncate text-base font-medium text-stone-700">{{ userStore.user?.email }}</span>
          <el-button type="danger" plain round size="default" class="!font-medium" @click="onLogout">退出</el-button>
        </div>
      </div>
    </el-header>
    <el-main class="pp-main mx-auto w-full max-w-6xl flex-1 px-4 py-8 sm:px-6 sm:py-10">
      <router-view />
    </el-main>
    <footer class="shrink-0 border-t border-stone-200/60 bg-white/60 py-4 text-center text-sm text-stone-500 backdrop-blur-sm">
      <span class="inline-block max-w-3xl px-4">本服务仅供学习辅助阅读，具体政策以当地经办部门解释为准。</span>
    </footer>
  </el-container>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const isExplain = computed(() => route.name === 'explain')
const isHistory = computed(() => route.name === 'history' || route.name === 'history-detail')

function onLogout() {
  userStore.logout()
  router.push({ name: 'login' })
}
</script>

<style scoped>
.pp-app :deep(.el-header) {
  padding-left: 0;
  padding-right: 0;
}

.pp-brand:hover .text-teal-800 {
  color: #115e59;
}
</style>
