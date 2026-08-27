<template>
  <!-- 筛选入口 + 全部已读 -->
  <view class="ios-search-bar">
    <view class="flex flex-1 items-center gap-16rpx pr-16rpx">
      <view class="ios-search-pill" @click="visible = true">
        <wd-icon name="search-line" size="17px" color="#98a2b3" />
        <text class="ios-search-text" :class="{ 'ios-search-placeholder': placeholder === '搜索消息' }">
          {{ placeholder }}
        </text>
        <wd-icon name="filter" size="16px" :color="hasFilter ? '#2f6bff' : '#c0c7d3'" />
      </view>
      <view class="read-all-btn" @click="handleReadAll">
        <wd-icon name="doublecheck" size="26rpx" color="#2f6bff" />
        <text>全部已读</text>
      </view>
    </view>
  </view>

  <!-- 搜索弹窗 -->
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
          已读状态
        </view>
        <wd-radio-group v-model="formData.readStatus" type="button">
          <wd-radio :value="-1">
            全部
          </wd-radio>
          <wd-radio :value="true">
            已读
          </wd-radio>
          <wd-radio :value="false">
            未读
          </wd-radio>
        </wd-radio-group>
      </view>
      <yd-search-date-range v-model="formData.createTime" label="发送时间" />
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
import { formatDate, formatDateRange } from '@/utils/date'

const emit = defineEmits<{
  search: [data: Record<string, any>]
  reset: []
  readAll: []
}>()

const visible = ref(false) // 搜索弹窗显示状态
const formData = reactive({
  readStatus: -1 as -1 | boolean, // -1 表示全部, true 已读, false 未读
  createTime: [undefined, undefined] as [number | undefined, number | undefined],
}) // 搜索表单数据

/** 搜索条件 placeholder 拼接 */
const placeholder = computed(() => {
  const conditions: string[] = []
  if (formData.readStatus === true) {
    conditions.push('已读')
  } else if (formData.readStatus === false) {
    conditions.push('未读')
  }
  if (formData.createTime?.[0] && formData.createTime?.[1]) {
    conditions.push(`${formatDate(formData.createTime[0])}~${formatDate(formData.createTime[1])}`)
  }
  return conditions.length > 0 ? conditions.join(' | ') : '搜索消息'
})

/** 是否设置了筛选项（用于筛选图标高亮） */
const hasFilter = computed(() =>
  formData.readStatus !== -1 || !!(formData.createTime?.[0] && formData.createTime?.[1]))

/** 全部已读 */
function handleReadAll() {
  emit('readAll')
}

/** 搜索按钮操作 */
function handleSearch() {
  visible.value = false
  emit('search', {
    readStatus: formData.readStatus === -1 ? undefined : formData.readStatus,
    createTime: formatDateRange(formData.createTime),
  })
}

/** 重置按钮操作 */
function handleReset() {
  formData.readStatus = -1
  formData.createTime = [undefined, undefined]
  visible.value = false
  emit('reset')
}
</script>

<style lang="scss" scoped>
.read-all-btn {
  display: flex;
  align-items: center;
  gap: 8rpx;
  height: 68rpx;
  padding: 0 24rpx;
  border-radius: 999rpx;
  font-size: 23rpx;
  font-weight: 600;
  color: #2f6bff;
  background: #eaf1ff;
  flex-shrink: 0;

  &:active {
    opacity: 0.85;
  }
}
</style>
