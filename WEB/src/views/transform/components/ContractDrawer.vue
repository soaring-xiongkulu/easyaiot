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
        <Button
          v-if="!state.isView"
          type="primary"
          :loading="state.saving"
          @click="handleOk"
        >
          {{ modelRef.enabled ? '保存并启用' : '保存' }}
        </Button>
      </div>
    </template>

    <Spin :spinning="state.loading || state.saving">
      <div class="drawer-content">
        <div class="pipeline-banner">
          <div class="pipe-node">
            <div class="pipe-node__label">数据源</div>
            <div class="pipe-node__value">{{ flowTypeLabel(modelRef.flowType) }}</div>
          </div>
          <div class="pipe-line" />
          <div class="pipe-node">
            <div class="pipe-node__label">映射</div>
            <div class="pipe-node__value">{{ mappingLabel }}</div>
          </div>
          <div class="pipe-line" />
          <div class="pipe-node">
            <div class="pipe-node__label">数据目的</div>
            <div class="pipe-node__value">{{ partyLabel }}</div>
          </div>
          <div class="pipe-line" />
          <div class="pipe-node">
            <div class="pipe-node__label">通道</div>
            <div class="pipe-node__value">{{ channelLabel(modelRef.channel) }}</div>
          </div>
        </div>

        <Divider orientation="left">基础信息</Divider>
        <BasicForm @register="registerForm" />

        <Divider orientation="left">数据源</Divider>
        <Form :label-col="labelCol" :wrapper-col="wrapperCol" :disabled="state.isView" class="section-form">
          <FormItem label="数据类型" required>
            <div class="flow-grid">
              <div
                v-for="item in flowTypeOptions"
                :key="item.value"
                class="flow-card"
                :class="{
                  'flow-card--active': modelRef.flowType === item.value,
                  'flow-card--disabled': state.isView,
                }"
                @click="!state.isView && (modelRef.flowType = item.value)"
              >
                <div class="flow-card__title">{{ item.label }}</div>
                <div class="flow-card__desc">{{ item.desc }}</div>
              </div>
            </div>
          </FormItem>
        </Form>

        <Divider orientation="left">数据目的</Divider>
        <Form :label-col="labelCol" :wrapper-col="wrapperCol" :disabled="state.isView" class="section-form">
          <FormItem label="转发通道" required>
            <ChannelTypePicker
              :value="modelRef.channel"
              :disabled="state.isView"
              @update:value="onChannelChange"
            />
          </FormItem>
          <Row :gutter="16">
            <Col :span="12">
              <FormItem label="数据目的" required>
                <Select
                  v-model:value="modelRef.partyId"
                  :options="partyOptions"
                  placeholder="请选择已配置的数据目的"
                  show-search
                  :filter-option="filterOption"
                  allow-clear
                  @change="onPartyChange"
                />
              </FormItem>
            </Col>
            <Col :span="12">
              <FormItem label="投递地址" required>
                <div class="endpoint-row">
                  <Input
                    v-model:value="modelRef.endpoint"
                    :placeholder="endpointPlaceholder(modelRef.channel)"
                  />
                  <Button
                    v-if="!state.isView && selectedPartyBaseUrl"
                    size="small"
                    @click="fillEndpointFromParty"
                  >
                    填入基础地址
                  </Button>
                </div>
                <div v-if="selectedPartyBaseUrl" class="form-hint">
                  目的地基础地址：{{ selectedPartyBaseUrl }}
                </div>
              </FormItem>
            </Col>
          </Row>
        </Form>

        <Divider orientation="left">映射</Divider>
        <Form :label-col="labelCol" :wrapper-col="wrapperCol" :disabled="state.isView" class="section-form">
          <FormItem label="映射模板">
            <Select
              v-model:value="modelRef.mappingId"
              :options="mappingOptions"
              placeholder="不选则透传原始报文"
              allow-clear
              show-search
              :filter-option="filterOption"
            />
          </FormItem>
        </Form>

        <Divider orientation="left">请求头</Divider>
        <Form :label-col="labelCol" :wrapper-col="wrapperCol" :disabled="state.isView" class="section-form">
          <FormItem label="请求头">
            <KvEditor
              v-model:value="headers"
              :disabled="state.isView"
              hint="如 Authorization、X-Api-Key；HTTP 通道会合并到投递请求"
              key-placeholder="Header 名"
              value-placeholder="Header 值"
            />
          </FormItem>
        </Form>
      </div>
    </Spin>
  </BasicDrawer>
</template>

<script lang="ts" setup>
import { computed, reactive, ref, watch } from 'vue'
import { Col, Divider, Form, FormItem, Input, Row, Select, Spin } from 'ant-design-vue'
import { BasicDrawer, useDrawerInner } from '@/components/Drawer'
import { BasicForm, useForm } from '@/components/Form'
import { Button } from '@/components/Button'
import { useMessage } from '@/hooks/web/useMessage'
import {
  createTransformContract,
  getTransformMappingList,
  getTransformPartyList,
  updateTransformContract,
} from '@/api/device/transform'
import {
  channelLabel,
  endpointPlaceholder,
  flowTypeLabel,
  flowTypeOptions,
} from '../data'
import ChannelTypePicker from './ChannelTypePicker.vue'
import KvEditor from './KvEditor.vue'

defineOptions({ name: 'TransformContractDrawer' })

const emit = defineEmits(['success', 'register'])
const { createMessage } = useMessage()

const labelCol = { style: { width: '150px' } }
const wrapperCol = { span: 21 }

const state = reactive({ isEdit: false, isView: false, loading: false, saving: false })
const modelRef = reactive({
  id: '',
  partyId: undefined as string | undefined,
  flowType: 'DATA',
  channel: 'http',
  endpoint: '',
  mappingId: undefined as string | undefined,
  enabled: true,
})
const headers = ref<Recordable>({})
const partyOptions = ref<{ label: string; value: string }[]>([])
const mappingOptions = ref<{ label: string; value: string }[]>([])
const parties = ref<Recordable[]>([])
const mappings = ref<Recordable[]>([])

const getTitle = computed(() =>
  state.isView ? '查看转发规则' : state.isEdit ? '编辑转发规则' : '新建转发规则',
)

const partyLabel = computed(() => {
  const p = parties.value.find((item) => item.id === modelRef.partyId)
  return p?.name || modelRef.partyId || '未选择'
})

const mappingLabel = computed(() => {
  if (!modelRef.mappingId) return '透传'
  const m = mappings.value.find((item) => item.id === modelRef.mappingId)
  return m?.name || modelRef.mappingId
})

const selectedPartyBaseUrl = computed(() => {
  const p = parties.value.find((item) => item.id === modelRef.partyId)
  return p?.config?.baseUrl ? String(p.config.baseUrl) : ''
})

const [registerForm, { setFieldsValue, validate, resetFields, setProps }] = useForm({
  labelWidth: 150,
  baseColProps: { span: 12 },
  showActionButtonGroup: false,
  schemas: [
    {
      field: 'id',
      label: '规则编码',
      component: 'Input',
      required: true,
      componentProps: { placeholder: '如 rule-mes-data' },
    },
    {
      field: 'enabled',
      label: '运行状态',
      component: 'Switch',
      defaultValue: true,
      componentProps: { checkedChildren: '运行中', unCheckedChildren: '已停止' },
      helpMessage: '运行中的规则会消费对应数据源并转发至目的地',
    },
  ],
})

watch(
  () => modelRef.enabled,
  (val) => setFieldsValue({ enabled: val }),
)

function filterOption(input: string, option: any) {
  return String(option?.label || '')
    .toLowerCase()
    .includes(input.toLowerCase())
}

function onChannelChange(val: string) {
  if (state.isView) return
  modelRef.channel = val
}

function onPartyChange() {
  if (state.isView) return
  if (!modelRef.endpoint?.trim() && selectedPartyBaseUrl.value) {
    modelRef.endpoint = selectedPartyBaseUrl.value
  }
}

function fillEndpointFromParty() {
  if (selectedPartyBaseUrl.value) {
    modelRef.endpoint = selectedPartyBaseUrl.value
    createMessage.success('已填入目的地基础地址，可按需追加路径')
  }
}

function resetModel() {
  modelRef.id = ''
  modelRef.partyId = undefined
  modelRef.flowType = 'DATA'
  modelRef.channel = 'http'
  modelRef.endpoint = ''
  modelRef.mappingId = undefined
  modelRef.enabled = true
  headers.value = {}
}

const [register, { closeDrawer }] = useDrawerInner(async (data) => {
  resetModel()
  await resetFields()
  state.isEdit = !!data?.isUpdate
  state.isView = !!data?.isView
  state.loading = true
  try {
    const [partyList, mappingList] = await Promise.all([
      getTransformPartyList(),
      getTransformMappingList(),
    ])
    parties.value = partyList
    mappings.value = mappingList
    partyOptions.value = partyList.map((p) => ({
      label: `${p.name} (${p.id})${p.config?.baseUrl ? '' : ' · 未配基础地址'}`,
      value: p.id,
      disabled: p.enabled === false,
    }))
    mappingOptions.value = mappingList
      .filter((m) => m.enabled !== false)
      .map((m) => ({
        label: `${m.name} (${m.id}) · ${Object.keys(m.fields || {}).length} 字段`,
        value: m.id,
      }))

    await setProps({
      disabled: state.isView,
      schemas: [
        {
          field: 'id',
          label: '规则编码',
          component: 'Input',
          required: true,
          componentProps: {
            placeholder: '如 rule-mes-data',
            disabled: state.isEdit || state.isView,
          },
        },
        {
          field: 'enabled',
          label: '运行状态',
          component: 'Switch',
          defaultValue: true,
          componentProps: {
            checkedChildren: '运行中',
            unCheckedChildren: '已停止',
            disabled: state.isView,
            onChange: (checked: boolean) => {
              modelRef.enabled = !!checked
            },
          },
          helpMessage: '运行中的规则会消费对应数据源并转发至目的地',
        },
      ],
    })

    if ((state.isEdit || state.isView) && data?.record) {
      const record = data.record
      modelRef.id = record.id || ''
      modelRef.partyId = record.partyId
      modelRef.flowType = record.flowType || 'DATA'
      modelRef.channel = record.channel || 'http'
      modelRef.endpoint = record.endpoint || ''
      modelRef.mappingId = record.mappingId || undefined
      modelRef.enabled = !!record.enabled
      headers.value = { ...(record.headers || {}) }
      await setFieldsValue({ id: modelRef.id, enabled: modelRef.enabled })
    }
  } finally {
    state.loading = false
  }
})

function handleCancel() {
  closeDrawer()
}

async function handleOk() {
  try {
    const values = await validate()
    modelRef.id = String(values.id || '').trim()
    modelRef.enabled = !!values.enabled
    if (!modelRef.id) {
      createMessage.warning('请填写规则编码')
      return
    }
    if (!modelRef.partyId) {
      createMessage.warning('请选择数据目的')
      return
    }
    if (!modelRef.endpoint?.trim()) {
      createMessage.warning('请填写投递地址')
      return
    }
    state.saving = true
    const payload = {
      id: modelRef.id,
      partyId: modelRef.partyId,
      flowType: modelRef.flowType,
      channel: modelRef.channel,
      endpoint: modelRef.endpoint.trim(),
      mappingId: modelRef.mappingId || '',
      enabled: !!modelRef.enabled,
      headers: headers.value || {},
    }
    if (state.isEdit) await updateTransformContract(payload.id, payload)
    else await createTransformContract(payload)
    createMessage.success('转发规则保存成功')
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

.pipeline-banner {
  display: flex;
  align-items: stretch;
  gap: 0;
  padding: 12px;
  margin-bottom: 8px;
  border-radius: 4px;
  background: #fafbfc;
  border: 1px solid #ebebeb;
}

.pipe-node {
  flex: 1;
  min-width: 0;
  padding: 8px 10px;
  background: #fff;
  border-radius: 4px;
  border: 1px solid #ebebeb;
}

.pipe-node__label {
  font-size: 12px;
  color: #86909c;
  margin-bottom: 4px;
}

.pipe-node__value {
  font-size: 14px;
  font-weight: 600;
  color: #1d2129;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.pipe-line {
  width: 24px;
  flex-shrink: 0;
  position: relative;
  align-self: center;

  &::before {
    content: '';
    position: absolute;
    left: 4px;
    right: 4px;
    top: 50%;
    height: 1px;
    background: #c9cdd4;
  }

  &::after {
    content: '';
    position: absolute;
    right: 2px;
    top: 50%;
    margin-top: -3.5px;
    border: 3.5px solid transparent;
    border-left-color: #86909c;
  }
}

.flow-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
  width: 100%;
}

.flow-card {
  padding: 14px 16px;
  border: 1px solid #e5e6eb;
  border-radius: 8px;
  background: #fff;
  cursor: pointer;
  transition: border-color 0.2s, box-shadow 0.2s, background 0.2s;

  &:hover:not(.flow-card--disabled) {
    border-color: #91b5ff;
  }

  &--active {
    border-color: #266cfb;
    background: #f7faff;
    box-shadow: 0 0 0 1px #266cfb inset;
  }

  &--disabled {
    cursor: default;
  }
}

.flow-card__title {
  font-size: 14px;
  font-weight: 600;
  color: #1d2129;
}

.flow-card__desc {
  margin-top: 4px;
  font-size: 12px;
  color: #86909c;
  line-height: 1.45;
}

.endpoint-row {
  display: flex;
  gap: 8px;
  align-items: center;

  :deep(.ant-input) {
    flex: 1;
  }
}

.section-form {
  :deep(.ant-form-item) {
    margin-bottom: 16px;
  }
}

.form-hint {
  margin-top: 4px;
  color: #86909c;
  font-size: 13px;
  line-height: 1.5;
}

.footer-buttons {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  gap: 8px;
}
</style>
