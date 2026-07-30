<template>
  <BasicDrawer
    v-bind="$attrs"
    @register="register"
    :title="getTitle"
    width="720"
    placement="right"
    :showFooter="true"
    :showCancelBtn="false"
    :showOkBtn="false"
    destroy-on-close
  >
    <template #footer>
      <div class="footer-buttons">
        <Button @click="handleCancel">取消</Button>
        <Button type="primary" :loading="state.saving" @click="handleOk">
          {{ enabledPreview ? '保存并启动' : '保存' }}
        </Button>
      </div>
    </template>

    <Spin :spinning="state.loading || state.saving">
      <div class="drawer-content">
        <div class="pipeline-banner">
          <div class="pipe-node">
            <div class="pipe-node__label">入站数据源</div>
            <div class="pipe-node__value">{{ flowTypeLabel(preview.flowType) }}</div>
          </div>
          <div class="pipe-line" />
          <div class="pipe-node">
            <div class="pipe-node__label">映射模板</div>
            <div class="pipe-node__value">{{ mappingLabel }}</div>
          </div>
          <div class="pipe-line" />
          <div class="pipe-node">
            <div class="pipe-node__label">运行状态</div>
            <div class="pipe-node__value">{{ enabledPreview ? '运行中' : '已停止' }}</div>
          </div>
        </div>

        <Divider orientation="left">基础信息</Divider>
        <BasicForm @register="registerForm" />
      </div>
    </Spin>
  </BasicDrawer>
</template>

<script lang="ts" setup>
import { computed, reactive, ref } from 'vue'
import { Divider, Spin } from 'ant-design-vue'
import { BasicDrawer, useDrawerInner } from '@/components/Drawer'
import { BasicForm, useForm } from '@/components/Form'
import { Button } from '@/components/Button'
import { useMessage } from '@/hooks/web/useMessage'
import {
  createTransformPipeline,
  getTransformMappingList,
  updateTransformPipeline,
} from '@/api/device/transform'
import { flowTypeLabel, flowTypeOptions } from '../data'

defineOptions({ name: 'TransformPipelineDrawer' })

const emit = defineEmits(['success', 'register'])
const { createMessage } = useMessage()

const state = reactive({ isEdit: false, loading: false, saving: false })
const mappings = ref<Recordable[]>([])
const preview = reactive({
  flowType: 'DATA',
  mappingId: '' as string,
  enabled: true,
})

const getTitle = computed(() => (state.isEdit ? '编辑全局预处理' : '配置全局预处理'))
const enabledPreview = computed(() => !!preview.enabled)
const mappingLabel = computed(() => {
  if (!preview.mappingId) return '透传'
  const m = mappings.value.find((item) => item.id === preview.mappingId)
  return m?.name || preview.mappingId
})

const [registerForm, { setFieldsValue, validate, resetFields, updateSchema, setProps }] = useForm({
  labelWidth: 150,
  baseColProps: { span: 12 },
  showActionButtonGroup: false,
  schemas: [
    {
      field: 'id',
      label: '流程编码',
      component: 'Input',
      required: true,
      componentProps: { placeholder: '如 pipe-device-data' },
    },
    {
      field: 'name',
      label: '流程名称',
      component: 'Input',
      required: true,
      componentProps: { placeholder: '如 设备数据标准转换' },
    },
    {
      field: 'flowType',
      label: '数据源类型',
      component: 'Select',
      required: true,
      defaultValue: 'DATA',
      componentProps: {
        options: flowTypeOptions,
        onChange: (val: string) => {
          preview.flowType = val
        },
      },
    },
    {
      field: 'mappingId',
      label: '映射模板',
      component: 'Select',
      componentProps: {
        options: [],
        allowClear: true,
        placeholder: '可选，不选则透传',
        onChange: (val: string) => {
          preview.mappingId = val || ''
        },
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
        onChange: (checked: boolean) => {
          preview.enabled = !!checked
        },
      },
      helpMessage: '运行中禁止随意删除；停用后再调整映射更安全',
    },
  ],
})

const [register, { closeDrawer }] = useDrawerInner(async (data) => {
  await resetFields()
  preview.flowType = 'DATA'
  preview.mappingId = ''
  preview.enabled = true
  state.isEdit = !!data?.isUpdate
  state.loading = true
  try {
    const list = await getTransformMappingList()
    mappings.value = list
    const mappingOptions = list.map((m) => ({
      label: `${m.name} (${m.id}) · ${Object.keys(m.fields || {}).length} 字段`,
      value: m.id,
    }))
    await updateSchema({
      field: 'mappingId',
      componentProps: {
        options: mappingOptions,
        allowClear: true,
        placeholder: '可选，不选则透传',
        onChange: (val: string) => {
          preview.mappingId = val || ''
        },
      },
    })
    await setProps({
      schemas: undefined,
    })
    if (state.isEdit && data?.record) {
      const record = data.record
      preview.flowType = record.flowType || 'DATA'
      preview.mappingId = record.mappingId || ''
      preview.enabled = !!record.enabled
      await setFieldsValue({
        id: record.id || '',
        name: record.name || '',
        flowType: record.flowType || 'DATA',
        mappingId: record.mappingId || undefined,
        enabled: !!record.enabled,
      })
      await updateSchema({
        field: 'id',
        componentProps: { disabled: true },
      })
    } else {
      await updateSchema({
        field: 'id',
        componentProps: { disabled: false, placeholder: '如 pipe-device-data' },
      })
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
    state.saving = true
    const payload = {
      id: String(values.id).trim(),
      name: String(values.name).trim(),
      flowType: values.flowType,
      mappingId: values.mappingId || '',
      enabled: !!values.enabled,
    }
    if (state.isEdit) await updateTransformPipeline(payload.id, payload)
    else await createTransformPipeline(payload)
    createMessage.success('全局预处理保存成功')
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
  color: #999;
  margin-bottom: 4px;
}

.pipe-node__value {
  font-size: 14px;
  font-weight: 600;
  color: #181818;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.pipe-line {
  width: 28px;
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

.footer-buttons {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  gap: 8px;
}
</style>
