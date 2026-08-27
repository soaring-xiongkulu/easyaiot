<template>
  <view class="yd-page-container yd-page-container-paging">
    <wd-navbar title="模型管理" placeholder safe-area-inset-top fixed>
      <template #right>
        <AppNavUserButton />
      </template>
    </wd-navbar>

    <SearchForm @search="handleQuery" @reset="handleReset" />

    <z-paging
      ref="pagingRef"
      v-model="list"
      :fixed="false"
      class="min-h-0 flex-1"
      :default-page-size="10"
      empty-view-text="暂无模型"
      @query="queryList"
    >
      <view class="p-24rpx">
        <view
          v-for="item in list"
          :key="item.id"
          class="model-card"
          hover-class="model-card--pressed"
          :hover-stay-time="60"
          @click="handleDetail(item)"
        >
          <image
            v-if="item.imageUrl"
            :src="resolveModelImageDisplayUrl(item.imageUrl)"
            mode="aspectFill"
            class="model-thumb"
          />
          <view v-else class="model-thumb model-thumb--empty">
            <view class="i-carbon-cube text-52rpx text-[#98a2b3]" />
          </view>
          <view class="min-w-0 flex-1">
            <view class="mb-8rpx flex items-start justify-between gap-12rpx">
              <view class="truncate text-30rpx font-semibold" style="color: var(--app-text-1, #10131a)">
                {{ item.name }}
              </view>
              <view class="status-pill" :class="`status-pill--${getModelStatusTagType(item.status)}`">
                {{ getModelStatusText(item.status) }}
              </view>
            </view>
            <view class="mb-10rpx flex items-center gap-10rpx">
              <text class="version-chip">v{{ item.version || '-' }}</text>
            </view>
            <view class="line-clamp-2 text-24rpx leading-relaxed" style="color: var(--app-text-3, #98a2b3)">
              {{ item.description || '暂无描述' }}
            </view>
          </view>
        </view>
        <view class="h-20rpx" />
      </view>
    </z-paging>

    <DetailPopup ref="detailPopupRef" />
  </view>
</template>

<script lang="ts" setup>
import type { ModelInfo } from '@/api/model'
import { ref } from 'vue'
import { getModelPage } from '@/api/model'
import AppNavUserButton from '@/components/app-nav-user-button.vue'
import { getModelStatusTagType, getModelStatusText } from '@/utils/model/trainTaskUtils'
import { resolveModelImageDisplayUrl } from '@/utils/mediaDisplay'
import { parseListResponse } from '@/utils/listResponse'
import DetailPopup from './components/detail-popup.vue'
import SearchForm from './components/search-form.vue'

definePage({
  style: {
    navigationStyle: 'custom',
  },
})

const list = ref<ModelInfo[]>([])
const pagingRef = ref<any>()
const queryParams = ref<Record<string, any>>({})
const detailPopupRef = ref<InstanceType<typeof DetailPopup>>()

async function queryList(pageNo: number, pageSize: number) {
  try {
    const res = await getModelPage({ ...queryParams.value, pageNo, pageSize })
    const { list: data, total } = parseListResponse<ModelInfo>(res, ['data'])
    pagingRef.value?.completeByTotal(data, total)
  } catch {
    pagingRef.value?.complete(false)
  }
}

function handleQuery(data?: Record<string, any>) {
  queryParams.value = { ...data }
  pagingRef.value?.reload()
}

function handleReset() {
  handleQuery()
}

function handleDetail(item: ModelInfo) {
  detailPopupRef.value?.open(item)
}
</script>

<style lang="scss" scoped>
.model-card {
  display: flex;
  gap: 22rpx;
  margin-bottom: 22rpx;
  padding: 24rpx;
  background: var(--app-card-bg, #ffffff);
  border-radius: 28rpx;
  box-shadow: var(--app-card-shadow);
  transition: transform 0.12s ease;

  &--pressed {
    transform: scale(0.98);
    opacity: 0.92;
  }
}

.model-thumb {
  width: 132rpx;
  height: 132rpx;
  border-radius: 20rpx;
  background: #f0f2f6;
  flex-shrink: 0;

  &--empty {
    display: flex;
    align-items: center;
    justify-content: center;
    background: linear-gradient(135deg, #f5f8ff 0%, #eef2fa 100%);
  }
}

.status-pill {
  padding: 4rpx 14rpx;
  border-radius: 999rpx;
  font-size: 20rpx;
  font-weight: 600;
  color: #2f6bff;
  background: #eaf1ff;
  flex-shrink: 0;

  &--danger {
    color: #e5484d;
    background: #fef2f2;
  }

  &--warning {
    color: #d97706;
    background: #fdf3e2;
  }

  &--success {
    color: #0fa36e;
    background: #e6f7f1;
  }

  &--info,
  &--primary {
    color: #2f6bff;
    background: #eaf1ff;
  }
}

.version-chip {
  padding: 2rpx 14rpx;
  border-radius: 999rpx;
  font-size: 20rpx;
  font-weight: 700;
  color: var(--app-text-2, #3d4558);
  background: #f4f6fb;
}
</style>
