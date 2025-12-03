<template>
  <div class="service-status-tab">
    <a-spin :spinning="loading">
      <a-row :gutter="16">
        <!-- 抽帧器状态 -->
        <a-col :span="24" v-if="task.extractor_id">
          <a-card title="抽帧器状态" :bordered="false" class="service-card">
            <template #extra>
              <a-button type="link" @click="handleViewLogs('extractor')" :disabled="!task.extractor_id">
                <template #icon><FileTextOutlined /></template>
                查看日志
              </a-button>
            </template>
            <a-descriptions :column="2" bordered size="small">
              <a-descriptions-item label="抽帧器名称">
                {{ task.extractor_name || '--' }}
              </a-descriptions-item>
              <a-descriptions-item label="运行状态">
                <a-tag :color="getStatusColor(extractorStatus?.status)">
                  {{ getStatusText(extractorStatus?.status) }}
                </a-tag>
              </a-descriptions-item>
              <a-descriptions-item label="服务器IP">
                {{ extractorStatus?.server_ip || '--' }}
              </a-descriptions-item>
              <a-descriptions-item label="服务端口">
                {{ extractorStatus?.port || '--' }}
              </a-descriptions-item>
              <a-descriptions-item label="进程ID">
                {{ extractorStatus?.process_id || '--' }}
              </a-descriptions-item>
              <a-descriptions-item label="最后心跳时间">
                {{ formatTime(extractorStatus?.last_heartbeat) }}
              </a-descriptions-item>
            </a-descriptions>
          </a-card>
        </a-col>

        <!-- 排序器状态 -->
        <a-col :span="24" v-if="task.sorter_id">
          <a-card title="排序器状态" :bordered="false" class="service-card">
            <template #extra>
              <a-button type="link" @click="handleViewLogs('sorter')" :disabled="!task.sorter_id">
                <template #icon><FileTextOutlined /></template>
                查看日志
              </a-button>
            </template>
            <a-descriptions :column="2" bordered size="small">
              <a-descriptions-item label="排序器名称">
                {{ task.sorter_name || '--' }}
              </a-descriptions-item>
              <a-descriptions-item label="运行状态">
                <a-tag :color="getStatusColor(sorterStatus?.status)">
                  {{ getStatusText(sorterStatus?.status) }}
                </a-tag>
              </a-descriptions-item>
              <a-descriptions-item label="服务器IP">
                {{ sorterStatus?.server_ip || '--' }}
              </a-descriptions-item>
              <a-descriptions-item label="服务端口">
                {{ sorterStatus?.port || '--' }}
              </a-descriptions-item>
              <a-descriptions-item label="进程ID">
                {{ sorterStatus?.process_id || '--' }}
              </a-descriptions-item>
              <a-descriptions-item label="最后心跳时间">
                {{ formatTime(sorterStatus?.last_heartbeat) }}
              </a-descriptions-item>
            </a-descriptions>
          </a-card>
        </a-col>

        <!-- 推送器状态 -->
        <a-col :span="24" v-if="task.pusher_id">
          <a-card title="推送器状态" :bordered="false" class="service-card">
            <template #extra>
              <a-button type="link" @click="handleViewLogs('pusher')" :disabled="!task.pusher_id">
                <template #icon><FileTextOutlined /></template>
                查看日志
              </a-button>
            </template>
            <a-descriptions :column="2" bordered size="small">
              <a-descriptions-item label="推送器名称">
                {{ task.pusher_name || '--' }}
              </a-descriptions-item>
              <a-descriptions-item label="运行状态">
                <a-tag :color="getStatusColor(pusherStatus?.status)">
                  {{ getStatusText(pusherStatus?.status) }}
                </a-tag>
              </a-descriptions-item>
              <a-descriptions-item label="服务器IP">
                {{ pusherStatus?.server_ip || '--' }}
              </a-descriptions-item>
              <a-descriptions-item label="服务端口">
                {{ pusherStatus?.port || '--' }}
              </a-descriptions-item>
              <a-descriptions-item label="进程ID">
                {{ pusherStatus?.process_id || '--' }}
              </a-descriptions-item>
              <a-descriptions-item label="最后心跳时间">
                {{ formatTime(pusherStatus?.last_heartbeat) }}
              </a-descriptions-item>
            </a-descriptions>
          </a-card>
        </a-col>

        <!-- 无服务提示 -->
        <a-col :span="24" v-if="!task.extractor_id && !task.sorter_id && !task.pusher_id">
          <a-empty description="该算法任务未配置抽帧器、排序器或推送器" />
        </a-col>
      </a-row>
    </a-spin>

    <!-- 日志查看模态框 -->
    <ServiceLogsModal @register="registerLogsModal" />
  </div>
</template>

<script lang="ts" setup>
import { ref, watch, onMounted } from 'vue';
import { Card, Descriptions, DescriptionsItem, Tag, Button, Spin, Row, Col, Empty } from 'ant-design-vue';
import { FileTextOutlined } from '@ant-design/icons-vue';
import { useModal } from '@/components/Modal';
import { 
  getAlgorithmTask, 
  getTaskServicesStatus,
  getTaskExtractorLogs, 
  getTaskSorterLogs, 
  getTaskPusherLogs 
} from '@/api/device/algorithm_task';
import type { AlgorithmTask, FrameExtractor, Sorter, Pusher } from '@/api/device/algorithm_task';
import moment from 'moment';
import ServiceLogsModal from './ServiceLogsModal.vue';

defineOptions({ name: 'ServiceStatusTab' });

const props = defineProps<{
  task: AlgorithmTask;
}>();

const loading = ref(false);
const extractorStatus = ref<FrameExtractor | null>(null);
const sorterStatus = ref<Sorter | null>(null);
const pusherStatus = ref<Pusher | null>(null);

const [registerLogsModal, { openModal: openLogsModal }] = useModal();

// 加载服务状态
const loadServiceStatus = async () => {
  if (!props.task?.id) return;
  
  try {
    loading.value = true;
    const response = await getTaskServicesStatus(props.task.id);
    
    // 处理响应
    let statusData: any = null;
    if (response && typeof response === 'object' && 'code' in response) {
      // 完整响应对象
      if (response.code === 0 && response.data) {
        statusData = response.data;
      }
    } else {
      // 直接返回的数据对象（响应转换器已处理）
      statusData = response;
    }
    
    if (statusData) {
      extractorStatus.value = statusData.extractor || null;
      sorterStatus.value = statusData.sorter || null;
      pusherStatus.value = statusData.pusher || null;
    }
  } catch (error) {
    console.error('加载服务状态失败', error);
  } finally {
    loading.value = false;
  }
};

// 查看日志
const handleViewLogs = async (type: 'extractor' | 'sorter' | 'pusher') => {
  if (!props.task?.id) return;
  
  try {
    let logsResponse;
    let title = '';
    
    switch (type) {
      case 'extractor':
        logsResponse = await getTaskExtractorLogs(props.task.id, { lines: 500 });
        title = `${props.task.extractor_name || '抽帧器'} - 日志`;
        break;
      case 'sorter':
        logsResponse = await getTaskSorterLogs(props.task.id, { lines: 500 });
        title = `${props.task.sorter_name || '排序器'} - 日志`;
        break;
      case 'pusher':
        logsResponse = await getTaskPusherLogs(props.task.id, { lines: 500 });
        title = `${props.task.pusher_name || '推送器'} - 日志`;
        break;
    }
    
    if (logsResponse.code === 0 && logsResponse.data) {
      openLogsModal(true, {
        title,
        logs: logsResponse.data.logs,
        autoRefresh: false,
      });
    }
  } catch (error) {
    console.error('获取日志失败', error);
  }
};

// 获取状态颜色
const getStatusColor = (status?: string) => {
  switch (status) {
    case 'running':
      return 'green';
    case 'stopped':
      return 'default';
    case 'error':
      return 'red';
    default:
      return 'default';
  }
};

// 获取状态文本
const getStatusText = (status?: string) => {
  switch (status) {
    case 'running':
      return '运行中';
    case 'stopped':
      return '已停止';
    case 'error':
      return '错误';
    default:
      return '未知';
  }
};

// 格式化时间
const formatTime = (time?: string) => {
  if (!time) return '--';
  return moment(time).format('YYYY-MM-DD HH:mm:ss');
};

// 监听任务变化
watch(() => props.task, () => {
  if (props.task?.id) {
    loadServiceStatus();
  }
}, { immediate: true });

onMounted(() => {
  if (props.task?.id) {
    loadServiceStatus();
  }
});
</script>

<style lang="less" scoped>
.service-status-tab {
  padding: 16px;
}

.service-card {
  margin-bottom: 16px;
}
</style>

