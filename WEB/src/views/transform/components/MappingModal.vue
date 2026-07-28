<template>
  <BasicModal
    v-bind="$attrs"
    :title="isUpdate ? '编辑映射模板' : '新增映射模板'"
    width="560px"
    destroyOnClose
    @register="registerModal"
    @ok="handleSubmit"
  >
    <BasicForm @register="registerForm" />
  </BasicModal>
</template>

<script lang="ts" setup>
import { ref, unref } from 'vue'
import { BasicForm, useForm } from '@/components/Form'
import { BasicModal, useModalInner } from '@/components/Modal'
import { useMessage } from '@/hooks/web/useMessage'
import { createTransformMapping, updateTransformMapping } from '@/api/device/transform'
import { getMappingFormSchema, parseJsonField } from '../data'

defineOptions({ name: 'TransformMappingModal' })
const emit = defineEmits(['success', 'register'])
const { createMessage } = useMessage()
const isUpdate = ref(false)

const [registerForm, { setFieldsValue, resetFields, validate, setProps }] = useForm({
  labelWidth: 120,
  baseColProps: { span: 24 },
  schemas: getMappingFormSchema(false),
  showActionButtonGroup: false,
})

const [registerModal, { setModalProps, closeModal }] = useModalInner(async (data) => {
  resetFields()
  isUpdate.value = !!data?.isUpdate
  setProps({ schemas: getMappingFormSchema(unref(isUpdate)) })
  setModalProps({ confirmLoading: false })
  if (unref(isUpdate) && data?.record) {
    const record = data.record
    setFieldsValue({
      id: record.id,
      name: record.name,
      enabled: !!record.enabled,
      fieldsText: JSON.stringify(record.fields || {}, null, 2),
    })
  } else {
    setFieldsValue({ id: '', name: '', enabled: true, fieldsText: '{}' })
  }
})

async function handleSubmit() {
  try {
    const values = await validate()
    setModalProps({ confirmLoading: true })
    const payload = {
      id: values.id,
      name: values.name,
      enabled: !!values.enabled,
      fields: parseJsonField(values.fieldsText, '字段映射'),
    }
    if (unref(isUpdate)) await updateTransformMapping(payload.id, payload)
    else await createTransformMapping(payload)
    closeModal()
    emit('success')
    createMessage.success('映射模板保存成功')
  } catch (error: any) {
    if (error?.message) createMessage.error(error.message)
  } finally {
    setModalProps({ confirmLoading: false })
  }
}
</script>
