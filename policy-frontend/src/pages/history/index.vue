<template>
  <div class="history-page">
    <header class="history-hero">
      <h1 class="history-title">我的解读记录</h1>
      <p class="history-desc">按时间查看您曾保存的白话解读，点「查看」可回看全文与原文。</p>
    </header>

    <div class="history-card">
      <el-table
        v-loading="loading"
        :data="items"
        stripe
        class="history-table"
        style="width: 100%"
        empty-text="暂无记录，去「白话解读」生成一条吧"
      >
        <el-table-column prop="created_at" label="保存时间" min-width="200" />
        <el-table-column prop="topic" label="主题" width="130">
          <template #default="{ row }">
            {{ topicLabel(row.topic) }}
          </template>
        </el-table-column>
        <el-table-column prop="summary_one_line" label="一句话摘要" min-width="220" show-overflow-tooltip />
        <el-table-column label="操作" width="120" align="center">
          <template #default="{ row }">
            <el-button type="primary" round size="default" @click="goDetail(row.record_id)">查看</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { fetchExplanations, type ExplanationListItem } from '@/apis/policy_api'

const router = useRouter()

const loading = ref(false)
const items = ref<ExplanationListItem[]>([])

function topicLabel(t: string) {
  if (t === 'medical_insurance') return '医保'
  if (t === 'pension') return '养老保险'
  return '社保综合'
}

onMounted(async () => {
  loading.value = true
  try {
    const res = await fetchExplanations({ limit: 50, offset: 0 })
    items.value = res.items
  } catch {
    ElMessage.error('加载失败')
  } finally {
    loading.value = false
  }
})

function goDetail(id: string) {
  router.push({ name: 'history-detail', params: { id } })
}
</script>

<style scoped>
.history-page {
  max-width: 72rem;
  margin-left: auto;
  margin-right: auto;
}

.history-hero {
  margin-bottom: 1.5rem;
  padding: 1.5rem 1.35rem;
  border-radius: 1.15rem;
  border: 1px solid rgba(15, 118, 110, 0.15);
  background: linear-gradient(120deg, rgba(255, 255, 255, 0.95), rgba(240, 253, 250, 0.85));
  box-shadow: 0 2px 16px rgba(15, 118, 110, 0.06);
}

.history-title {
  margin: 0 0 0.5rem;
  font-size: 1.65rem;
  font-weight: 800;
  color: #0c0a09;
}

.history-desc {
  margin: 0;
  font-size: 1.1rem;
  line-height: 1.55;
  color: #57534e;
}

.history-card {
  border-radius: 1.15rem;
  border: 1px solid rgba(120, 113, 108, 0.18);
  background: #fff;
  box-shadow: 0 4px 20px rgba(28, 25, 23, 0.06);
  padding: 0.5rem 0.25rem 1rem;
  overflow: hidden;
}

@media (min-width: 640px) {
  .history-card {
    padding: 0.75rem 0.5rem 1.25rem;
  }
}

.history-table :deep(.el-table__header th) {
  font-size: 1.05rem;
  font-weight: 700;
  color: #292524;
  background: #f5f5f4 !important;
}

.history-table :deep(.el-table__body td) {
  font-size: 1.05rem;
  padding-top: 0.85rem !important;
  padding-bottom: 0.85rem !important;
}
</style>
