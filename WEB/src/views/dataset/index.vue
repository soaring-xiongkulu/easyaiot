<template>
  <div class="device-wrapper">
    <div class="device-tab page-content-card">
      <Tabs
        v-model:activeKey="state.activeKey"
        :animated="{ inkBar: true, tabPane: false }"
        :destroyInactiveTabPane="true"
        :tabBarGutter="60"
      >
        <TabPane key="list" tab="数据集管理">
          <div class="device-list-pane">
            <DatasetList />
          </div>
        </TabPane>
      </Tabs>
    </div>
  </div>
</template>
<script lang="ts" setup name="noticeSetting">
import { reactive } from 'vue';
import { Tabs } from 'ant-design-vue';
import DatasetList from '@/views/dataset/components/DatasetList/index.vue';

defineOptions({ name: 'DATASET' });

const TabPane = Tabs.TabPane;

const state = reactive({
  activeKey: 'list',
});
</script>

<style lang="less" scoped>
:deep(.iot-basic-table-action.left) {
  justify-content: center;
}

.device-wrapper {
  padding: 0;
  box-sizing: border-box;
  min-height: calc(100vh - 88px);
  background: #ffffff;

  .page-content-card {
    background: #fff;
    border-radius: 0;
    overflow: hidden;
  }

  .device-tab {
    :deep(.ant-tabs-nav) {
      padding: 5px 0 0 25px;
      margin-bottom: 0;
    }

    :deep(.ant-tabs) {
      background-color: #fff;
    }
  }

  .device-list-pane {
    min-height: calc(100vh - 200px);
  }

  :deep(.ant-form-item) {
    margin-bottom: 10px;
  }

  :deep(.iot-basic-table-form-container) {
    padding: 0;
    background: #fff;

    .ant-form {
      margin-bottom: 0;
      border-radius: 0;
      background: transparent;
      padding: 16px 16px 0;
    }
  }

  :deep(.ant-table-wrapper) {
    border-radius: 0;
    background: #fff;
    padding: 8px 16px 16px;
  }
}
</style>
