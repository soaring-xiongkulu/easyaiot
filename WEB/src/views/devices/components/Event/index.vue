<template>
  <div class="event-log-container">
    <!-- 左侧筛选条件 -->
    <div class="filter-panel">
      <div class="filter-header">
        <h3>筛选条件</h3>
      </div>
      <div class="filter-content">
        <div class="filter-item">
          <label>事件类型</label>
          <Select
            v-model:value="filterForm.eventType"
            placeholder="全部"
            allowClear
            @change="handleFilterChange"
          >
            <SelectOption value="INFO">信息</SelectOption>
            <SelectOption value="WARN">警告</SelectOption>
            <SelectOption value="ERROR">错误</SelectOption>
          </Select>
        </div>
        <div class="filter-item">
          <label>事件名称</label>
          <Input
            v-model:value="filterForm.eventName"
            placeholder="请输入事件名称"
            allowClear
            @pressEnter="handleFilterChange"
          />
        </div>
        <div class="filter-item">
          <label>时间范围</label>
          <RangePicker
            v-model:value="filterForm.timeRange"
            show-time
            format="YYYY-MM-DD HH:mm:ss"
            @change="handleFilterChange"
          />
        </div>
        <div class="filter-actions">
          <Button type="primary" @click="handleFilterChange" :loading="loading">
            查询
          </Button>
          <Button @click="handleReset">重置</Button>
        </div>
      </div>
    </div>

    <!-- 右侧日志展示 -->
    <div class="log-panel">
      <div class="log-header">
        <div class="log-title">
          <Icon icon="ant-design:file-text-outlined" />
          <span>事件日志</span>
        </div>
        <div class="log-actions">
          <Button size="small" @click="refreshLogs" :loading="loading">
            <Icon icon="ant-design:reload-outlined" />
            刷新
          </Button>
        </div>
      </div>
      <div class="log-content" ref="logContainerRef">
        <div v-if="logList.length === 0" class="empty-state">
          <Icon icon="ant-design:inbox-outlined" />
          <p>暂无日志数据</p>
        </div>
        <div v-else class="log-list">
          <div
            v-for="(log, index) in logList"
            :key="log.id || index"
            class="log-item"
            :class="getLogItemClass(log)"
          >
            <div class="log-time">
              <Icon icon="ant-design:clock-circle-outlined" />
              {{ formatTime(log.createTime) }}
            </div>
            <div class="log-type">
              <Tag :color="getEventTypeColor(log.eventType)">
                {{ getEventTypeText(log.eventType) }}
              </Tag>
            </div>
            <div class="log-name">
              <strong>{{ log.eventName || '--' }}</strong>
            </div>
            <div class="log-content-text">
              <pre>{{ formatLogContent(log) }}</pre>
            </div>
            <div class="log-meta">
              <span>设备标识: {{ log.deviceIdentification || '--' }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue';
import { useRoute } from 'vue-router';
import { getEventList } from '@/api/device/entity-views';
import moment from 'moment';
import { Button, Input, Select, SelectOption, Tag, DatePicker } from 'ant-design-vue';
import { Icon } from '@/components/Icon';
import { useMessage } from '@/hooks/web/useMessage';

const { RangePicker } = DatePicker;

defineOptions({ name: 'DeviceEvent' });

const route = useRoute();
const { createMessage } = useMessage();

// 获取设备ID
const deviceId = computed(() => route.params?.id as string);

// 筛选表单
const filterForm = reactive({
  eventType: undefined,
  eventName: undefined,
  timeRange: undefined,
});

// 日志列表
const logList = ref<any[]>([]);
const loading = ref(false);
const logContainerRef = ref<HTMLElement | null>(null);

// 获取事件日志数据
const fetchEventData = async () => {
  loading.value = true;
  try {
    const params: any = {
      deviceId: deviceId.value,
      page: 1,
      pageSize: 1000, // 获取更多数据用于展示
    };

    if (filterForm.eventType) {
      params.eventType = filterForm.eventType;
    }
    if (filterForm.eventName) {
      params.eventName = filterForm.eventName;
    }
    if (filterForm.timeRange && filterForm.timeRange.length === 2) {
      params.startTime = moment(filterForm.timeRange[0]).format('YYYY-MM-DD HH:mm:ss');
      params.endTime = moment(filterForm.timeRange[1]).format('YYYY-MM-DD HH:mm:ss');
    }

    const response = await getEventList(params);
    const data = response?.data || response?.list || [];
    
    // 按时间倒序排序（最新的在第一条）
    logList.value = data.sort((a, b) => {
      const timeA = moment(a.createTime).valueOf();
      const timeB = moment(b.createTime).valueOf();
      return timeB - timeA;
    });
  } catch (error) {
    console.error('获取事件日志数据失败:', error);
    createMessage.error('获取事件日志失败');
    logList.value = [];
  } finally {
    loading.value = false;
  }
};

// 筛选变化处理
const handleFilterChange = () => {
  fetchEventData();
};

// 重置筛选
const handleReset = () => {
  filterForm.eventType = undefined;
  filterForm.eventName = undefined;
  filterForm.timeRange = undefined;
  fetchEventData();
};

// 刷新日志
const refreshLogs = () => {
  fetchEventData();
};

// 格式化时间
const formatTime = (time: string) => {
  if (!time) return '--';
  return moment(time).format('YYYY-MM-DD HH:mm:ss');
};

// 格式化日志内容
const formatLogContent = (log: any) => {
  if (log.eventContent) {
    if (typeof log.eventContent === 'object') {
      return JSON.stringify(log.eventContent, null, 2);
    }
    return log.eventContent;
  }
  return '--';
};

// 获取事件类型文本
const getEventTypeText = (type: string) => {
  const typeMap: Record<string, string> = {
    INFO: '信息',
    WARN: '警告',
    ERROR: '错误',
  };
  return typeMap[type] || type || '--';
};

// 获取事件类型颜色
const getEventTypeColor = (type: string) => {
  const colorMap: Record<string, string> = {
    INFO: 'blue',
    WARN: 'orange',
    ERROR: 'red',
  };
  return colorMap[type] || 'default';
};

// 获取日志项样式类
const getLogItemClass = (log: any) => {
  return {
    'log-item-info': log.eventType === 'INFO',
    'log-item-warn': log.eventType === 'WARN',
    'log-item-error': log.eventType === 'ERROR',
  };
};

// 自动滚动到顶部（最新日志）
watch(logList, () => {
  if (logContainerRef.value) {
    logContainerRef.value.scrollTop = 0;
  }
}, { deep: true });

onMounted(() => {
  fetchEventData();
});
</script>

<style lang="less" scoped>
.event-log-container {
  display: flex;
  height: 100%;
  min-height: 500px;
  gap: 12px;
  background: transparent;

  // 左侧筛选面板
  .filter-panel {
    width: 300px;
    flex-shrink: 0;
    background: #ffffff;
    border-radius: 6px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
    border: 1px solid #f0f0f0;
    display: flex;
    flex-direction: column;
    align-self: flex-start;
    height: fit-content;
    max-height: calc(100vh - 200px);

    .filter-header {
      padding: 14px 18px;
      border-bottom: 1px solid #f5f5f5;
      background: linear-gradient(to bottom, #fafafa, #ffffff);

      h3 {
        margin: 0;
        font-size: 14px;
        font-weight: 600;
        color: #262626;
        display: flex;
        align-items: center;
        gap: 8px;
      }
    }

    .filter-content {
      padding: 18px;
      overflow-y: auto;

      .filter-item {
        margin-bottom: 18px;

        label {
          display: block;
          margin-bottom: 8px;
          font-size: 12px;
          font-weight: 500;
          color: #595959;
        }

        :deep(.ant-input),
        :deep(.ant-select-selector),
        :deep(.ant-picker) {
          border-radius: 6px;
          border-color: #e0e0e0;
          transition: all 0.3s ease;
          box-shadow: 0 1px 2px rgba(0, 0, 0, 0.02);

          &:hover {
            border-color: #40a9ff;
            box-shadow: 0 2px 4px rgba(64, 169, 255, 0.08);
          }

          &:focus,
          &.ant-picker-focused {
            border-color: #1890ff;
            box-shadow: 0 0 0 3px rgba(24, 144, 255, 0.08);
          }
        }

        :deep(.ant-input) {
          padding: 6px 12px;
          font-size: 13px;
        }

        :deep(.ant-select-selector) {
          padding: 4px 8px;
        }
      }

      .filter-actions {
        display: flex;
        gap: 10px;
        margin-top: 20px;

        :deep(.ant-btn) {
          flex: 1;
          border-radius: 6px;
          height: 36px;
          font-weight: 500;
          transition: all 0.3s ease;
          box-shadow: 0 2px 4px rgba(0, 0, 0, 0.04);

          &:hover {
            transform: translateY(-1px);
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.08);
          }

          &.ant-btn-primary {
            box-shadow: 0 2px 4px rgba(24, 144, 255, 0.2);

            &:hover {
              box-shadow: 0 4px 8px rgba(24, 144, 255, 0.3);
            }
          }
        }
      }
    }
  }

  // 右侧日志展示面板
  .log-panel {
    flex: 1;
    display: flex;
    flex-direction: column;
    background: #ffffff;
    border-radius: 6px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
    border: 1px solid #f0f0f0;
    overflow: hidden;
    min-height: 0;

    .log-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 12px 16px;
      border-bottom: 1px solid #e8e8e8;
      background: #fafafa;
      flex-shrink: 0;

      .log-title {
        display: flex;
        align-items: center;
        gap: 8px;
        font-size: 14px;
        font-weight: 600;
        color: #262626;

        :deep(.anticon) {
          font-size: 16px;
          color: #1890ff;
        }
      }

      .log-actions {
        :deep(.ant-btn) {
          border-radius: 2px;
        }
      }
    }

    .log-content {
      flex: 1;
      overflow-y: auto;
      padding: 16px;
      background: #ffffff;
      min-height: 0;

      &::-webkit-scrollbar {
        width: 8px;
      }

      &::-webkit-scrollbar-track {
        background: #f5f5f5;
      }

      &::-webkit-scrollbar-thumb {
        background: #d9d9d9;
        border-radius: 0;

        &:hover {
          background: #bfbfbf;
        }
      }

      .empty-state {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        height: 100%;
        min-height: 300px;
        color: #999;

        :deep(.anticon) {
          font-size: 48px;
          margin-bottom: 16px;
          opacity: 0.5;
        }

        p {
          margin: 0;
          font-size: 14px;
        }
      }

      .log-list {
        display: flex;
        flex-direction: column;
        gap: 12px;
      }

      .log-item {
        padding: 12px;
        background: #ffffff;
        border-radius: 2px;
        border: 1px solid #e8e8e8;
        transition: border-color 0.2s;
        position: relative;

        &::before {
          content: '';
          position: absolute;
          left: 0;
          top: 0;
          bottom: 0;
          width: 2px;
          background: #1890ff;
          opacity: 0;
          transition: opacity 0.2s;
        }

        &:hover {
          border-color: #1890ff;

          &::before {
            opacity: 1;
          }
        }

        &.log-item-info::before {
          background: #1890ff;
        }

        &.log-item-warn::before {
          background: #fa8c16;
        }

        &.log-item-error::before {
          background: #ff4d4f;
        }

        .log-time {
          display: flex;
          align-items: center;
          gap: 6px;
          font-size: 12px;
          color: #8c8c8c;
          margin-bottom: 8px;

          :deep(.anticon) {
            font-size: 14px;
          }
        }

        .log-type {
          margin-bottom: 8px;
        }

        .log-name {
          font-size: 13px;
          color: #262626;
          margin-bottom: 10px;

          strong {
            font-weight: 600;
          }
        }

        .log-content-text {
          background: #fafafa;
          border-radius: 2px;
          padding: 10px;
          margin-bottom: 10px;
          border: 1px solid #f0f0f0;

          pre {
            margin: 0;
            font-size: 12px;
            line-height: 1.6;
            color: #595959;
            white-space: pre-wrap;
            word-break: break-word;
            font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', 'Consolas', 'source-code-pro', monospace;
          }
        }

        .log-meta {
          display: flex;
          align-items: center;
          gap: 16px;
          font-size: 12px;
          color: #8c8c8c;
        }
      }
    }
  }
}
</style>
