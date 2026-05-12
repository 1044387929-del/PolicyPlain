<template>
  <div v-loading="loading">
    <el-button class="mb-4" @click="$router.push('/history')">返回列表</el-button>
    <div v-if="detail">
      <h2 class="mb-4 text-xl font-semibold">解读详情</h2>
      <el-descriptions :column="1" border class="mb-6">
        <el-descriptions-item label="记录 ID">{{ detail.record_id }}</el-descriptions-item>
        <el-descriptions-item label="主题">{{ detail.topic }}</el-descriptions-item>
        <el-descriptions-item label="时间">{{ detail.created_at }}</el-descriptions-item>
      </el-descriptions>
      <el-card v-if="detail.input_text" class="mb-4">
        <template #header>原文</template>
        <pre class="whitespace-pre-wrap text-sm">{{ detail.input_text }}</pre>
      </el-card>
      <el-card>
        <template #header>结构化结果</template>
        <pre class="whitespace-pre-wrap text-sm">{{ pretty }}</pre>
      </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { fetchExplanationDetail, type ExplanationDetailResponse } from '@/apis/policy_api'

const route = useRoute()
const loading = ref(false)
const detail = ref<ExplanationDetailResponse | null>(null)

const pretty = computed(() =>
  detail.value ? JSON.stringify(detail.value.result, null, 2) : '',
)

onMounted(async () => {
  const id = route.params.id as string
  loading.value = true
  try {
    detail.value = await fetchExplanationDetail(id)
  } catch {
    ElMessage.error('加载失败或无权限')
  } finally {
    loading.value = false
  }
})
</script>
