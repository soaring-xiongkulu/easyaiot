<template>
  <div
    ref="panelRef"
    class="transfer-panel"
    :class="{ 'transfer-panel-collapsed': collapsed }"
    :style="resizable && !collapsed && height != null ? { height: height + 'px' } : undefined"
  >
    <div v-if="resizable && !collapsed" class="transfer-panel-resize" @mousedown.prevent="onResizeStart" />
    <div class="transfer-panel-head">
      <div class="transfer-panel-actions">
        <!-- Collapse toggle: pinned far left; collapsing hides ONLY the task
             list — this button bar stays so the panel can be re-expanded. -->
        <button
          class="filter-icon-btn"
          :title="collapsed ? t('sftp.transferPanel.show') : t('sftp.transferPanel.hide')"
          @click="emit('update:collapsed', !collapsed)"
        ><el-icon><ChevronDown v-if="!collapsed" :size="'0.875rem'" /><ChevronUp v-else :size="'0.875rem'" /></el-icon></button>
        <span v-if="title" class="transfer-panel-title">{{ title }}</span>
      </div>
      <div class="transfer-panel-actions">
        <slot name="actions" />
        <button
          class="filter-icon-btn"
          :disabled="!hasFinished"
          :title="t('companion.clearTransfers')"
          @click="emit('clearCompleted')"
        ><el-icon><BrushCleaning :size="'0.875rem'" /></el-icon></button>
        <slot name="actions-end" />
      </div>
    </div>
    <div v-if="!collapsed && !tasks.length" class="transfer-empty">{{ t('companion.noTransfers') }}</div>
    <div v-else-if="!collapsed" class="transfer-progress-bar">
      <div v-for="task in tasks" :key="task.id" class="transfer-task-wrap">
        <div class="transfer-task">
          <span class="task-type"><ArrowUp v-if="task.type === 'upload'" :size="'0.75rem'" /><ArrowDown v-else :size="'0.75rem'" /></span>
          <span
            class="task-name"
            :class="{ clickable: task.files.length > 0 }"
            :title="task.files.length > 0 ? (expanded[task.id] ? t('sftp.hideFiles') : t('sftp.showFiles')) : undefined"
            @click="toggleExpand(task)"
          >{{ task.name }}<span v-if="task.fileCount > 0" class="task-dir-detail">{{ task.completedFiles }}/{{ task.fileCount }}</span></span>
          <span class="task-eta" v-if="task.eta">{{ task.eta }}</span>
          <span class="task-speed" v-if="task.status === 'running' || task.status === 'paused'">{{ task.speed || '--' }}</span>
          <el-progress
            :percentage="task.percentage"
            :status="task.status === 'error' ? 'exception' : task.status === 'cancelled' ? 'warning' : undefined"
            :stroke-width="4"
            style="flex: 1"
          />
          <div class="task-actions">
            <button
              v-if="task.status === 'running'"
              class="btn btn-ghost btn-icon btn-sm"
              :title="t('sftp.pauseTransfer')"
              @click="emit('pause', task.id)"
            ><Pause :size="'0.875rem'" /></button>
            <button
              v-else-if="task.status === 'paused'"
              class="btn btn-ghost btn-icon btn-sm"
              :title="t('sftp.resumeTransfer')"
              @click="emit('resume', task.id)"
            ><Play :size="'0.875rem'" /></button>
            <button
              v-if="task.status === 'running' || task.status === 'paused'"
              class="btn btn-ghost btn-icon btn-sm danger"
              :title="t('sftp.cancelTransfer')"
              @click="emit('cancel', task.id)"
            ><X :size="'0.875rem'" /></button>
            <button
              v-if="task.status === 'error'"
              class="btn btn-ghost btn-icon btn-sm"
              :title="t('sftp.retryTransfer')"
              @click="emit('retry', task)"
            ><RotateCcw :size="'0.875rem'" /></button>
            <span v-else-if="task.status === 'cancelled'" class="status-text">{{ t('sftp.cancelled') }}</span>
            <span v-else-if="task.status === 'done'" class="status-text done" :title="t('sftp.done')"><Check :size="'0.875rem'" /></span>
            <span v-if="task.status === 'error'" class="status-text error">{{ t('sftp.error') }}</span>
          </div>
        </div>
        <div
          v-if="expanded[task.id] && task.files.length > 0"
          class="task-files"
          :title="t('sftp.fileProgress')"
        >
          <div
            v-for="f in task.files.slice(-200)"
            :key="f.path"
            class="task-file"
            :class="'f-' + f.status"
          >
            <span class="task-file-name">{{ f.path }}</span>
            <span class="task-file-status">{{ t('sftp.fileStatus.' + f.status) }}</span>
          </div>
          <div v-if="task.files.length > 200" class="task-file-more">…</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed } from 'vue'
import { X, Pause, Play, ArrowUp, ArrowDown, Check, RotateCcw, BrushCleaning, ChevronUp, ChevronDown } from '@lucide/vue'
import { useI18n } from '../i18n'
import type { TransferTaskUI } from '../stores/panelStore'

const props = defineProps<{
  tasks: TransferTaskUI[]
  height?: number
  resizable?: boolean
  title?: string
  /** Collapsed = only the button bar is shown; the task list is hidden. */
  collapsed?: boolean
}>()

const emit = defineEmits<{
  (e: 'cancel', taskId: string): void
  (e: 'pause', taskId: string): void
  (e: 'resume', taskId: string): void
  (e: 'retry', task: TransferTaskUI): void
  (e: 'clearCompleted'): void
  (e: 'update:height', h: number): void
  (e: 'update:collapsed', v: boolean): void
}>()

const { t } = useI18n()
const panelRef = ref<HTMLElement | null>(null)

// Which tasks have their per-file detail expanded (directory transfers).
const expanded = reactive<Record<string, boolean>>({})

function toggleExpand(task: TransferTaskUI) {
  if (task.files.length === 0) return
  expanded[task.id] = !expanded[task.id]
}

const hasFinished = computed(() =>
  props.tasks.some(t => t.status === 'done' || t.status === 'error' || t.status === 'cancelled')
)

function onResizeStart(e: MouseEvent) {
  const el = panelRef.value
  if (!el) return
  const startY = e.clientY
  const startH = el.offsetHeight
  const maxH = el.parentElement ? Math.max(el.parentElement.clientHeight - 60, 120) : 720
  function onMove(ev: MouseEvent) {
    emit('update:height', Math.min(Math.max(startH + (startY - ev.clientY), 100), maxH))
  }
  function onUp() {
    document.removeEventListener('mousemove', onMove)
    document.removeEventListener('mouseup', onUp)
  }
  document.addEventListener('mousemove', onMove)
  document.addEventListener('mouseup', onUp)
}
</script>

<style scoped>
.transfer-panel {
  position: relative;
  display: flex;
  flex-direction: column;
  min-height: 6.25rem;
  border-top: 1px solid var(--border-subtle);
  background: var(--bg-elevated);
  flex-shrink: 0;
}
/* Collapsed: only the button bar remains — no reserved body height. */
.transfer-panel-collapsed {
  min-height: 0;
}
.transfer-panel-resize {
  height: 0.25rem;
  cursor: ns-resize;
  flex-shrink: 0;
  background: transparent;
}
.transfer-panel-resize:hover {
  background: var(--accent);
  opacity: 0.5;
}
.transfer-panel-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.375rem 0.5rem 0.25rem;
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--text-secondary);
  flex-shrink: 0;
}
.transfer-panel-title {
  font-weight: 600;
  color: var(--text-primary);
}
.transfer-panel-actions {
  display: flex;
  align-items: center;
  gap: 0.125rem;
}
.filter-icon-btn {
  font-size: 0.875rem;
  width: 1.625rem;
  height: 1.625rem;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0;
  border: none;
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--text-muted);
  cursor: pointer;
  flex-shrink: 0;
}
.filter-icon-btn:hover {
  color: var(--text-primary);
  background: var(--bg-hover);
}
.filter-icon-btn:disabled {
  opacity: 0.4;
  cursor: default;
}
.transfer-empty {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-muted);
  font-size: 0.75rem;
  pointer-events: none;
  z-index: 0;
}
.transfer-panel :deep(.transfer-progress-bar) {
  border-top: none;
  max-height: none;
  flex: 1;
  overflow-y: auto;
}
.transfer-progress-bar {
  padding: 0.25rem 0.75rem;
  background: var(--bg-elevated);
  border-top: 1px solid var(--border-subtle);
  max-height: 12.5rem;
  overflow-y: auto;
}
.transfer-task {
  display: flex;
  align-items: center;
  gap: 0.375rem;
  padding: 0;
  height: 1.625rem;
}
.task-type {
  display: inline-flex;
  align-items: center;
  color: var(--accent);
  flex-shrink: 0;
}
.task-name {
  font-size: 0.6875rem;
  line-height: 1;
  font-family: var(--font-mono);
  color: var(--text-secondary);
  min-width: 5.625rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.task-name.clickable {
  cursor: pointer;
}
.task-name.clickable:hover {
  color: var(--text-primary);
}
.task-dir-detail {
  margin-left: 0.25rem;
  color: var(--text-disabled);
}
.task-files {
  padding: 0.125rem 0 0.25rem 1.125rem;
}
.task-file {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  height: 1rem;
  font-size: 0.625rem;
  line-height: 1;
  font-family: var(--font-mono);
}
.task-file-name {
  color: var(--text-secondary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.task-file-status {
  flex-shrink: 0;
  color: var(--text-disabled);
}
.task-file.f-done .task-file-status {
  color: var(--accent);
}
.task-file.f-failed .task-file-status {
  color: var(--error);
}
.task-file-more {
  font-size: 0.625rem;
  color: var(--text-disabled);
}
.task-eta {
  font-size: 0.625rem;
  line-height: 1;
  font-family: var(--font-mono);
  color: var(--text-disabled);
  min-width: 3rem;
  flex-shrink: 0;
}
.task-speed {
  font-size: 0.625rem;
  line-height: 1;
  font-family: var(--font-mono);
  color: var(--text-disabled);
  min-width: 3.5rem;
  flex-shrink: 0;
}
.task-actions {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  flex-shrink: 0;
  min-width: 3.25rem;
  height: 1.5rem;
}
.status-text {
  font-size: 0.625rem;
  line-height: 1;
  color: var(--text-disabled);
  flex-shrink: 0;
}
.status-text.done {
  color: var(--accent);
}
.status-text.error {
  color: var(--error);
}
</style>

<style>
/* Progress percentage text — not scoped so it penetrates el-progress */
.transfer-progress-bar .el-progress__text {
  font-size: 0.6875rem !important;
  font-family: var(--font-mono);
}
</style>