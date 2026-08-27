<template>
  <view class="ios-search-bar">
    <view class="ios-search-pill" @click="visible = true">
      <wd-icon name="search-line" size="17px" color="#98a2b3" />
      <text class="ios-search-text" :class="{ 'ios-search-placeholder': placeholder === '搜索模型' }">
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
          模型名称
        </view>
        <wd-input v-model="formData.search" placeholder="模糊搜索" clearable />
      </view>
      <view class="yd-search-form-item">
        <view class="yd-search-form-label">
          部署状态
        </view>
        <wd-radio-group v-model="formData.status" type="button">
          <wd-radio value="">
            全部
          </wd-radio>
          <wd-radio value="0">
            未部署
          </wd-radio>
          <wd-radio value="1">
            已部署
          </wd-radio>
          <wd-radio value="3">
            已下线
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
  status: '' as '' | '0' | '1' | '3',
})

const placeholder = computed(() => {
  const parts: string[] = []
  if (formData.search)
    parts.push(formData.search)
  if (formData.status === '0')
    parts.push('未部署')
  if (formData.status === '1')
    parts.push('已部署')
  if (formData.status === '3')
    parts.push('已下线')
  return parts.length ? parts.join(' | ') : '搜索模型'
})

/** 是否设置了筛选项（用于筛选图标高亮） */
const hasFilter = computed(() => !!formData.search || formData.status !== '')

function handleSearch() {
  visible.value = false
  emit('search', {
    search: formData.search || undefined,
    status: formData.status === '' ? undefined : Number(formData.status),
  })
}

function handleReset() {
  formData.search = ''
  formData.status = ''
  visible.value = false
  emit('reset')
}
</script>
