<template>
  <Tooltip :title="title">
    <button
      type="button"
      class="overlay-btn"
      :class="{ 'overlay-btn--danger': danger }"
      @click="emit('click')"
    >
      <slot></slot>
    </button>
  </Tooltip>
</template>

<script lang="ts" setup>
import { Tooltip } from 'ant-design-vue'

defineOptions({ name: 'TransformOverlayBtn' })

withDefaults(
  defineProps<{
    title: string
    danger?: boolean
  }>(),
  { danger: false },
)

const emit = defineEmits<{ (e: 'click'): void }>()
</script>

<style lang="less" scoped>
.overlay-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 34px;
  height: 34px;
  border: none;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.92);
  color: #266cfb;
  font-size: 16px;
  cursor: pointer;
  transition: background 0.2s, color 0.2s, transform 0.2s;

  &:hover {
    background: #fff;
    transform: scale(1.08);
  }

  &--danger {
    color: #f5222d;

    &:hover {
      background: #fff1f0;
    }
  }
}
</style>
