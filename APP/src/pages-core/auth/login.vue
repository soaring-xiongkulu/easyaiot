<template>
  <view class="auth-container">
    <view class="auth-content">
      <Header subtitle="智能物联网管理平台" />

      <view class="form-container">
        <view class="form-title">
          欢迎登录
        </view>
        <view class="form-desc">
          使用账号密码登录，管理设备、训练模型与监控数据
        </view>

        <TenantPicker ref="tenantPickerRef" />
        <view class="input-item">
          <wd-icon name="user" size="20px" color="#2f6bff" />
          <wd-input
            v-model="formData.username"
            placeholder="请输入用户名"
            clearable
            clear-trigger="focus"
          />
        </view>
        <view class="input-item">
          <wd-icon name="lock" size="20px" color="#2f6bff" />
          <wd-input
            v-model="formData.password"
            placeholder="请输入密码"
            clearable
            clear-trigger="focus"
            show-password
          />
        </view>
        <view v-if="captchaEnabled">
          <Verify
            ref="verifyRef"
            :captcha-type="captchaType"
            explain="向右滑动完成验证"
            :img-size="{ width: '300px', height: '150px' }"
            mode="pop"
            @success="verifySuccess"
          />
        </view>

        <view class="form-actions">
          <text class="action-link" @click="goToForgetPassword">
            忘记密码？
          </text>
        </view>

        <view class="login-btn">
          <wd-button block :loading="loading" type="primary" @click="handleLogin">
            登 录
          </wd-button>
        </view>

        <view class="auth-footer">
          <text class="auth-footer__text">还没有账号？</text>
          <text class="auth-footer__link" @click="goToRegister">创建账号</text>
        </view>
      </view>
    </view>
  </view>
</template>

<script lang="ts" setup>
import { useToast } from '@wot-ui/ui/components/wd-toast'
import { reactive, ref } from 'vue'
import type { ILoginForm } from '@/api/login'
import {
  FORGET_PASSWORD_PAGE,
  REGISTER_PAGE,
} from '@/router/config'
import { useTokenStore } from '@/store/token'
import { ensureDecodeURIComponent, redirectAfterLogin } from '@/utils'
import Header from './components/header.vue'
import TenantPicker from './components/tenant-picker.vue'
import Verify from './components/verifition/verify.vue'

defineOptions({
  name: 'LoginPage',
  style: {
    navigationStyle: 'custom',
  },
})

definePage({
  style: {
    navigationStyle: 'custom',
  },
})

const toast = useToast()
const loading = ref(false)
const redirectUrl = ref<string>()
const tenantPickerRef = ref<InstanceType<typeof TenantPicker>>()
const captchaEnabled = import.meta.env.VITE_APP_CAPTCHA_ENABLE === 'true'
const verifyRef = ref()
const captchaType = ref('blockPuzzle')

const formData = reactive({
  username: import.meta.env.VITE_APP_DEFAULT_LOGIN_USERNAME || '',
  password: import.meta.env.VITE_APP_DEFAULT_LOGIN_PASSWORD || '',
})

onLoad((options) => {
  if (options?.redirect) {
    redirectUrl.value = ensureDecodeURIComponent(options.redirect)
  }
})

async function getCode() {
  if (!captchaEnabled) {
    await verifySuccess({})
  } else {
    verifyRef.value.show()
  }
}

async function handleLogin() {
  if (!tenantPickerRef.value?.validate()) {
    return
  }
  if (!formData.username) {
    toast.warning('请输入用户名')
    return
  }
  if (!formData.password) {
    toast.warning('请输入密码')
    return
  }
  await getCode()
}

async function verifySuccess(params: any) {
  loading.value = true
  try {
    const tokenStore = useTokenStore()
    const loginPayload: ILoginForm = {
      type: 'username',
      username: formData.username,
      password: formData.password,
    }
    if (captchaEnabled && params.captchaVerification) {
      loginPayload.captchaVerification = params.captchaVerification
    }
    await tokenStore.login(loginPayload)
    redirectAfterLogin(redirectUrl.value)
  } finally {
    loading.value = false
  }
}

function goToRegister() {
  uni.navigateTo({ url: REGISTER_PAGE })
}

function goToForgetPassword() {
  uni.navigateTo({ url: FORGET_PASSWORD_PAGE })
}
</script>

<style lang="scss" scoped>
@import './styles/auth.scss';

.form-actions {
  justify-content: flex-end;
}
</style>
