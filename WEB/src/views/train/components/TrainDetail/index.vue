<template>
  <div class="train-wrapper">
    <div class="train-tab">
      <Tabs
        :animated="{ inkBar: true, tabPane: true }"
        :activeKey="state.activeKey"
        :tabBarGutter="60"
        @tabClick="handleTabClick"
      >
        <TabPane key="1" tab="模型训练">
          <TrainList></TrainList>
        </TabPane>
        <TabPane key="2" tab="模型推理">
          <ModelServiceList></ModelServiceList>
        </TabPane>
        <TabPane key="4" tab="模型导出">
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
import ModelServiceList from "@/views/train/components/ModelServiceList/index.vue";
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
