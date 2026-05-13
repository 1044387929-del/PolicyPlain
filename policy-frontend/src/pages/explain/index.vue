<template>
  <div class="explain-page">
    <div class="explain-top-strip">
      <div class="explain-top-strip-inner">
        <span class="explain-topic-label">解读主题</span>
        <el-radio-group v-model="topic" size="large" class="explain-radio-row explain-radio-row--top">
          <el-radio-button value="general">社保综合</el-radio-button>
          <el-radio-button value="medical_insurance">医保</el-radio-button>
          <el-radio-button value="pension">养老保险</el-radio-button>
        </el-radio-group>
        <span class="explain-topic-hint">按关心领域选一项；不确定请选「社保综合」</span>
      </div>
    </div>

    <header class="explain-lead">
      <h1 class="explain-lead-title">白话解读与追问</h1>
      <p class="explain-lead-desc">
        页面主体展示<strong>生成结果</strong>与<strong>追问对话</strong>。右侧填写政策材料后点「生成」；手机端结果在侧滑抽屉中打开。
      </p>
    </header>

    <div class="explain-shell">
      <section class="explain-main-stage" aria-label="白话解读与追问">
        <div class="explain-main-sticky">
          <div v-if="!inlinePreviewActive" class="explain-preview-empty">
            <p class="explain-preview-empty-title">在此查看解读与对话</p>
            <p class="explain-preview-empty-desc">
              宽屏下此处占据主要区域：生成中的进度、结构化白话、朗读与追问都会显示在这里。请先在<strong>右侧</strong>粘贴正文、填写链接或上传截图，再点「生成白话解读」。
            </p>
          </div>
          <div v-else class="explain-preview-pane">
            <div class="drawer-body-root explain-preview-body">
              <div v-if="statusMessage" class="drawer-status">{{ statusMessage }}</div>
              <template v-if="!displayResult && loading">
                <div class="drawer-generating drawer-generating--wait">
                  <div class="drawer-gen-head">
                    <el-icon class="drawer-gen-icon is-loading"><Loading /></el-icon>
                    <div>
                      <p class="drawer-gen-title">正在生成白话解读</p>
                      <p class="drawer-gen-desc">
                        服务端通过 SSE 推送可解析的结构化片段，下方会随推送<strong>逐步出现</strong>摘要与条目；完成后会保存记录并支持自动朗读。
                      </p>
                    </div>
                  </div>
                  <el-skeleton animated :rows="4" class="drawer-wait-skel" />
                </div>
              </template>
              <div v-else-if="displayResult" class="drawer-result">
                <ExplainResultElder
                  :key="displayResult.record_id"
                  :result="displayResult"
                  :animate-entry="displayResult.record_id !== STREAMING_RECORD_ID"
                  :auto-speak-when-ready="displayResult.record_id !== STREAMING_RECORD_ID"
                />
                <FollowUpChat
                  v-if="displayResult.record_id !== STREAMING_RECORD_ID"
                  :key="displayResult.record_id"
                  :record-id="displayResult.record_id"
                />
                <p v-if="displayResult.record_id === STREAMING_RECORD_ID" class="drawer-stream-hint">
                  内容仍在补充中，请稍候…
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      <div class="explain-input-column">
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
              <h2 class="explain-step-title">提供政策内容</h2>
              <p class="explain-step-hint">
                可组合使用：粘贴文字、填写政府公开页链接、上传截图识别；至少一种。若同时有链接与正文，会先抓网页要点再<strong>合并</strong>后解读。
              </p>
            </div>
          </div>

          <div class="explain-field-block">
            <label class="explain-field-label">政策原文（粘贴，或由「上传截图」识别后填入）</label>
            <el-input
              v-model="text"
              type="textarea"
              :rows="8"
              placeholder="把通知、办事指南或政策条文粘贴到此处；也可先上传截图，识别结果会出现在这里…"
              class="explain-textarea"
            />
            <p class="explain-char-count">当前字数：{{ text.length }}</p>
          </div>

          <div class="explain-field-block explain-field-block--spaced">
            <label class="explain-field-label">政策网页链接（选填）</label>
            <el-input
              v-model="pageUrl"
              type="url"
              size="large"
              clearable
              placeholder="例如：https://www.gov.cn/… 政府或人社部门公开页面"
              class="explain-url-input"
            />
            <p class="explain-field-help">
              填写后会抓取该页正文并提炼要点；若同时有粘贴文字，会把<strong>网页要点 + 您的粘贴</strong>一起解读。仅支持公网 http/https。
            </p>
          </div>

          <div class="explain-ocr-row">
            <p class="explain-ocr-hint">
              拍了纸质通知、电子版截图？上传 <strong>JPG / PNG / WebP</strong>（单张不超过 8MB），识别文字会<strong>追加到上方原文框</strong>。需服务端配置
              <code>PADDLE_OCR_ACCESS_TOKEN</code>（与 hr-backend 相同）。
            </p>
            <el-upload
              :show-file-list="false"
              accept="image/jpeg,image/png,image/webp"
              :disabled="ocrLoading"
              :before-upload="beforeOcrUpload"
              :http-request="runOcrUpload"
            >
              <el-button type="success" plain size="large" class="explain-ocr-btn" :loading="ocrLoading">
                上传截图识别文字
              </el-button>
            </el-upload>
          </div>
        </section>

        <section class="explain-cta-wrap explain-cta-wrap--sidebar">
          <el-button type="primary" size="large" class="explain-cta-btn" :loading="loading" @click="onGenerate">
            生成白话解读
          </el-button>
        </section>
      </div>
    </div>

    <el-drawer
      v-if="!desktop"
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
          <span v-if="loading && !displayResult" class="drawer-sub">{{ drawerSub }}</span>
        </div>
      </template>

      <div class="drawer-body-root">
        <div v-if="statusMessage" class="drawer-status">{{ statusMessage }}</div>
        <template v-if="!displayResult && loading">
          <div class="drawer-generating drawer-generating--wait">
            <div class="drawer-gen-head">
              <el-icon class="drawer-gen-icon is-loading"><Loading /></el-icon>
              <div>
                <p class="drawer-gen-title">正在生成白话解读</p>
                <p class="drawer-gen-desc">
                  服务端通过 SSE 推送可解析的结构化片段，下方会随推送<strong>逐步出现</strong>摘要与条目；完成后会保存记录并支持自动朗读。
                </p>
              </div>
            </div>
            <el-skeleton animated :rows="4" class="drawer-wait-skel" />
          </div>
        </template>
        <div v-else-if="displayResult" class="drawer-result">
          <ExplainResultElder
            :key="displayResult.record_id"
            :result="displayResult"
            :animate-entry="displayResult.record_id !== STREAMING_RECORD_ID"
            :auto-speak-when-ready="displayResult.record_id !== STREAMING_RECORD_ID"
          />
          <FollowUpChat
            v-if="displayResult.record_id !== STREAMING_RECORD_ID"
            :key="displayResult.record_id"
            :record-id="displayResult.record_id"
          />
          <p v-if="displayResult.record_id === STREAMING_RECORD_ID" class="drawer-stream-hint">
            内容仍在补充中，请稍候…
          </p>
        </div>
      </div>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, shallowRef } from 'vue'
import type { UploadRawFile, UploadRequestOptions } from 'element-plus'
import { ElMessage } from 'element-plus'
import { Loading } from '@element-plus/icons-vue'
import ExplainResultElder from '@/components/ExplainResultElder.vue'
import FollowUpChat from '@/components/FollowUpChat.vue'
import {
  explainPolicyStream,
  ocrPolicyImage,
  type ExplainPartialPayload,
  type ExplainResponse,
} from '@/apis/policy_api'

const STREAMING_RECORD_ID = '__streaming__'

const topic = ref<'general' | 'medical_insurance' | 'pension'>('general')
const text = ref('')
const pageUrl = ref('')
const loading = ref(false)
const finalResult = shallowRef<ExplainResponse | null>(null)
const streamingPreview = shallowRef<ExplainResponse | null>(null)
const statusMessage = ref('')

const ocrLoading = ref(false)

const displayResult = computed(() => finalResult.value ?? streamingPreview.value)
const drawerVisible = ref(false)
const desktop = ref(false)
const inlinePreviewActive = ref(false)
let abortCtl: AbortController | null = null
let desktopMql: MediaQueryList | null = null

function syncDesktopMq() {
  if (typeof window === 'undefined') return
  desktop.value = window.matchMedia('(min-width: 768px)').matches
}

onMounted(() => {
  syncDesktopMq()
  desktopMql = window.matchMedia('(min-width: 768px)')
  desktopMql.addEventListener('change', syncDesktopMq)
})

onUnmounted(() => {
  desktopMql?.removeEventListener('change', syncDesktopMq)
})

const drawerSub = computed(() => {
  if (displayResult.value) return ''
  if (statusMessage.value) return statusMessage.value
  return '正在生成结构化白话，请稍候…'
})

function resetPreviewSession() {
  abortCtl?.abort()
  abortCtl = null
  loading.value = false
  statusMessage.value = ''
  finalResult.value = null
  streamingPreview.value = null
  inlinePreviewActive.value = false
}

function onDrawerClosed() {
  resetPreviewSession()
}

function beforeOcrUpload(file: UploadRawFile) {
  const ok = file.type === 'image/jpeg' || file.type === 'image/png' || file.type === 'image/webp'
  if (!ok) {
    ElMessage.error('仅支持 JPG、PNG、WebP 图片')
    return false
  }
  const max = 8 * 1024 * 1024
  if (file.size > max) {
    ElMessage.error('图片请勿超过 8MB')
    return false
  }
  return true
}

async function runOcrUpload(options: UploadRequestOptions) {
  ocrLoading.value = true
  try {
    const res = await ocrPolicyImage(options.file as File)
    const t = res.text.trim()
    if (!t) {
      ElMessage.warning('未识别到文字，请换更清晰的政策截图重试')
      options.onSuccess(res as never)
      return
    }
    if (text.value.trim()) text.value = `${text.value.trim()}\n\n${t}`
    else text.value = t
    ElMessage.success('已填入正文框，可再编辑后点击「生成白话解读」')
    options.onSuccess(res as never)
  } catch (e: unknown) {
    const ax = e as { response?: { data?: { detail?: string } } }
    const d = ax.response?.data?.detail
    ElMessage.error(typeof d === 'string' ? d : '识别失败，请稍后重试')
    options.onError?.(e as never)
  } finally {
    ocrLoading.value = false
  }
}

async function onGenerate() {
  if (loading.value) return

  const t = text.value.trim()
  const u = pageUrl.value.trim()
  if (!t && !u) {
    ElMessage.warning('请至少填写正文、或填写政策网页链接、或先上传截图识别出文字')
    return
  }
  if (u && !/^https?:\/\//i.test(u)) {
    ElMessage.warning('链接需以 http:// 或 https:// 开头')
    return
  }

  statusMessage.value = ''
  finalResult.value = null
  streamingPreview.value = null
  syncDesktopMq()
  if (desktop.value) {
    inlinePreviewActive.value = true
    drawerVisible.value = false
  } else {
    inlinePreviewActive.value = false
    drawerVisible.value = true
  }
  loading.value = true
  abortCtl = new AbortController()
  const signal = abortCtl.signal

  const commonCallbacks = {
    onStatus: (s: { message?: string }) => {
      if (s.message) statusMessage.value = s.message
    },
    onPartial: (data: ExplainPartialPayload) => {
      streamingPreview.value = { record_id: STREAMING_RECORD_ID, ...data }
    },
    onDone: (r: ExplainResponse) => {
      statusMessage.value = ''
      streamingPreview.value = null
      finalResult.value = r
      ElMessage.success('解读完成')
    },
    onError: (detail: string) => {
      ElMessage.error(detail)
      syncDesktopMq()
      if (!desktop.value) {
        drawerVisible.value = false
      } else {
        inlinePreviewActive.value = false
      }
      loading.value = false
      statusMessage.value = ''
      finalResult.value = null
      streamingPreview.value = null
    },
  }

  const payload = {
    text: t,
    topic: topic.value,
    ...(u ? { url: u } : {}),
  }

  try {
    await explainPolicyStream(payload, commonCallbacks, { signal })
  } catch {
    if (!signal.aborted) ElMessage.error('解读失败，请稍后重试')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.explain-page {
  width: 100%;
  max-width: 52rem;
  margin-left: auto;
  margin-right: auto;
}

@media (min-width: 768px) {
  .explain-page {
    max-width: min(96rem, 100%);
    padding-left: 0.25rem;
    padding-right: 0.25rem;
  }
}

.explain-top-strip {
  position: sticky;
  top: 0;
  z-index: 5;
  margin-bottom: 1rem;
  padding: 0.85rem 1rem;
  border-radius: 1rem;
  border: 1px solid rgba(15, 118, 110, 0.22);
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.97) 0%, rgba(240, 253, 250, 0.9) 100%);
  box-shadow: 0 2px 14px rgba(15, 118, 110, 0.08);
  backdrop-filter: blur(10px);
}

.explain-top-strip-inner {
  display: flex;
  flex-direction: column;
  gap: 0.65rem;
}

@media (min-width: 640px) {
  .explain-top-strip-inner {
    flex-direction: row;
    flex-wrap: wrap;
    align-items: center;
    gap: 0.65rem 1rem;
  }
}

.explain-topic-label {
  flex-shrink: 0;
  font-size: 1.05rem;
  font-weight: 800;
  color: #0f766e;
  letter-spacing: 0.04em;
}

.explain-topic-hint {
  flex: 1 1 auto;
  min-width: 8rem;
  font-size: 0.95rem;
  line-height: 1.45;
  color: #57534e;
}

@media (min-width: 640px) {
  .explain-topic-hint {
    text-align: right;
  }
}

.explain-lead {
  margin-bottom: 1.25rem;
  padding: 1rem 1.15rem 1.15rem;
  border-radius: 1rem;
  border: 1px solid rgba(120, 113, 108, 0.14);
  background: rgba(255, 255, 255, 0.75);
  box-shadow: 0 1px 10px rgba(28, 25, 23, 0.04);
}

.explain-lead-title {
  margin: 0 0 0.4rem;
  font-size: clamp(1.35rem, 3vw, 1.65rem);
  font-weight: 800;
  line-height: 1.25;
  color: #0c0a09;
}

.explain-lead-desc {
  margin: 0;
  font-size: 1.02rem;
  line-height: 1.55;
  color: #44403c;
}

.explain-lead-desc strong {
  color: #0f766e;
  font-weight: 700;
}

.explain-shell {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

@media (min-width: 768px) {
  .explain-shell {
    flex-direction: row;
    align-items: flex-start;
    gap: 1.35rem;
  }
}

.explain-main-stage {
  display: none;
  min-width: 0;
}

@media (min-width: 768px) {
  .explain-main-stage {
    display: block;
    flex: 1 1 0;
    order: -1;
    min-height: min(70vh, 36rem);
  }
}

.explain-input-column {
  flex-shrink: 0;
  min-width: 0;
}

@media (min-width: 768px) {
  .explain-input-column {
    flex: 0 0 min(22rem, 32vw);
    max-width: 26rem;
  }
}

.explain-main-sticky {
  position: sticky;
  top: 5.5rem;
  max-height: calc(100vh - 6.25rem);
  overflow: auto;
  padding-bottom: 0.5rem;
}

.explain-preview-empty {
  border: 1px dashed rgba(15, 118, 110, 0.35);
  border-radius: 1rem;
  padding: 1.5rem 1.25rem 1.65rem;
  min-height: min(48vh, 26rem);
  display: flex;
  flex-direction: column;
  justify-content: center;
  background: linear-gradient(180deg, rgba(250, 250, 249, 0.98) 0%, rgba(240, 253, 250, 0.45) 100%);
}

.explain-preview-empty-title {
  margin: 0 0 0.55rem;
  font-size: 1.35rem;
  font-weight: 800;
  color: #0f766e;
}

.explain-preview-empty-desc {
  margin: 0;
  font-size: 1.05rem;
  line-height: 1.65;
  color: #57534e;
}

.explain-preview-pane {
  border-radius: 1.05rem;
  border: 1px solid rgba(120, 113, 108, 0.2);
  background: #fafaf9;
  box-shadow: 0 4px 18px rgba(28, 25, 23, 0.06);
  overflow: hidden;
}

.explain-preview-body {
  padding: 1rem 1.15rem 1.25rem;
}

.explain-radio-row--top {
  flex: 1 1 auto;
}

.explain-radio-row--top :deep(.el-radio-button__inner) {
  font-size: 1.05rem;
  padding: 0.6rem 1rem;
}

.explain-card {
  margin-bottom: 1.25rem;
  padding: 1.35rem 1.2rem 1.45rem;
  border-radius: 1.15rem;
  border: 1px solid var(--pp-card-border, rgba(120, 113, 108, 0.18));
  background: var(--pp-card, #fff);
  box-shadow: 0 2px 16px rgba(28, 25, 23, 0.06);
}

@media (min-width: 640px) {
  .explain-card {
    padding: 1.5rem 1.5rem 1.6rem;
  }
}

.explain-card--notice {
  padding: 0.85rem 1rem;
  background: linear-gradient(180deg, #fffbeb 0%, #fff 100%);
  border-color: rgba(245, 158, 11, 0.35);
}

.explain-alert :deep(.el-alert__title) {
  font-size: 1.05rem;
  font-weight: 700;
}

.explain-alert :deep(.el-alert__description) {
  margin-top: 0.3rem;
  font-size: 0.98rem;
  line-height: 1.55;
  color: #44403c;
}

.explain-step-head {
  display: flex;
  gap: 0.85rem;
  align-items: flex-start;
  margin-bottom: 1.1rem;
}

.explain-step-num {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 2.35rem;
  height: 2.35rem;
  border-radius: 0.7rem;
  font-size: 1.15rem;
  font-weight: 800;
  color: #fff;
  background: linear-gradient(145deg, #0d9488, #0f766e);
  box-shadow: 0 2px 8px rgba(15, 118, 110, 0.35);
}

.explain-step-title {
  margin: 0 0 0.3rem;
  font-size: 1.2rem;
  font-weight: 800;
  color: #0c0a09;
}

.explain-step-hint {
  margin: 0;
  font-size: 0.98rem;
  line-height: 1.5;
  color: #57534e;
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

.explain-field-block {
  margin-top: 0.25rem;
}

.explain-field-block--spaced {
  margin-top: 1.2rem;
}

.explain-field-label {
  display: block;
  margin-bottom: 0.55rem;
  font-size: 1.05rem;
  font-weight: 700;
  color: #292524;
}

.explain-field-help,
.explain-char-count {
  margin: 0.55rem 0 0;
  font-size: 0.95rem;
  line-height: 1.5;
  color: #57534e;
}

.explain-ocr-row {
  margin-top: 0.85rem;
  padding: 0.9rem 1rem;
  border-radius: 0.85rem;
  border: 1px dashed rgba(15, 118, 110, 0.45);
  background: rgba(240, 253, 250, 0.65);
}

.explain-ocr-hint {
  margin: 0 0 0.75rem;
  font-size: 0.95rem;
  line-height: 1.55;
  color: #44403c;
}

.explain-ocr-hint code {
  font-size: 0.88rem;
  word-break: break-all;
  color: #0f766e;
}

.explain-ocr-btn {
  width: 100%;
}

@media (min-width: 640px) {
  .explain-ocr-btn {
    width: auto;
    min-width: 13rem;
  }
}

.explain-textarea :deep(.el-textarea__inner) {
  font-size: 1.05rem;
  line-height: 1.6;
  border-radius: 0.75rem;
  padding: 0.85rem 1rem;
}

.explain-url-input :deep(.el-input__wrapper) {
  border-radius: 0.75rem;
  padding: 0.3rem 0.9rem;
  min-height: 3rem;
}

.explain-url-input :deep(.el-input__inner) {
  font-size: 1.02rem;
}

.explain-cta-wrap {
  position: sticky;
  bottom: 0;
  z-index: 2;
  margin-top: 0.25rem;
  padding: 1rem 0 0.35rem;
  background: linear-gradient(180deg, transparent 0%, rgba(240, 253, 250, 0.55) 35%, rgba(255, 255, 255, 0.96) 100%);
}

@media (min-width: 768px) {
  .explain-cta-wrap--sidebar {
    margin-top: 0;
    padding-bottom: 0.75rem;
  }
}

.explain-cta-btn {
  width: 100%;
  height: auto !important;
  padding: 0.95rem 1.35rem !important;
  font-size: 1.15rem !important;
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

.drawer-generating {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
  overflow-y: auto;
}

.drawer-gen-head {
  display: flex;
  gap: 1rem;
  align-items: flex-start;
  padding: 1rem 1.15rem;
  border-radius: 0.85rem;
  background: #fff;
  border: 1px solid #e7e5e4;
  box-shadow: 0 2px 10px rgba(28, 25, 23, 0.04);
}

.drawer-gen-icon {
  flex-shrink: 0;
  font-size: 2rem;
  color: #0f766e;
  margin-top: 0.15rem;
}

.drawer-gen-title {
  margin: 0 0 0.35rem;
  font-size: 1.25rem;
  font-weight: 800;
  color: #0c0a09;
}

.drawer-gen-desc {
  margin: 0;
  font-size: 1.05rem;
  line-height: 1.55;
  color: #57534e;
}

.drawer-generating--wait {
  justify-content: flex-start;
}

.drawer-wait-skel {
  margin-top: 0.25rem;
}

.drawer-stream-hint {
  margin: 1rem 0 0;
  padding: 0.85rem 1rem;
  font-size: 1.05rem;
  line-height: 1.5;
  color: #57534e;
  text-align: center;
  border-radius: 0.65rem;
  background: rgba(15, 118, 110, 0.08);
  border: 1px solid rgba(15, 118, 110, 0.2);
}

.drawer-result {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding-bottom: 0.5rem;
}
</style>
