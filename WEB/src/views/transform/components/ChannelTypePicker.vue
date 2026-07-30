<template>
  <div class="channel-picker" :class="{ 'channel-picker--disabled': disabled }">
    <div
      v-for="item in options"
      :key="item.value"
      class="channel-card"
      :class="{ 'channel-card--active': value === item.value }"
      @click="!disabled && emit('update:value', item.value)"
    >
      <div class="channel-card__body">
        <div class="channel-card__title">{{ item.label }}</div>
        <div class="channel-card__desc">{{ item.desc }}</div>
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { channelMetaOptions } from '../data'

defineOptions({ name: 'TransformChannelTypePicker' })

withDefaults(
  defineProps<{
    value?: string
    disabled?: boolean
  }>(),
  { disabled: false },
)

const emit = defineEmits<{
  (e: 'update:value', value: string): void
}>()

const options = channelMetaOptions
</script>

<style lang="less" scoped>
.channel-picker {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 8px;
  width: 100%;

  &--disabled .channel-card {
    cursor: default;
    opacity: 0.75;
  }
}

.channel-card {
  padding: 10px 12px;
  border: 1px solid #ebebeb;
  border-radius: 4px;
  background: #fff;
  cursor: pointer;
  transition: border-color 0.15s;

  &:hover {
    border-color: #91b5ff;
  }

  &--active {
    border-color: #266cfb;
    background: #f7faff;
  }
}

.channel-card__title {
  font-size: 13px;
  font-weight: 600;
  color: #1d2129;
}

.channel-card__desc {
  margin-top: 2px;
  font-size: 12px;
  color: #86909c;
  line-height: 1.4;
}
</style>
