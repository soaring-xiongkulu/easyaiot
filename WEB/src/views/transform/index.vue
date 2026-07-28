<template>
  <div class="transform-wrapper">
    <div class="transform-tab">
      <Tabs
        :animated="{ inkBar: true, tabPane: true }"
        :activeKey="state.activeKey"
        :tabBarGutter="60"
        @tabClick="handleTabClick"
      >
        <TabPane key="overview" tab="对接概览">
          <OverviewPanel />
        </TabPane>
        <TabPane key="party" tab="对接系统">
          <PartyPanel />
        </TabPane>
        <TabPane key="contract" tab="推送规则">
          <ContractPanel />
        </TabPane>
        <TabPane key="convert" tab="数据转换">
          <ConvertPanel />
        </TabPane>
        <TabPane key="trace" tab="推送记录">
          <TracePanel />
        </TabPane>
      </Tabs>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { reactive } from 'vue'
import { TabPane, Tabs } from 'ant-design-vue'
import OverviewPanel from './components/OverviewPanel.vue'
import PartyPanel from './components/PartyPanel.vue'
import ContractPanel from './components/ContractPanel.vue'
import ConvertPanel from './components/ConvertPanel.vue'
import TracePanel from './components/TracePanel.vue'

defineOptions({ name: 'Transform' })

const state = reactive({
  activeKey: 'overview',
})

const handleTabClick = (activeKey: string) => {
  state.activeKey = activeKey
}
</script>

<style lang="less" scoped>
.transform-wrapper {
  height: calc(100vh - 64px);
  display: flex;
  flex-direction: column;
  overflow: hidden;

  :deep(.ant-tabs-nav) {
    padding: 5px 0 0 25px;
    flex-shrink: 0;
  }

  .transform-tab {
    flex: 1;
    min-height: 0;
    padding: 16px 19px 12px 15px;
    display: flex;
    flex-direction: column;
    overflow: hidden;

    .ant-tabs {
      background-color: #ffffff;
      flex: 1;
      min-height: 0;
      display: flex;
      flex-direction: column;
      overflow: hidden;

      :deep(.ant-tabs-nav) {
        padding: 5px 0 0 25px;
        flex-shrink: 0;
      }

      :deep(.ant-tabs-content-holder) {
        flex: 1;
        min-height: 0;
        overflow: hidden;
      }

      :deep(.ant-tabs-content) {
        height: 100%;
      }

      :deep(.ant-tabs-tabpane) {
        height: 100%;
        overflow: hidden;

        > div {
          height: 100%;
          min-height: 0;
        }
      }
    }
  }
}
</style>
