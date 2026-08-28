<script lang="ts" setup>
/**
 * 告警处理页（FLOW 独立菜单）：路由规则（告警→流程自动派单）+ 处理记录（责任闭环）
 * Tab 组织方式参考流媒体（camera）模块。
 */
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { Button, Form, FormItem, Input, InputNumber, Modal, Select, Switch, TabPane, Tabs, Tag, Textarea } from 'ant-design-vue'
import type { FormSchema } from '@/components/Table'
import { BasicTable, TableAction, useTable } from '@/components/Table'
import { useMessage } from '@/hooks/web/useMessage'
import { Icon } from '@/components/Icon'
import {
  createAlertRouteRule,
  deleteAlertRouteRule,
  getAlertRouteRulePage,
  updateAlertRouteRule,
  updateAlertRouteRuleEnabled,
  type AlertMatchCondition,
  type FlowAlertRouteRuleVO,
} from '@/api/flow/alertRouteRule'
import { getAlertRecordPage, triggerAlertRecord } from '@/api/flow/alertRecord'
import { getSimpleProcessDefinitionList } from '@/api/flow/definition'
import { formatToDateTime } from '@/utils/dateUtil'

defineOptions({ name: 'FlowAlert' })

const router = useRouter()
const { createMessage, createConfirm } = useMessage()

const activeKey = ref('rule')

// ==================== 路由规则 ====================
const definitionOptions = ref<{ label: string; value: string }[]>([])

onMounted(async () => {
  const list = await getSimpleProcessDefinitionList().catch(() => [])
  definitionOptions.value = (list ?? []).map((item: any) => ({ label: `${item.name}(v${item.version})`, value: item.key }))
})

const ALERT_FIELDS = [
  { label: '告警对象', value: 'object' },
  { label: '告警事件', value: 'event' },
  { label: '任务类型', value: 'taskType' },
  { label: '任务名称', value: 'taskName' },
  { label: '设备名称', value: 'deviceName' },
  { label: '设备编号', value: 'deviceId' },
  { label: '边缘节点', value: 'edgeNodeId' },
]

const ALERT_OPS = [
  { label: '等于', value: 'EQ' },
  { label: '不等于', value: 'NE' },
  { label: '属于(逗号分隔)', value: 'IN' },
  { label: '前缀匹配', value: 'PREFIX' },
  { label: '正则匹配', value: 'REGEX' },
]

const ruleColumns = [
  { title: '规则名称', dataIndex: 'ruleName', width: 180 },
  { title: '优先级', dataIndex: 'priority', width: 90 },
  { title: '触发流程', dataIndex: 'processDefinitionKey', width: 220 },
  { title: '匹配条件', dataIndex: 'matchConditions', width: 320 },
  { title: '去重窗口', dataIndex: 'dedupWindowSeconds', width: 100 },
  { title: '状态', dataIndex: 'enabled', width: 80 },
  { title: '操作', dataIndex: 'action', width: 160, fixed: 'right' as const },
]

const [registerRuleTable, { reload: reloadRules }] = useTable({
  title: '告警路由规则',
  api: getAlertRouteRulePage,
  columns: ruleColumns,
  useSearchForm: false,
  showTableSetting: true,
  actionColumn: undefined,
})

function formatConditions(conditions?: AlertMatchCondition[]) {
  if (!conditions?.length) {
    return '全部告警'
  }
  return conditions.map(item => `${fieldLabel(item.field)} ${opLabel(item.op)} ${item.value}`).join(' 且 ')
}

function fieldLabel(field: string) {
  return ALERT_FIELDS.find(item => item.value === field)?.label ?? field
}

function opLabel(op: string) {
  return ALERT_OPS.find(item => item.value === op)?.label ?? op
}

// ---------- 规则编辑 ----------
const ruleModalOpen = ref(false)
const ruleSaving = ref(false)
const ruleForm = ref<FlowAlertRouteRuleVO>(newRuleForm())

function newRuleForm(): FlowAlertRouteRuleVO {
  return {
    ruleName: '',
    priority: 0,
    processDefinitionKey: undefined as unknown as string,
    matchConditions: [],
    dedupWindowSeconds: 300,
    enabled: true,
    remark: '',
  }
}

function openRuleCreate() {
  ruleForm.value = newRuleForm()
  ruleModalOpen.value = true
}

function openRuleEdit(record: Recordable) {
  ruleForm.value = {
    ...record,
    matchConditions: (record.matchConditions ?? []).map((item: AlertMatchCondition) => ({ ...item })),
  } as FlowAlertRouteRuleVO
  ruleModalOpen.value = true
}

function addCondition() {
  ruleForm.value.matchConditions.push({ field: 'event', op: 'EQ', value: '' })
}

function removeCondition(index: number) {
  ruleForm.value.matchConditions.splice(index, 1)
}

async function handleRuleSubmit() {
  const form = ruleForm.value
  if (!form.ruleName || !form.processDefinitionKey) {
    createMessage.warning('请填写规则名称并选择触发流程')
    return
  }
  if (form.matchConditions.some(item => !item.field || item.value === '')) {
    createMessage.warning('匹配条件未填写完整')
    return
  }
  ruleSaving.value = true
  try {
    if (form.id) {
      await updateAlertRouteRule(form)
    }
    else {
      await createAlertRouteRule(form)
    }
    ruleModalOpen.value = false
    createMessage.success('保存成功')
    reloadRules()
  }
  finally {
    ruleSaving.value = false
  }
}

async function handleRuleToggle(record: Recordable) {
  await updateAlertRouteRuleEnabled(record.id, !record.enabled)
  createMessage.success(record.enabled ? '已停用' : '已启用')
  reloadRules()
}

function handleRuleDelete(record: Recordable) {
  createConfirm({
    title: '删除路由规则',
    iconType: 'warning',
    content: `确定删除规则「${record.ruleName}」吗？`,
    async onOk() {
      await deleteAlertRouteRule(record.id)
      createMessage.success('删除成功')
      reloadRules()
    },
  })
}

// ==================== 处理记录 ====================
const recordColumns = [
  { title: '告警ID', dataIndex: 'alertId', width: 90 },
  { title: '告警来源', dataIndex: 'alertSource', width: 110 },
  { title: '处理流程', dataIndex: 'processDefinitionKey', width: 200 },
  { title: '状态', dataIndex: 'processInstanceStatus', width: 110 },
  { title: '当前节点', dataIndex: 'currentTaskName', width: 140 },
  { title: '当前责任人', dataIndex: 'currentAssignees', width: 140 },
  { title: '发起时间', dataIndex: 'createTime', width: 170 },
  { title: '完成时间', dataIndex: 'finishTime', width: 170 },
]

const RECORD_STATUS: Record<number, { text: string; color: string }> = {
  1: { text: '处理中', color: 'processing' },
  2: { text: '已处理', color: 'success' },
  3: { text: '已关闭(误报)', color: 'error' },
  4: { text: '已取消', color: 'default' },
}

const recordSearchSchema: FormSchema[] = [
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

const [registerRecordTable, { reload: reloadRecords }] = useTable({
  title: '告警处理记录',
  api: getAlertRecordPage,
  columns: recordColumns,
  formConfig: { labelWidth: 80, schemas: recordSearchSchema },
  useSearchForm: true,
  showTableSetting: true,
})

function handleViewInstance(record: Recordable) {
  if (!record.processInstanceId) {
    createMessage.warning('该记录暂无关联流程实例')
    return
  }
  router.push({ path: '/flow/process-instance/detail', query: { id: record.processInstanceId } })
}

const manualModalOpen = ref(false)
const manualAlertId = ref<number>()
const manualProcessKey = ref<string>()

function openManualTrigger(record?: Recordable) {
  manualAlertId.value = record?.alertId
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
  reloadRecords()
}
</script>

<template>
  <div class="flow-alert-page">
    <Tabs v-model:activeKey="activeKey" :destroyInactiveTabPane="true">
      <!-- 路由规则 -->
      <TabPane key="rule">
        <template #tab>
          <Icon icon="ant-design:apartment-outlined" /> 路由规则
        </template>
        <BasicTable @register="registerRuleTable">
          <template #toolbar>
            <Button v-auth="['flow:alert-route-rule:create']" type="primary" preIcon="ant-design:plus-outlined" @click="openRuleCreate">
              新建规则
            </Button>
          </template>
          <template #bodyCell="{ column, record }">
            <template v-if="column.dataIndex === 'priority'">
              <Tag :color="record.priority >= 100 ? 'orange' : 'default'">{{ record.priority }}</Tag>
            </template>
            <template v-else-if="column.dataIndex === 'processDefinitionKey'">
              <Tag color="blue">{{ record.processDefinitionKey }}</Tag>
            </template>
            <template v-else-if="column.dataIndex === 'matchConditions'">
              <span :title="formatConditions(record.matchConditions)">{{ formatConditions(record.matchConditions) }}</span>
            </template>
            <template v-else-if="column.dataIndex === 'dedupWindowSeconds'">
              {{ record.dedupWindowSeconds ? `${record.dedupWindowSeconds}s` : '不去重' }}
            </template>
            <template v-else-if="column.dataIndex === 'enabled'">
              <Switch
                :checked="record.enabled"
                checked-children="启用"
                un-checked-children="停用"
                @change="handleRuleToggle(record)"
              />
            </template>
            <template v-else-if="column.dataIndex === 'action'">
              <TableAction
                :actions="[
                  { icon: 'ant-design:edit-outlined', label: '编辑', auth: 'flow:alert-route-rule:update', onClick: openRuleEdit.bind(null, record) },
                  {
                    icon: 'ant-design:delete-outlined',
                    label: '删除',
                    danger: true,
                    auth: 'flow:alert-route-rule:delete',
                    popConfirm: { title: '确认删除该规则？', confirm: handleRuleDelete.bind(null, record) },
                  },
                ]"
              />
            </template>
          </template>
        </BasicTable>
      </TabPane>

      <!-- 处理记录 -->
      <TabPane key="record">
        <template #tab>
          <Icon icon="ant-design:file-done-outlined" /> 处理记录
        </template>
        <div class="flow-alert-page__record-bar">
          <span class="flow-alert-page__record-tip">
            告警命中规则后自动发起处理流程，此处可查看每条告警的责任闭环状态
          </span>
          <Button preIcon="ant-design:thunderbolt-outlined" @click="openManualTrigger()">手动发起处理</Button>
        </div>
        <BasicTable @register="registerRecordTable">
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
      </TabPane>
    </Tabs>

    <!-- 规则编辑弹窗 -->
    <Modal
      v-model:open="ruleModalOpen"
      :title="ruleForm.id ? '编辑路由规则' : '新建路由规则'"
      :width="640"
      :confirm-loading="ruleSaving"
      ok-text="保存"
      cancel-text="取消"
      @ok="handleRuleSubmit"
    >
      <Form layout="vertical" style="margin-top: 12px">
        <div style="display: flex; gap: 12px">
          <FormItem label="规则名称" required style="flex: 1">
            <Input v-model:value="ruleForm.ruleName" placeholder="如：周界入侵-安防组处理" :maxlength="60" />
          </FormItem>
          <FormItem label="优先级(大者先匹配)" style="width: 180px">
            <InputNumber v-model:value="ruleForm.priority" style="width: 100%" />
          </FormItem>
        </div>
        <FormItem label="命中后发起的流程" required>
          <Select
            v-model:value="ruleForm.processDefinitionKey"
            placeholder="选择已发布的告警处理流程"
            :options="definitionOptions"
            show-search
            option-filter-prop="label"
          />
        </FormItem>
        <FormItem>
          <template #label>
            匹配条件（全部满足才命中；不配条件 = 匹配全部告警）
          </template>
          <div v-for="(condition, idx) in ruleForm.matchConditions" :key="idx" class="rule-cond-row">
            <Select v-model:value="condition.field" :options="ALERT_FIELDS" style="flex: 1.2" />
            <Select v-model:value="condition.op" :options="ALERT_OPS" style="flex: 1.2" />
            <Input v-model:value="condition.value" placeholder="匹配值" style="flex: 1.6" />
            <Button type="text" danger @click="removeCondition(idx)">
              <Icon icon="ant-design:delete-outlined" />
            </Button>
          </div>
          <Button type="dashed" block @click="addCondition">
            <Icon icon="ant-design:plus-outlined" /> 添加条件
          </Button>
        </FormItem>
        <div style="display: flex; gap: 12px">
          <FormItem label="去重窗口(秒，同设备+任务+事件去重)" style="flex: 1">
            <InputNumber v-model:value="ruleForm.dedupWindowSeconds" :min="0" style="width: 100%" />
          </FormItem>
          <FormItem label="启用" style="width: 120px">
            <Switch v-model:checked="ruleForm.enabled" checked-children="启用" un-checked-children="停用" />
          </FormItem>
        </div>
        <FormItem label="备注">
          <Textarea v-model:value="ruleForm.remark" :rows="2" />
        </FormItem>
      </Form>
    </Modal>

    <!-- 手动发起弹窗 -->
    <Modal
      v-model:open="manualModalOpen"
      title="手动发起告警处理"
      :width="480"
      ok-text="发起"
      cancel-text="取消"
      @ok="submitManualTrigger"
    >
      <Form layout="vertical" style="margin-top: 12px">
        <FormItem label="告警 ID" required>
          <InputNumber v-model:value="manualAlertId" style="width: 100%" placeholder="video 库 alert 表主键" />
        </FormItem>
        <FormItem label="处理流程" required>
          <Select v-model:value="manualProcessKey" :options="definitionOptions" placeholder="选择已发布的流程" />
        </FormItem>
      </Form>
    </Modal>
  </div>
</template>

<style lang="less" scoped>
.flow-alert-page {
  padding: 8px;

  &__record-bar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0 4px 8px;
  }

  &__record-tip {
    color: #8c94a5;
    font-size: 12px;
  }
}

.rule-cond-row {
  display: flex;
  gap: 8px;
  align-items: center;
  margin-bottom: 8px;
}
</style>
