<template>
  <a-modal
    :open="open"
    :title="title"
    :width="width"
    :footer="null"
    centered
    destroy-on-close
    :mask-closable="!loading"
    :closable="!loading"
    @cancel="!loading && emit('update:open', false)"
  >
    <p class="lead" v-if="description">{{ description }}</p>
    <div class="detail" v-if="rows.length">
      <div class="row" v-for="r in rows" :key="r.label">
        <span>{{ r.label }}</span>
        <strong>{{ r.value }}</strong>
      </div>
    </div>
    <a-alert v-if="warning" type="warning" show-icon :message="warning" style="margin-top: 12px" />
    <slot />
    <div class="footer">
      <a-button
        v-if="secondaryText"
        :disabled="loading"
        @click="emit('secondary')"
      >
        {{ secondaryText }}
      </a-button>
      <div class="footer-spacer" />
      <a-button :disabled="loading" @click="emit('update:open', false)">{{ cancelText }}</a-button>
      <a-button type="primary" :danger="danger" :loading="loading" @click="emit('confirm')">
        {{ okText }}
      </a-button>
    </div>
  </a-modal>
</template>

<script setup lang="ts">
withDefaults(
  defineProps<{
    open: boolean
    title: string
    description?: string
    warning?: string
    okText?: string
    cancelText?: string
    secondaryText?: string
    danger?: boolean
    loading?: boolean
    width?: number
    rows?: { label: string; value: string }[]
  }>(),
  {
    okText: '确认执行',
    cancelText: '取消',
    secondaryText: '',
    danger: false,
    loading: false,
    width: 560,
    rows: () => [],
  },
)

const emit = defineEmits<{
  'update:open': [boolean]
  confirm: []
  secondary: []
}>()
</script>

<style scoped>
.lead {
  margin: 0 0 12px;
  color: var(--c-text-2);
  font-size: 14px;
  line-height: 22px;
}

.detail {
  border: 1px solid var(--c-border);
  border-radius: var(--radius);
  background: var(--c-fill);
  overflow: hidden;
}

.row {
  display: grid;
  grid-template-columns: 88px 1fr;
  gap: 12px;
  padding: 10px 14px;
  border-bottom: 1px solid var(--c-border);
  font-size: 13px;
}

.row:last-child {
  border-bottom: 0;
}

.row span {
  color: var(--c-text-3);
}

.row strong {
  font-weight: 500;
  word-break: break-all;
  text-align: right;
  line-height: 1.5;
}

.footer {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 20px;
}

.footer-spacer {
  flex: 1;
}
</style>
