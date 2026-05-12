<template>
  <el-container class="min-h-screen">
    <el-header class="flex items-center justify-between border-b border-stone-200 bg-white px-4">
      <div class="flex items-center gap-4">
        <span class="text-lg font-semibold text-teal-800">PolicyPlain</span>
        <el-button text type="primary" @click="$router.push('/')">解读</el-button>
        <el-button text type="primary" @click="$router.push('/history')">历史</el-button>
      </div>
      <div class="flex items-center gap-2">
        <span class="text-sm text-stone-600">{{ userStore.user?.username }}</span>
        <el-button size="small" @click="onLogout">退出</el-button>
      </div>
    </el-header>
    <el-main class="max-w-5xl mx-auto w-full px-4 py-6">
      <router-view />
    </el-main>
  </el-container>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const userStore = useUserStore()

function onLogout() {
  userStore.logout()
  router.push({ name: 'login' })
}
</script>
