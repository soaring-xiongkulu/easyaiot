<script lang="ts" setup>
/**
 * 告警工单（原「工作流」独立菜单收敛为告警管理内 Tab）：
 * 工单列表 / 我的待办 / 已办任务 / 流程实例 / 路由规则 / 流程模型
 * 界面与模型管理（train）一致：白色背景 + BasicTable 纯列表，无卡片模式。
 */
import { computed, ref, watch } from 'vue'
import { TabPane, Tabs } from 'ant-design-vue'
import TicketList from './TicketList.vue'
import RouteRuleList from './RouteRuleList.vue'
import TaskTable from '@/views/flow/task/TaskTable.vue'
import ProcessInstanceTable from '@/views/flow/processInstance/ProcessInstanceTable.vue'
import FlowModel from '@/views/flow/model/index.vue'
import { usePermission } from '@/hooks/web/usePermission'

defineOptions({ name: 'AlarmTicket' })

const { hasPermission } = usePermission()
const showModelTab = computed(() => hasPermission('flow:model:query', false))

// 记住当前子 Tab：从流程设计页返回时恢复到离开时的位置（如流程模型）
const TICKET_TAB_KEY = 'easyaiot:alarm-ticket-tab'
const INSTANCE_TAB_KEY = 'easyaiot:alarm-ticket-instance-tab'
const activeKey = ref<string>(sessionStorage.getItem(TICKET_TAB_KEY) || 'ticket')
const instanceTab = ref<string>(sessionStorage.getItem(INSTANCE_TAB_KEY) || 'my')

watch(activeKey, (v) => sessionStorage.setItem(TICKET_TAB_KEY, v))
watch(instanceTab, (v) => sessionStorage.setItem(INSTANCE_TAB_KEY, v))
</script>

<template>
  <div class="alarm-ticket">
    <Tabs v-model:activeKey="activeKey" :destroyInactiveTabPane="true">
      <TabPane key="ticket" tab="工单列表">
        <TicketList />
      </TabPane>
      <TabPane key="todo" tab="我的待办">
        <TaskTable type="todo" />
      </TabPane>
      <TabPane key="done" tab="已办任务">
        <TaskTable type="done" />
      </TabPane>
      <TabPane key="instance" tab="流程实例">
        <Tabs v-model:activeKey="instanceTab" :destroyInactiveTabPane="true" class="alarm-ticket__sub-tabs">
          <TabPane key="my" tab="我的流程">
            <ProcessInstanceTable type="my" />
          </TabPane>
          <TabPane key="manager" tab="全部流程">
            <ProcessInstanceTable type="manager" />
          </TabPane>
        </Tabs>
      </TabPane>
      <TabPane key="rule" tab="路由规则">
        <RouteRuleList />
      </TabPane>
      <TabPane v-if="showModelTab" key="model" tab="流程模型">
        <FlowModel />
      </TabPane>
    </Tabs>
  </div>
</template>

<style lang="less" scoped>
.alarm-ticket {
  :deep(.ant-tabs-nav) {
    padding: 0 16px;
    margin-bottom: 0;
  }

  &__sub-tabs {
    :deep(.ant-tabs-nav) {
      padding: 0 4px;
    }
  }
}
</style>
