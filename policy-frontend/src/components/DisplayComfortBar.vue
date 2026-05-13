<template>
  <button
    v-if="!store.panelOpen"
    type="button"
    class="pp-comfort-fab"
    aria-label="打开看字大小设置"
    @click="store.setPanelOpen(true)"
  >
    <span class="pp-comfort-fab-line">看字</span>
    <span class="pp-comfort-fab-line">大小</span>
  </button>

  <div
    v-else
    class="pp-comfort-bar"
    role="toolbar"
    aria-label="全局看字大小，整页一起放大"
  >
    <div class="pp-comfort-head">
      <p class="pp-comfort-title">看字大小</p>
      <button
        type="button"
        class="pp-comfort-collapse"
        aria-label="收起看字大小面板"
        @click="store.setPanelOpen(false)"
      >
        收起
      </button>
    </div>
    <p class="pp-comfort-hint">点下面按钮，整页字一起变大，方便阅读。</p>
    <div class="pp-comfort-btns" role="group" aria-label="字号档位">
      <button
        v-for="opt in options"
        :key="opt.value"
        type="button"
        class="pp-comfort-btn"
        :class="{ 'pp-comfort-btn--active': store.level === opt.value }"
        :aria-pressed="store.level === opt.value"
        @click="store.setLevel(opt.value)"
      >
        <span class="pp-comfort-btn-label">{{ opt.label }}</span>
        <span class="pp-comfort-btn-desc">{{ opt.desc }}</span>
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useDisplayComfortStore, type TextScaleLevel } from '@/stores/displayComfort'

const store = useDisplayComfortStore()

const options: { value: TextScaleLevel; label: string; desc: string }[] = [
  { value: 'standard', label: '标准', desc: '默认大小' },
  { value: 'large', label: '大字', desc: '约大两成' },
  { value: 'xlarge', label: '特大', desc: '约大三成' },
]
</script>

<style scoped>
.pp-comfort-fab {
  position: fixed;
  right: max(0.75rem, env(safe-area-inset-right));
  bottom: max(0.75rem, env(safe-area-inset-bottom));
  z-index: 5100;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.05rem;
  min-width: 4.25rem;
  min-height: 4.25rem;
  padding: 0.5rem 0.65rem;
  border: 2px solid #0f766e;
  border-radius: 1rem;
  background: linear-gradient(160deg, #0d9488, #0f766e);
  color: #fff;
  cursor: pointer;
  box-shadow:
    0 4px 12px rgba(15, 118, 110, 0.45),
    0 2px 4px rgb(0 0 0 / 0.08);
  transition:
    transform 0.15s,
    box-shadow 0.15s;
}

.pp-comfort-fab:hover {
  transform: scale(1.03);
  box-shadow:
    0 6px 16px rgba(15, 118, 110, 0.5),
    0 2px 4px rgb(0 0 0 / 0.1);
}

.pp-comfort-fab:focus-visible {
  outline: 3px solid #fbbf24;
  outline-offset: 3px;
}

.pp-comfort-fab-line {
  font-size: 1.05rem;
  font-weight: 800;
  line-height: 1.15;
  letter-spacing: 0.06em;
}

.pp-comfort-bar {
  position: fixed;
  right: max(0.75rem, env(safe-area-inset-right));
  bottom: max(0.75rem, env(safe-area-inset-bottom));
  z-index: 5100;
  width: min(20.5rem, calc(100vw - 1.5rem));
  padding: 1rem 1.1rem 1.1rem;
  border-radius: 1rem;
  border: 2px solid rgba(15, 118, 110, 0.35);
  background: linear-gradient(165deg, #fff 0%, #f0fdfa 100%);
  box-shadow:
    0 4px 6px rgb(0 0 0 / 0.06),
    0 12px 28px rgba(15, 118, 110, 0.18);
}

.pp-comfort-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
  margin-bottom: 0.25rem;
}

.pp-comfort-title {
  margin: 0;
  font-size: 1.2rem;
  font-weight: 800;
  color: #0f766e;
  letter-spacing: 0.02em;
}

.pp-comfort-collapse {
  flex-shrink: 0;
  padding: 0.45rem 0.85rem;
  border-radius: 0.5rem;
  border: 2px solid #d6d3d1;
  background: #fff;
  font-size: 1rem;
  font-weight: 700;
  color: #44403c;
  cursor: pointer;
  transition:
    border-color 0.15s,
    background 0.15s;
}

.pp-comfort-collapse:hover {
  border-color: #a8a29e;
  background: #fafaf9;
}

.pp-comfort-collapse:focus-visible {
  outline: 3px solid #0d9488;
  outline-offset: 2px;
}

.pp-comfort-hint {
  margin: 0 0 0.85rem;
  font-size: 0.95rem;
  line-height: 1.5;
  color: #57534e;
}

.pp-comfort-btns {
  display: flex;
  flex-direction: column;
  gap: 0.55rem;
}

.pp-comfort-btn {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 0.15rem;
  width: 100%;
  padding: 0.75rem 0.9rem;
  border-radius: 0.65rem;
  border: 2px solid #d6d3d1;
  background: #fff;
  cursor: pointer;
  text-align: left;
  transition:
    border-color 0.15s,
    background 0.15s,
    box-shadow 0.15s;
}

.pp-comfort-btn:hover {
  border-color: #0d9488;
  background: #f0fdfa;
}

.pp-comfort-btn:focus-visible {
  outline: 3px solid #0d9488;
  outline-offset: 2px;
}

.pp-comfort-btn--active {
  border-color: #0f766e;
  background: rgba(15, 118, 110, 0.12);
  box-shadow: inset 0 0 0 1px rgba(15, 118, 110, 0.2);
}

.pp-comfort-btn-label {
  font-size: 1.15rem;
  font-weight: 800;
  color: #1c1917;
}

.pp-comfort-btn-desc {
  font-size: 0.9rem;
  color: #78716c;
}

@media (min-width: 640px) {
  .pp-comfort-btns {
    flex-direction: row;
    flex-wrap: wrap;
    gap: 0.5rem;
  }

  .pp-comfort-btn {
    flex: 1 1 calc(33.333% - 0.35rem);
    min-width: 5.2rem;
    align-items: center;
    text-align: center;
  }

  .pp-comfort-btn-label {
    font-size: 1.05rem;
  }

  .pp-comfort-btn-desc {
    display: none;
  }
}
</style>
