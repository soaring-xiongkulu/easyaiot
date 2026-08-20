<script lang="ts" setup>
import { computed, reactive, ref, unref } from 'vue'
import { Form, Input } from 'ant-design-vue'
import LoginFormTitle from './LoginFormTitle.vue'
import { LoginStateEnum, useFormRules, useFormValid, useLoginState } from './useLogin'
import { CountdownInput } from '@/components/CountDown'
import { useI18n } from '@/hooks/web/useI18n'
import { useMessage } from '@/hooks/web/useMessage'
import { useUserStore } from '@/store/modules/user'
import { usePermissionStore } from '@/store/modules/permission'
import { useGlobSetting } from '@/hooks/setting'
import { useDesign } from '@/hooks/web/useDesign'
import * as authUtil from '@/utils/auth'

import { Verify } from '@/components/Verifition'
import { getTenantIdByName, sendSmsCode } from '@/api/base/login'
import { Button } from '@/components/Button'
import { isLoginCaptchaEnabled, isLoginTenantEnabled } from '@/utils/deployProfile'
const FormItem = Form.Item

const { t } = useI18n()
const { prefixCls } = useDesign('login')
const { createMessage, notification, createErrorModal } = useMessage()
const { handleBackLogin, getLoginState } = useLoginState()
const { tenantEnable, captchaEnable } = useGlobSetting()
const loginTenantEnabled = isLoginTenantEnabled()
const loginCaptchaEnabled = isLoginCaptchaEnabled()
const { getFormRules } = useFormRules()
const userStore = useUserStore()
const permissionStore = usePermissionStore()

const formRef = ref()
const loading = ref(false)

const mobileCodeTimer = ref(0)
const scene = ref(21)

const verify = ref()
const captchaType = ref('blockPuzzle') // blockPuzzle 滑块 clickWord 点击文字

const formData = reactive({
  tenantName: 'Admin-IoT',
  mobile: '',
  mobileCode: '',
  captchaVerification: '',
})

const { validForm } = useFormValid(formRef)

const getShow = computed(() => unref(getLoginState) === LoginStateEnum.MOBILE)

// 获取验证码
async function getCode() {
  if (!loginCaptchaEnabled || captchaEnable === 'false') {
    await handleLogin()
  }
  else {
    verify.value.show()
  }
}

async function getTenantId() {
  if (loginTenantEnabled && tenantEnable === 'true') {
    const res = await getTenantIdByName(formData.tenantName)
    authUtil.setTenantId(res.id)
  }
  else {
    authUtil.setTenantId(1)
  }
}

async function handleLogin() {
  const data = await validForm()
  if (!data)
    return
  try {
    loading.value = true
    const userInfo = await userStore.smsLogin({
      mobile: data.mobile,
      code: data.mobileCode,
      mode: 'none', // 不要默认的错误提示
    })
    if (userInfo) {
    if (userInfo) {
      const perms = userInfo.permissions
      await permissionStore.changePermissionCode(Array.isArray(perms) ? perms : [])
    }
      notification.success({
        message: t('sys.login.loginSuccessTitle'),
        description: `${t('sys.login.loginSuccessDesc')}: ${userInfo.user.nickname}`,
        duration: 3,
      })
    }
  }
 catch (error) {
    console.error(error)
    createErrorModal({
      title: t('sys.api.errorTip'),
      content: (error as unknown as Error).message || t('sys.api.networkExceptionMsg'),
      getContainer: () => document.body.querySelector(`.${prefixCls}`) || document.body,
    })
  }
  finally {
    loading.value = false
  }
}

async function getSmsCode() {
  await getTenantId()
  if (mobileCodeTimer.value > 0)
    return
  const data = await validForm()
  if (!data)
    return
  const res = await sendSmsCode(formData.mobile, scene.value)
  if (res) {
    createMessage.success(t('common.successText'))
    mobileCodeTimer.value = 60
  }
}
</script>

<template>
  <div v-if="getShow">
    <LoginFormTitle class="enter-x" />
    <Form ref="formRef" class="enter-x p-4" :model="formData" :rules="getFormRules">
      <FormItem v-if="loginTenantEnabled && tenantEnable === 'true'" name="tenantName" class="enter-x">
        <Input
          v-model:value="formData.tenantName"
          size="large"
          :placeholder="t('sys.login.tenantName')"
          class="fix-auto-fill"
        />
      </FormItem>
      <FormItem name="mobile" class="enter-x">
        <Input v-model:value="formData.mobile" size="large" :placeholder="t('sys.login.mobile')" class="fix-auto-fill" />
      </FormItem>
      <FormItem name="mobileCode" class="enter-x">
        <CountdownInput
          v-model:value="formData.mobileCode"
          size="large"
          class="fix-auto-fill"
          :count="mobileCodeTimer"
          :send-code-api="getSmsCode"
          :placeholder="t('sys.login.smsCode')"
        />
      </FormItem>

      <FormItem class="enter-x">
        <Button type="primary" size="large" block :loading="loading" @click="getCode">
          {{ t('sys.login.loginButton') }}
        </Button>
        <Button size="large" block class="mt-4" @click="handleBackLogin">
          {{ t('sys.login.backSignIn') }}
        </Button>
      </FormItem>
    </Form>
    <Verify
      v-if="loginCaptchaEnabled && captchaEnable !== 'false'"
      ref="verify"
      mode="pop"
      :captcha-type="captchaType"
      :img-size="{ width: '400px', height: '200px' }"
      @success="handleLogin"
    />
  </div>
</template>
