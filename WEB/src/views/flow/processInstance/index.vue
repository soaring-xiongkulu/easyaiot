<script lang="ts" setup>
/**
 * 我的流程 / 流程管理（Tab 切换，参考流媒体页 Tab 组织方式）
 */
import { ref } from 'vue'
import { TabPane, Tabs } from 'ant-design-vue'
import ProcessInstanceTable from './ProcessInstanceTable.vue'

defineOptions({ name: 'FlowProcessInstance' })

const activeKey = ref('my')
</script>

<template>
  <div class="flow-instance-page">
    <Tabs v-model:activeKey="activeKey" :destroyInactiveTabPane="true">
      <TabPane key="my" tab="我的流程">
        <ProcessInstanceTable type="my" />
      </TabPane>
      <TabPane key="manager" tab="全部流程">
        <ProcessInstanceTable type="manager" />
      </TabPane>
    </Tabs>
  </div>
</template>

<style lang="less" scoped>
.flow-instance-page {
  padding: 8px 8px 0;
}
</style>
