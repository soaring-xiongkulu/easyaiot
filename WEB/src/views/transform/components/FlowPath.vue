<template>
  <div class="flow-path" :title="fullText">
    <span class="node node--src">{{ source }}</span>
    <span class="arrow" />
    <span class="node node--map">{{ mapping }}</span>
    <span class="arrow" />
    <span class="node node--dst">{{ destination }}</span>
  </div>
</template>

<script lang="ts" setup>
import { computed } from 'vue'

defineOptions({ name: 'TransformFlowPath' })

const props = defineProps<{
  source: string
  mapping: string
  destination: string
}>()

const fullText = computed(
  () => `${props.source} → ${props.mapping} → ${props.destination}`,
)
</script>

<style lang="less" scoped>
.flow-path {
  display: inline-flex;
  align-items: center;
  max-width: 100%;
  gap: 0;
}

.node {
  display: inline-block;
  max-width: 108px;
  padding: 1px 8px;
  border-radius: 3px;
  font-size: 12px;
  line-height: 20px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  border: 1px solid transparent;

  &--src {
    color: #1d2129;
    background: #f7f8fa;
    border-color: #e5e6eb;
  }

  &--map {
    color: #1d2129;
    background: #f7f8fa;
    border-color: #e5e6eb;
  }

  &--dst {
    color: #1d2129;
    background: #f7f8fa;
    border-color: #e5e6eb;
  }
}

.arrow {
  width: 14px;
  height: 1px;
  margin: 0 3px;
  background: #c9cdd4;
  position: relative;
  flex-shrink: 0;

  &::after {
    content: '';
    position: absolute;
    right: -1px;
    top: -3px;
    border: 3.5px solid transparent;
    border-left-color: #c9cdd4;
  }
}
</style>
