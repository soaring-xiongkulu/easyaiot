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

        <Divider orientation="left">字段映射</Divider>
        <FieldMappingEditor v-model:value="fields" :disabled="state.isView" />

        <Divider orientation="left">JSON 预览</Divider>
        <pre class="json-preview">{{ jsonPreview }}</pre>
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
import { createTransformMapping, updateTransformMapping } from '@/api/device/transform'
import FieldMappingEditor from './FieldMappingEditor.vue'

defineOptions({ name: 'TransformMappingDrawer' })

const emit = defineEmits(['success', 'register'])
const { createMessage } = useMessage()

const state = reactive({ isEdit: false, isView: false, saving: false })
const fields = ref<Record<string, string>>({})

const getTitle = computed(() =>
  state.isView ? '查看映射模板' : state.isEdit ? '编辑映射模板' : '新增映射模板',
)
const jsonPreview = computed(() => JSON.stringify(fields.value || {}, null, 2))

const [registerForm, { setFieldsValue, validate, resetFields, setProps }] = useForm({
  labelWidth: 150,
  baseColProps: { span: 12 },
  showActionButtonGroup: false,
  schemas: [
    {
      field: 'id',
      label: '模板编码',
      component: 'Input',
      required: true,
      componentProps: { placeholder: '如 map-mes-order' },
    },
    {
      field: 'name',
      label: '模板名称',
      component: 'Input',
      required: true,
      componentProps: { placeholder: '如 MES 工单映射' },
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

const [register, { closeDrawer }] = useDrawerInner(async (data) => {
  await resetFields()
  fields.value = {}
  state.isEdit = !!data?.isUpdate
  state.isView = !!data?.isView
  await setProps({ disabled: state.isView })

  if ((state.isEdit || state.isView) && data?.record) {
    const record = data.record
    await setFieldsValue({
      id: record.id || '',
      name: record.name || '',
      enabled: !!record.enabled,
    })
    fields.value = { ...(record.fields || {}) }
    await setProps({
      disabled: state.isView,
      schemas: [
        {
          field: 'id',
          label: '模板编码',
          component: 'Input',
          required: true,
          componentProps: { disabled: true },
        },
        {
          field: 'name',
          label: '模板名称',
          component: 'Input',
          required: true,
          componentProps: { disabled: state.isView },
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
    const values = await validate()
    const fieldMap = fields.value || {}
    if (!Object.keys(fieldMap).length) {
      createMessage.warning('请至少添加一条字段映射')
      return
    }
    state.saving = true
    const payload = {
      id: String(values.id).trim(),
      name: String(values.name).trim(),
      enabled: !!values.enabled,
      fields: fieldMap,
    }
    if (state.isEdit) await updateTransformMapping(payload.id, payload)
    else await createTransformMapping(payload)
    createMessage.success('映射模板保存成功')
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

.json-preview {
  margin: 0;
  padding: 12px;
  background: #fafbfc;
  border: 1px solid #ebebeb;
  border-radius: 4px;
  font-size: 12px;
  line-height: 1.5;
  color: #333;
  max-height: 220px;
  overflow: auto;
}

.footer-buttons {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  gap: 8px;
}
</style>
