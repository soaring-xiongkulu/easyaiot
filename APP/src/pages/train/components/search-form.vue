<template>
  <view class="ios-search-bar">
    <view class="ios-search-pill" @click="visible = true">
      <wd-icon name="search-line" size="17px" color="#98a2b3" />
      <text class="ios-search-text" :class="{ 'ios-search-placeholder': placeholder === '搜索训练任务' }">
        {{ placeholder }}
      </text>
      <wd-icon name="filter" size="16px" :color="hasFilter ? '#2f6bff' : '#c0c7d3'" />
    </view>
  </view>

  <wd-popup
    v-model="visible"
    position="top"
    :custom-style="getTopPopupStyle()"
    :modal-style="getTopPopupModalStyle()"
    @close="visible = false"
  >
    <view class="yd-search-form-container">
      <view class="yd-search-form-item">
        <view class="yd-search-form-label">
          任务名称
        </view>
        <wd-input v-model="formData.task_name" placeholder="模糊搜索" clearable />
      </view>
      <view class="yd-search-form-item">
        <view class="yd-search-form-label">
          训练进度
        </view>
        <wd-radio-group v-model="formData.progress_filter" type="button">
          <wd-radio value="">
            全部
          </wd-radio>
          <wd-radio value="pending">
            未开始
          </wd-radio>
          <wd-radio value="running">
            进行中
          </wd-radio>
          <wd-radio value="completed">
            已完成
          </wd-radio>
        </wd-radio-group>
      </view>
      <view class="yd-search-form-actions">
        <wd-button class="flex-1" variant="plain" @click="handleReset">
          重置
        </wd-button>
        <wd-button class="flex-1" type="primary" @click="handleSearch">
          搜索
        </wd-button>
      </view>
    </view>
  </wd-popup>
</template>

<script lang="ts" setup>
import { computed, reactive, ref } from 'vue'
import { getTopPopupModalStyle, getTopPopupStyle } from '@/utils'

const emit = defineEmits<{
  search: [data: Record<string, any>]
  reset: []
}>()

const visible = ref(false)
const formData = reactive({
  task_name: '',
  progress_filter: '' as '' | 'pending' | 'running' | 'completed',
})

const placeholder = computed(() => {
  const parts: string[] = []
  if (formData.task_name)
    parts.push(formData.task_name)
  if (formData.progress_filter === 'pending')
    parts.push('未开始')
  if (formData.progress_filter === 'running')
    parts.push('进行中')
  if (formData.progress_filter === 'completed')
    parts.push('已完成')
  return parts.length ? parts.join(' | ') : '搜索训练任务'
})

/** 是否设置了筛选项（用于筛选图标高亮） */
const hasFilter = computed(() => !!formData.task_name || formData.progress_filter !== '')

function handleSearch() {
  visible.value = false
  emit('search', {
    task_name: formData.task_name || undefined,
    progress_filter: formData.progress_filter || undefined,
  })
}

function handleReset() {
  formData.task_name = ''
  formData.progress_filter = ''
  visible.value = false
  emit('reset')
}
</script>
