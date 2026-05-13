import { ref } from 'vue'
import type { ExplainResponse } from '@/apis/policy_api'

export type SpeakState = 'idle' | 'speaking' | 'paused'

const speakState = ref<SpeakState>('idle')

export function isSpeechSynthesisSupported(): boolean {
  return typeof window !== 'undefined' && 'speechSynthesis' in window
}

/** 拼成一段适合朗读的白话（顺序与页面一致） */
export function buildPolicyNarration(r: ExplainResponse): string {
  const chunks: string[] = []
  chunks.push('先给您说个明白。', r.summary_one_line)
  if (r.applicability?.length) {
    chunks.push('这事儿跟您有没有关系。', r.applicability.join('。'))
  }
  chunks.push('要准备些啥。', r.materials?.source_note ?? '')
  const items = r.materials?.items ?? []
  if (items.length) chunks.push(items.join('。'))
  chunks.push('办事渠道。', r.channels.join('。'))
  chunks.push('时间上的提醒。', r.important_dates.join('。'))
  if (r.common_misunderstandings?.length) {
    chunks.push('别误会这几件事。', r.common_misunderstandings.join('。'))
  }
  if (r.uncovered_points?.length) {
    chunks.push('原文里没写到的。', r.uncovered_points.join('。'))
  }
  chunks.push('心里不踏实时，可以这样核实。', r.verification_hints.join('。'))
  if (r.warnings?.length) chunks.push('温馨提示。', r.warnings.join('。'))
  return chunks.filter(Boolean).join('。')
}

function pickZhVoice(): SpeechSynthesisVoice | null {
  const list = window.speechSynthesis.getVoices()
  return (
    list.find((v) => v.lang === 'zh-CN') ||
    list.find((v) => v.lang.startsWith('zh')) ||
    null
  )
}

export function usePolicySpeak() {
  function stop() {
    if (!isSpeechSynthesisSupported()) return
    window.speechSynthesis.cancel()
    speakState.value = 'idle'
  }

  function pause() {
    if (!isSpeechSynthesisSupported()) return
    if (window.speechSynthesis.speaking && !window.speechSynthesis.paused) {
      window.speechSynthesis.pause()
      speakState.value = 'paused'
    }
  }

  function resume() {
    if (!isSpeechSynthesisSupported()) return
    if (window.speechSynthesis.paused) {
      window.speechSynthesis.resume()
      speakState.value = 'speaking'
    }
  }

  function speak(text: string) {
    if (!isSpeechSynthesisSupported()) return
    const raw = text.replace(/\s+/g, ' ').trim()
    if (!raw) return

    stop()

    const run = () => {
      const u = new SpeechSynthesisUtterance(raw)
      u.lang = 'zh-CN'
      u.rate = 0.9
      u.pitch = 1
      const voice = pickZhVoice()
      if (voice) u.voice = voice
      u.onend = () => {
        speakState.value = 'idle'
      }
      u.onerror = () => {
        speakState.value = 'idle'
      }
      speakState.value = 'speaking'
      window.speechSynthesis.speak(u)
    }

    if (window.speechSynthesis.getVoices().length === 0) {
      window.speechSynthesis.addEventListener('voiceschanged', run, { once: true })
    } else {
      run()
    }
  }

  return {
    speakState,
    speak,
    pause,
    resume,
    stop,
  }
}
