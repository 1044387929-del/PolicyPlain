<template>
  <div
    class="flex min-h-screen flex-col justify-center bg-gradient-to-br from-teal-50 via-sky-50 to-amber-50 px-4 py-12 sm:px-6 lg:px-8"
  >
    <div class="sm:mx-auto sm:w-full sm:max-w-md">
      <div class="rounded-2xl border border-white/60 bg-white/40 px-5 py-6 text-center shadow-lg backdrop-blur-md">
        <h1 class="text-3xl font-extrabold tracking-tight text-teal-900">PolicyPlain</h1>
        <p class="mt-2 text-base font-medium text-stone-600">社保 · 医保 · 养老 — 政策白话助手</p>
        <p v-if="subtitle" class="mt-3 text-lg text-stone-700">{{ subtitle }}</p>
      </div>
    </div>
    <div class="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
      <div class="rounded-2xl border border-stone-200/80 bg-white/95 px-6 py-9 shadow-xl sm:px-10">
        <slot />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  subtitle?: string
}>()
</script>
