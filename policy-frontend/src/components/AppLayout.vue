<template>
  <div class="pp-shell flex min-h-screen flex-col">
    <header class="pp-top shrink-0 border-b border-amber-200/40 bg-gradient-to-r from-white via-teal-50/90 to-amber-50/50 shadow-sm backdrop-blur-md">
      <div class="pp-top-inner mx-auto flex w-full max-w-[100rem] flex-col gap-3 px-4 py-3 sm:flex-row sm:items-center sm:justify-between sm:px-6">
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
        <div class="flex items-center gap-3 rounded-2xl border border-teal-200/60 bg-white/80 px-4 py-2.5 shadow-inner">
          <span class="max-w-[14rem] truncate text-base font-medium text-stone-700">{{ userStore.user?.email }}</span>
          <el-button type="danger" plain round size="default" class="!font-medium" @click="onLogout">退出</el-button>
        </div>
      </div>
    </header>

    <div class="pp-mid flex min-h-0 flex-1">
      <aside class="pp-rail hidden shrink-0 lg:flex" aria-hidden="true">
        <div class="pp-rail-visual" :style="{ backgroundImage: `url(${IMG_LAYOUT_RAIL})` }" />
        <div class="pp-rail-overlay" />
        <div class="pp-rail-copy">
          <p class="pp-rail-title">颐养 · 安心办</p>
          <p class="pp-rail-sub">政策听得懂，办事少跑腿</p>
          <div class="pp-rail-cloud" aria-hidden="true" />
        </div>
      </aside>

      <main class="pp-main min-w-0 flex-1 overflow-x-hidden px-4 py-8 sm:px-6 sm:py-10">
        <div class="pp-main-inner mx-auto w-full max-w-6xl">
          <router-view />
        </div>
      </main>
    </div>

    <footer class="pp-foot shrink-0 border-t border-stone-200/70 bg-gradient-to-r from-stone-50 via-white to-teal-50/40 py-4 text-center text-sm text-stone-600 backdrop-blur-sm">
      <p class="mx-auto mb-1 max-w-3xl px-4">本服务仅供学习辅助阅读，具体政策以当地经办部门解释为准。</p>
      <p class="mx-auto max-w-3xl px-4 text-xs text-stone-400">{{ UNSPLASH_LICENSE_NOTE }}</p>
    </footer>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { IMG_LAYOUT_RAIL, UNSPLASH_LICENSE_NOTE } from '@/constants/elderImagery'

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
.pp-brand:hover .text-teal-800 {
  color: #115e59;
}

.pp-rail {
  position: relative;
  width: min(18vw, 15rem);
  min-width: 12rem;
  flex-direction: column;
  border-right: 1px solid rgba(180, 83, 9, 0.12);
  background: linear-gradient(180deg, #fffbeb 0%, #f0fdfa 55%, #e7f5f4 100%);
}

.pp-rail-visual {
  position: absolute;
  inset: 0;
  background-size: cover;
  background-position: center 20%;
  opacity: 0.42;
  filter: saturate(1.05);
}

.pp-rail-overlay {
  position: absolute;
  inset: 0;
  background: linear-gradient(180deg, rgba(255, 251, 235, 0.75) 0%, rgba(240, 253, 250, 0.55) 45%, rgba(15, 118, 110, 0.35) 100%);
}

.pp-rail-copy {
  position: relative;
  z-index: 1;
  margin-top: auto;
  padding: 1.25rem 1rem 1.75rem;
  text-align: center;
}

.pp-rail-title {
  margin: 0 0 0.35rem;
  font-size: 1.15rem;
  font-weight: 800;
  letter-spacing: 0.12em;
  color: #0f766e;
  text-shadow: 0 1px 0 rgba(255, 255, 255, 0.8);
}

.pp-rail-sub {
  margin: 0;
  font-size: 0.9rem;
  line-height: 1.45;
  color: #44403c;
  font-weight: 600;
}

.pp-rail-cloud {
  margin: 1rem auto 0;
  width: 4.5rem;
  height: 1.25rem;
  border-radius: 999px;
  background: radial-gradient(ellipse at 30% 40%, rgba(255, 255, 255, 0.95), transparent 55%),
    radial-gradient(ellipse at 70% 50%, rgba(255, 255, 255, 0.75), transparent 50%);
  opacity: 0.85;
}
</style>
