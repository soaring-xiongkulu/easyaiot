<template>
  <BasicModal
    v-bind="$attrs"
    @register="register"
    :title="title"
    width="1200px"
    :footer="null"
    :maskClosable="false"
  >
    <div class="logs-container">
      <div class="logs-header">
        <div class="logs-header-left">
          <FileTextOutlined />
          <span class="logs-title">服务日志</span>
        </div>
        <div class="logs-header-right">
          <a-button type="primary" @click="handleRefresh" :loading="loading">
            <template #icon><ReloadOutlined /></template>
            刷新
          </a-button>
        </div>
      </div>
      <div class="logs-content-wrapper">
        <a-spin :spinning="loading" tip="加载日志中...">
          <div class="logs-content" ref="logsContentRef" :class="{ 'empty-state': !logs }">
            <div v-if="logs" class="logs-text">
              <pre>{{ logs }}</pre>
            </div>
            <a-empty v-else description="暂无日志" />
          </div>
        </a-spin>
      </div>
    </div>
  </BasicModal>
</template>

<script lang="ts" setup>
import { ref, nextTick } from 'vue';
import { BasicModal, useModalInner } from '@/components/Modal';
import { Button, Spin, Empty } from 'ant-design-vue';
import { ReloadOutlined, FileTextOutlined } from '@ant-design/icons-vue';

defineOptions({ name: 'ServiceLogsModal' });

const loading = ref(false);
const logs = ref('');
const logsContentRef = ref();
const title = ref('服务日志');

const [register, { closeModal }] = useModalInner((data) => {
  if (data) {
    title.value = data.title || '服务日志';
    logs.value = data.logs || '';
  }
});

const handleRefresh = () => {
  // 刷新逻辑由父组件处理
  // 这里可以触发事件通知父组件刷新
};

const scrollToBottom = () => {
  if (logsContentRef.value) {
    logsContentRef.value.scrollTop = logsContentRef.value.scrollHeight;
  }
};
</script>

<style lang="less" scoped>
.logs-container {
  display: flex;
  flex-direction: column;
  height: 70vh;
  max-height: 700px;
  min-height: 550px;
}

.logs-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: #fafafa;
  border: 1px solid #e8e8e8;
  border-radius: 4px;
  margin-bottom: 12px;
}

.logs-content-wrapper {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.logs-content {
  flex: 1;
  overflow-y: auto;
  overflow-x: auto;
  background: #f5f5f5;
  border: 1px solid #d9d9d9;
  border-radius: 4px;
  min-height: 0;

  &.empty-state {
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .logs-text {
    padding: 16px;
    font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
    font-size: 13px;
    line-height: 1.6;
    color: #262626;

    pre {
      margin: 0;
      white-space: pre-wrap;
      word-wrap: break-word;
      word-break: break-all;
    }
  }
}
</style>

