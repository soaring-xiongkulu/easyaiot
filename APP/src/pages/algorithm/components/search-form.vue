<template>
  <view class="ios-search-bar">
    <view class="ios-search-pill" @click="visible = true">
      <wd-icon name="search-line" size="17px" color="#98a2b3" />
      <text class="ios-search-text" :class="{ 'ios-search-placeholder': placeholder === '搜索算法任务' }">
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
        <wd-input v-model="formData.search" placeholder="模糊搜索" clearable />
      </view>
      <view class="yd-search-form-item">
        <view class="yd-search-form-label">
          任务类型
        </view>
        <wd-radio-group v-model="formData.task_type" type="button">
          <wd-radio value="">
            全部
          </wd-radio>
          <wd-radio value="realtime">
            实时
          </wd-radio>
          <wd-radio value="snap">
            抓拍
          </wd-radio>
          <wd-radio value="patrol">
            巡检
          </wd-radio>
        </wd-radio-group>
      </view>
      <view class="yd-search-form-item">
        <view class="yd-search-form-label">
          运行状态
        </view>
        <wd-radio-group v-model="formData.is_enabled" type="button">
          <wd-radio value="">
            全部
          </wd-radio>
          <wd-radio value="true">
            运行中
          </wd-radio>
          <wd-radio value="false">
            已停止
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
  search: '',
  task_type: '' as '' | 'realtime' | 'snap' | 'patrol',
  is_enabled: '' as '' | 'true' | 'false',
})

const placeholder = computed(() => {
  const parts: string[] = []
  if (formData.search)
    parts.push(formData.search)
  if (formData.task_type === 'realtime')
    parts.push('实时')
  if (formData.task_type === 'snap')
    parts.push('抓拍')
  if (formData.task_type === 'patrol')
    parts.push('巡检')
  if (formData.is_enabled === 'true')
    parts.push('运行中')
  if (formData.is_enabled === 'false')
    parts.push('已停止')
  return parts.length ? parts.join(' | ') : '搜索算法任务'
})

/** 是否设置了筛选项（用于筛选图标高亮） */
const hasFilter = computed(() =>
  !!formData.search || formData.task_type !== '' || formData.is_enabled !== '')

function handleSearch() {
  visible.value = false
  emit('search', {
    search: formData.search || undefined,
    task_type: formData.task_type || undefined,
    is_enabled: formData.is_enabled === '' ? undefined : formData.is_enabled === 'true',
  })
}

function handleReset() {
  formData.search = ''
  formData.task_type = ''
  formData.is_enabled = ''
  visible.value = false
  emit('reset')
}
</script>
