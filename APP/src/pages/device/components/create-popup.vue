<template>
  <wd-popup v-model="visible" position="bottom" custom-style="border-radius: 24rpx 24rpx 0 0; max-height: 85vh;">
    <view class="p-32rpx">
      <view class="mb-24rpx text-center text-32rpx font-semibold">
        添加设备
      </view>

      <!-- 类型切换 -->
      <view class="mode-tabs mb-24rpx">
        <view
          class="mode-tab"
          :class="{ 'mode-tab--active': mode === 'camera' }"
          @click="mode = 'camera'"
        >
          摄像头 RTSP
        </view>
        <view
          class="mode-tab"
          :class="{ 'mode-tab--active': mode === 'nvr' }"
          @click="mode = 'nvr'"
        >
          录像机 NVR
        </view>
      </view>

      <scroll-view scroll-y class="max-h-60vh">
        <!-- 摄像头直连 -->
        <template v-if="mode === 'camera'">
          <view class="mb-24rpx">
            <view class="mb-12rpx text-26rpx text-[#666]">
              设备名称
            </view>
            <wd-input v-model="form.name" placeholder="可选，默认可由系统生成" clearable />
          </view>

          <view class="mb-24rpx">
            <view class="mb-12rpx text-26rpx text-[#666]">
              RTSP 地址 <text class="text-[#f56c6c]">*</text>
            </view>
            <wd-textarea
              v-model="form.source"
              placeholder="rtsp://username:password@ip:port/path"
              :maxlength="500"
            />
          </view>
        </template>

        <!-- NVR 登记并批量挂载通道 -->
        <template v-else>
          <view class="mb-24rpx">
            <view class="mb-12rpx text-26rpx text-[#666]">
              录像机名称
            </view>
            <wd-input v-model="form.nvrName" placeholder="可选，如：公司录像机" clearable />
          </view>

          <view class="mb-24rpx flex gap-24rpx">
            <view class="flex-1">
              <view class="mb-12rpx text-26rpx text-[#666]">
                IP 地址 <text class="text-[#f56c6c]">*</text>
              </view>
              <wd-input
                v-model="form.ip"
                placeholder="例如 192.168.1.64"
                clearable
              />
            </view>
            <view class="w-200rpx">
              <view class="mb-12rpx text-26rpx text-[#666]">
                端口
              </view>
              <wd-input v-model="form.port" type="number" placeholder="8000" />
            </view>
          </view>

          <view class="mb-24rpx flex gap-24rpx">
            <view class="flex-1">
              <view class="mb-12rpx text-26rpx text-[#666]">
                账号
              </view>
              <wd-input v-model="form.username" placeholder="设备登录账号" clearable />
            </view>
            <view class="flex-1">
              <view class="mb-12rpx text-26rpx text-[#666]">
                密码
              </view>
              <wd-input
                v-model="form.password"
                placeholder="设备登录密码"
                show-password
              />
            </view>
          </view>

          <view class="tip-card">
            注册成功后自动发现并挂载全部通道，首次注册约需数秒到一分钟。
          </view>
        </template>
      </scroll-view>

      <view class="mt-24rpx flex gap-24rpx">
        <wd-button class="flex-1" plain @click="visible = false">
          取消
        </wd-button>
        <wd-button class="flex-1" type="primary" :loading="submitting" @click="handleSubmit">
          {{ mode === 'nvr' ? '注册并拉取通道' : '注册' }}
        </wd-button>
      </view>
    </view>
  </wd-popup>
</template>

<script lang="ts" setup>
import { reactive, ref } from 'vue'
import { useToast } from '@wot-ui/ui/components/wd-toast'
import { registerDevice, registerNvrWithChannels } from '@/api/video/camera'

const emit = defineEmits<{ success: [] }>()
const toast = useToast()
const visible = ref(false)
const submitting = ref(false)
const mode = ref<'camera' | 'nvr'>('camera')

const form = reactive({
  name: '',
  source: '',
  nvrName: '',
  ip: '',
  port: '',
  username: '',
  password: '',
})

function resetForm() {
  form.name = ''
  form.source = ''
  form.nvrName = ''
  form.ip = ''
  form.port = ''
  form.username = ''
  form.password = ''
}

async function submitCamera() {
  const source = form.source.trim()
  if (!source) {
    toast.warning('请输入 RTSP 地址')
    return false
  }
  await registerDevice({
    name: form.name.trim() || `设备_${Date.now()}`,
    source,
  })
  toast.success('设备注册成功')
  return true
}

async function submitNvr() {
  const ip = form.ip.trim()
  if (!ip) {
    toast.warning('请输入录像机 IP 地址')
    return false
  }
  const port = Number(form.port) || 8000
  submitting.value = true
  try {
    const nvr = await registerNvrWithChannels({
      ip,
      port,
      username: form.username.trim() || undefined,
      password: form.password || undefined,
      name: form.nvrName.trim() || undefined,
    })
    const count = Number(nvr?.camera_count ?? nvr?.cameras?.length ?? 0)
    toast.success(count ? `录像机注册成功，挂载 ${count} 路通道` : '录像机注册成功')
    return true
  } catch (err: any) {
    toast.error(err?.msg || err?.message || '录像机注册失败，请检查 IP / 账号密码与网络')
    return false
  } finally {
    submitting.value = false
  }
}

async function handleSubmit() {
  if (submitting.value)
    return
  if (mode.value === 'nvr') {
    // NVR 枚举较慢，registerNvrWithChannels 内部已持有 loading
    if (await submitNvr()) {
      visible.value = false
      emit('success')
    }
    return
  }
  submitting.value = true
  try {
    if (await submitCamera()) {
      visible.value = false
      emit('success')
    }
  } catch (err: any) {
    toast.error(err?.msg || err?.message || '注册失败')
  } finally {
    submitting.value = false
  }
}

function openCreate(nvrMode = false) {
  resetForm()
  mode.value = nvrMode ? 'nvr' : 'camera'
  visible.value = true
}

defineExpose({ openCreate })
</script>

<style lang="scss" scoped>
.mode-tabs {
  display: flex;
  gap: 14rpx;
}

.mode-tab {
  flex: 1;
  padding: 16rpx 0;
  border-radius: 999rpx;
  text-align: center;
  font-size: 26rpx;
  font-weight: 600;
  color: var(--app-text-2, #4e5969);
  background: #f2f3f5;
  transition: all 0.18s ease;

  &--active {
    color: var(--app-brand, #2f6bff);
    background: #eaf1ff;
  }
}

.tip-card {
  padding: 18rpx 22rpx;
  border-radius: 20rpx;
  background: #f7f9fc;
  color: var(--app-text-3, #98a2b3);
  font-size: 23rpx;
  line-height: 1.6;
}
</style>
