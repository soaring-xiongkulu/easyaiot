<template>
  <BasicModal
    v-bind="$attrs"
    :title="isUpdate ? '编辑转换流程' : '新增转换流程'"
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
import {
  createTransformPipeline,
  getTransformMappingList,
  updateTransformPipeline,
} from '@/api/device/transform'
import { getPipelineFormSchema } from '../data'

defineOptions({ name: 'TransformPipelineModal' })
const emit = defineEmits(['success', 'register'])
const { createMessage } = useMessage()
const isUpdate = ref(false)

const [registerForm, { setFieldsValue, resetFields, validate, setProps }] = useForm({
  labelWidth: 120,
  baseColProps: { span: 24 },
  schemas: getPipelineFormSchema(false, []),
  showActionButtonGroup: false,
})

const [registerModal, { setModalProps, closeModal }] = useModalInner(async (data) => {
  resetFields()
  isUpdate.value = !!data?.isUpdate
  setModalProps({ confirmLoading: false })

  const mappings = await getTransformMappingList()
  const mappingOptions = mappings.map((m) => ({ label: `${m.name} (${m.id})`, value: m.id }))
  setProps({ schemas: getPipelineFormSchema(unref(isUpdate), mappingOptions) })

  if (unref(isUpdate) && data?.record) {
    const record = data.record
    setFieldsValue({
      id: record.id,
      name: record.name,
      flowType: record.flowType || 'DATA',
      mappingId: record.mappingId || undefined,
      enabled: !!record.enabled,
    })
  } else {
    setFieldsValue({
      id: '',
      name: '',
      flowType: 'DATA',
      mappingId: undefined,
      enabled: true,
    })
  }
})

async function handleSubmit() {
  try {
    const values = await validate()
    setModalProps({ confirmLoading: true })
    const payload = {
      id: values.id,
      name: values.name,
      flowType: values.flowType,
      mappingId: values.mappingId || '',
      enabled: !!values.enabled,
    }
    if (unref(isUpdate)) await updateTransformPipeline(payload.id, payload)
    else await createTransformPipeline(payload)
    closeModal()
    emit('success')
    createMessage.success('转换流程保存成功')
  } catch (error: any) {
    if (error?.message) createMessage.error(error.message)
  } finally {
    setModalProps({ confirmLoading: false })
  }
}
</script>
