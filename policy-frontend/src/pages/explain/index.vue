<template>
  <div class="policy-page text-base leading-relaxed">
    <el-alert type="warning" show-icon :closable="false" class="mb-4 text-base">
      本工具仅供阅读辅助，不构成法律或行政意见。待遇与规则以当地最新政策及经办答复为准。粘贴内容可能保存在您的账号下以便回看。
    </el-alert>

    <el-form label-position="top" class="space-y-3">
      <el-form-item label="主题（可选）">
        <el-radio-group v-model="topic" size="large">
          <el-radio-button value="general">社保综合</el-radio-button>
          <el-radio-button value="medical_insurance">医保</el-radio-button>
          <el-radio-button value="pension">养老保险</el-radio-button>
        </el-radio-group>
      </el-form-item>
      <el-form-item label="粘贴政策或通知原文">
        <el-input
          v-model="text"
          type="textarea"
          :rows="14"
          placeholder="请将通知、办事指南或政策条文粘贴到此处…"
          class="text-base"
        />
        <div class="mt-1 text-sm text-stone-500">字数：{{ text.length }}</div>
      </el-form-item>
      <el-button type="primary" size="large" :loading="loading" @click="onExplain">生成白话解读</el-button>
    </el-form>

    <div v-if="result" class="mt-8 space-y-4">
      <el-card shadow="hover">
        <template #header><span class="text-lg font-medium">一句话摘要</span></template>
        <p>{{ result.summary_one_line }}</p>
      </el-card>
      <el-card shadow="hover">
        <template #header><span class="text-lg font-medium">适用条件</span></template>
        <ul class="list-disc pl-5 space-y-1">
          <li v-for="(x, i) in result.applicability" :key="'a' + i">{{ x }}</li>
        </ul>
      </el-card>
      <el-card shadow="hover">
        <template #header><span class="text-lg font-medium">材料</span></template>
        <p class="mb-2 text-stone-600">{{ result.materials?.source_note }}</p>
        <ul class="list-disc pl-5 space-y-1">
          <li v-for="(x, i) in result.materials?.items || []" :key="'m' + i">{{ x }}</li>
        </ul>
      </el-card>
      <el-card shadow="hover">
        <template #header><span class="text-lg font-medium">渠道与时间</span></template>
        <p class="font-medium">办理渠道</p>
        <ul class="list-disc pl-5 mb-3">
          <li v-for="(x, i) in result.channels" :key="'c' + i">{{ x }}</li>
        </ul>
        <p class="font-medium">时间节点</p>
        <ul class="list-disc pl-5">
          <li v-for="(x, i) in result.important_dates" :key="'d' + i">{{ x }}</li>
        </ul>
      </el-card>
      <el-card v-if="result.common_misunderstandings?.length" shadow="hover">
        <template #header><span class="text-lg font-medium">易误读提醒</span></template>
        <ul class="list-disc pl-5">
          <li v-for="(x, i) in result.common_misunderstandings" :key="'e' + i">{{ x }}</li>
        </ul>
      </el-card>
      <el-card v-if="result.uncovered_points?.length" shadow="hover">
        <template #header><span class="text-lg font-medium">原文未覆盖</span></template>
        <ul class="list-disc pl-5">
          <li v-for="(x, i) in result.uncovered_points" :key="'u' + i">{{ x }}</li>
        </ul>
      </el-card>
      <el-card shadow="hover">
        <template #header><span class="text-lg font-medium">进一步核实</span></template>
        <ul class="list-disc pl-5">
          <li v-for="(x, i) in result.verification_hints" :key="'v' + i">{{ x }}</li>
        </ul>
      </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { explainPolicy, type ExplainResponse } from '@/apis/policy_api'

const topic = ref<'general' | 'medical_insurance' | 'pension'>('general')
const text = ref('')
const loading = ref(false)
const result = ref<ExplainResponse | null>(null)

async function onExplain() {
  if (!text.value.trim()) {
    ElMessage.warning('请先粘贴正文')
    return
  }
  loading.value = true
  result.value = null
  try {
    result.value = await explainPolicy({ text: text.value, topic: topic.value })
    ElMessage.success('解读完成')
  } catch {
    ElMessage.error('解读失败，请稍后重试')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.policy-page :deep(.el-textarea__inner) {
  font-size: 1.05rem;
  line-height: 1.6;
}
</style>
