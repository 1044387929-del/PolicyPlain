<template>
  <div class="auth-shell flex min-h-screen flex-col lg:flex-row">
    <div
      class="auth-visual relative order-first min-h-[12rem] shrink-0 bg-stone-200 lg:order-none lg:min-h-screen lg:w-[min(42%,26rem)] lg:max-w-md"
      :style="{ backgroundImage: `url(${IMG_AUTH_PANEL})` }"
      role="img"
      :aria-label="'配图：家庭陪伴氛围'"
    >
      <div class="auth-visual-overlay absolute inset-0 bg-gradient-to-br from-teal-900/75 via-teal-800/55 to-amber-900/45" />
      <div class="auth-visual-copy relative z-[1] flex h-full flex-col justify-end p-6 text-white lg:p-10">
        <p class="m-0 text-xs font-medium uppercase tracking-[0.2em] text-teal-100/90">PolicyPlain</p>
        <p class="mt-2 text-xl font-bold leading-snug drop-shadow-sm sm:text-2xl">社保 · 医保 · 养老</p>
        <p class="mt-2 max-w-sm text-base leading-relaxed text-teal-50/95">政策白话助手，字号清晰、步骤好懂，陪您安心办。</p>
      </div>
    </div>

    <div
      class="auth-main flex flex-1 flex-col justify-center bg-gradient-to-br from-teal-50/90 via-white to-amber-50/50 px-4 py-10 sm:px-8 lg:px-12 lg:py-14"
    >
      <div class="mx-auto w-full max-w-md">
        <div class="mb-8 rounded-2xl border border-teal-200/50 bg-white/70 px-5 py-5 text-center shadow-md backdrop-blur-sm lg:hidden">
          <h1 class="m-0 text-2xl font-extrabold tracking-tight text-teal-900">PolicyPlain</h1>
          <p class="mt-2 text-base font-medium text-stone-600">社保 · 医保 · 养老 — 政策白话助手</p>
          <p v-if="subtitle" class="mt-2 text-lg text-stone-700">{{ subtitle }}</p>
        </div>

        <div class="hidden text-center lg:mb-8 lg:block">
          <h1 class="m-0 text-3xl font-extrabold tracking-tight text-teal-900">PolicyPlain</h1>
          <p class="mt-2 text-base font-medium text-stone-600">社保 · 医保 · 养老 — 政策白话助手</p>
          <p v-if="subtitle" class="mt-3 text-lg text-stone-700">{{ subtitle }}</p>
        </div>

        <div class="rounded-2xl border border-stone-200/80 bg-white/95 px-6 py-9 shadow-xl sm:px-10">
          <slot />
        </div>

        <p class="mt-6 text-center text-xs leading-relaxed text-stone-400">{{ UNSPLASH_LICENSE_NOTE }}</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { IMG_AUTH_PANEL, UNSPLASH_LICENSE_NOTE } from '@/constants/elderImagery'

defineProps<{
  subtitle?: string
}>()
</script>

<style scoped>
.auth-visual {
  background-size: cover;
  background-position: center 30%;
}
</style>
