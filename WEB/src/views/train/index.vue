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
<!--          <GpuStackMonitorTip class="page-monitor-tip" />-->
          <ModelList />
        </TabPane>
        <TabPane v-if="showAdvancedTabs" key="6" tab="模型训练">
          <TrainTaskList
            :tab-active="state.activeKey === '6'"
            :auto-open="route.query.launch === '1'"
            :initial-dataset-id="initialDatasetId"
          />
        </TabPane>
        <TabPane key="2" tab="模型推理">
          <AiModelTool :initialLLMId="initialLLMId" :tab-active="state.activeKey === '2'" />
        </TabPane>
        <TabPane v-if="showAdvancedTabs" key="7" tab="SAM 万物识别">
          <SamInferencePage />
        </TabPane>
        <TabPane v-if="showAdvancedTabs" key="3" tab="模型导出">
          <ModelExport></ModelExport>
        </TabPane>
        <TabPane v-if="showAdvancedTabs" key="4" tab="模型部署">
          <DeployService></DeployService>
        </TabPane>
        <TabPane v-if="showAdvancedTabs" key="5" tab="大模型管理">
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
import TrainTaskList from "@/views/train/components/TrainTaskList/index.vue";
import AiModelTool from "@/views/train/components/AiModelTool/index.vue";
import ModelExport from "@/views/train/components/ModelExport/index.vue";
import DeployService from "@/views/train/components/DeployService/index.vue";
import LLMManage from "@/views/train/components/LLMManage/index.vue";
import SamInferencePage from "@/views/model/SamInference/index.vue";
import GpuStackMonitorTip from '@/components/GpuStackMonitorTip/index.vue';
import { isTrainAdvancedEnabled } from '@/utils/deployProfile';

defineOptions({name: 'TRAIN'})

const route = useRoute();
const showAdvancedTabs = isTrainAdvancedEnabled();

const TRAIN_TAB_KEYS = {
  MODEL_LIST: '1',
  INFERENCE: '2',
  EXPORT: '3',
  DEPLOY: '4',
  LLM: '5',
  TRAIN_TASK: '6',
  SAM: '7',
} as const;

const MINI_TRAIN_TAB_KEYS = new Set<string>([
  TRAIN_TAB_KEYS.MODEL_LIST,
  TRAIN_TAB_KEYS.INFERENCE,
]);

function normalizeTrainRouteTab(tab: string): string {
  if (!showAdvancedTabs && !MINI_TRAIN_TAB_KEYS.has(tab)) {
    return TRAIN_TAB_KEYS.MODEL_LIST;
  }
  return tab;
}

const state = reactive({
  activeKey: TRAIN_TAB_KEYS.MODEL_LIST
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

const initialDatasetId = computed(() => {
  const value = route.query.datasetId;
  return typeof value === 'string' ? value : undefined;
});

// 处理路由参数，自动切换到指定tab
onMounted(() => {
  const tab = route.query.tab as string;
  if (tab) {
    state.activeKey = normalizeTrainRouteTab(tab);
  }
});
</script>

<style lang="less" scoped>
.train-wrapper {
  height: calc(100vh - 64px);
  display: flex;
  flex-direction: column;
  overflow: hidden;

  :deep(.ant-tabs-nav) {
    padding: 5px 0 0 25px;
    flex-shrink: 0;
  }

  .train-tab {
    flex: 1;
    min-height: 0;
    padding: 16px 19px 12px 15px;
    display: flex;
    flex-direction: column;
    overflow: hidden;

    .ant-tabs {
      background-color: #FFFFFF;
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
