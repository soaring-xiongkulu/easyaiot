<template>
  <BasicDrawer
    v-bind="$attrs"
    @register="register"
    :title="getTitle"
    width="1200"
    placement="right"
    :showFooter="true"
    :showCancelBtn="false"
    :showOkBtn="false"
    destroy-on-close
  >
    <template #footer>
      <div class="footer-buttons">
        <Button @click="handleCancel">{{ state.isView ? '关闭' : '取消' }}</Button>
        <Button v-if="!state.isView" type="primary" :loading="state.saving" @click="handleOk">
          保存
        </Button>
      </div>
    </template>

    <Spin :spinning="state.saving">
      <div class="drawer-content">
        <Divider orientation="left">基础信息</Divider>
        <BasicForm @register="registerForm" />

        <Divider orientation="left">连接配置</Divider>
        <BasicForm @register="registerConfigForm" />

        <Divider orientation="left">高级配置</Divider>
        <Form :label-col="labelCol" :wrapper-col="wrapperCol" :disabled="state.isView" class="section-form">
          <FormItem label="扩展配置">
            <KvEditor
              v-model:value="extraConfig"
              :disabled="state.isView"
              hint="除基础字段外的自定义键值，将合并写入系统配置"
              key-placeholder="配置键"
              value-placeholder="配置值"
            />
          </FormItem>
        </Form>
      </div>
    </Spin>
  </BasicDrawer>
</template>

<script lang="ts" setup>
import { computed, reactive, ref } from 'vue'
import { Divider, Form, FormItem, Spin } from 'ant-design-vue'
import { BasicDrawer, useDrawerInner } from '@/components/Drawer'
import { BasicForm, useForm } from '@/components/Form'
import { Button } from '@/components/Button'
import { useMessage } from '@/hooks/web/useMessage'
import { createTransformParty, updateTransformParty } from '@/api/device/transform'
import { partyTypeOptions } from '../data'
import KvEditor from './KvEditor.vue'

defineOptions({ name: 'TransformPartyDrawer' })

const emit = defineEmits(['success', 'register'])
const { createMessage } = useMessage()

const labelCol = { style: { width: '150px' } }
const wrapperCol = { span: 21 }
const state = reactive({ isEdit: false, isView: false, saving: false })
const extraConfig = ref<Recordable>({})
const KNOWN_KEYS = ['baseUrl', 'timeoutSeconds', 'partySecret', 'authToken']

const getTitle = computed(() =>
  state.isView ? '查看数据目的' : state.isEdit ? '编辑数据目的' : '新增数据目的',
)

const [registerForm, { setFieldsValue, validate, resetFields, setProps }] = useForm({
  labelWidth: 150,
  baseColProps: { span: 12 },
  showActionButtonGroup: false,
  schemas: [
    {
      field: 'id',
      label: '目的地编码',
      component: 'Input',
      required: true,
      componentProps: { placeholder: '如 demo-mes、plant-erp' },
    },
    {
      field: 'name',
      label: '目的地名称',
      component: 'Input',
      required: true,
      componentProps: { placeholder: '如 产线 MES / 仓储 WMS' },
    },
    {
      field: 'type',
      label: '系统类型',
      component: 'Select',
      required: true,
      defaultValue: 'mes.rest',
      componentProps: { options: partyTypeOptions, placeholder: '请选择对接系统类型' },
    },
    {
      field: 'enabled',
      label: '启用状态',
      component: 'Switch',
      defaultValue: true,
      componentProps: { checkedChildren: '启用', unCheckedChildren: '停用' },
    },
  ],
})

const [registerConfigForm, {
  setFieldsValue: setConfigValues,
  validate: validateConfig,
  resetFields: resetConfig,
  setProps: setConfigProps,
}] = useForm({
  labelWidth: 150,
  baseColProps: { span: 12 },
  showActionButtonGroup: false,
  schemas: [
    {
      field: 'baseUrl',
      label: '基础地址',
      component: 'Input',
      required: true,
      componentProps: { placeholder: 'https://mes.example.com' },
      helpMessage: '建议填写对方系统入口；创建规则时可一键填入投递地址',
    },
    {
      field: 'timeoutSeconds',
      label: '超时(秒)',
      component: 'InputNumber',
      defaultValue: 10,
      componentProps: { min: 1, max: 120, style: { width: '100%' } },
    },
    {
      field: 'partySecret',
      label: '签名密钥',
      component: 'InputPassword',
      componentProps: { placeholder: '可选，HTTP 投递写入 X-Transform-Signature' },
    },
    {
      field: 'authToken',
      label: '授权 Token',
      component: 'Input',
      componentProps: { placeholder: '可选，Bearer Token' },
    },
  ],
})

function applyConfig(config: Recordable = {}) {
  setConfigValues({
    baseUrl: config.baseUrl ? String(config.baseUrl) : '',
    timeoutSeconds: config.timeoutSeconds != null ? Number(config.timeoutSeconds) : 10,
    partySecret: config.partySecret ? String(config.partySecret) : '',
    authToken: config.authToken ? String(config.authToken) : '',
  })
  const extra: Recordable = {}
  Object.keys(config || {}).forEach((key) => {
    if (!KNOWN_KEYS.includes(key)) extra[key] = config[key]
  })
  extraConfig.value = extra
}

function buildConfig(configValues: Recordable): Recordable {
  const config: Recordable = { ...extraConfig.value }
  if (configValues.baseUrl?.trim()) config.baseUrl = String(configValues.baseUrl).trim()
  if (configValues.timeoutSeconds != null) config.timeoutSeconds = Number(configValues.timeoutSeconds)
  if (configValues.partySecret?.trim()) config.partySecret = String(configValues.partySecret).trim()
  if (configValues.authToken?.trim()) config.authToken = String(configValues.authToken).trim()
  return config
}

const [register, { closeDrawer }] = useDrawerInner(async (data) => {
  await resetFields()
  await resetConfig()
  extraConfig.value = {}
  state.isEdit = !!data?.isUpdate
  state.isView = !!data?.isView
  await setProps({ disabled: state.isView })
  await setConfigProps({ disabled: state.isView })

  if ((state.isEdit || state.isView) && data?.record) {
    const record = data.record
    await setFieldsValue({
      id: record.id || '',
      name: record.name || '',
      type: record.type || 'mes.rest',
      enabled: !!record.enabled,
    })
    applyConfig(record.config || {})
    await setProps({
      disabled: state.isView,
      schemas: [
        {
          field: 'id',
          label: '目的地编码',
          component: 'Input',
          required: true,
          componentProps: { disabled: true, placeholder: '如 demo-mes' },
        },
        {
          field: 'name',
          label: '目的地名称',
          component: 'Input',
          required: true,
          componentProps: { placeholder: '如 产线 MES', disabled: state.isView },
        },
        {
          field: 'type',
          label: '系统类型',
          component: 'Select',
          required: true,
          componentProps: {
            options: partyTypeOptions,
            disabled: state.isView,
          },
        },
        {
          field: 'enabled',
          label: '启用状态',
          component: 'Switch',
          componentProps: {
            checkedChildren: '启用',
            unCheckedChildren: '停用',
            disabled: state.isView,
          },
        },
      ],
    })
  }
})

function handleCancel() {
  closeDrawer()
}

async function handleOk() {
  try {
    const [values, configValues] = await Promise.all([validate(), validateConfig()])
    state.saving = true
    const payload = {
      id: String(values.id).trim(),
      name: String(values.name).trim(),
      type: values.type,
      enabled: !!values.enabled,
      config: buildConfig(configValues),
    }
    if (state.isEdit) await updateTransformParty(payload.id, payload)
    else await createTransformParty(payload)
    createMessage.success('数据目的保存成功')
    closeDrawer()
    emit('success')
  } catch (error: any) {
    if (error?.message) createMessage.error(error.message)
  } finally {
    state.saving = false
  }
}
</script>

<style lang="less" scoped>
.drawer-content {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.section-form {
  :deep(.ant-form-item) {
    margin-bottom: 16px;
  }
}

.footer-buttons {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  gap: 8px;
}
</style>
