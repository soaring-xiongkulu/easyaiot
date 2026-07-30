<template>
  <div class="visualize-wrapper">
    <div class="visualize-tab">
      <Tabs
        :animated="{ inkBar: true, tabPane: true }"
        :activeKey="state.activeKey"
        :tabBarGutter="60"
        @tabClick="handleTabClick"
      >
        <TabPane key="1" tab="项目管理">
          <ProjectList />
        </TabPane>
        <TabPane key="2" tab="模板中心">
          <TemplateList />
        </TabPane>
        <TabPane key="3" tab="素材库">
          <AssetList />
        </TabPane>
        <TabPane key="4" tab="数据源">
          <DataSourceList />
        </TabPane>
        <TabPane key="5" tab="服务部署">
          <DeployList />
        </TabPane>
      </Tabs>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { reactive, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { TabPane, Tabs } from 'ant-design-vue'
import ProjectList from './components/ProjectList/index.vue'
import TemplateList from './components/TemplateList/index.vue'
import AssetList from './components/AssetList/index.vue'
import DataSourceList from './components/DataSourceList/index.vue'
import DeployList from './components/DeployList/index.vue'

defineOptions({ name: 'Visualize' })

const route = useRoute()

const state = reactive({
  activeKey: '1',
})

function handleTabClick(key: string) {
  state.activeKey = key
}

onMounted(() => {
  const tab = String(route.query.tab || '')
  if (['1', '2', '3', '4', '5'].includes(tab)) {
    state.activeKey = tab
  }
})
</script>

<style lang="less" scoped>
.visualize-wrapper {
  height: calc(100vh - 64px);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: #ffffff;

  :deep(.ant-tabs-nav) {
    padding: 5px 0 0 25px;
    flex-shrink: 0;
  }

  .visualize-tab {
    flex: 1;
    min-height: 0;
    padding: 0;
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
