<template>
  <BasicDrawer
    v-bind="$attrs"
    @register="register"
    :title="drawerTitle"
    width="1200px"
    :maskClosable="true"
  >
    <div class="service-manage-container">
      <a-spin :spinning="loading">
        <a-empty
          v-if="!loading && serviceList.length === 0"
          description="该算法任务未关联任何服务"
        />
        <a-table
          v-else
          :columns="columns"
          :data-source="serviceList"
          :pagination="false"
          :loading="loading"
          row-key="id"
        >
          <template #bodyCell="{ column, record }">
            <template v-if="column.dataIndex === 'service_name'">
              <div class="service-name-cell">
                <Icon :icon="getServiceIcon(record.service_type)" :size="20" />
                <span class="service-name">{{ record.service_name }}</span>
              </div>
            </template>
            <template v-else-if="column.dataIndex === 'status'">
              <a-tag :color="getStatusColor(record.status)">
                {{ getStatusText(record.status) }}
              </a-tag>
            </template>
            <template v-else-if="column.dataIndex === 'server_info'">
              <div class="server-info">
                <div v-if="record.server_ip">
                  <span class="label">服务器:</span>
                  <span>{{ record.server_ip }}</span>
                  <span v-if="record.port">:{{ record.port }}</span>
                </div>
                <div v-if="record.process_id">
                  <span class="label">进程ID:</span>
                  <span>{{ record.process_id }}</span>
                </div>
                <div v-if="record.last_heartbeat">
                  <span class="label">最后心跳:</span>
                  <span>{{ formatDateTime(record.last_heartbeat) }}</span>
                </div>
              </div>
            </template>
            <template v-else-if="column.dataIndex === 'action'">
              <div class="action-buttons">
                <a-button
                  type="link"
                  size="small"
                  @click="handleViewLogs(record)"
                  :disabled="!record.log_path"
                >
                  <template #icon>
                    <FileTextOutlined />
                  </template>
                  日志
                </a-button>
                <a-button
                  v-if="record.status === 'running'"
                  type="link"
                  size="small"
                  danger
                  @click="handleStop(record)"
                >
                  <template #icon>
                    <PauseCircleOutlined />
                  </template>
                  停止
                </a-button>
                <a-button
                  v-else
                  type="link"
                  size="small"
                  @click="handleStart(record)"
                >
                  <template #icon>
                    <PlayCircleOutlined />
                  </template>
                  启动
                </a-button>
              </div>
            </template>
          </template>
        </a-table>
      </a-spin>
    </div>

    <!-- 日志查看模态框 -->
    <ServiceLogsModal @register="registerLogsModal" />
  </BasicDrawer>
</template>

<script lang="ts" setup>
import { ref, computed } from 'vue';
import { BasicDrawer, useDrawerInner } from '@/components/Drawer';
import { Table, Tag, Button, Spin, Empty } from 'ant-design-vue';
import {
  FileTextOutlined,
  PauseCircleOutlined,
  PlayCircleOutlined,
} from '@ant-design/icons-vue';
import { Icon } from '@/components/Icon';
import { useMessage } from '@/hooks/web/useMessage';
import {
  getAlgorithmTask,
  getFrameExtractor,
  getSorter,
  getPusher,
  getTaskExtractorLogs,
  getTaskSorterLogs,
  getTaskPusherLogs,
  type AlgorithmTask,
  type FrameExtractor,
  type Sorter,
  type Pusher,
} from '@/api/device/algorithm_task';
import ServiceLogsModal from './ServiceLogsModal.vue';
import { useModal } from '@/components/Modal';

defineOptions({ name: 'ServiceManageDrawer' });

const { createMessage } = useMessage();
const [registerLogsModal, { openModal: openLogsModal }] = useModal();

const loading = ref(false);
const taskInfo = ref<AlgorithmTask | null>(null);
const extractorInfo = ref<FrameExtractor | null>(null);
const sorterInfo = ref<Sorter | null>(null);
const pusherInfo = ref<Pusher | null>(null);

const drawerTitle = computed(() => {
  return '帧管道管理器';
});

// 服务列表
const serviceList = computed(() => {
  const list: any[] = [];
  
  // 添加算法服务
  if (taskInfo.value && taskInfo.value.algorithm_services && Array.isArray(taskInfo.value.algorithm_services)) {
    taskInfo.value.algorithm_services.forEach((service: any) => {
      let server_ip: string | undefined;
      let port: string | undefined;
      
      // 尝试解析服务 URL
      if (service.service_url) {
        try {
          const url = new URL(service.service_url);
          server_ip = url.hostname;
          port = url.port || (url.protocol === 'https:' ? '443' : '80');
        } catch (e) {
          // URL 解析失败，尝试从字符串中提取
          const match = service.service_url.match(/https?:\/\/([^:]+)(?::(\d+))?/);
          if (match) {
            server_ip = match[1];
            port = match[2] || (service.service_url.includes('https') ? '443' : '80');
          }
        }
      }
      
      list.push({
        id: `algorithm_${service.id}`,
        service_type: 'algorithm',
        service_name: service.service_name || '算法服务',
        status: service.is_enabled ? 'running' : 'stopped',
        server_ip,
        port,
        process_id: undefined,
        last_heartbeat: undefined,
        log_path: undefined,
        raw_data: service,
      });
    });
  }
  
  if (extractorInfo.value) {
    list.push({
      id: `extractor_${extractorInfo.value.id}`,
      service_type: 'extractor',
      service_name: extractorInfo.value.extractor_name || '抽帧器',
      status: extractorInfo.value.status || 'stopped',
      server_ip: extractorInfo.value.server_ip,
      port: extractorInfo.value.port,
      process_id: extractorInfo.value.process_id,
      last_heartbeat: extractorInfo.value.last_heartbeat,
      log_path: extractorInfo.value.log_path,
      raw_data: extractorInfo.value,
    });
  }
  
  if (sorterInfo.value) {
    list.push({
      id: `sorter_${sorterInfo.value.id}`,
      service_type: 'sorter',
      service_name: sorterInfo.value.sorter_name || '排序器',
      status: sorterInfo.value.status || 'stopped',
      server_ip: sorterInfo.value.server_ip,
      port: sorterInfo.value.port,
      process_id: sorterInfo.value.process_id,
      last_heartbeat: sorterInfo.value.last_heartbeat,
      log_path: sorterInfo.value.log_path,
      raw_data: sorterInfo.value,
    });
  }
  
  if (pusherInfo.value) {
    list.push({
      id: `pusher_${pusherInfo.value.id}`,
      service_type: 'pusher',
      service_name: pusherInfo.value.pusher_name || '推送器',
      status: pusherInfo.value.status || 'stopped',
      server_ip: pusherInfo.value.server_ip,
      port: pusherInfo.value.port,
      process_id: pusherInfo.value.process_id,
      last_heartbeat: pusherInfo.value.last_heartbeat,
      log_path: pusherInfo.value.log_path,
      raw_data: pusherInfo.value,
    });
  }
  
  return list;
});

// 表格列定义
const columns = [
  {
    title: '服务名称',
    dataIndex: 'service_name',
    width: 150,
  },
  {
    title: '运行状态',
    dataIndex: 'status',
    width: 100,
  },
  {
    title: '服务器信息',
    dataIndex: 'server_info',
    width: 250,
  },
  {
    title: '操作',
    dataIndex: 'action',
    width: 200,
    fixed: 'right',
  },
];

// 获取服务图标
const getServiceIcon = (serviceType: string) => {
  const iconMap: Record<string, string> = {
    algorithm: 'ant-design:robot-outlined',
    extractor: 'ant-design:file-image-outlined',
    sorter: 'ant-design:sort-ascending-outlined',
    pusher: 'ant-design:send-outlined',
  };
  return iconMap[serviceType] || 'ant-design:appstore-outlined';
};

// 获取状态颜色
const getStatusColor = (status: string) => {
  const colorMap: Record<string, string> = {
    running: 'green',
    stopped: 'default',
    error: 'red',
  };
  return colorMap[status] || 'default';
};

// 获取状态文本
const getStatusText = (status: string) => {
  const textMap: Record<string, string> = {
    running: '运行中',
    stopped: '已停止',
    error: '错误',
  };
  return textMap[status] || status;
};

// 格式化时间
const formatDateTime = (dateString: string) => {
  if (!dateString) return '--';
  try {
    const date = new Date(dateString);
    if (isNaN(date.getTime())) {
      return dateString;
    }
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    const hours = String(date.getHours()).padStart(2, '0');
    const minutes = String(date.getMinutes()).padStart(2, '0');
    const seconds = String(date.getSeconds()).padStart(2, '0');
    return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`;
  } catch (e) {
    return dateString;
  }
};

// 加载服务信息
const loadServiceInfo = async (taskId: number) => {
  loading.value = true;
  try {
    // 获取任务详情
    // 注意：由于响应转换器在 isTransformResponse: true 时，如果 code === 0 且没有 total 字段，
    // 会直接返回 data.data（即任务对象本身），而不是包含 code 的完整响应
    const taskResponse = await getAlgorithmTask(taskId);
    
    // 检查返回的是完整响应对象还是直接的数据对象
    if (taskResponse && typeof taskResponse === 'object' && 'code' in taskResponse) {
      // 如果是完整响应对象（包含 code 字段）
      if (taskResponse.code !== 0) {
        createMessage.error(taskResponse.msg || '获取任务信息失败');
        return;
      }
      taskInfo.value = taskResponse.data;
    } else {
      // 如果直接返回的是数据对象（响应转换器已处理）
      taskInfo.value = taskResponse as AlgorithmTask;
    }
    
    // 并行获取三个服务的信息
    const promises: Promise<any>[] = [];
    
    if (taskInfo.value.extractor_id) {
      promises.push(
        getFrameExtractor(taskInfo.value.extractor_id).catch((err) => {
          console.error('获取抽帧器信息失败', err);
          return null;
        })
      );
    } else {
      promises.push(Promise.resolve(null));
    }
    
    if (taskInfo.value.sorter_id) {
      promises.push(
        getSorter(taskInfo.value.sorter_id).catch((err) => {
          console.error('获取排序器信息失败', err);
          return null;
        })
      );
    } else {
      promises.push(Promise.resolve(null));
    }
    
    if (taskInfo.value.pusher_id) {
      promises.push(
        getPusher(taskInfo.value.pusher_id).catch((err) => {
          console.error('获取推送器信息失败', err);
          return null;
        })
      );
    } else {
      promises.push(Promise.resolve(null));
    }
    
    const results = await Promise.all(promises);
    
    // 处理抽帧器响应
    if (results[0]) {
      if (results[0] && typeof results[0] === 'object' && 'code' in results[0]) {
        // 完整响应对象
        extractorInfo.value = results[0].code === 0 ? results[0].data : null;
      } else {
        // 直接返回的数据对象
        extractorInfo.value = results[0] as FrameExtractor;
      }
    } else {
      extractorInfo.value = null;
    }
    
    // 处理排序器响应
    if (results[1]) {
      if (results[1] && typeof results[1] === 'object' && 'code' in results[1]) {
        // 完整响应对象
        sorterInfo.value = results[1].code === 0 ? results[1].data : null;
      } else {
        // 直接返回的数据对象
        sorterInfo.value = results[1] as Sorter;
      }
    } else {
      sorterInfo.value = null;
    }
    
    // 处理推送器响应
    if (results[2]) {
      if (results[2] && typeof results[2] === 'object' && 'code' in results[2]) {
        // 完整响应对象
        pusherInfo.value = results[2].code === 0 ? results[2].data : null;
      } else {
        // 直接返回的数据对象
        pusherInfo.value = results[2] as Pusher;
      }
    } else {
      pusherInfo.value = null;
    }
  } catch (error) {
    console.error('加载服务信息失败', error);
    createMessage.error('加载服务信息失败');
  } finally {
    loading.value = false;
  }
};

// 查看日志
const handleViewLogs = async (record: any) => {
  if (!taskInfo.value) {
    createMessage.warning('任务信息不存在');
    return;
  }
  
  openLogsModal(true, {
    title: `${record.service_name} - 日志`,
    taskId: taskInfo.value.id,
    serviceType: record.service_type,
  });
};

// 启动服务
const handleStart = async (record: any) => {
  createMessage.warning('服务启动功能需要后端支持，当前暂未实现');
  // TODO: 实现服务启动功能
  // 这里需要调用后端API来启动对应的服务
  // 可能需要通过算法任务的启动来间接启动服务
};

// 停止服务
const handleStop = async (record: any) => {
  createMessage.warning('服务停止功能需要后端支持，当前暂未实现');
  // TODO: 实现服务停止功能
  // 这里需要调用后端API来停止对应的服务
  // 可能需要通过算法任务的停止来间接停止服务
};

// 注册抽屉
const [register] = useDrawerInner(async (data) => {
  // 重置状态
  taskInfo.value = null;
  extractorInfo.value = null;
  sorterInfo.value = null;
  pusherInfo.value = null;
  
  if (data && data.taskId) {
    await loadServiceInfo(data.taskId);
  }
});
</script>

<style lang="less" scoped>
.service-manage-container {
  padding: 16px;
  
  .service-name-cell {
    display: flex;
    align-items: center;
    gap: 8px;
    
    .service-name {
      font-weight: 500;
    }
  }
  
  .server-info {
    font-size: 12px;
    color: #666;
    
    .label {
      color: #999;
      margin-right: 4px;
    }
    
    > div {
      margin-bottom: 4px;
      
      &:last-child {
        margin-bottom: 0;
      }
    }
  }
  
  .action-buttons {
    display: flex;
    gap: 8px;
  }
}
</style>

