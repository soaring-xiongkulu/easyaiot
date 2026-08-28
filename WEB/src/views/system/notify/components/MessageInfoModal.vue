<script lang="ts" setup>
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import type { MessageInfo } from './message.data'
import { infoSchema } from './message.data'
import { BasicModal, useModalInner } from '@/components/Modal'
import { Description, useDescription } from '@/components/Description/index'
import { Button } from '@/components/Button'

defineOptions({ name: 'MessageInfoModal' })

const data = ref<MessageInfo>()

const [innerRegister] = useModalInner((value: MessageInfo) => {
  data.value = value
})

const [descriptionRegister] = useDescription({
  column: 1,
  schema: infoSchema,
  data,
})

/** FLOW deepLink（约定 flow://instance/{processInstanceId}?taskId={taskId}，Flowable ID 为 UUID） */
const flowLink = computed(() => {
  const content = data.value?.templateContent || ''
  const match = content.match(/flow:\/\/instance\/([A-Za-z0-9-]+)(?:\?taskId=([A-Za-z0-9-]+))?/)
  return match ? { id: match[1], taskId: match[2] } : null
})

const router = useRouter()

function handleGoFlow() {
  if (!flowLink.value) return
  router.push({
    path: '/flow/process-instance/detail',
    query: { id: flowLink.value.id, ...(flowLink.value.taskId ? { taskId: flowLink.value.taskId } : {}) },
  })
}
</script>

<template>
  <BasicModal title="站内信详情" @register="innerRegister">
    <Description @register="descriptionRegister" />
    <template v-if="flowLink" #footer>
      <Button type="primary" @click="handleGoFlow">去处理</Button>
    </template>
  </BasicModal>
</template>
