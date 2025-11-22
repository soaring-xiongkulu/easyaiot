<template>
  <div class="train-wrapper">
    <div class="train-tab">
      <Tabs
        :animated="{ inkBar: true, tabPane: true }"
        :activeKey="state.activeKey"
        :tabBarGutter="60"
        @tabClick="handleTabClick"
      >
        <TabPane key="1" tab="模型管理">
          <ModelList></ModelList>
        </TabPane>
        <TabPane key="2" tab="模型推理">
          <AiModelTool></AiModelTool>
        </TabPane>
        <TabPane key="3" tab="模型导出">
          <ModelExport></ModelExport>
        </TabPane>
        <TabPane key="4" tab="模型部署">
          <DeployService></DeployService>
        </TabPane>
      </Tabs>
    </div>
  </div>
</template>

<script lang="ts" setup name="TrainService">
import {reactive, onMounted} from 'vue';
import {useRoute} from 'vue-router';
import { TabPane, Tabs } from "ant-design-vue";
import ModelList from "@/views/train/components/ModelList/index.vue";
import AiModelTool from "@/views/train/components/AiModelTool/index.vue";
import ModelExport from "@/views/train/components/ModelExport/index.vue";
import DeployService from "@/views/train/components/DeployService/index.vue";

defineOptions({name: 'TRAIN'})

const route = useRoute();

const state = reactive({
  activeKey: '1'
});

const handleTabClick = (activeKey: string) => {
  state.activeKey = activeKey;
};

// 处理路由参数，自动切换到指定tab
onMounted(() => {
  const tab = route.query.tab as string;
  if (tab) {
    state.activeKey = tab;
  }
});
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
