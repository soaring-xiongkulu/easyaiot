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
          <AiModelTool :initialLLMId="initialLLMId"></AiModelTool>
        </TabPane>
        <TabPane key="3" tab="模型导出">
          <ModelExport></ModelExport>
        </TabPane>
        <TabPane key="4" tab="模型部署">
          <DeployService></DeployService>
        </TabPane>
        <TabPane key="5" tab="大模型管理">
          <LLMManage ref="llmManageRef"></LLMManage>
        </TabPane>
      </Tabs>
    </div>
  </div>
</template>

<script lang="ts" setup name="TrainService">
import {reactive, onMounted, ref, computed} from 'vue';
import {useRoute} from 'vue-router';
import { TabPane, Tabs } from "ant-design-vue";
import ModelList from "@/views/train/components/ModelList/index.vue";
import AiModelTool from "@/views/train/components/AiModelTool/index.vue";
import ModelExport from "@/views/train/components/ModelExport/index.vue";
import DeployService from "@/views/train/components/DeployService/index.vue";
import LLMManage from "@/views/train/components/LLMManage/index.vue";

defineOptions({name: 'TRAIN'})

const route = useRoute();

const state = reactive({
  activeKey: '1'
});

// 大模型管理组件引用
const llmManageRef = ref();

const handleTabClick = (activeKey: string) => {
  state.activeKey = activeKey;
  // 切换到大模型管理标签页时，刷新数据
  if (activeKey === '5' && llmManageRef.value) {
    llmManageRef.value.refresh();
  }
};

// 从路由参数获取大模型ID
const initialLLMId = computed(() => {
  const llmId = route.query.llmId as string;
  return llmId ? parseInt(llmId, 10) : null;
});

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
