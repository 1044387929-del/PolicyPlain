<template>
  <div class="elder-result text-stone-900 space-y-6 md:space-y-8">
    <div v-if="speechSupported" class="elder-speak-bar">
      <p class="elder-speak-hint">{{ speakHint }}</p>
      <div class="elder-speak-actions">
        <template v-if="speakState === 'idle'">
          <el-button type="primary" plain size="large" @click="readAloud">朗读全文</el-button>
        </template>
        <template v-else-if="speakState === 'speaking'">
          <el-button type="warning" plain size="large" @click="pause">暂停朗读</el-button>
          <el-button plain size="large" @click="stop">停止</el-button>
        </template>
        <template v-else>
          <el-button type="primary" plain size="large" @click="resume">继续朗读</el-button>
          <el-button plain size="large" @click="stop">停止</el-button>
        </template>
      </div>
    </div>
    <p v-else class="elder-speak-unsupported">当前环境不支持语音朗读，可换用 Chrome 或 Edge 浏览器。</p>

    <section class="elder-hero rounded-2xl border-2 border-amber-200/80 bg-amber-50/90 px-5 py-6 md:px-8 md:py-8 shadow-sm">
      <p class="elder-kicker mb-2 text-lg font-medium text-amber-900/90 md:text-xl">先给您说个明白</p>
      <p class="elder-summary text-2xl font-semibold leading-snug tracking-wide text-stone-900 md:text-3xl">
        {{ summaryDisplayed }}<span v-if="animateEntry && !showRest" class="elder-caret" aria-hidden="true" />
      </p>
    </section>

    <Transition name="elder-fade">
      <div v-show="showRest" class="elder-rest stack-y">
        <section v-if="result.applicability.length" class="elder-block">
          <h2 class="elder-h2">这事儿跟您有没有关系</h2>
          <ul class="elder-list">
            <li v-for="(x, i) in result.applicability" :key="'a' + i">{{ x }}</li>
          </ul>
        </section>

        <section class="elder-block">
          <h2 class="elder-h2">要准备些啥</h2>
          <p class="elder-para">{{ result.materials?.source_note }}</p>
          <ul v-if="(result.materials?.items || []).length" class="elder-list">
            <li v-for="(x, i) in result.materials?.items || []" :key="'m' + i">{{ x }}</li>
          </ul>
        </section>

        <section class="elder-block">
          <h2 class="elder-h2">去哪儿办、啥时候办</h2>
          <h3 class="elder-h3">办事渠道</h3>
          <ul class="elder-list mb-6">
            <li v-for="(x, i) in result.channels" :key="'c' + i">{{ x }}</li>
          </ul>
          <h3 class="elder-h3">时间上的提醒</h3>
          <ul class="elder-list">
            <li v-for="(x, i) in result.important_dates" :key="'d' + i">{{ x }}</li>
          </ul>
        </section>

        <section v-if="result.common_misunderstandings?.length" class="elder-block elder-block-warn">
          <h2 class="elder-h2">别误会这几件事</h2>
          <ul class="elder-list">
            <li v-for="(x, i) in result.common_misunderstandings" :key="'e' + i">{{ x }}</li>
          </ul>
        </section>

        <section v-if="result.uncovered_points?.length" class="elder-block">
          <h2 class="elder-h2">原文里没写到的</h2>
          <ul class="elder-list">
            <li v-for="(x, i) in result.uncovered_points" :key="'u' + i">{{ x }}</li>
          </ul>
        </section>

        <section class="elder-block">
          <h2 class="elder-h2">心里不踏实时，可以这样核实</h2>
          <ul class="elder-list">
            <li v-for="(x, i) in result.verification_hints" :key="'v' + i">{{ x }}</li>
          </ul>
        </section>

        <section v-if="result.warnings?.length" class="elder-foot rounded-xl border border-stone-300 bg-stone-100 px-5 py-4 md:px-6">
          <h2 class="elder-h2 elder-foot-title mb-3">温馨提示</h2>
          <ul class="elder-list elder-foot-list">
            <li v-for="(x, i) in result.warnings" :key="'w' + i">{{ x }}</li>
          </ul>
        </section>
      </div>
    </Transition>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import type { ExplainResponse } from '@/apis/policy_api'
import {
  buildPolicyNarration,
  isSpeechSynthesisSupported,
  usePolicySpeak,
} from '@/composables/usePolicySpeak'

const props = withDefaults(
  defineProps<{
    result: ExplainResponse
    /** 为 true 时：摘要用打字机效果，其余区块再淡入（解读页）；历史详情请用默认 false */
    animateEntry?: boolean
    /** 为 true 时：正文就绪后自动开始朗读（解读页） */
    autoSpeakWhenReady?: boolean
  }>(),
  { animateEntry: false, autoSpeakWhenReady: false },
)

const { speakState, speak, pause, resume, stop } = usePolicySpeak()
const speechSupported = ref(false)

const speakHint = computed(() => {
  if (!speechSupported.value) return ''
  if (speakState.value === 'speaking') return '正在朗读，可随时点「暂停朗读」。'
  if (speakState.value === 'paused') return '朗读已暂停，点「继续朗读」接着听，或点「停止」结束。'
  return props.autoSpeakWhenReady
    ? '内容就绪后会自动朗读；也可先点「朗读全文」。'
    : '需要时点「朗读全文」收听整篇白话。'
})

function readAloud() {
  speak(buildPolicyNarration(props.result))
}

const summaryDisplayed = ref(props.result.summary_one_line)
const showRest = ref(!props.animateEntry)

let tick: ReturnType<typeof setInterval> | null = null

function clearTick() {
  if (tick) {
    clearInterval(tick)
    tick = null
  }
}

function runEntryAnimation() {
  clearTick()
  stop()
  const full = props.result.summary_one_line ?? ''
  if (!props.animateEntry) {
    summaryDisplayed.value = full
    showRest.value = true
    return
  }
  summaryDisplayed.value = ''
  showRest.value = false
  if (!full.length) {
    summaryDisplayed.value = ''
    showRest.value = true
    return
  }
  let i = 0
  const charsPerStep = 2
  const ms = 26
  tick = setInterval(() => {
    i += charsPerStep
    if (i >= full.length) {
      summaryDisplayed.value = full
      clearTick()
      showRest.value = true
    } else {
      summaryDisplayed.value = full.slice(0, i)
    }
  }, ms)
}

watch(
  () => props.result,
  () => runEntryAnimation(),
  { immediate: true },
)

watch(showRest, (v, ov) => {
  if (v && ov === false && props.autoSpeakWhenReady) {
    speak(buildPolicyNarration(props.result))
  }
})

onMounted(() => {
  speechSupported.value = isSpeechSynthesisSupported()
  if (speechSupported.value) {
    window.speechSynthesis.getVoices()
  }
})

onUnmounted(() => {
  clearTick()
  stop()
})
</script>

<style scoped>
.elder-result {
  max-width: 48rem;
}

.elder-speak-bar {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  border-radius: 1rem;
  border: 1px solid #e7e5e4;
  background: #fafaf9;
  padding: 1.25rem 1.25rem;
}

@media (min-width: 768px) {
  .elder-speak-bar {
    flex-direction: row;
    align-items: center;
    justify-content: space-between;
    padding: 1.25rem 1.5rem;
  }
}

.elder-speak-hint {
  margin: 0;
  font-size: 1.1rem;
  line-height: 1.55;
  color: #44403c;
}

.elder-speak-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
}

.elder-speak-unsupported {
  margin: 0;
  font-size: 1.1rem;
  color: #78716c;
}

.stack-y {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

@media (min-width: 768px) {
  .stack-y {
    gap: 2rem;
  }
}

.elder-caret {
  display: inline-block;
  width: 0.12em;
  height: 1em;
  margin-left: 0.06em;
  vertical-align: -0.12em;
  background: #d97706;
  animation: elder-blink 0.85s step-end infinite;
}

@keyframes elder-blink {
  50% {
    opacity: 0;
  }
}

.elder-fade-enter-active {
  transition: opacity 0.45s ease;
}

.elder-fade-enter-from {
  opacity: 0;
}

.elder-block {
  border-radius: 1rem;
  border: 1px solid #e7e5e4;
  background: #fff;
  box-shadow: 0 1px 2px rgb(0 0 0 / 0.05);
  padding: 1.5rem 1.25rem;
}

@media (min-width: 768px) {
  .elder-block {
    padding: 2rem 2rem;
  }
}

.elder-block-warn {
  border-color: #fecdd3;
  background: rgb(255 241 242 / 0.85);
}

.elder-h2 {
  margin-bottom: 1rem;
  font-size: 1.35rem;
  font-weight: 700;
  line-height: 1.3;
  color: #0c0a09;
}

@media (min-width: 768px) {
  .elder-h2 {
    font-size: 1.6rem;
  }
}

.elder-h3 {
  margin-bottom: 0.5rem;
  font-size: 1.15rem;
  font-weight: 600;
  color: #292524;
}

@media (min-width: 768px) {
  .elder-h3 {
    font-size: 1.3rem;
  }
}

.elder-para {
  margin-bottom: 1rem;
  font-size: 1.15rem;
  line-height: 1.75;
  color: #292524;
}

@media (min-width: 768px) {
  .elder-para {
    font-size: 1.25rem;
  }
}

.elder-list {
  margin: 0;
  padding: 0;
  list-style: none;
}

.elder-list li {
  position: relative;
  margin-bottom: 1rem;
  padding-left: 1.1rem;
  border-left: 4px solid rgb(251 191 36 / 0.95);
  font-size: 1.15rem;
  line-height: 1.75;
  color: #292524;
}

@media (min-width: 768px) {
  .elder-list li {
    padding-left: 1.25rem;
    font-size: 1.25rem;
    line-height: 1.75;
  }
}

.elder-foot-title,
.elder-foot-list {
  color: #292524;
}
</style>
