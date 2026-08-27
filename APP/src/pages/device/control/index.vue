<template>
  <view class="page-container">
    <wd-navbar
      :title="deviceName || '设备控制台'"
      left-arrow
      placeholder
      safe-area-inset-top
      fixed
      @click-left="handleBack"
    >
      <template #right>
        <wd-icon name="refresh" size="20px" color="#6b7688" @click="handleRefresh" />
      </template>
    </wd-navbar>

    <!-- 设备信息条 -->
    <view class="device-banner">
      <view class="banner-avatar">
        <text>{{ (deviceName || '设').slice(0, 1) }}</text>
      </view>
      <view class="banner-info">
        <text class="banner-name">{{ deviceName || deviceIdentification || '--' }}</text>
        <view class="banner-meta">
          <text class="banner-product">{{ productIdentification }}</text>
          <text v-if="template" class="banner-version">面板 v{{ template.version ?? 1 }} · {{ template.templateName }}</text>
        </view>
      </view>
    </view>

    <!-- 加载中 -->
    <view v-if="loadingTemplate" class="state-box">
      <wd-loading color="#0957de" />
      <text>正在获取产品控制面板…</text>
    </view>

    <!-- 未配置模板 -->
    <view v-else-if="!pages.length" class="state-box empty-template">
      <wd-icon name="apply" size="64px" color="#cbd2dd" />
      <text class="empty-title">该产品暂未配置控制面板</text>
      <text class="empty-desc">请在 WEB 管理端「App 面板模板」中为产品\n创建并发布控制页模板</text>
    </view>

    <!-- 动态面板 -->
    <scroll-view v-else scroll-y class="panel-scroll">
      <PanelRenderer
        ref="rendererRef"
        :pages="pages"
        :device-id="deviceId"
        :device-identification="deviceIdentification"
        :product-identification="productIdentification"
      />
      <view class="panel-footer-space" />
    </scroll-view>
  </view>
</template>

<script lang="ts" setup>
import type { AppPanelTemplate, PanelTemplatePage } from '@/api/device/panel'
import { onLoad } from '@dcloudio/uni-app'
import { ref } from 'vue'
import PanelRenderer from '@/components/panel/PanelRenderer.vue'
import { getPublishedPanelByProduct, parsePanelTemplate } from '@/api/device/panel'

definePage({
  style: {
    navigationStyle: 'custom',
  },
})

const deviceId = ref<number | string>('')
const deviceIdentification = ref('')
const productIdentification = ref('')
const deviceName = ref('')

const loadingTemplate = ref(true)
const template = ref<AppPanelTemplate | null>(null)
const pages = ref<PanelTemplatePage[]>([])
const rendererRef = ref()

onLoad((query) => {
  deviceId.value = query?.id ?? ''
  deviceIdentification.value = decodeURIComponent(query?.deviceIdentification ?? '')
  productIdentification.value = decodeURIComponent(query?.productIdentification ?? '')
  deviceName.value = decodeURIComponent(query?.name ?? '')
  loadTemplate()
})

async function loadTemplate() {
  loadingTemplate.value = true
  try {
    template.value = await getPublishedPanelByProduct(productIdentification.value)
    pages.value = parsePanelTemplate(template.value)
  }
  finally {
    loadingTemplate.value = false
  }
}

function handleRefresh() {
  if (rendererRef.value)
    rendererRef.value.refresh()
}

function handleBack() {
  uni.navigateBack({ delta: 1 })
}
</script>

<style lang="scss" scoped>
.page-container {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: linear-gradient(180deg, #e9f0fb 0%, #f5f7fb 30%);
}

.device-banner {
  display: flex;
  align-items: center;
  gap: 20rpx;
  margin: 16rpx 24rpx 24rpx;
  padding: 28rpx;
  background: #ffffff;
  border-radius: 28rpx;
  box-shadow: 0 4rpx 20rpx rgba(23, 43, 77, 0.05);
}

.banner-avatar {
  width: 96rpx;
  height: 96rpx;
  border-radius: 28rpx;
  background: linear-gradient(135deg, #66a6ff, #0957de);
  color: #fff;
  font-size: 40rpx;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
}

.banner-info {
  flex: 1;
  min-width: 0;
}

.banner-name {
  font-size: 32rpx;
  font-weight: 700;
  color: #10131a;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.banner-meta {
  display: flex;
  align-items: center;
  gap: 12rpx;
  margin-top: 8rpx;

  .banner-product,
  .banner-version {
    font-size: 22rpx;
    color: #98a2b3;
  }
}

.panel-scroll {
  flex: 1;
  height: 0;
  padding: 0 24rpx;
  box-sizing: border-box;
}

.panel-footer-space {
  height: 60rpx;
}

.state-box {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 20rpx;
  font-size: 26rpx;
  color: #98a2b3;
}

.empty-title {
  margin-top: 8rpx;
  font-size: 30rpx;
  font-weight: 600;
  color: #2a3344;
}

.empty-desc {
  text-align: center;
  line-height: 1.7;
}
</style>
