<template>
  <BasicModal
    v-bind="$attrs"
    :title="isUpdate ? '编辑对接系统' : '新增对接系统'"
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
import { createTransformParty, updateTransformParty } from '@/api/device/transform'
import { getPartyFormSchema, parseJsonField } from '../data'

defineOptions({ name: 'TransformPartyModal' })
const emit = defineEmits(['success', 'register'])
const { createMessage } = useMessage()
const isUpdate = ref(false)

const [registerForm, { setFieldsValue, resetFields, validate, setProps }] = useForm({
  labelWidth: 120,
  baseColProps: { span: 24 },
  schemas: getPartyFormSchema(false),
  showActionButtonGroup: false,
})

const [registerModal, { setModalProps, closeModal }] = useModalInner(async (data) => {
  resetFields()
  isUpdate.value = !!data?.isUpdate
  setProps({ schemas: getPartyFormSchema(unref(isUpdate)) })
  setModalProps({ confirmLoading: false })
  if (unref(isUpdate) && data?.record) {
    const record = data.record
    setFieldsValue({
      id: record.id,
      name: record.name,
      type: record.type,
      enabled: !!record.enabled,
      configText: JSON.stringify(record.config || {}, null, 2),
    })
  } else {
    setFieldsValue({ id: '', name: '', type: 'mes.rest', enabled: true, configText: '{}' })
  }
})

async function handleSubmit() {
  try {
    const values = await validate()
    setModalProps({ confirmLoading: true })
    const payload = {
      id: values.id,
      name: values.name,
      type: values.type,
      enabled: !!values.enabled,
      config: parseJsonField(values.configText, '系统配置'),
    }
    if (unref(isUpdate)) await updateTransformParty(payload.id, payload)
    else await createTransformParty(payload)
    closeModal()
    emit('success')
    createMessage.success('对接系统保存成功')
  } catch (error: any) {
    if (error?.message) createMessage.error(error.message)
  } finally {
    setModalProps({ confirmLoading: false })
  }
}
</script>
