<template>
  <div>
    <h2 class="mb-4 text-xl font-semibold">我的解读记录</h2>
    <el-table v-loading="loading" :data="items" stripe style="width: 100%">
      <el-table-column prop="created_at" label="时间" width="200" />
      <el-table-column prop="topic" label="主题" width="120" />
      <el-table-column prop="summary_one_line" label="摘要" show-overflow-tooltip />
      <el-table-column label="操作" width="120">
        <template #default="{ row }">
          <el-button type="primary" link @click="goDetail(row.record_id)">查看</el-button>
        </template>
      </el-table-column>
    </el-table>
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
