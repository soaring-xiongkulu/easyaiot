<template>
  <a-drawer
    class="log-drawer"
    :open="open"
    :title="title"
    :width="drawerWidth"
    placement="right"
    destroy-on-close
    @close="emit('update:open', false)"
  >
    <template #extra><span class="muted">日志工具</span></template>

    <div class="meta" v-if="meta.length">
      <div v-for="m in meta" :key="m.label" class="meta-item">
        <span>{{ m.label }}</span>
        <b>{{ m.value }}</b>
      </div>
    </div>

    <div class="toolbar">
      <div class="toolbar-left">
        <a-checkbox v-model:checked="autoScrollEnabled">自动滚动</a-checkbox>
        <a-checkbox v-model:checked="wrapEnabled">自动换行</a-checkbox>
      </div>
      <a-space :size="8" class="toolbar-right">
        <a-button size="small" @click="copyLogs">复制内容</a-button>
        <a-button size="small" @click="scrollToBottom">跳到底部</a-button>
        <a-button v-if="onRefresh" size="small" type="primary" :loading="loading" @click="onRefresh">刷新日志</a-button>
      </a-space>
    </div>

    <a-spin :spinning="loading">
      <pre
        ref="preRef"
        class="logs viewer"
        :class="wrapEnabled ? 'wrap-mode' : 'plain-mode'"
      >{{ content || '暂无内容' }}</pre>
    </a-spin>
  </a-drawer>
</template>

<script setup lang="ts">
import { computed, nextTick, ref, watch } from 'vue'
import { message } from 'ant-design-vue'

const props = withDefaults(
  defineProps<{
    open: boolean
    title: string
    content: string
    loading?: boolean
    meta?: { label: string; value: string }[]
    width?: number | string
    onRefresh?: () => void | Promise<void>
    autoScroll?: boolean
  }>(),
  {
    loading: false,
    meta: () => [],
    autoScroll: true,
  },
)

const emit = defineEmits<{ 'update:open': [boolean] }>()
const preRef = ref<HTMLPreElement | null>(null)

const drawerWidth = computed(() => props.width ?? Math.min(Math.floor(window.innerWidth * 0.94), 1480))

const autoScrollEnabled = ref(props.autoScroll)
const wrapEnabled = ref(true)
watch(
  () => props.autoScroll,
  (v) => {
    autoScrollEnabled.value = !!v
  },
)

watch(
  () => [props.content, props.open],
  async () => {
    if (!autoScrollEnabled.value || !props.open) return
    await nextTick()
    scrollToBottom()
  },
)

async function scrollToBottom() {
  await nextTick()
  if (preRef.value) preRef.value.scrollTop = preRef.value.scrollHeight
}

async function copyLogs() {
  try {
    await navigator.clipboard.writeText(props.content || '')
    message.success('已复制')
  } catch {
    message.error('复制失败')
  }
}
</script>

<style scoped>
.meta {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
  margin-bottom: 12px;
}

.meta-item {
  border: 1px solid var(--c-border);
  border-radius: var(--radius);
  padding: 10px 12px;
  background: var(--c-fill);
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.meta-item span {
  color: var(--c-text-3);
  font-size: 12px;
}

.meta-item b {
  font-size: 13px;
  font-weight: 500;
  word-break: break-all;
}

.toolbar {
  border: 1px solid var(--c-border);
  border-radius: var(--radius);
  background: #fcfcfc;
  margin-bottom: 12px;
  min-height: 42px;
  padding: 8px 10px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  flex-wrap: wrap;
}

.toolbar-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.viewer {
  min-height: calc(100vh - 250px);
  max-height: calc(100vh - 190px);
  font-size: 13px;
  line-height: 1.75;
  border: 1px solid #2a2a2a;
}

.wrap-mode {
  white-space: pre-wrap;
  word-break: break-word;
}

.plain-mode {
  white-space: pre;
  word-break: normal;
  overflow-x: auto;
}

@media (max-width: 900px) {
  .toolbar {
    align-items: flex-start;
  }
}

:deep(.log-drawer .ant-drawer-body) {
  padding: 12px;
}
</style>
