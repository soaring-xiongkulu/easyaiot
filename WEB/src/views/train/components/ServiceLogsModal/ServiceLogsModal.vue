<template>
  <BasicModal
    v-bind="$attrs"
    @register="register"
    title="服务日志"
    width="800px"
    :footer="null"
  >
    <div class="logs-container">
      <a-spin :spinning="loading">
        <div class="logs-content" ref="logsContentRef">
          <pre v-if="logs">{{ logs }}</pre>
          <a-empty v-else description="暂无日志"/>
        </div>
      </a-spin>
      <div class="logs-footer">
        <a-button @click="handleRefresh">刷新</a-button>
        <a-button @click="handleClose">关闭</a-button>
      </div>
    </div>
  </BasicModal>
</template>

<script lang="ts" setup>
import {ref, nextTick, watch} from 'vue';
import {BasicModal, useModalInner} from '@/components/Modal';
import {useMessage} from '@/hooks/web/useMessage';
import {getDeployServiceLogs} from '@/api/device/model';
import {Empty as AEmpty, Spin as ASpin, Button as AButton} from 'ant-design-vue';

const {createMessage} = useMessage();

const loading = ref(false);
const logs = ref('');
const logsContentRef = ref();
const currentServiceId = ref<number | null>(null);

const [register, {closeModal}] = useModalInner(async (data) => {
  if (data && data.record) {
    currentServiceId.value = data.record.id;
    await fetchLogs();
  }
});

const fetchLogs = async () => {
  if (!currentServiceId.value) return;
  
  try {
    loading.value = true;
    const res = await getDeployServiceLogs(currentServiceId.value, {lines: 500});
    logs.value = res.data?.logs || '';
    
    // 滚动到底部
    await nextTick();
    if (logsContentRef.value) {
      logsContentRef.value.scrollTop = logsContentRef.value.scrollHeight;
    }
  } catch (error) {
    console.error('获取日志失败:', error);
    createMessage.error('获取日志失败');
  } finally {
    loading.value = false;
  }
};

const handleRefresh = async () => {
  await fetchLogs();
};

const handleClose = () => {
  closeModal();
};

// 监听日志变化，自动滚动到底部
watch(logs, () => {
  nextTick(() => {
    if (logsContentRef.value) {
      logsContentRef.value.scrollTop = logsContentRef.value.scrollHeight;
    }
  });
});
</script>

<style lang="less" scoped>
.logs-container {
  display: flex;
  flex-direction: column;
  height: 500px;
}

.logs-content {
  flex: 1;
  overflow-y: auto;
  background: #1e1e1e;
  color: #d4d4d4;
  padding: 16px;
  border-radius: 4px;
  font-family: 'Courier New', monospace;
  font-size: 12px;
  line-height: 1.5;

  pre {
    margin: 0;
    white-space: pre-wrap;
    word-wrap: break-word;
  }
}

.logs-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid #f0f0f0;
}
</style>

