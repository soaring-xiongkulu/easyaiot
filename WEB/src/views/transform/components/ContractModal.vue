<template>
  <BasicModal
    v-bind="$attrs"
    :title="isUpdate ? '编辑推送规则' : '新增推送规则'"
    width="640px"
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
  createTransformContract,
  getTransformMappingList,
  getTransformPartyList,
  updateTransformContract,
} from '@/api/device/transform'
import { getContractFormSchema, parseJsonField } from '../data'

defineOptions({ name: 'TransformContractModal' })
const emit = defineEmits(['success', 'register'])
const { createMessage } = useMessage()
const isUpdate = ref(false)

const [registerForm, { setFieldsValue, resetFields, validate, setProps }] = useForm({
  labelWidth: 120,
  baseColProps: { span: 24 },
  schemas: getContractFormSchema(false, [], []),
  showActionButtonGroup: false,
})

const [registerModal, { setModalProps, closeModal }] = useModalInner(async (data) => {
  resetFields()
  isUpdate.value = !!data?.isUpdate
  setModalProps({ confirmLoading: false })

  const [parties, mappings] = await Promise.all([getTransformPartyList(), getTransformMappingList()])
  const partyOptions = parties.map((p) => ({ label: `${p.name} (${p.id})`, value: p.id }))
  const mappingOptions = mappings.map((m) => ({ label: `${m.name} (${m.id})`, value: m.id }))
  setProps({ schemas: getContractFormSchema(unref(isUpdate), partyOptions, mappingOptions) })

  if (unref(isUpdate) && data?.record) {
    const record = data.record
    setFieldsValue({
      id: record.id,
      partyId: record.partyId,
      flowType: record.flowType || 'DATA',
      channel: record.channel || 'party',
      endpoint: record.endpoint || '',
      mappingId: record.mappingId || undefined,
      enabled: !!record.enabled,
      headersText: JSON.stringify(record.headers || {}, null, 2),
    })
  } else {
    setFieldsValue({
      id: '',
      partyId: undefined,
      flowType: 'DATA',
      channel: 'party',
      endpoint: '',
      mappingId: undefined,
      enabled: true,
      headersText: '{}',
    })
  }
})

async function handleSubmit() {
  try {
    const values = await validate()
    setModalProps({ confirmLoading: true })
    const payload = {
      id: values.id,
      partyId: values.partyId,
      flowType: values.flowType,
      channel: values.channel,
      endpoint: values.endpoint,
      mappingId: values.mappingId || '',
      enabled: !!values.enabled,
      headers: parseJsonField(values.headersText, '请求头'),
    }
    if (unref(isUpdate)) await updateTransformContract(payload.id, payload)
    else await createTransformContract(payload)
    closeModal()
    emit('success')
    createMessage.success('推送规则保存成功')
  } catch (error: any) {
    if (error?.message) createMessage.error(error.message)
  } finally {
    setModalProps({ confirmLoading: false })
  }
}
</script>
