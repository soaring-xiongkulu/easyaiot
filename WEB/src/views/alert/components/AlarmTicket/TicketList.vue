<script lang="ts" setup>
/**
 * 告警工单列表：告警命中路由规则后生成的处理工单（责任闭环），支持手动为存量告警发起工单
 */
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { Form, FormItem, InputNumber, Modal, Select, Tag } from 'ant-design-vue'
import type { FormSchema } from '@/components/Table'
import { BasicTable, TableAction, useTable } from '@/components/Table'
import { Button } from '@/components/Button'
import { useMessage } from '@/hooks/web/useMessage'
import { getAlertRecordPage, triggerAlertRecord } from '@/api/flow/alertRecord'
import { getSimpleProcessDefinitionList } from '@/api/flow/definition'
import { formatToDateTime } from '@/utils/dateUtil'

defineOptions({ name: 'AlarmTicketList' })

const router = useRouter()
const { createMessage } = useMessage()

const RECORD_STATUS: Record<number, { text: string; color: string }> = {
  1: { text: '处理中', color: 'processing' },
  2: { text: '已处理', color: 'success' },
  3: { text: '已关闭(误报)', color: 'error' },
  4: { text: '已取消', color: 'default' },
}

const columns = [
  { title: '告警ID', dataIndex: 'alertId', width: 90 },
  { title: '告警来源', dataIndex: 'alertSource', width: 110 },
  { title: '处理流程', dataIndex: 'processDefinitionKey', width: 200 },
  { title: '状态', dataIndex: 'processInstanceStatus', width: 110 },
  { title: '当前节点', dataIndex: 'currentTaskName', width: 140 },
  { title: '当前责任人', dataIndex: 'currentAssignees', width: 140 },
  { title: '发起时间', dataIndex: 'createTime', width: 170 },
  { title: '完成时间', dataIndex: 'finishTime', width: 170 },
]

const searchSchema: FormSchema[] = [
  { label: '告警ID', field: 'alertId', component: 'Input', colProps: { span: 8 } },
  {
    label: '状态',
    field: 'processInstanceStatus',
    component: 'Select',
    componentProps: {
      options: Object.entries(RECORD_STATUS).map(([value, item]) => ({ label: item.text, value: Number(value) })),
      allowClear: true,
    },
    colProps: { span: 8 },
  },
]

const [registerTable, { reload }] = useTable({
  title: '告警工单列表',
  api: getAlertRecordPage,
  columns,
  formConfig: { labelWidth: 80, schemas: searchSchema },
  useSearchForm: true,
  showTableSetting: false,
  canResize: true,
  showIndexColumn: false,
  rowKey: 'id',
})

// ---------- 手动发起工单 ----------
const definitionOptions = ref<{ label: string; value: string }[]>([])

onMounted(async () => {
  const list = await getSimpleProcessDefinitionList().catch(() => [])
  definitionOptions.value = (list ?? []).map((item: any) => ({ label: `${item.name}(v${item.version})`, value: item.key }))
})

const manualModalOpen = ref(false)
const manualAlertId = ref<number>()
const manualProcessKey = ref<string>()

function openManualTrigger() {
  manualAlertId.value = undefined
  manualProcessKey.value = definitionOptions.value[0]?.value
  manualModalOpen.value = true
}

async function submitManualTrigger() {
  if (!manualAlertId.value || !manualProcessKey.value) {
    createMessage.warning('请填写告警 ID 并选择流程')
    return
  }
  await triggerAlertRecord({ alertId: manualAlertId.value, processDefinitionKey: manualProcessKey.value })
  manualModalOpen.value = false
  createMessage.success('已发起处理流程')
  reload()
}

function handleViewInstance(record: Recordable) {
  if (!record.processInstanceId) {
    createMessage.warning('该工单暂无关联流程实例')
    return
  }
  router.push({ path: '/flow/process-instance/detail', query: { id: record.processInstanceId } })
}
</script>

<template>
  <div class="ticket-list">
    <BasicTable @register="registerTable">
      <template #toolbar>
        <span class="ticket-list__tip">告警命中路由规则后自动生成工单，此处可查看每条告警的责任闭环状态</span>
        <Button v-auth="['flow:alert-record:trigger']" type="primary" preIcon="ant-design:thunderbolt-outlined" @click="openManualTrigger">
          手动发起工单
        </Button>
      </template>
      <template #bodyCell="{ column, record }">
        <template v-if="column.dataIndex === 'alertSource'">
          <Tag color="purple">{{ record.alertSource === 'VIDEO_TASK' ? '算法任务' : record.alertSource }}</Tag>
        </template>
        <template v-else-if="column.dataIndex === 'processDefinitionKey'">
          <Tag color="blue">{{ record.processDefinitionKey || '—' }}</Tag>
        </template>
        <template v-else-if="column.dataIndex === 'processInstanceStatus'">
          <Tag :color="RECORD_STATUS[record.processInstanceStatus]?.color ?? 'default'">
            {{ RECORD_STATUS[record.processInstanceStatus]?.text ?? record.processInstanceStatus }}
          </Tag>
        </template>
        <template v-else-if="column.dataIndex === 'currentAssignees'">
          <span>{{ record.currentAssignees || '—' }}</span>
        </template>
        <template v-else-if="column.dataIndex === 'createTime'">
          <span>{{ record.createTime ? formatToDateTime(record.createTime) : '—' }}</span>
        </template>
        <template v-else-if="column.dataIndex === 'finishTime'">
          <span>{{ record.finishTime ? formatToDateTime(record.finishTime) : '—' }}</span>
        </template>
        <template v-else-if="column.dataIndex === 'action'">
          <TableAction
            :actions="[
              {
                icon: 'ant-design:eye-outlined',
                label: '处理进度',
                disabled: !record.processInstanceId,
                onClick: handleViewInstance.bind(null, record),
              },
            ]"
          />
        </template>
      </template>
    </BasicTable>

    <Modal
      v-model:open="manualModalOpen"
      title="手动发起告警工单"
      :width="480"
      ok-text="发起"
      cancel-text="取消"
      @ok="submitManualTrigger"
    >
      <Form layout="vertical" style="margin-top: 12px">
        <FormItem label="告警 ID" required>
          <InputNumber v-model:value="manualAlertId" style="width: 100%" placeholder="告警记录主键" />
        </FormItem>
        <FormItem label="处理流程" required>
          <Select v-model:value="manualProcessKey" :options="definitionOptions" placeholder="选择已发布的流程" />
        </FormItem>
      </Form>
    </Modal>
  </div>
</template>

<style lang="less" scoped>
.ticket-list {
  &__tip {
    margin-right: auto;
    overflow: hidden;
    color: #8c94a5;
    font-size: 12px;
    white-space: nowrap;
    text-overflow: ellipsis;
  }
}
</style>
