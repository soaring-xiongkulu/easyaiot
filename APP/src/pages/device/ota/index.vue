<template>
  <view class="page-container">
    <wd-navbar title="OTA 升级" left-arrow placeholder safe-area-inset-top fixed @click-left="handleBack" />

    <scroll-view scroll-y class="ota-scroll">
      <!-- 设备与当前版本 -->
      <view class="card head-card">
        <view class="head-main">
          <view class="head-avatar">
            <text>{{ avatarLetter }}</text>
          </view>
          <view class="head-info">
            <text class="head-name">{{ deviceName || deviceIdentification || '--' }}</text>
            <view class="head-version">
              <text class="head-version-label">当前版本</text>
              <text class="head-version-value">{{ deviceVersion || '未知（首次检测后记录）' }}</text>
            </view>
          </view>
        </view>
        <view class="head-actions">
          <view class="check-btn" :class="{ 'check-btn--loading': otaState.checking }" @click="handleCheck">
            <wd-loading v-if="otaState.checking" size="16px" color="#ffffff" />
            <wd-icon v-else name="search-line" size="16px" color="#ffffff" />
            <text>{{ otaState.checking ? '检测中…' : '检查更新' }}</text>
          </view>
        </view>
        <view v-if="otaState.checkError" class="check-error">
          {{ otaState.checkError }}
        </view>
      </view>

      <!-- 检测结果 -->
      <view v-if="!otaState.checking && hasChecked && !otaState.items.length" class="card empty-card">
        <view class="empty-icon">
          <wd-icon name="check-circle" size="48px" color="#12b77c" />
        </view>
        <text class="empty-title">已是最新版本</text>
        <text class="empty-desc">平台没有比当前更高的可用版本</text>
      </view>

      <view v-for="item in otaState.items" :key="item.type" class="card pkg-card">
        <view class="pkg-head">
          <view class="pkg-type" :style="{ background: `${typeColor(item.type)}14`, color: typeColor(item.type) }">
            <text>{{ typeName(item.type) }}</text>
          </view>
          <text class="channel-tag" :class="`channel-tag--${item.channel === 1 ? 'test' : 'release'}`">
            {{ item.channel === 1 ? '测试通道' : '正式通道' }}
          </text>
          <text v-if="item.mustPass === 1" class="force-tag force-tag--must">必经版本</text>
          <text v-else-if="item.forceUpdate === 1" class="force-tag">强制升级</text>
        </view>

        <text class="pkg-name">{{ item.name || '升级包' }}</text>

        <view class="version-flow">
          <text class="version-from">{{ deviceVersion || '当前' }}</text>
          <view class="version-arrow">
            <wd-icon name="arrow-right" size="16px" color="#2f6bff" />
          </view>
          <text class="version-to">{{ item.version }}</text>
        </view>

        <view class="pkg-meta">
          <text v-if="item.fileSize">{{ formatSize(item.fileSize) }}</text>
          <text v-if="item.fileName" class="pkg-file">{{ item.fileName }}</text>
        </view>

        <view v-if="item.changelog" class="pkg-changelog">
          <text>{{ item.changelog }}</text>
        </view>

        <!-- 升级执行区 -->
        <view v-if="runOf(item.type).stage !== 'idle'" class="run-area">
          <view class="step-row">
            <view
              v-for="step in stepList"
              :key="step.key"
              class="step"
              :class="stepClass(runOf(item.type), step.key)"
            >
              <view class="step-dot">
                <wd-icon v-if="stepDone(runOf(item.type), step.key)" name="check" size="18rpx" color="#ffffff" />
              </view>
              <text class="step-label">{{ step.label }}</text>
            </view>
          </view>

          <template v-if="runOf(item.type).stage === 'downloading' || runOf(item.type).stage === 'verifying'">
            <view class="progress-bar">
              <view class="progress-inner" :style="{ width: `${runOf(item.type).progress}%` }" />
            </view>
            <text class="run-text">
              {{ runOf(item.type).stage === 'downloading' ? `下载中 ${runOf(item.type).progress}%` : `校验安装包 ${runOf(item.type).progress}%` }}
            </text>
          </template>
          <text v-else-if="runOf(item.type).stage === 'installing'" class="run-text">正在安装并上报结果…</text>
          <template v-else-if="runOf(item.type).stage === 'done'">
            <text class="run-text run-text--ok">升级完成，设备版本已同步为 v{{ item.version }}</text>
            <view class="run-actions">
              <view class="run-btn run-btn--ghost" @click="handleCheck">
                再查一次
              </view>
              <view class="run-btn run-btn--primary" @click="handleBack">
                完成
              </view>
            </view>
          </template>
          <template v-else-if="runOf(item.type).stage === 'failed'">
            <text class="run-text run-text--err">{{ runOf(item.type).errorMsg || '升级失败，请重试' }}</text>
            <view v-if="runOf(item.type).verifySkippedReason" class="run-skip-tip">
              {{ runOf(item.type).verifySkippedReason }}
            </view>
            <view class="run-actions">
              <view class="run-btn run-btn--primary" @click="handleUpgrade(item)">
                重试
              </view>
            </view>
          </template>
        </view>

        <view v-else class="pkg-actions">
          <view
            class="upgrade-btn"
            :class="{ 'upgrade-btn--disabled': busy }"
            @click="handleUpgrade(item)"
          >
            <text>{{ busy ? '升级进行中…' : '立即升级' }}</text>
          </view>
          <text v-if="item.forceUpdate === 1 || item.mustPass === 1" class="force-note">该版本不可跳过</text>
        </view>
      </view>

      <!-- 流程说明 -->
      <view v-if="otaState.items.length" class="flow-tip">
        <text>以上流程以设备身份执行：检测 → 命中 → 下载 → MD5 校验 → 安装 → 启动，各阶段实时上报平台留痕，启动成功后自动回写设备版本。</text>
      </view>
      <view class="h-40rpx" />
    </scroll-view>
  </view>
</template>

<script lang="ts" setup>
import type { OtaUpgradeItem } from '@/api/device/ota'
import { onLoad } from '@dcloudio/uni-app'
import { OTA_PACKAGE_TYPES, otaPackageTypeName } from '@/api/device/ota'
import { getDeviceByIdentification } from '@/api/device/panel'
import {
  canSkipUpgrade,
  checkDeviceUpgrade,
  otaUpgradeState as otaState,
  runDeviceUpgrade,
} from '@/service/ota-upgrade'

definePage({
  style: {
    navigationStyle: 'custom',
  },
})

const deviceIdentification = ref('')
const productIdentification = ref('')
const deviceName = ref('')
const deviceVersion = ref('')
const hasChecked = ref(false)
/** 当前正在执行的包类型（同一时间只允许一个升级任务） */
const runningType = ref<number | null>(null)

const busy = computed(() => runningType.value !== null)

const avatarLetter = computed(() => (deviceName.value || deviceIdentification.value || '设').slice(0, 1).toUpperCase())

const stepList = [
  { key: 'hit', label: '命中' },
  { key: 'download', label: '下载' },
  { key: 'verify', label: '校验' },
  { key: 'install', label: '安装' },
  { key: 'done', label: '完成' },
] as const

type StepKey = typeof stepList[number]['key']

const stageStepIndex: Record<string, StepKey> = {
  reporting: 'hit',
  downloading: 'download',
  verifying: 'verify',
  installing: 'install',
  done: 'done',
  failed: 'download',
}

function runOf(type: number) {
  return (
    otaState.runs[type] || {
      stage: 'idle' as const,
      progress: 0,
      errorMsg: '',
      verifySkippedReason: '',
    }
  )
}

function typeName(type: number) {
  return otaPackageTypeName(type)
}

function typeColor(type: number) {
  return OTA_PACKAGE_TYPES.find(t => t.code === type)?.color || '#2f6bff'
}

function formatSize(bytes: number) {
  if (bytes >= 1024 * 1024) {
    return `${(bytes / 1024 / 1024).toFixed(1)} MB`
  }
  if (bytes >= 1024) {
    return `${(bytes / 1024).toFixed(0)} KB`
  }
  return `${bytes} B`
}

function stepIndex(run: { stage: string }): number {
  if (run.stage === 'idle') {
    return -1
  }
  const key = stageStepIndex[run.stage]
  return stepList.findIndex(s => s.key === key)
}

function stepClass(run: { stage: string, errorMsg?: string }, key: StepKey) {
  const current = stepIndex(run)
  const idx = stepList.findIndex(s => s.key === key)
  if (run.stage === 'failed' && idx === current) {
    return 'step--error'
  }
  if (idx < current) {
    return 'step--done'
  }
  if (idx === current) {
    return 'step--active'
  }
  return ''
}

function stepDone(run: { stage: string }, key: StepKey) {
  const current = stepIndex(run)
  const idx = stepList.findIndex(s => s.key === key)
  return run.stage !== 'failed' && idx < current
}

onLoad((query) => {
  deviceIdentification.value = decodeURIComponent(query?.deviceIdentification ?? '')
  productIdentification.value = decodeURIComponent(query?.productIdentification ?? '')
  deviceName.value = decodeURIComponent(query?.name ?? '')
  deviceVersion.value = decodeURIComponent(query?.version ?? '')
  doCheck()
})

function handleCheck() {
  if (!otaState.checking) {
    doCheck()
  }
}

async function doCheck() {
  try {
    hasChecked.value = true
    const items = await checkDeviceUpgrade({
      deviceIdentification: deviceIdentification.value,
      productIdentification: productIdentification.value || undefined,
      deviceVersion: deviceVersion.value || undefined,
    })
    // 检测前后版本可能变化，刷新本地展示
    await refreshDeviceVersion()
    if (!items.length) {
      return
    }
  } catch {
    // 错误信息已在 otaState.checkError 中
  }
}

async function refreshDeviceVersion() {
  const detail = await getDeviceByIdentification(productIdentification.value, deviceIdentification.value)
  if (detail?.deviceVersion) {
    deviceVersion.value = detail.deviceVersion
  }
}

async function handleUpgrade(item: OtaUpgradeItem) {
  if (busy.value) {
    return
  }
  if (!canSkipUpgrade(item)) {
    uni.showToast({ icon: 'none', title: '该版本不可跳过，将直接开始升级' })
  }
  runningType.value = item.type
  try {
    await runDeviceUpgrade(
      {
        deviceIdentification: deviceIdentification.value,
        productIdentification: productIdentification.value || undefined,
        deviceVersion: deviceVersion.value || undefined,
      },
      item,
    )
    if (runOf(item.type).stage === 'done') {
      await refreshDeviceVersion()
    }
  } finally {
    runningType.value = null
  }
}

function handleBack() {
  uni.navigateBack({ delta: 1 })
}
</script>

<style lang="scss" scoped>
.page-container {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: var(--app-page-bg, #f2f2f7);
}

.ota-scroll {
  flex: 1;
  height: 0;
  padding: 16rpx 24rpx 0;
  box-sizing: border-box;
}

.card {
  margin-bottom: 22rpx;
  padding: 28rpx;
  background: #ffffff;
  border-radius: 28rpx;
  box-shadow: var(--app-card-shadow, 0 2rpx 8rpx rgba(23, 43, 77, 0.04), 0 12rpx 32rpx rgba(23, 43, 77, 0.06));
}

// ==================== 头部 ====================
.head-main {
  display: flex;
  align-items: center;
  gap: 22rpx;
}

.head-avatar {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 96rpx;
  height: 96rpx;
  border-radius: 28rpx;
  color: #ffffff;
  font-size: 42rpx;
  font-weight: 700;
  background: linear-gradient(135deg, #5d9bff 0%, #2f6bff 60%, #1f56d6 100%);
  box-shadow: 0 10rpx 22rpx rgba(47, 107, 255, 0.28);
  flex-shrink: 0;
}

.head-info {
  flex: 1;
  min-width: 0;
}

.head-name {
  font-size: 32rpx;
  font-weight: 700;
  color: var(--app-text-1, #10131a);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.head-version {
  display: flex;
  align-items: baseline;
  gap: 14rpx;
  margin-top: 10rpx;
}

.head-version-label {
  font-size: 22rpx;
  color: var(--app-text-3, #98a2b3);
  flex-shrink: 0;
}

.head-version-value {
  font-size: 26rpx;
  font-weight: 700;
  color: #2f6bff;
  word-break: break-all;
}

.head-actions {
  margin-top: 24rpx;
}

.check-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12rpx;
  height: 80rpx;
  border-radius: 999rpx;
  background: linear-gradient(135deg, #4a8bff, #2f6bff);
  color: #ffffff;
  font-size: 28rpx;
  font-weight: 600;
  box-shadow: 0 10rpx 24rpx rgba(47, 107, 255, 0.3);

  &:active {
    opacity: 0.9;
  }

  &--loading {
    opacity: 0.85;
  }
}

.check-error {
  margin-top: 18rpx;
  padding: 16rpx 20rpx;
  border-radius: 14rpx;
  background: #fef2f2;
  color: #dc2626;
  font-size: 24rpx;
}

// ==================== 空态 ====================
.empty-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 60rpx 28rpx;
}

.empty-icon {
  margin-bottom: 20rpx;
}

.empty-title {
  font-size: 30rpx;
  font-weight: 700;
  color: var(--app-text-1, #10131a);
}

.empty-desc {
  margin-top: 10rpx;
  font-size: 24rpx;
  color: var(--app-text-3, #98a2b3);
}

// ==================== 升级项卡片 ====================
.pkg-head {
  display: flex;
  align-items: center;
  gap: 12rpx;
  flex-wrap: wrap;
}

.pkg-type {
  padding: 6rpx 18rpx;
  border-radius: 10rpx;
  font-size: 22rpx;
  font-weight: 700;
}

.channel-tag {
  padding: 4rpx 14rpx;
  border-radius: 999rpx;
  font-size: 20rpx;
  font-weight: 600;

  &--test {
    color: #7c3aed;
    background: #ede9fe;
  }

  &--release {
    color: #0fa36e;
    background: #e6f7f1;
  }
}

.force-tag {
  padding: 4rpx 14rpx;
  border-radius: 999rpx;
  font-size: 20rpx;
  font-weight: 600;
  color: #dc2626;
  background: #fef2f2;

  &--must {
    color: #b45309;
    background: #fdf3e2;
  }
}

.pkg-name {
  display: block;
  margin-top: 20rpx;
  font-size: 30rpx;
  font-weight: 700;
  color: var(--app-text-1, #10131a);
}

.version-flow {
  display: flex;
  align-items: center;
  gap: 16rpx;
  margin-top: 18rpx;
  padding: 16rpx 22rpx;
  border-radius: 16rpx;
  background: #f7f9fd;
}

.version-from {
  font-size: 24rpx;
  color: var(--app-text-3, #98a2b3);
}

.version-arrow {
  display: flex;
}

.version-to {
  font-size: 28rpx;
  font-weight: 700;
  color: #2f6bff;
}

.pkg-meta {
  display: flex;
  align-items: center;
  gap: 20rpx;
  margin-top: 16rpx;
  font-size: 22rpx;
  color: var(--app-text-3, #98a2b3);
}

.pkg-file {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.pkg-changelog {
  margin-top: 16rpx;
  padding: 18rpx 20rpx;
  border-radius: 14rpx;
  background: #f7f9fd;
  color: var(--app-text-2, #3d4558);
  font-size: 24rpx;
  line-height: 1.7;
  word-break: break-all;
}

.pkg-actions {
  margin-top: 22rpx;
}

.upgrade-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 78rpx;
  border-radius: 999rpx;
  background: linear-gradient(135deg, #4a8bff, #2f6bff);
  color: #ffffff;
  font-size: 28rpx;
  font-weight: 600;
  box-shadow: 0 10rpx 24rpx rgba(47, 107, 255, 0.28);

  &:active {
    opacity: 0.9;
  }

  &--disabled {
    opacity: 0.5;
  }
}

.force-note {
  display: block;
  margin-top: 12rpx;
  font-size: 22rpx;
  color: #b45309;
  text-align: center;
}

// ==================== 升级执行 ====================
.run-area {
  margin-top: 24rpx;
  padding-top: 24rpx;
  border-top: 1rpx solid var(--app-separator, rgba(23, 43, 77, 0.06));
}

.step-row {
  display: flex;
  justify-content: space-between;
}

.step {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10rpx;
  flex: 1;
}

.step-dot {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 34rpx;
  height: 34rpx;
  border-radius: 50%;
  background: #e6eaf2;
  color: #ffffff;
  transition: all 0.2s ease;
}

.step-label {
  font-size: 21rpx;
  color: var(--app-text-3, #98a2b3);
}

.step--active {
  .step-dot {
    background: #2f6bff;
    box-shadow: 0 0 0 8rpx rgba(47, 107, 255, 0.14);
  }

  .step-label {
    color: #2f6bff;
    font-weight: 700;
  }
}

.step--done {
  .step-dot {
    background: #12b77c;
  }

  .step-label {
    color: #0fa36e;
  }
}

.step--error {
  .step-dot {
    background: #dc2626;
  }

  .step-label {
    color: #dc2626;
    font-weight: 700;
  }
}

.progress-bar {
  height: 14rpx;
  overflow: hidden;
  margin-top: 26rpx;
  border-radius: 999rpx;
  background: #e6eaf2;
}

.progress-inner {
  height: 100%;
  border-radius: 999rpx;
  background: linear-gradient(90deg, #4a8bff, #2f6bff);
  transition: width 0.2s ease;
}

.run-text {
  display: block;
  margin-top: 16rpx;
  color: var(--app-text-2, #3d4558);
  text-align: center;
  font-size: 24rpx;

  &--ok {
    color: #0fa36e;
    font-weight: 600;
  }

  &--err {
    color: #dc2626;
  }
}

.run-skip-tip {
  margin-top: 10rpx;
  font-size: 22rpx;
  color: #b45309;
  text-align: center;
}

.run-actions {
  display: flex;
  gap: 20rpx;
  margin-top: 22rpx;
}

.run-btn {
  display: flex;
  flex: 1;
  align-items: center;
  justify-content: center;
  height: 74rpx;
  border-radius: 999rpx;
  font-size: 27rpx;
  font-weight: 600;

  &:active {
    opacity: 0.9;
  }

  &--ghost {
    border: 1rpx solid #cbd5e1;
    color: var(--app-text-2, #3d4558);
    background: #ffffff;
  }

  &--primary {
    color: #ffffff;
    background: linear-gradient(135deg, #4a8bff, #2f6bff);
  }
}

.flow-tip {
  margin: 0 8rpx;
  padding: 0 16rpx;
  font-size: 22rpx;
  line-height: 1.7;
  color: #8a94a6;
}
</style>
