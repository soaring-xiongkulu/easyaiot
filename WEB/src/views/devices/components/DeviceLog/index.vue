<template>
  <div class="device-log-container">
    <!-- 左侧筛选条件 -->
    <div class="filter-panel">
      <div class="filter-header">
        <h3>筛选条件</h3>
      </div>
      <div class="filter-content">
        <div class="filter-item">
          <label>操作类型</label>
          <Select
            v-model:value="filterForm.actionType"
            placeholder="全部"
            allowClear
            @change="handleFilterChange"
          >
            <SelectOption value="ADD">新增</SelectOption>
            <SelectOption value="UPDATE">更新</SelectOption>
            <SelectOption value="DELETE">删除</SelectOption>
            <SelectOption value="QUERY">查询</SelectOption>
            <SelectOption value="LOGIN">登录</SelectOption>
            <SelectOption value="LOGOUT">登出</SelectOption>
          </Select>
        </div>
        <div class="filter-item">
          <label>操作人</label>
          <Input
            v-model:value="filterForm.userName"
            placeholder="请输入操作人"
            allowClear
            @pressEnter="handleFilterChange"
          />
        </div>
        <div class="filter-item">
          <label>操作结果</label>
          <Select
            v-model:value="filterForm.status"
            placeholder="全部"
            allowClear
            @change="handleFilterChange"
          >
            <SelectOption value="SUCCESS">成功</SelectOption>
            <SelectOption value="FAILED">失败</SelectOption>
          </Select>
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
          <span>设备日志</span>
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
            <div class="log-meta-row">
              <Tag :color="getActionTypeColor(log.actionType)">
                {{ getActionTypeText(log.actionType) }}
              </Tag>
              <Tag :color="getStatusColor(log.status)">
                {{ getStatusText(log.status) }}
              </Tag>
            </div>
            <div class="log-content-text">
              <div class="content-label">操作内容：</div>
              <pre>{{ formatLogContent(log) }}</pre>
            </div>
            <div class="log-info">
              <span>操作人: {{ log.userName || '--' }}</span>
              <span>IP地址: {{ log.ipAddress || '--' }}</span>
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
import { getLog } from '@/api/device/entity-views';
import moment from 'moment';
import { Button, Input, Select, SelectOption, Tag, DatePicker } from 'ant-design-vue';
import { Icon } from '@/components/Icon';
import { useMessage } from '@/hooks/web/useMessage';

const { RangePicker } = DatePicker;

defineOptions({ name: 'DeviceLog' });

const route = useRoute();
const { createMessage } = useMessage();

// 获取设备ID
const deviceId = computed(() => route.params?.id as string);

// 筛选表单
const filterForm = reactive({
  actionType: undefined,
  userName: undefined,
  status: undefined,
  timeRange: undefined,
});

// 日志列表
const logList = ref<any[]>([]);
const loading = ref(false);
const logContainerRef = ref<HTMLElement | null>(null);

// 获取设备日志数据
const fetchDeviceLogData = async () => {
  loading.value = true;
  try {
    const params: any = {
      page: 1,
      pageSize: 1000, // 获取更多数据用于展示
    };

    if (filterForm.actionType) {
      params.actionType = filterForm.actionType;
    }
    if (filterForm.userName) {
      params.userName = filterForm.userName;
    }
    if (filterForm.status) {
      params.status = filterForm.status;
    }
    if (filterForm.timeRange && filterForm.timeRange.length === 2) {
      params.startTime = moment(filterForm.timeRange[0]).format('YYYY-MM-DD HH:mm:ss');
      params.endTime = moment(filterForm.timeRange[1]).format('YYYY-MM-DD HH:mm:ss');
    }

    const response = await getLog({
      module: 'DEVICE',
      id: deviceId.value,
      params,
    });
    
    const data = response?.data || response?.list || [];
    
    // 按时间倒序排序（最新的在第一条）
    logList.value = data.sort((a, b) => {
      const timeA = moment(a.createTime).valueOf();
      const timeB = moment(b.createTime).valueOf();
      return timeB - timeA;
    });
  } catch (error) {
    console.error('获取设备日志数据失败:', error);
    createMessage.error('获取设备日志失败');
    logList.value = [];
  } finally {
    loading.value = false;
  }
};

// 筛选变化处理
const handleFilterChange = () => {
  fetchDeviceLogData();
};

// 重置筛选
const handleReset = () => {
  filterForm.actionType = undefined;
  filterForm.userName = undefined;
  filterForm.status = undefined;
  filterForm.timeRange = undefined;
  fetchDeviceLogData();
};

// 刷新日志
const refreshLogs = () => {
  fetchDeviceLogData();
};

// 格式化时间
const formatTime = (time: string) => {
  if (!time) return '--';
  return moment(time).format('YYYY-MM-DD HH:mm:ss');
};

// 格式化日志内容
const formatLogContent = (log: any) => {
  if (log.actionData) {
    if (typeof log.actionData === 'object') {
      return JSON.stringify(log.actionData, null, 2);
    }
    return log.actionData;
  }
  return '--';
};

// 获取操作类型文本
const getActionTypeText = (type: string) => {
  const typeMap: Record<string, string> = {
    ADD: '新增',
    UPDATE: '更新',
    DELETE: '删除',
    QUERY: '查询',
    LOGIN: '登录',
    LOGOUT: '登出',
  };
  return typeMap[type] || type || '--';
};

// 获取操作类型颜色
const getActionTypeColor = (type: string) => {
  const colorMap: Record<string, string> = {
    ADD: 'green',
    UPDATE: 'blue',
    DELETE: 'red',
    QUERY: 'cyan',
    LOGIN: 'purple',
    LOGOUT: 'orange',
  };
  return colorMap[type] || 'default';
};

// 获取状态文本
const getStatusText = (status: string) => {
  const statusMap: Record<string, string> = {
    SUCCESS: '成功',
    FAILED: '失败',
  };
  return statusMap[status] || status || '--';
};

// 获取状态颜色
const getStatusColor = (status: string) => {
  const colorMap: Record<string, string> = {
    SUCCESS: 'green',
    FAILED: 'red',
  };
  return colorMap[status] || 'default';
};

// 获取日志项样式类
const getLogItemClass = (log: any) => {
  return {
    'log-item-success': log.status === 'SUCCESS',
    'log-item-failed': log.status === 'FAILED',
  };
};

// 自动滚动到顶部（最新日志）
watch(logList, () => {
  if (logContainerRef.value) {
    logContainerRef.value.scrollTop = 0;
  }
}, { deep: true });

onMounted(() => {
  fetchDeviceLogData();
});
</script>

<style lang="less" scoped>
.device-log-container {
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

        &.log-item-success::before {
          background: #52c41a;
        }

        &.log-item-failed::before {
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

        .log-meta-row {
          display: flex;
          gap: 8px;
          margin-bottom: 10px;
        }

        .log-content-text {
          margin-bottom: 10px;

          .content-label {
            font-size: 12px;
            font-weight: 600;
            color: #595959;
            margin-bottom: 6px;
          }

          pre {
            margin: 0;
            background: #fafafa;
            border-radius: 2px;
            padding: 10px;
            border: 1px solid #f0f0f0;
            font-size: 12px;
            line-height: 1.6;
            color: #595959;
            white-space: pre-wrap;
            word-break: break-word;
            font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', 'Consolas', 'source-code-pro', monospace;
          }
        }

        .log-info {
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
