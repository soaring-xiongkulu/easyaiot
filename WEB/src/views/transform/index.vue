<template>
  <div class="transform-wrapper">
    <div class="transform-tab">
      <Tabs
        class="tf-tabs-bar"
        :animated="{ inkBar: true, tabPane: false }"
        :activeKey="state.activeKey"
        :tabBarGutter="40"
        @tabClick="handleTabClick"
      >
        <TabPane key="cluster" tab="运行集群" />
        <TabPane key="contract" tab="转发规则" />
        <TabPane key="party" tab="数据目的" />
        <TabPane key="mapping" tab="映射模板" />
        <TabPane key="trace" tab="投递监控" />
      </Tabs>

      <div class="transform-tab-content">
        <ClusterPanel v-if="state.activeKey === 'cluster'" />
        <ContractPanel v-else-if="state.activeKey === 'contract'" @goto="handleGoto" />
        <PartyPanel v-else-if="state.activeKey === 'party'" @goto="handleGoto" />
        <MappingPanel v-else-if="state.activeKey === 'mapping'" />
        <TracePanel v-else-if="state.activeKey === 'trace'" />
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { reactive } from 'vue'
import { TabPane, Tabs } from 'ant-design-vue'
import ClusterPanel from './components/ClusterPanel.vue'
import ContractPanel from './components/ContractPanel.vue'
import PartyPanel from './components/PartyPanel.vue'
import MappingPanel from './components/MappingPanel.vue'
import TracePanel from './components/TracePanel.vue'

defineOptions({ name: 'Transform' })

const state = reactive({
  activeKey: 'cluster',
})

const handleTabClick = (activeKey: string) => {
  state.activeKey = activeKey
}

const handleGoto = (key: string) => {
  state.activeKey = key === 'overview' ? 'cluster' : key
}
</script>

<style lang="less" scoped>
@import './theme.less';

.transform-wrapper {
  height: calc(100vh - 64px);
  min-height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: @tf-bg;

  .transform-tab {
    flex: 1;
    min-height: 0;
    padding: 0;
    display: flex;
    flex-direction: column;
    overflow: hidden;
  }

  :deep(.tf-tabs-bar .ant-tabs-nav) {
    margin: 0;
    padding: 5px 0 0 25px;
    background: @tf-bg;
    border-bottom: 1px solid @tf-border;

    &::before {
      border-bottom: none;
    }
  }

  :deep(.tf-tabs-bar .ant-tabs-tab) {
    padding: 14px 2px;
    font-size: @tf-font-body;
    color: @tf-text-secondary;

    &:hover {
      color: @tf-primary;
    }

    &.ant-tabs-tab-active .ant-tabs-tab-btn {
      color: @tf-primary;
      font-weight: 600;
    }
  }

  :deep(.tf-tabs-bar .ant-tabs-ink-bar) {
    height: 3px;
    border-radius: 2px 2px 0 0;
    background: @tf-primary;
  }

  :deep(.tf-tabs-bar .ant-tabs-content-holder) {
    display: none;
  }

  .transform-tab-content {
    flex: 1;
    min-height: 0;
    overflow: hidden;
    padding: 12px 16px 16px;
    background: @tf-bg;

    > * {
      height: 100%;
      min-height: 0;
    }
  }
}
</style>
