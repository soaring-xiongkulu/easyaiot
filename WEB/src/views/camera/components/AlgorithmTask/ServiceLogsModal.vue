<template>
  <BasicModal
    v-bind="$attrs"
    @register="register"
    title="算法任务日志"
    width="1200px"
    :footer="null"
    :maskClosable="false"
  >
    <div class="logs-container">
      <div class="logs-header">
        <div class="logs-header-left">
          <FileTextOutlined />
          <span class="logs-title">实时日志</span>
          <a-badge v-if="autoRefresh" :count="'自动刷新'" :number-style="{backgroundColor: '#52c41a'}" />
        </div>
        <div class="logs-header-right">
          <a-switch 
            v-model:checked="autoRefresh" 
            checked-children="自动刷新" 
            un-checked-children="手动刷新"
            @change="handleAutoRefreshChange"
          />
          <a-select 
            v-model:value="refreshInterval" 
            style="width: 100px; margin-left: 8px;"
            :disabled="!autoRefresh"
            @change="handleIntervalChange"
          >
            <a-select-option :value="3">3秒</a-select-option>
            <a-select-option :value="5">5秒</a-select-option>
            <a-select-option :value="10">10秒</a-select-option>
            <a-select-option :value="30">30秒</a-select-option>
          </a-select>
        </div>
      </div>
      <div class="logs-content-wrapper">
        <a-spin :spinning="loading" tip="加载日志中...">
          <div class="logs-content" ref="logsContentRef" @scroll="handleScroll" :class="{ 'empty-state': !logs }">
            <div v-if="logs" class="logs-text">
              <pre>{{ logs }}</pre>
            </div>
            <a-empty v-else description="暂无日志" />
          </div>
        </a-spin>
      </div>
      <div class="logs-footer">
        <div class="logs-footer-left">
          <a-button type="primary" @click="handleRefresh" :loading="loading">
            <template #icon><ReloadOutlined /></template>
            刷新
          </a-button>
          <a-button @click="handleClear">
            <template #icon><ClearOutlined /></template>
            清空显示
          </a-button>
          <a-button @click="handleScrollToBottom">
            <template #icon><VerticalAlignBottomOutlined /></template>
            滚动到底部
          </a-button>
        </div>
        <div class="logs-footer-right">
          <a-button @click="handleClose">关闭</a-button>
        </div>
      </div>
    </div>
  </BasicModal>
</template>

<script lang="ts" setup>
import {ref, nextTick, watch, onUnmounted, onMounted} from 'vue';
import {BasicModal, useModalInner} from '@/components/Modal';
import {useMessage} from '@/hooks/web/useMessage';
import {
  Empty as AEmpty, 
  Spin as ASpin, 
  Button as AButton,
  Switch as ASwitch,
  Select as ASelect,
  SelectOption as ASelectOption,
  Badge as ABadge
} from 'ant-design-vue';
import {
  ReloadOutlined,
  ClearOutlined,
  VerticalAlignBottomOutlined,
  FileTextOutlined
} from '@ant-design/icons-vue';
import {
  getTaskExtractorLogs,
  getTaskSorterLogs,
  getTaskPusherLogs,
  getTaskRealtimeLogs,
} from '@/api/device/algorithm_task';

defineOptions({ name: 'ServiceLogsModal' });

const {createMessage} = useMessage();

const loading = ref(false);
const logs = ref('');
const logsContentRef = ref();
const logParams = ref<{
  taskId?: number;
  serviceType?: string;
}>({});
const autoRefresh = ref(false);
const refreshInterval = ref(5);
const refreshTimer = ref<NodeJS.Timeout | null>(null);
const isScrolling = ref(false);

const [register, {closeModal}] = useModalInner(async (data) => {
  // 先清除之前的定时器
  if (refreshTimer.value) {
    clearInterval(refreshTimer.value);
    refreshTimer.value = null;
  }
  
  if (data) {
    logs.value = data.logs || '';
    logParams.value = {
      taskId: data.taskId,
      serviceType: data.serviceType,
    };
    
    // 重置滚动状态，确保打开时滚动到底部
    isScrolling.value = false;
    
    // 如果有参数，自动加载日志
    if (data.taskId && data.serviceType && !data.logs) {
      await loadLogs(data.taskId, data.serviceType);
    }
    
    // 确保滚动到底部
    await nextTick();
    setTimeout(() => {
      scrollToBottom();
    }, 100);
    
    // 如果有有效的参数，自动开启自动刷新
    if (data.taskId && data.serviceType) {
      autoRefresh.value = true;
      startAutoRefresh();
    }
  }
});

const loadLogs = async (taskId: number, serviceType: string) => {
  if (!taskId || !serviceType) return;
  
  try {
    loading.value = true;
    let logsResponse;
    
    if (serviceType === 'realtime' || serviceType === 'snap') {
      // 抓拍算法任务也使用 realtime 日志接口
      logsResponse = await getTaskRealtimeLogs(taskId, { lines: 500 });
    } else if (serviceType === 'extractor') {
      logsResponse = await getTaskExtractorLogs(taskId, { lines: 500 });
    } else if (serviceType === 'sorter') {
      logsResponse = await getTaskSorterLogs(taskId, { lines: 500 });
    } else if (serviceType === 'pusher') {
      logsResponse = await getTaskPusherLogs(taskId, { lines: 500 });
    } else {
      return;
    }
    
    // 响应转换器会将 data.data 直接返回，所以 logsResponse 就是 data.data 的内容
    // 如果 logsResponse 有 code 字段，说明是完整响应对象；否则就是转换后的 data.data
    if (logsResponse && typeof logsResponse === 'object') {
      if ('code' in logsResponse) {
        // 完整响应对象
        if (logsResponse.code === 0 && logsResponse.data) {
          logs.value = logsResponse.data.logs || '';
        } else {
          logs.value = `获取日志失败: ${logsResponse.msg || '未知错误'}`;
        }
      } else if ('logs' in logsResponse) {
        // 转换后的 data.data 对象，直接包含 logs 字段
        logs.value = logsResponse.logs || '';
      } else {
        logs.value = '获取日志失败: 响应数据格式错误';
      }
      
      // 只有在用户没有手动滚动时才自动滚动到底部
      if (logs.value && !isScrolling.value) {
        await nextTick();
        // 使用 setTimeout 确保 DOM 更新完成后再滚动
        setTimeout(() => {
          scrollToBottom();
        }, 50);
      }
    } else {
      logs.value = '获取日志失败: 响应数据格式错误';
    }
  } catch (error) {
    console.error('获取日志失败', error);
    createMessage.error('获取日志失败');
    logs.value = '';
  } finally {
    loading.value = false;
  }
};

const handleRefresh = async () => {
  if (logParams.value.taskId && logParams.value.serviceType) {
    await loadLogs(logParams.value.taskId, logParams.value.serviceType);
  }
};

const handleClear = () => {
  logs.value = '';
  createMessage.success('已清空显示');
};

const handleClose = () => {
  // 关闭时清除定时器
  if (refreshTimer.value) {
    clearInterval(refreshTimer.value);
    refreshTimer.value = null;
  }
  closeModal();
};

const scrollToBottom = () => {
  if (logsContentRef.value) {
    logsContentRef.value.scrollTop = logsContentRef.value.scrollHeight;
  }
};

const handleScrollToBottom = () => {
  scrollToBottom();
  createMessage.success('已滚动到底部');
};

const handleAutoRefreshChange = (checked: boolean) => {
  if (checked) {
    startAutoRefresh();
  } else {
    stopAutoRefresh();
  }
};

const handleIntervalChange = () => {
  if (autoRefresh.value) {
    stopAutoRefresh();
    startAutoRefresh();
  }
};

const startAutoRefresh = () => {
  if (refreshTimer.value) {
    clearInterval(refreshTimer.value);
  }
  refreshTimer.value = setInterval(() => {
    if (logParams.value.taskId && logParams.value.serviceType) {
      loadLogs(logParams.value.taskId, logParams.value.serviceType);
    }
  }, refreshInterval.value * 1000);
};

const stopAutoRefresh = () => {
  if (refreshTimer.value) {
    clearInterval(refreshTimer.value);
    refreshTimer.value = null;
  }
};

// 监听滚动事件，判断用户是否手动滚动
const handleScroll = () => {
  if (!logsContentRef.value) return;
  const {scrollTop, scrollHeight, clientHeight} = logsContentRef.value;
  // 如果滚动位置不在底部附近（留10px的误差），则认为用户手动滚动了
  isScrolling.value = scrollTop < scrollHeight - clientHeight - 10;
};

// 监听日志变化，如果用户在底部附近，自动滚动到底部
watch(logs, () => {
  nextTick(() => {
    if (logsContentRef.value && !isScrolling.value) {
      scrollToBottom();
    }
  });
});

// 组件挂载时初始化滚动监听
onMounted(() => {
  if (logsContentRef.value) {
    logsContentRef.value.addEventListener('scroll', handleScroll);
  }
});

// 组件卸载时清除定时器和事件监听
onUnmounted(() => {
  if (refreshTimer.value) {
    clearInterval(refreshTimer.value);
  }
  if (logsContentRef.value) {
    logsContentRef.value.removeEventListener('scroll', handleScroll);
  }
});
</script>

<style lang="less" scoped>
.logs-container {
  display: flex;
  flex-direction: column;
  height: 70vh;
  max-height: 700px;
  min-height: 550px;
  position: relative;
  overflow: hidden; // 防止整个容器滚动
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
  flex-shrink: 0; // 防止 header 被压缩

  .logs-header-left {
    display: flex;
    align-items: center;
    gap: 8px;

    .logs-title {
      font-weight: 500;
      font-size: 14px;
      color: #262626;
    }
  }

  .logs-header-right {
    display: flex;
    align-items: center;
    gap: 8px;
  }
}

.logs-content-wrapper {
  flex: 1;
  min-height: 0; // 允许 flex 子元素收缩
  display: flex;
  flex-direction: column;
  overflow: hidden; // 防止 wrapper 滚动
  
  // 确保 a-spin 组件不影响布局
  :deep(.ant-spin-nested-loading) {
    flex: 1;
    min-height: 0;
    display: flex;
    flex-direction: column;
  }
  
  :deep(.ant-spin-container) {
    flex: 1;
    min-height: 0;
    display: flex;
    flex-direction: column;
  }
}

.logs-content {
  flex: 1;
  overflow-y: auto;
  overflow-x: auto;
  background: #f5f5f5;
  border: 1px solid #d9d9d9;
  border-radius: 4px;
  position: relative;
  min-height: 0; // 允许 flex 子元素收缩

  &::-webkit-scrollbar {
    width: 8px;
    height: 8px;
  }

  &::-webkit-scrollbar-track {
    background: #fafafa;
    border-radius: 4px;
  }

  &::-webkit-scrollbar-thumb {
    background: #bfbfbf;
    border-radius: 4px;

    &:hover {
      background: #999;
    }
  }

  // 空状态时使用 flex 布局居中
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
      color: inherit;
      
      // 日志行高亮
      :deep(span) {
        display: block;
        padding: 2px 0;
        
        &:hover {
          background: rgba(0, 0, 0, 0.04);
        }
      }
    }
  }

  // 空状态样式
  :deep(.ant-empty) {
    margin: 0;
    
    .ant-empty-description {
      color: #8c8c8c;
    }
  }
}

.logs-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 12px;
  padding: 12px 0;
  border-top: 1px solid #e8e8e8;
  flex-shrink: 0; // 防止 footer 被压缩
  position: relative; // 确保 footer 在正常文档流中
  z-index: 10; // 确保 footer 在最上层
  background: #fff; // 确保 footer 有背景色，不会被内容遮挡

  .logs-footer-left {
    display: flex;
    gap: 8px;
  }

  .logs-footer-right {
    display: flex;
    gap: 8px;
  }
}

// 响应式设计
@media (max-width: 768px) {
  .logs-container {
    height: 65vh;
    max-height: 600px;
    min-height: 500px;
  }

  .logs-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;

    .logs-header-right {
      width: 100%;
      justify-content: space-between;
    }
  }

  .logs-footer {
    flex-direction: column;
    gap: 8px;

    .logs-footer-left,
    .logs-footer-right {
      width: 100%;
      justify-content: center;
    }
  }
}
</style>

