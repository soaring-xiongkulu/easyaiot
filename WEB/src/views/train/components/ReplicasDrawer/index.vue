<template>
  <BasicDrawer
    v-bind="$attrs"
    @register="registerDrawer"
    title="模型实例"
    width="1300"
  >
    <!-- 集群访问接口 -->
    <div class="cluster-endpoint-container" v-if="clusterEndpointUrl">
      <!-- 提示信息Alert -->
      <Alert
        type="warning"
        class="cluster-endpoint-tip-alert"
        :show-icon="false"
      >
        <template #message>
          <div class="cluster-endpoint-tip">
            <span class="tip-icon">🎉</span>
            <span class="tip-text">请自行前往模型推理页面，可快速验证该集群实例的推理性能与响应能力，支持实时测试模型推理效果<span class="tip-icon">✨</span></span>
          </div>
        </template>
      </Alert>
      
      <!-- 模型服务Alert -->
      <Alert
        type="info"
        class="cluster-endpoint-service-alert"
        :show-icon="false"
      >
        <template #message>
          <div class="cluster-endpoint-row" @click="handleTestCluster">
            <span class="cluster-endpoint-label">模型服务:</span>
            <div class="cluster-endpoint-value">
              <span class="endpoint-text" :title="clusterEndpointUrl">
                {{ clusterEndpointUrl }}<span class="click-hint">👈</span>
              </span>
            </div>
          </div>
        </template>
      </Alert>
    </div>
    <BasicTable
      @register="registerTable"
      :row-key="'id'"
    >
      <template #bodyCell="{ column, record }">
        <template v-if="column.dataIndex === 'status'">
          <Tag :color="getStatusColor(record.status)">
            {{ getStatusText(record.status) }}
          </Tag>
        </template>
        <template v-if="column.dataIndex === 'inference_endpoint'">
          <div style="display: flex; align-items: center; gap: 8px;">
            <span style="flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
              {{ record.inference_endpoint || '--' }}
            </span>
            <Icon 
              icon="tdesign:copy-filled" 
              class="copy-icon-endpoint"
              @click="handleCopyEndpoint(record.inference_endpoint)"
            />
          </div>
        </template>
        <template v-if="column.dataIndex === 'deploy_time'">
          {{ formatDateTime(record.deploy_time) }}
        </template>
        <template v-if="column.dataIndex === 'action'">
          <TableAction
            :actions="[
              {
                icon: 'mdi:play-outline',
                tooltip: { title: '启动', placement: 'top' },
                onClick: () => handleStart(record),
                disabled: record.status === 'running',
                style: 'color: #52c41a; padding: 0 8px; font-size: 16px;'
              },
              {
                icon: 'mdi:stop-outline',
                tooltip: { title: '停止', placement: 'top' },
                onClick: () => handleStop(record),
                disabled: record.status !== 'running',
                style: 'color: #ff4d4f; padding: 0 8px; font-size: 16px;'
              },
              {
                icon: 'mdi:restart',
                tooltip: { title: '重启', placement: 'top' },
                onClick: () => handleRestart(record),
                disabled: record.status !== 'running',
                style: 'color: #1890ff; padding: 0 8px; font-size: 16px;'
              },
              {
                icon: 'mdi:file-document-outline',
                tooltip: { title: '查看日志', placement: 'top' },
                onClick: () => handleViewLogs(record),
                style: 'color: #1890ff; padding: 0 8px; font-size: 16px;'
              }
            ]"
            :action-style="{
              display: 'flex',
              flexWrap: 'nowrap',
              gap: '4px',
              alignItems: 'center',
              marginRight: '0'
            }"
          />
        </template>
      </template>
    </BasicTable>
    <ServiceLogsModal
      v-if="showLogsModal"
      @register="registerLogsModal"
      @close="handleLogsModalClose"
    />
  </BasicDrawer>
</template>

<script lang="ts" setup>
import {nextTick, ref} from 'vue';
import {BasicDrawer, useDrawerInner} from '@/components/Drawer';
import type {DrawerProps} from '@/components/Drawer/src/typing';
import {BasicTable, TableAction, useTable} from '@/components/Table';
import {Tag, Alert} from 'ant-design-vue';
import {useMessage} from '@/hooks/web/useMessage';
import {useGlobSetting} from '@/hooks/setting';
import {Icon} from '@/components/Icon';
import {useModal} from '@/components/Modal';
import {
  startDeployService,
  stopDeployService,
  restartDeployService,
  getDeployServiceReplicas
} from '@/api/device/model';
import ServiceLogsModal from '../ServiceLogsModal/ServiceLogsModal.vue';

defineOptions({name: 'ReplicasDrawer'});

const {createMessage} = useMessage();
const globSetting = useGlobSetting();
const showLogsModal = ref(false);
const serviceNameRef = ref<string>('');
const modelIdRef = ref<number | null>(null);
const clusterEndpointUrl = ref<string>('');

// 获取集群访问接口URL
const getClusterEndpointUrl = (modelId: number) => {
  if (!modelId) return '';
  return `/model/cluster/${modelId}/inference/run`;
};

const [registerDrawer, {setDrawerProps, closeDrawer}] = useDrawerInner((data) => {
  // 保存服务名称和模型ID
  if (data && data.serviceName) {
    serviceNameRef.value = data.serviceName;
    // 如果有传入的model_id，使用它；否则等待从API获取
    if (data.modelId) {
      modelIdRef.value = data.modelId;
      clusterEndpointUrl.value = getClusterEndpointUrl(data.modelId);
    } else {
      modelIdRef.value = null;
      clusterEndpointUrl.value = '';
    }
  } else if (data && data.replicas) {
    // 兼容旧版本：如果传入的是replicas数组，使用前端分页
    serviceNameRef.value = '';
    // 从第一个副本获取model_id
    if (Array.isArray(data.replicas) && data.replicas.length > 0 && data.replicas[0].model_id) {
      modelIdRef.value = data.replicas[0].model_id;
      clusterEndpointUrl.value = getClusterEndpointUrl(data.replicas[0].model_id);
    } else {
      modelIdRef.value = null;
      clusterEndpointUrl.value = '';
    }
  }
  
  // 刷新表格数据
  nextTick(() => {
    reload();
  });
});

const [registerLogsModal, {
  openModal: openServiceLogsModal,
  closeModal: closeServiceLogsModal
}] = useModal();

// 表格列定义
const columns = [
  {
    title: 'ID',
    dataIndex: 'id',
    width: 80,
  },
  {
    title: '服务器IP',
    dataIndex: 'server_ip',
    width: 120,
  },
  {
    title: '端口',
    dataIndex: 'port',
    width: 80,
  },
  {
    title: '推理接口',
    dataIndex: 'inference_endpoint',
    width: 280,
    ellipsis: true,
  },
  {
    title: '状态',
    dataIndex: 'status',
    width: 100,
  },
  {
    title: 'MAC地址',
    dataIndex: 'mac_address',
    width: 150,
  },
  {
    title: '进程ID',
    dataIndex: 'process_id',
    width: 100,
  },
  {
    title: '部署时间',
    dataIndex: 'deploy_time',
    width: 180,
  },
  {
    title: '操作',
    dataIndex: 'action',
    width: 150,
    fixed: 'right',
  },
];

const [registerTable, {reload, setTableData}] = useTable({
  title: '',
  columns: columns,
  useSearchForm: false,
  showTableSetting: true,
  api: async (params) => {
    // 如果使用后端分页（有serviceName）
    if (serviceNameRef.value) {
      const pageNo = params.pageNo || params.page || 1;
      const pageSize = params.pageSize || 10;
      // 调用API，传递分页参数
      const response = await getDeployServiceReplicas(serviceNameRef.value, pageNo, pageSize);
      const result = response?.data || response;
      if (result && result.code === 0) {
        const records = Array.isArray(result.data) ? result.data : [];
        // 从第一个记录获取model_id（如果还没有设置）
        if (records.length > 0 && records[0].model_id && !modelIdRef.value) {
          modelIdRef.value = records[0].model_id;
          clusterEndpointUrl.value = getClusterEndpointUrl(records[0].model_id);
        }
        return {
          data: records,
          total: result.total || 0,
        };
      }
      return { data: [], total: 0 };
    }
    // 兼容旧版本：前端分页（如果没有serviceName，返回空数据）
    return { data: [], total: 0 };
  },
  pagination: {
    pageSize: 10,
    showSizeChanger: true,
    pageSizeOptions: ['10', '20', '50', '100'],
    showTotal: (total) => `共 ${total} 条`,
  },
  canResize: true,
  showIndexColumn: false,
  immediate: false,
  fetchSetting: {
    listField: 'data',
    totalField: 'total',
  },
});

// 状态相关
const getStatusColor = (status) => {
  const colorMap = {
    'running': 'green',
    'stopped': 'default',
    'error': 'red',
    'offline': 'orange'
  };
  return colorMap[status] || 'default';
};

const getStatusText = (status) => {
  const textMap = {
    'running': '运行中',
    'stopped': '已停止',
    'error': '错误',
    'offline': '离线'
  };
  return textMap[status] || status;
};

// 格式化时间
const formatDateTime = (dateString: string) => {
  if (!dateString || dateString === '--') return '--';
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

// 启动服务
const handleStart = async (record) => {
  try {
    const response = await startDeployService(record.id);
    // 检查响应中是否有警告标记
    if (response && (response as any).warning) {
      // 显示警告信息（模型下载失败但服务记录已创建）
      const warningMsg = (response as any).msg || '模型文件下载失败，请检查模型文件路径和MinIO配置';
      createMessage.warning(warningMsg);
    } else {
      createMessage.success('服务启动成功');
    }
    emit('refresh');
    reload();
  } catch (error: any) {
    const errorMsg = error?.response?.data?.msg || error?.message || '服务启动失败';
    createMessage.error(errorMsg);
    console.error('服务启动失败:', error);
  }
};

// 停止服务
const handleStop = async (record) => {
  try {
    await stopDeployService(record.id);
    createMessage.success('服务停止成功');
    emit('refresh');
    reload();
  } catch (error) {
    createMessage.error('服务停止失败');
    console.error('服务停止失败:', error);
  }
};

// 重启服务
const handleRestart = async (record) => {
  try {
    await restartDeployService(record.id);
    createMessage.success('服务重启成功');
    emit('refresh');
    reload();
  } catch (error) {
    createMessage.error('服务重启失败');
    console.error('服务重启失败:', error);
  }
};

// 查看日志
const handleViewLogs = (record) => {
  showLogsModal.value = true;
  nextTick(() => {
    openServiceLogsModal(true, {record});
  });
};

const handleLogsModalClose = () => {
  showLogsModal.value = false;
};

// 复制推理接口
const handleCopyEndpoint = async (endpoint: string) => {
  if (!endpoint || endpoint === '--') {
    createMessage.warning('推理接口为空，无法复制');
    return;
  }
  
  try {
    if (navigator.clipboard) {
      await navigator.clipboard.writeText(endpoint);
      createMessage.success('推理接口已复制到剪贴板');
    } else {
      // 降级方案
      const textArea = document.createElement('textarea');
      textArea.value = endpoint;
      textArea.style.position = 'fixed';
      textArea.style.opacity = '0';
      document.body.appendChild(textArea);
      textArea.select();
      try {
        document.execCommand('copy');
        createMessage.success('推理接口已复制到剪贴板');
      } catch (err) {
        createMessage.error('复制失败，请手动复制');
      }
      document.body.removeChild(textArea);
    }
  } catch (error) {
    createMessage.error('复制失败');
    console.error('复制失败:', error);
  }
};

// 复制模型服务地址
const handleTestCluster = async () => {
  if (!clusterEndpointUrl.value) {
    createMessage.warning('模型服务地址为空，无法复制');
    return;
  }
  
  // 获取完整的URL
  const apiUrl = globSetting.apiUrl || window.location.origin;
  const baseUrl = apiUrl.replace(/\/$/, '');
  const fullUrl = `${baseUrl}${clusterEndpointUrl.value}`;
  
  try {
    if (navigator.clipboard) {
      await navigator.clipboard.writeText(fullUrl);
      createMessage.success('模型服务地址已复制到剪贴板');
    } else {
      // 降级方案
      const textArea = document.createElement('textarea');
      textArea.value = fullUrl;
      textArea.style.position = 'fixed';
      textArea.style.opacity = '0';
      document.body.appendChild(textArea);
      textArea.select();
      try {
        document.execCommand('copy');
        createMessage.success('模型服务地址已复制到剪贴板');
      } catch (err) {
        createMessage.error('复制失败，请手动复制');
      }
      document.body.removeChild(textArea);
    }
  } catch (error) {
    createMessage.error('复制失败');
    console.error('复制失败:', error);
  }
};

const emit = defineEmits(['refresh']);
</script>

<style lang="less" scoped>
.copy-icon-endpoint {
  cursor: pointer;
  color: #1890ff;
  font-size: 16px;
  flex-shrink: 0;
  transition: all 0.2s;
  
  &:hover {
    color: #40a9ff;
    transform: scale(1.1);
  }
  
  &:active {
    color: #096dd9;
    transform: scale(0.95);
  }
}

.cluster-endpoint-container {
  margin-bottom: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.cluster-endpoint-tip-alert {
  :deep(.ant-alert-message) {
    margin: 0;
    padding: 0;
  }

  :deep(.ant-alert-content) {
    margin: 0;
  }

  :deep(.ant-alert) {
    background: linear-gradient(135deg, #fffbe6 0%, #fff7d9 100%);
    border: 2px solid #faad14;
    border-radius: 8px;
    padding: 14px 16px;
    box-shadow: 0 2px 8px rgba(250, 173, 20, 0.15);
  }

  .cluster-endpoint-tip {
    display: flex;
    align-items: center;
    gap: 10px;
    width: 100%;

    .tip-icon {
      font-size: 18px;
      flex-shrink: 0;
      animation: sparkle 2s ease-in-out infinite;
      
      &:first-child {
        margin-right: 0;
      }
    }

    .tip-text {
      flex: 1;
      font-size: 14px;
      color: #ad6800;
      line-height: 1.6;
      font-weight: 400;
      
      .tip-icon {
        margin-left: 4px;
        display: inline-block;
        vertical-align: middle;
      }
    }
  }
}

.cluster-endpoint-service-alert {
  :deep(.ant-alert-message) {
    margin: 0;
    padding: 0;
  }

  :deep(.ant-alert-content) {
    margin: 0;
  }

  :deep(.ant-alert) {
    background: linear-gradient(135deg, #e6f4ff 0%, #bae7ff 100%);
    border: 2px solid #1890ff;
    border-radius: 8px;
    padding: 16px 18px;
    box-shadow: 0 2px 8px rgba(24, 144, 255, 0.15);
    transition: all 0.3s;

    &:hover {
      border-color: #40a9ff;
      box-shadow: 0 4px 12px rgba(24, 144, 255, 0.25);
      transform: translateY(-1px);
    }
  }

  .cluster-endpoint-row {
    display: flex;
    align-items: center;
    gap: 12px;
    min-width: 0;
    width: 100%;
    cursor: pointer;
  }

  .cluster-endpoint-label {
    font-size: 16px;
    color: #8c8c8c;
    font-weight: 600;
    flex-shrink: 0;
  }

  .cluster-endpoint-value {
    flex: 1;
    min-width: 0;
    transition: all 0.2s;

    .endpoint-text {
      font-size: 16px;
      font-weight: 600;
      color: #1890ff;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
      font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
      min-width: 0;
      
      .click-hint {
        margin-left: 4px;
        font-size: 18px;
        display: inline-block;
        vertical-align: middle;
        transition: transform 0.2s;
        animation: pointLeft 0.6s ease-in-out infinite;
      }
    }
  }
}

@keyframes pointLeft {
  0%, 100% {
    transform: translateX(0);
  }
  50% {
    transform: translateX(-4px);
  }
}

@keyframes sparkle {
  0%, 100% {
    transform: scale(1) rotate(0deg);
    opacity: 1;
  }
  50% {
    transform: scale(1.2) rotate(10deg);
    opacity: 0.8;
  }
}
</style>

