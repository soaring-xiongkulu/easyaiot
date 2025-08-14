<template>
  <div class="train-wrapper">
    <div class="train-tab">
      <Tabs
        :animated="{ inkBar: true, tabPane: true }"
        :activeKey="state.activeKey"
        :tabBarGutter="60"
        @tabClick="handleTabClick"
      >
        <TabPane key="1" tab="训练任务管理">
          <TrainList></TrainList>
        </TabPane>
        <TabPane key="2" tab="模型服务管理">
          <ModelList></ModelList>
        </TabPane>
        <TabPane key="3" tab="模型导出管理">
          <ExportList></ExportList>
        </TabPane>
      </Tabs>
    </div>
  </div>
</template>

<script lang="ts" setup name="TrainService">
import { reactive } from 'vue';
import { TabPane, Tabs } from "ant-design-vue";
import TrainList from "./components/TrainList/index.vue";
import ModelList from "./components/ModelList/index.vue";
import ExportList from "./components/ExportList/index.vue";

const state = reactive({
  activeKey: '1'
});

const handleTabClick = (activeKey: string) => {
  state.activeKey = activeKey;
};
</script>

<style lang="less" scoped>
.train-wrapper {
  :deep(.ant-tabs-nav) {
    padding: 5px 0 0 25px;
  }

  .train-tab {
    padding: 16px 19px 0 15px;

    .ant-tabs {
      background-color: #FFFFFF;

      :deep(.ant-tabs-nav) {
        padding: 5px 0 0 25px;
      }
    }
  }
}
</style>
