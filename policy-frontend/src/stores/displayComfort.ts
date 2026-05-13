import { defineStore } from 'pinia'
import { ref } from 'vue'

/** 全局字号档位：通过根节点 font-size 放大整站 rem，适老化阅读 */
export type TextScaleLevel = 'standard' | 'large' | 'xlarge'

const STORAGE_KEY = 'pp-text-scale'
const PANEL_OPEN_KEY = 'pp-comfort-panel-open'

function isLevel(v: string | null): v is TextScaleLevel {
  return v === 'standard' || v === 'large' || v === 'xlarge'
}

export function readStoredTextScale(): TextScaleLevel {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (isLevel(raw)) return raw
  } catch {
    /* ignore */
  }
  return 'standard'
}

export function applyTextScaleToDocument(level: TextScaleLevel) {
  document.documentElement.dataset.ppTextScale = level
}

function readPanelOpen(): boolean {
  try {
    const v = localStorage.getItem(PANEL_OPEN_KEY)
    if (v === '0') return false
    if (v === '1') return true
  } catch {
    /* ignore */
  }
  return true
}

export const useDisplayComfortStore = defineStore('displayComfort', () => {
  const level = ref<TextScaleLevel>(readStoredTextScale())
  const panelOpen = ref(readPanelOpen())

  function setLevel(next: TextScaleLevel) {
    level.value = next
    applyTextScaleToDocument(next)
    try {
      localStorage.setItem(STORAGE_KEY, next)
    } catch {
      /* ignore */
    }
  }

  function setPanelOpen(open: boolean) {
    panelOpen.value = open
    try {
      localStorage.setItem(PANEL_OPEN_KEY, open ? '1' : '0')
    } catch {
      /* ignore */
    }
  }

  return { level, setLevel, panelOpen, setPanelOpen }
})
