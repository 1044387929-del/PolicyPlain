<template>
  <div
    class="flex min-h-screen flex-col justify-center px-4 py-10 sm:px-6 lg:px-8 bg-gradient-to-br from-teal-100 to-sky-200"
  >
    <div class="sm:mx-auto sm:w-full sm:max-w-md">
      <h1 class="text-center text-2xl font-bold text-stone-900">PolicyPlain</h1>
      <p v-if="subtitle" class="mt-2 text-center text-sm text-stone-600">{{ subtitle }}</p>
    </div>
    <div class="mt-6 sm:mx-auto sm:w-full sm:max-w-md">
      <div class="rounded-lg bg-white px-6 py-8 shadow-md sm:px-8">
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
