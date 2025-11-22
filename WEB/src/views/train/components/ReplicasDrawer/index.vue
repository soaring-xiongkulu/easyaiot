<template>
  <BasicDrawer
    v-bind="$attrs"
    @register="registerDrawer"
    title="模型实例"
    width="1300"
  >
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
import {Tag} from 'ant-design-vue';
import {useMessage} from '@/hooks/web/useMessage';
import {Icon} from '@/components/Icon';
import {useModal} from '@/components/Modal';
import {
  startDeployService,
  stopDeployService,
  restartDeployService
} from '@/api/device/model';
import ServiceLogsModal from '../ServiceLogsModal/ServiceLogsModal.vue';

defineOptions({name: 'ReplicasDrawer'});

const {createMessage} = useMessage();
const showLogsModal = ref(false);
const replicasData = ref<any[]>([]);

const [registerDrawer, {setDrawerProps, closeDrawer}] = useDrawerInner((data) => {
  // 重置数据
  replicasData.value = [];
  
  // 如果有传入的副本数据，则设置
  if (data && data.replicas && Array.isArray(data.replicas)) {
    replicasData.value = data.replicas;
  }
  
  // 更新表格数据（在 nextTick 中确保表格已注册）
  nextTick(() => {
    setTableData(replicasData.value);
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
  pagination: false,
  canResize: true,
  showIndexColumn: false,
  immediate: false,
  dataSource: [],
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
    await startDeployService(record.id);
    createMessage.success('服务启动成功');
    emit('refresh');
    reload();
  } catch (error) {
    createMessage.error('服务启动失败');
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
</style>

