<template>
  <div class="explain-page">
    <header class="explain-hero">
      <p class="explain-hero-kicker">面向老年人与家属 · 字号大 · 步骤清晰</p>
      <h1 class="explain-hero-title">把政策条文，说成听得懂的家常话</h1>
      <p class="explain-hero-desc">
        支持<strong>粘贴正文</strong>或<strong>政府公开网页链接</strong>；生成后可朗读收听。内容会保存在您的账号下便于回看。
      </p>
    </header>

    <section class="explain-card explain-card--notice">
      <el-alert type="warning" show-icon :closable="false" class="explain-alert">
        <template #title>
          <span class="explain-alert-title">重要说明</span>
        </template>
        本工具仅供阅读辅助，不构成法律或行政意见。待遇与规则以当地最新政策及经办答复为准。
      </el-alert>
    </section>

    <section class="explain-card">
      <div class="explain-step-head">
        <span class="explain-step-num">1</span>
        <div>
          <h2 class="explain-step-title">选择解读主题</h2>
          <p class="explain-step-hint">按您关心的领域选一项即可，不确定可选「社保综合」。</p>
        </div>
      </div>
      <div class="explain-form-item-plain">
        <el-radio-group v-model="topic" size="large" class="explain-radio-row">
          <el-radio-button value="general">社保综合</el-radio-button>
          <el-radio-button value="medical_insurance">医保</el-radio-button>
          <el-radio-button value="pension">养老保险</el-radio-button>
        </el-radio-group>
      </div>
    </section>

    <section class="explain-card">
      <div class="explain-step-head">
        <span class="explain-step-num">2</span>
        <div>
          <h2 class="explain-step-title">提供政策内容</h2>
          <p class="explain-step-hint">二选一：把文字贴进来，或填写官网上的政策页面地址。</p>
        </div>
      </div>

      <div class="explain-source-toggle">
        <button
          type="button"
          class="explain-source-btn"
          :class="{ 'explain-source-btn--active': sourceMode === 'paste' }"
          @click="sourceMode = 'paste'"
        >
          粘贴正文
        </button>
        <button
          type="button"
          class="explain-source-btn"
          :class="{ 'explain-source-btn--active': sourceMode === 'url' }"
          @click="sourceMode = 'url'"
        >
          输入网址
        </button>
      </div>

      <div v-if="sourceMode === 'paste'" class="explain-field-block">
        <label class="explain-field-label">政策或通知原文</label>
        <el-input
          v-model="text"
          type="textarea"
          :rows="12"
          placeholder="把通知、办事指南或政策条文粘贴到此处…"
          class="explain-textarea"
        />
        <p class="explain-char-count">当前字数：{{ text.length }}</p>
      </div>

      <div v-else class="explain-field-block">
        <label class="explain-field-label">政策网页链接（须以 http 或 https 开头）</label>
        <el-input
          v-model="pageUrl"
          type="url"
          size="large"
          clearable
          placeholder="例如：https://www.gov.cn/… 政府或人社部门公开页面"
          class="explain-url-input"
        />
        <p class="explain-field-help">
          系统将抓取网页正文，提炼政策要点后再生成白话解读。仅支持公网链接，内网与本地地址不可用。
        </p>
      </div>
    </section>

    <section class="explain-cta-wrap">
      <el-button type="primary" size="large" class="explain-cta-btn" :loading="loading" @click="onGenerate">
        {{ sourceMode === 'paste' ? '生成白话解读' : '从网址生成白话解读' }}
      </el-button>
    </section>

    <el-drawer
      v-model="drawerVisible"
      direction="rtl"
      size="90%"
      :destroy-on-close="true"
      :close-on-click-modal="false"
      append-to-body
      class="explain-drawer-wrap"
      @closed="onDrawerClosed"
    >
      <template #header>
        <div class="drawer-header-inner">
          <span class="drawer-title">白话解读</span>
          <span v-if="loading && !result" class="drawer-sub">{{ drawerSub }}</span>
        </div>
      </template>

      <div class="drawer-body-root">
        <template v-if="!result">
          <div v-if="statusMessage && !streamText" class="drawer-status">{{ statusMessage }}</div>
          <div v-if="loading && !streamText && !statusMessage" class="drawer-connect">
            <el-icon class="drawer-connect-icon is-loading"><Loading /></el-icon>
            <p>正在连接服务器…</p>
          </div>
          <div v-if="streamText.length > 0" ref="streamScrollRef" class="drawer-stream">
            {{ streamText }}
          </div>
        </template>
        <div v-else class="drawer-result">
          <ExplainResultElder :result="result" :animate-entry="true" :auto-speak-when-ready="true" />
        </div>
      </div>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { Loading } from '@element-plus/icons-vue'
import ExplainResultElder from '@/components/ExplainResultElder.vue'
import {
  explainPolicyStream,
  explainPolicyStreamFromUrl,
  type ExplainResponse,
} from '@/apis/policy_api'

const topic = ref<'general' | 'medical_insurance' | 'pension'>('general')
const sourceMode = ref<'paste' | 'url'>('paste')
const text = ref('')
const pageUrl = ref('')
const loading = ref(false)
const result = ref<ExplainResponse | null>(null)
const streamText = ref('')
const statusMessage = ref('')
const drawerVisible = ref(false)
const streamScrollRef = ref<HTMLElement | null>(null)
let abortCtl: AbortController | null = null

const drawerSub = computed(() => {
  if (result.value) return ''
  if (statusMessage.value) return statusMessage.value
  if (streamText.value) return '正在流式接收白话解读…'
  return '正在处理，请稍候…'
})

function onDrawerClosed() {
  abortCtl?.abort()
  abortCtl = null
  loading.value = false
  streamText.value = ''
  statusMessage.value = ''
  result.value = null
}

async function onGenerate() {
  if (loading.value) return

  if (sourceMode.value === 'paste') {
    if (!text.value.trim()) {
      ElMessage.warning('请先粘贴正文')
      return
    }
  } else {
    const u = pageUrl.value.trim()
    if (!u) {
      ElMessage.warning('请先填写网址')
      return
    }
    if (!/^https?:\/\//i.test(u)) {
      ElMessage.warning('网址需以 http:// 或 https:// 开头')
      return
    }
  }

  streamText.value = ''
  statusMessage.value = ''
  result.value = null
  drawerVisible.value = true
  loading.value = true
  abortCtl = new AbortController()
  const signal = abortCtl.signal

  const commonCallbacks = {
    onStatus: (s: { message?: string }) => {
      if (s.message) statusMessage.value = s.message
    },
    onDelta: (t: string) => {
      if (!streamText.value) statusMessage.value = ''
      streamText.value += t
      void nextTick(() => {
        const el = streamScrollRef.value
        if (el) el.scrollTop = el.scrollHeight
      })
    },
    onDone: (r: ExplainResponse) => {
      streamText.value = ''
      statusMessage.value = ''
      result.value = r
      ElMessage.success('解读完成')
    },
    onError: (detail: string) => {
      ElMessage.error(detail)
    },
  }

  try {
    if (sourceMode.value === 'paste') {
      await explainPolicyStream({ text: text.value, topic: topic.value }, commonCallbacks, { signal })
    } else {
      await explainPolicyStreamFromUrl({ url: pageUrl.value.trim(), topic: topic.value }, commonCallbacks, {
        signal,
      })
    }
  } catch {
    if (!signal.aborted) ElMessage.error('解读失败，请稍后重试')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.explain-page {
  max-width: 52rem;
  margin-left: auto;
  margin-right: auto;
}

.explain-hero {
  margin-bottom: 2rem;
  padding: 1.75rem 1.5rem 2rem;
  border-radius: 1.25rem;
  border: 1px solid rgba(15, 118, 110, 0.2);
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.95) 0%, rgba(240, 253, 250, 0.9) 50%, rgba(255, 251, 235, 0.5) 100%);
  box-shadow: 0 4px 24px rgba(15, 118, 110, 0.08);
}

.explain-hero-kicker {
  margin: 0 0 0.5rem;
  font-size: 1rem;
  font-weight: 600;
  letter-spacing: 0.02em;
  color: #0f766e;
}

.explain-hero-title {
  margin: 0 0 0.75rem;
  font-size: clamp(1.5rem, 4vw, 1.95rem);
  font-weight: 800;
  line-height: 1.3;
  color: #0c0a09;
}

.explain-hero-desc {
  margin: 0;
  font-size: 1.1rem;
  line-height: 1.65;
  color: #44403c;
}

.explain-hero-desc strong {
  color: #0f766e;
  font-weight: 700;
}

.explain-card {
  margin-bottom: 1.5rem;
  padding: 1.5rem 1.35rem 1.6rem;
  border-radius: 1.15rem;
  border: 1px solid var(--pp-card-border, rgba(120, 113, 108, 0.18));
  background: var(--pp-card, #fff);
  box-shadow: 0 2px 16px rgba(28, 25, 23, 0.06);
}

@media (min-width: 640px) {
  .explain-card {
    padding: 1.75rem 1.75rem 1.85rem;
  }
}

.explain-card--notice {
  padding: 1rem 1.25rem;
  background: linear-gradient(180deg, #fffbeb 0%, #fff 100%);
  border-color: rgba(245, 158, 11, 0.35);
}

.explain-alert :deep(.el-alert__title) {
  font-size: 1.15rem;
  font-weight: 700;
}

.explain-alert :deep(.el-alert__description) {
  margin-top: 0.35rem;
  font-size: 1.05rem;
  line-height: 1.6;
  color: #44403c;
}

.explain-step-head {
  display: flex;
  gap: 1rem;
  align-items: flex-start;
  margin-bottom: 1.25rem;
}

.explain-step-num {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 2.5rem;
  height: 2.5rem;
  border-radius: 0.75rem;
  font-size: 1.25rem;
  font-weight: 800;
  color: #fff;
  background: linear-gradient(145deg, #0d9488, #0f766e);
  box-shadow: 0 2px 8px rgba(15, 118, 110, 0.35);
}

.explain-step-title {
  margin: 0 0 0.35rem;
  font-size: 1.35rem;
  font-weight: 800;
  color: #0c0a09;
}

.explain-step-hint {
  margin: 0;
  font-size: 1.05rem;
  line-height: 1.55;
  color: #57534e;
}

.explain-form-item-plain {
  margin-bottom: 0;
}

.explain-form-item-plain :deep(.el-form-item__content) {
  line-height: normal;
}

.explain-radio-row {
  width: 100%;
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.explain-radio-row :deep(.el-radio-button__inner) {
  font-size: 1.1rem;
  padding: 0.7rem 1.15rem;
  border-radius: 0.65rem !important;
}

.explain-source-toggle {
  display: flex;
  gap: 0.75rem;
  margin-bottom: 1.35rem;
  padding: 0.35rem;
  border-radius: 0.9rem;
  background: #f5f5f4;
  border: 1px solid #e7e5e4;
}

.explain-source-btn {
  flex: 1;
  cursor: pointer;
  border: none;
  border-radius: 0.65rem;
  padding: 0.85rem 1rem;
  font-size: 1.1rem;
  font-weight: 600;
  color: #57534e;
  background: transparent;
  transition:
    background 0.15s,
    color 0.15s,
    box-shadow 0.15s;
}

.explain-source-btn--active {
  color: #fff;
  background: linear-gradient(145deg, #0d9488, #0f766e);
  box-shadow: 0 2px 10px rgba(15, 118, 110, 0.35);
}

.explain-field-block {
  margin-top: 0.25rem;
}

.explain-field-label {
  display: block;
  margin-bottom: 0.6rem;
  font-size: 1.15rem;
  font-weight: 700;
  color: #292524;
}

.explain-field-help,
.explain-char-count {
  margin: 0.65rem 0 0;
  font-size: 1rem;
  line-height: 1.55;
  color: #57534e;
}

.explain-textarea :deep(.el-textarea__inner) {
  font-size: 1.15rem;
  line-height: 1.65;
  border-radius: 0.75rem;
  padding: 1rem 1.1rem;
}

.explain-url-input :deep(.el-input__wrapper) {
  border-radius: 0.75rem;
  padding: 0.35rem 1rem;
  min-height: 3.25rem;
}

.explain-url-input :deep(.el-input__inner) {
  font-size: 1.1rem;
}

.explain-cta-wrap {
  position: sticky;
  bottom: 0;
  z-index: 2;
  margin-top: 0.5rem;
  padding: 1.25rem 0 0.5rem;
  background: linear-gradient(180deg, transparent 0%, rgba(240, 253, 250, 0.65) 30%, rgba(240, 253, 250, 0.95) 100%);
}

.explain-cta-btn {
  width: 100%;
  height: auto !important;
  padding: 1rem 1.5rem !important;
  font-size: 1.25rem !important;
  font-weight: 700 !important;
  border-radius: 0.85rem !important;
  box-shadow: 0 4px 14px rgba(15, 118, 110, 0.28);
}

.drawer-header-inner {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  padding-right: 0.5rem;
}

.drawer-title {
  font-size: 1.35rem;
  font-weight: 700;
  color: #0c0a09;
}

.drawer-sub {
  font-size: 1rem;
  font-weight: 400;
  color: #78716c;
  line-height: 1.45;
}
</style>

<style>
.explain-drawer-wrap.el-drawer {
  --el-drawer-padding-primary: 0;
}

.explain-drawer-wrap .el-drawer__header {
  margin-bottom: 0;
  padding: 1rem 1.25rem;
  border-bottom: 1px solid #e7e5e4;
  background: linear-gradient(90deg, #fafaf9, #fff);
}

.explain-drawer-wrap .el-drawer__body {
  padding: 0;
  height: calc(100% - 3.75rem);
  overflow: hidden;
  display: flex;
  flex-direction: column;
  background: #fafaf9;
}

.drawer-body-root {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  padding: 1rem 1.25rem 1.5rem;
}

.drawer-status {
  margin-bottom: 1rem;
  padding: 1rem 1.25rem;
  font-size: 1.2rem;
  line-height: 1.55;
  color: #44403c;
  background: #fffbeb;
  border: 1px solid #fde68a;
  border-radius: 0.75rem;
}

.drawer-connect {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 1rem;
  padding: 2rem 1rem;
  font-size: 1.2rem;
  color: #44403c;
}

.drawer-connect-icon {
  font-size: 2.5rem;
  color: #d97706;
}

.drawer-stream {
  flex: 1;
  min-height: 12rem;
  max-height: 100%;
  overflow-y: auto;
  white-space: pre-wrap;
  word-break: break-word;
  font-family: ui-sans-serif, system-ui, sans-serif;
  font-size: 1.15rem;
  line-height: 1.75;
  color: #292524;
  padding: 1rem 1.1rem;
  border-radius: 0.75rem;
  background: #fff;
  border: 1px solid #e7e5e4;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.8);
}

.drawer-result {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding-bottom: 0.5rem;
}
</style>
