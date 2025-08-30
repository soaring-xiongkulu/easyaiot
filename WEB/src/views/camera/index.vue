<template>
  <div class="camera-container">
    <BasicTable @register="registerTable">
      <template #toolbar>
        <a-button type="primary" @click="handleScanOnvif">
          <template #icon><ScanOutlined /></template>
          扫描局域网ONVIF设备
        </a-button>
        <a-button @click="openAddModal('source')">
          <template #icon><VideoCameraAddOutlined /></template>
          新增视频源设备
        </a-button>
        <a-button @click="openAddModal('nvr')">
          <template #icon><ClusterOutlined /></template>
          新增NVR设备
        </a-button>
        <a-button @click="handleUpdateOnvifDevice">
          <template #icon><SyncOutlined /></template>
          更新ONVIF设备
        </a-button>
      </template>

      <template #bodyCell="{ column, record }">
        <!-- 统一复制功能组件 -->
        <template v-if="['id', 'name', 'model', 'source', 'rtmp_stream', 'http_stream'].includes(column.key)">
          <span style="cursor: pointer" @click="handleCopy(record[column.key])"><Icon
            icon="tdesign:copy-filled" color="#4287FCFF"/> {{ record[column.key] }}</span>
        </template>
        <template v-else-if="column.dataIndex === 'action'">
          <TableAction
            :actions="getTableActions(record)"
          />
        </template>
      </template>
    </BasicTable>

    <VideoModal @register="registerAddModel" @success="handleSuccess"/>
  </div>
</template>

<script lang="ts" setup>
import {reactive} from 'vue';
import {BasicTable, TableAction, useTable} from '@/components/Table';
import {useMessage} from '@/hooks/web/useMessage';
import {getBasicColumns, getFormConfig} from "./Data";
import {useModal} from "@/components/Modal";
import VideoModal from "./VideoModal/index.vue";
import {deleteDevice, getDeviceList, refreshDevices} from '@/api/device/camera';
import {
  ClusterOutlined,
  ScanOutlined,
  SyncOutlined,
  VideoCameraAddOutlined
} from '@ant-design/icons-vue';

const { createMessage } = useMessage();
const [registerAddModel, { openModal }] = useModal();

const state = reactive({
  boxIp: '',
});

const [registerTable, { reload }] = useTable({
  canResize: true,
  showIndexColumn: false,
  title: '摄像头列表',
  api: getDeviceList,
  columns: getBasicColumns(),
  useSearchForm: true,
  showTableSetting: false,
  pagination: true,
  formConfig: getFormConfig(),
  fetchSetting: {
    listField: 'data',
    totalField: 'total',
  },
  rowKey: 'id',
});

const getTableActions = (record) => [
  {
    icon: 'ant-design:eye-filled',
    tooltip: '详情',
    onClick: () => openAddModal('view', record)
  },
  {
    icon: 'ant-design:edit-filled',
    tooltip: '编辑',
    onClick: () => openAddModal('edit', record)
  },
  {
    icon: 'material-symbols:delete-outline-rounded',
    tooltip: '删除',
    popConfirm: {
      title: '确定删除此设备？',
      confirm: () => handleDelete(record)
    }
  }
];

async function handleCopy(record: object) {
  if (navigator.clipboard) {
    await navigator.clipboard.writeText(record);
  } else {
    const textarea = document.createElement('textarea');
    textarea.value = record;
    document.body.appendChild(textarea);
    textarea.select();
    document.execCommand('copy');
    document.body.removeChild(textarea);
  }
  createMessage.success('复制成功');
}

// 打开模态框
const openAddModal = (type, record = null) => {
  openModal(true, {
    type,
    record,
    isEdit: type === 'edit',
    isView: type === 'view'
  });
};

// 扫描ONVIF设备
const handleScanOnvif = () => {
  openAddModal('onvif');
};

// 刷新数据
const handleSuccess = () => {
  reload();
};

// 删除设备
const handleDelete = async (record) => {
  try {
    await deleteDevice(record.id); // 使用新的deleteDevice API
    createMessage.success('删除成功');
    handleSuccess();
  } catch (error) {
    console.error('删除失败', error);
    createMessage.error('删除失败');
  }
};

// 更新ONVIF设备
const handleUpdateOnvifDevice = async () => {
  try {
    await refreshDevices(); // 使用新的refreshDevices API
    createMessage.success('ONVIF设备更新成功');
    handleSuccess();
  } catch (error) {
    console.error('ONVIF设备更新失败', error);
    createMessage.error('ONVIF设备更新失败');
  }
};
</script>

<style scoped>
.camera-container {
  padding: 16px;
}
</style>
