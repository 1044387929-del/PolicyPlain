<template>
  <section v-if="recordId" class="follow-up-root">
    <h3 class="follow-up-title">追问</h3>
    <p class="follow-up-hint">结合本次保存的原文与白话解读提问；同一记录最多 3 轮，服务端会校验并写入历史。</p>

    <div v-if="messages.length" class="follow-up-list">
      <div v-for="m in messages" :key="m.id" class="follow-up-turn">
        <div class="follow-up-q">
          <span class="fu-label">问</span>
          <span class="fu-body">{{ m.question }}</span>
        </div>
        <div class="follow-up-a">
          <span class="fu-label">答</span>
          <span class="fu-body">{{ m.answer || '…' }}</span>
        </div>
      </div>
    </div>

    <div v-if="streamingText" class="follow-up-stream" aria-live="polite">
      <span class="fu-label fu-label--muted">答（生成中）</span>
      <p class="follow-up-stream-body">{{ streamingText }}</p>
    </div>

    <div v-if="!disabled" class="follow-up-input-row">
      <el-input
        v-model="draft"
        type="textarea"
        :rows="2"
        maxlength="4000"
        show-word-limit
        placeholder="例如：我外地参保的年限能合并算吗？要带哪些材料？"
        class="follow-up-textarea"
      />
      <el-button type="primary" size="large" class="follow-up-send" :loading="sending" @click="onSend">
        发送追问
      </el-button>
    </div>
    <p v-else class="follow-up-cap">本条解读的追问已达上限（3 轮）</p>
  </section>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { followUpPolicyStream, type FollowUpItem } from '@/apis/policy_api'

const props = defineProps<{
  recordId: string
  seedFollowups?: FollowUpItem[]
}>()

type LocalTurn = { id: string; question: string; answer: string }

const messages = ref<LocalTurn[]>([])
const draft = ref('')
const sending = ref(false)
const streamingText = ref('')
let abortCtl: AbortController | null = null

function syncFromSeed() {
  draft.value = ''
  streamingText.value = ''
  const s = props.seedFollowups ?? []
  messages.value = s.map((x) => ({ id: x.id, question: x.question, answer: x.answer }))
}

watch(
  () => [props.recordId, props.seedFollowups] as const,
  () => {
    syncFromSeed()
  },
  { immediate: true, deep: true },
)

const roundsUsed = computed(() => messages.value.length)
const disabled = computed(() => roundsUsed.value >= 3)

async function onSend() {
  const q = draft.value.trim()
  if (!q || sending.value || disabled.value) return
  sending.value = true
  streamingText.value = ''
  abortCtl = new AbortController()
  let acc = ''
  try {
    await followUpPolicyStream(
      props.recordId,
      q,
      {
        onDelta: (t) => {
          acc += t
          streamingText.value = acc
        },
        onDone: (p) => {
          messages.value.push({
            id: p.followup_id || `local-${Date.now()}`,
            question: q,
            answer: p.answer,
          })
          draft.value = ''
          streamingText.value = ''
          ElMessage.success('本轮追问已保存')
        },
        onError: (d) => {
          ElMessage.error(d)
        },
      },
      { signal: abortCtl.signal },
    )
  } finally {
    sending.value = false
    abortCtl = null
  }
}
</script>

<style scoped>
.follow-up-root {
  margin-top: 1.25rem;
  padding: 1.1rem 1.15rem 1.2rem;
  border-radius: 0.9rem;
  border: 1px solid rgba(15, 118, 110, 0.22);
  background: linear-gradient(180deg, rgba(240, 253, 250, 0.75) 0%, #fff 55%);
}

.follow-up-title {
  margin: 0 0 0.35rem;
  font-size: 1.2rem;
  font-weight: 800;
  color: #0f766e;
}

.follow-up-hint {
  margin: 0 0 1rem;
  font-size: 1rem;
  line-height: 1.55;
  color: #57534e;
}

.follow-up-list {
  display: flex;
  flex-direction: column;
  gap: 0.85rem;
  margin-bottom: 1rem;
}

.follow-up-turn {
  padding: 0.85rem 1rem;
  border-radius: 0.75rem;
  background: #fff;
  border: 1px solid #e7e5e4;
}

.follow-up-q,
.follow-up-a {
  display: flex;
  gap: 0.5rem;
  align-items: flex-start;
  font-size: 1.05rem;
  line-height: 1.6;
  color: #292524;
}

.follow-up-a {
  margin-top: 0.5rem;
  color: #44403c;
}

.fu-label {
  flex-shrink: 0;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 1.75rem;
  padding: 0.1rem 0.35rem;
  border-radius: 0.4rem;
  font-size: 0.85rem;
  font-weight: 800;
  color: #fff;
  background: #0f766e;
}

.follow-up-q .fu-label {
  background: #0d9488;
}

.fu-label--muted {
  background: #78716c;
}

.fu-body {
  flex: 1;
  white-space: pre-wrap;
  word-break: break-word;
}

.follow-up-stream {
  margin-bottom: 1rem;
  padding: 0.85rem 1rem;
  border-radius: 0.75rem;
  background: rgba(15, 118, 110, 0.06);
  border: 1px dashed rgba(15, 118, 110, 0.35);
}

.follow-up-stream-body {
  margin: 0.5rem 0 0;
  font-size: 1.05rem;
  line-height: 1.65;
  white-space: pre-wrap;
  word-break: break-word;
  color: #292524;
}

.follow-up-input-row {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.follow-up-textarea :deep(.el-textarea__inner) {
  font-size: 1.05rem;
  line-height: 1.55;
  border-radius: 0.65rem;
}

.follow-up-send {
  align-self: flex-start;
  font-weight: 700;
}

.follow-up-cap {
  margin: 0;
  font-size: 1.02rem;
  font-weight: 600;
  color: #78716c;
}
</style>
