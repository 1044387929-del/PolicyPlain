<template>
  <div v-loading="loading" class="detail-page">
    <el-button type="default" round size="large" class="detail-back" @click="$router.push('/history')">
      ← 返回列表
    </el-button>
    <div v-if="detail" class="detail-inner">
      <header class="detail-hero">
        <h1 class="detail-title">解读详情</h1>
        <p class="detail-desc">以下为本次保存的摘要信息与白话解读结果。</p>
      </header>

      <div class="detail-meta-card">
        <el-descriptions :column="1" border class="detail-desc-table">
          <el-descriptions-item label="记录编号">{{ detail.record_id }}</el-descriptions-item>
          <el-descriptions-item label="主题">{{ topicLabel(detail.topic) }}</el-descriptions-item>
          <el-descriptions-item label="保存时间">{{ detail.created_at }}</el-descriptions-item>
        </el-descriptions>
      </div>

      <el-card v-if="detail.input_text" shadow="never" class="detail-raw-card">
        <template #header><span class="detail-raw-head">保存的原文或来源摘录</span></template>
        <pre class="detail-raw-body">{{ detail.input_text }}</pre>
      </el-card>

      <ExplainResultElder v-if="mergedResult" :result="mergedResult" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import ExplainResultElder from '@/components/ExplainResultElder.vue'
import {
  fetchExplanationDetail,
  type ExplainResponse,
  type ExplanationDetailResponse,
} from '@/apis/policy_api'

const route = useRoute()
const loading = ref(false)
const detail = ref<ExplanationDetailResponse | null>(null)

const mergedResult = computed<ExplainResponse | null>(() => {
  if (!detail.value) return null
  return {
    record_id: detail.value.record_id,
    ...detail.value.result,
  }
})

function topicLabel(t: string) {
  if (t === 'medical_insurance') return '医保'
  if (t === 'pension') return '养老保险'
  return '社保综合'
}

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

<style scoped>
.detail-page {
  max-width: 52rem;
  margin-left: auto;
  margin-right: auto;
  font-size: 1.125rem;
  line-height: 1.65;
  color: #0c0a09;
}

.detail-back {
  margin-bottom: 1.25rem;
  font-size: 1.05rem !important;
  font-weight: 600 !important;
}

.detail-hero {
  margin-bottom: 1.25rem;
  padding: 1.35rem 1.25rem;
  border-radius: 1.1rem;
  border: 1px solid rgba(15, 118, 110, 0.15);
  background: linear-gradient(120deg, rgba(255, 255, 255, 0.95), rgba(240, 253, 250, 0.85));
  box-shadow: 0 2px 14px rgba(15, 118, 110, 0.06);
}

.detail-title {
  margin: 0 0 0.4rem;
  font-size: 1.65rem;
  font-weight: 800;
}

.detail-desc {
  margin: 0;
  font-size: 1.05rem;
  color: #57534e;
}

.detail-meta-card {
  margin-bottom: 1.5rem;
  border-radius: 1rem;
  overflow: hidden;
  border: 1px solid rgba(120, 113, 108, 0.18);
  box-shadow: 0 2px 12px rgba(28, 25, 23, 0.05);
}

.detail-desc-table :deep(.el-descriptions__label) {
  font-size: 1.05rem;
  font-weight: 700;
  width: 8.5rem;
}

.detail-desc-table :deep(.el-descriptions__content) {
  font-size: 1.05rem;
}

.detail-raw-card {
  margin-bottom: 1.5rem;
  border-radius: 1rem !important;
  border: 1px solid #e7e5e4 !important;
}

.detail-raw-card :deep(.el-card__header) {
  padding: 1rem 1.25rem;
  background: #fafaf9;
}

.detail-raw-head {
  font-size: 1.15rem;
  font-weight: 700;
}

.detail-raw-body {
  margin: 0;
  white-space: pre-wrap;
  font-family: ui-sans-serif, system-ui, sans-serif;
  font-size: 1.05rem;
  line-height: 1.7;
  color: #44403c;
}
</style>
