<template>
  <div class="directory-manage-wrapper">
    <div class="directory-layout">
      <!-- 左侧：目录树 -->
      <div class="directory-sidebar">
        <div class="sidebar-header">
          <a-button type="primary" @click="handleAddDirectoryOrDevice" block>
            <template #icon>
              <PlusOutlined />
            </template>
            添加目录/摄像头
          </a-button>
        </div>
        <div class="sidebar-tree">
          <a-spin :spinning="treeLoading">
            <a-tree
              v-if="treeData.length > 0"
              v-model:expandedKeys="expandedKeys"
              v-model:selectedKeys="selectedKeys"
              :tree-data="treeData"
              :field-names="{ children: 'children', title: 'title', key: 'key' }"
              @select="handleTreeSelect"
              class="directory-tree"
            />
            <a-empty v-else description="暂无目录" />
          </a-spin>
        </div>
      </div>

      <!-- 右侧：设备列表 -->
      <div class="device-content">
        <BasicTable @register="registerTable">
          <template #toolbar>
            <span v-if="selectedDirectoryId" class="directory-title">
              当前目录：{{ selectedDirectoryName }}
            </span>
            <span v-else class="directory-title-empty">
              请选择左侧目录查看设备
            </span>
          </template>
          <template #bodyCell="{ column, record }">
            <!-- 统一复制功能组件 -->
            <template
              v-if="['id', 'name', 'model', 'source', 'rtmp_stream', 'http_stream'].includes(column.key)">
              <span style="cursor: pointer" @click="handleCopy(record[column.key])">
                <Icon icon="tdesign:copy-filled" color="#4287FCFF"/> {{ record[column.key] }}
              </span>
            </template>

            <!-- 在线状态显示 -->
            <template v-else-if="column.dataIndex === 'online'">
              <a-tag :color="record.online ? 'green' : 'red'">
                {{ record.online ? '在线' : '离线' }}
              </a-tag>
            </template>

            <!-- 流媒体状态显示 -->
            <template v-else-if="column.dataIndex === 'stream_status'">
              <a-tag :color="getStreamStatusColor(getDeviceStreamStatus(record.id))">
                {{ getStreamStatusText(getDeviceStreamStatus(record.id)) }}
              </a-tag>
            </template>

            <template v-else-if="column.dataIndex === 'action'">
              <TableAction :actions="getTableActions(record)" />
            </template>
          </template>
        </BasicTable>
      </div>
    </div>

    <!-- 添加目录/摄像头模态框 -->
    <AddDirectoryOrDeviceModal
      @register="registerAddModal"
      @success="handleSuccess"
    />
    
    <!-- 目录编辑/创建模态框 -->
    <DirectoryModal
      @register="registerDirectoryModal"
      @success="handleDirectorySuccess"
    />
  </div>
</template>

<script lang="ts" setup>
import { ref, reactive, computed, onMounted, h, watch } from 'vue';
import { useMessage } from '@/hooks/web/useMessage';
import { useModal } from '@/components/Modal';
import { BasicTable, TableAction, useTable } from '@/components/Table';
import { Icon } from '@/components/Icon';
import { Tree as ATree, Empty as AEmpty, Spin as ASpin, Tag as ATag } from 'ant-design-vue';
import {
  getDirectoryList,
  deleteDirectory,
  getDirectoryDevices,
  getDeviceList,
  getStreamStatus,
  startStreamForwarding,
  stopStreamForwarding,
  type DeviceDirectory,
  type DeviceInfo,
  type StreamStatusResponse,
} from '@/api/device/camera';
import DirectoryModal from './DirectoryModal.vue';
import AddDirectoryOrDeviceModal from './AddDirectoryOrDeviceModal.vue';
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  FolderOutlined,
} from '@ant-design/icons-vue';

const { createMessage } = useMessage();
const [registerDirectoryModal, { openModal: openDirectoryModal }] = useModal();
const [registerAddModal, { openModal: openAddModal }] = useModal();

// 目录树相关
const treeData = ref<any[]>([]);
const treeLoading = ref(false);
const expandedKeys = ref<string[]>([]);
const selectedKeys = ref<string[]>([]);
const selectedDirectoryId = ref<number | null>(null);
const selectedDirectoryName = ref<string>('');

// 设备流状态映射
const deviceStreamStatuses = ref<Record<string, string>>({});

// 将目录树转换为树形组件所需格式
const convertToTreeData = (directories: DeviceDirectory[]): any[] => {
  return directories.map((dir) => ({
    key: `dir_${dir.id}`,
    title: dir.name,
    directory: dir,
    children: dir.children && dir.children.length > 0 ? convertToTreeData(dir.children) : undefined,
    icon: () => h(FolderOutlined),
  }));
};

// 加载目录树
const loadDirectoryTree = async () => {
  try {
    treeLoading.value = true;
    const response = await getDirectoryList();
    const data = response.code !== undefined ? response.data : response;
    if (data && Array.isArray(data)) {
      treeData.value = convertToTreeData(data);
      // 默认展开第一层
      if (treeData.value.length > 0) {
        expandedKeys.value = treeData.value.map(item => item.key);
      }
    } else {
      treeData.value = [];
    }
  } catch (error) {
    console.error('加载目录树失败', error);
    treeData.value = [];
  } finally {
    treeLoading.value = false;
  }
};

// 树节点选择处理
const handleTreeSelect = (selectedKeysValue: string[], info: any) => {
  if (selectedKeysValue.length === 0) {
    selectedDirectoryId.value = null;
    selectedDirectoryName.value = '';
    // 清空设备列表
    if (registerTable) {
      reloadDeviceTable();
    }
    return;
  }

  const selectedKey = selectedKeysValue[0];
  if (selectedKey.startsWith('dir_')) {
    const directoryId = parseInt(selectedKey.replace('dir_', ''));
    const directory = findDirectoryById(treeData.value, directoryId);
    if (directory) {
      selectedDirectoryId.value = directoryId;
      selectedDirectoryName.value = directory.title;
      // 加载该目录下的设备
      reloadDeviceTable();
    }
  } else {
    // 如果选择的是设备节点，不做处理
    selectedDirectoryId.value = null;
    selectedDirectoryName.value = '';
    reloadDeviceTable();
  }
};

// 根据ID查找目录
const findDirectoryById = (tree: any[], id: number): any => {
  for (const node of tree) {
    if (node.key === `dir_${id}`) {
      return node;
    }
    if (node.children) {
      const found = findDirectoryById(node.children, id);
      if (found) return found;
    }
  }
  return null;
};

// 获取设备表格列配置
const getDeviceColumns = () => {
  return [
    {
      title: '设备ID',
      dataIndex: 'id',
      width: 120,
    },
    {
      title: '设备名称',
      dataIndex: 'name',
      width: 120,
    },
    {
      title: '设备型号',
      dataIndex: 'model',
      width: 120,
    },
    {
      title: '在线状态',
      dataIndex: 'online',
      width: 100,
    },
    {
      title: '制造商',
      dataIndex: 'manufacturer',
      width: 90,
    },
    {
      title: 'IP地址',
      dataIndex: 'ip',
      width: 120,
    },
    {
      title: '端口',
      dataIndex: 'port',
      width: 80,
    },
    {
      title: '拉流地址',
      dataIndex: 'source',
      width: 200,
    },
    {
      title: '推流地址',
      dataIndex: 'rtmp_stream',
      width: 200,
    },
    {
      title: '播放地址',
      dataIndex: 'http_stream',
      width: 200,
    },
    {
      title: '流状态',
      dataIndex: 'stream_status',
      width: 100,
    },
    {
      title: '操作',
      dataIndex: 'action',
      width: 200,
      fixed: 'right',
    },
  ];
};

// 设备表格配置
const [registerTable, { reload: reloadDeviceTable }] = useTable({
  title: '设备列表',
  api: async (params) => {
    // 如果没有选择目录，返回空数据
    if (!selectedDirectoryId.value) {
      return { data: [], total: 0 };
    }

    try {
      const response = await getDirectoryDevices(selectedDirectoryId.value, {
        pageNo: params.pageNo || 1,
        pageSize: params.pageSize || 10,
        search: params.search || '',
      });
      
      const data = response.code !== undefined ? response.data : response;
      const total = response.code !== undefined ? response.total : (Array.isArray(data) ? data.length : 0);
      
      if (data && Array.isArray(data)) {
        // 初始化设备流状态
        const devicesWithStatus = data.map((device: DeviceInfo) => {
          if (!deviceStreamStatuses.value[device.id]) {
            deviceStreamStatuses.value[device.id] = 'unknown';
          }
          return {
            ...device,
            stream_status: deviceStreamStatuses.value[device.id] || 'unknown',
          };
        });
        
        // 检查设备流状态
        checkAllDevicesStreamStatus(data);
        
        return {
          data: devicesWithStatus,
          total: total,
        };
      }
      return { data: [], total: 0 };
    } catch (error) {
      console.error('加载设备列表失败', error);
      return { data: [], total: 0 };
    }
  },
  columns: getDeviceColumns(),
  useSearchForm: true,
  formConfig: {
    labelWidth: 80,
    schemas: [
      {
        field: 'search',
        label: '搜索',
        component: 'Input',
        componentProps: {
          placeholder: '请输入设备名称或ID',
        },
      },
    ],
  },
  showTableSetting: true,
  pagination: true,
  rowKey: 'id',
  canResize: true,
});

// 获取流状态文本
const getStreamStatusText = (status: string) => {
  const statusMap: Record<string, string> = {
    'running': '运行中',
    'stopped': '已停止',
    'error': '错误',
    'unknown': '未知'
  };
  return statusMap[status] || status || '未知';
};

// 获取流状态颜色
const getStreamStatusColor = (status: string) => {
  const colorMap: Record<string, string> = {
    'running': 'green',
    'stopped': 'red',
    'error': 'orange',
    'unknown': 'default'
  };
  return colorMap[status] || 'default';
};

// 安全获取设备流状态
const getDeviceStreamStatus = (deviceId: string) => {
  if (!deviceStreamStatuses.value || !deviceStreamStatuses.value[deviceId]) {
    return 'unknown';
  }
  return deviceStreamStatuses.value[deviceId];
};

// 检查单个设备的流状态
const checkDeviceStreamStatus = async (deviceId: string) => {
  try {
    if (!deviceStreamStatuses.value) {
      deviceStreamStatuses.value = {};
    }
    const response: StreamStatusResponse = await getStreamStatus(deviceId);
    if (response.code === 0) {
      deviceStreamStatuses.value[deviceId] = response.data.status;
    } else {
      deviceStreamStatuses.value[deviceId] = 'error';
    }
  } catch (error) {
    console.error(`检查设备 ${deviceId} 流状态失败`, error);
    if (!deviceStreamStatuses.value) {
      deviceStreamStatuses.value = {};
    }
    deviceStreamStatuses.value[deviceId] = 'error';
  }
};

// 检查所有设备的流状态
const checkAllDevicesStreamStatus = async (devices: DeviceInfo[]) => {
  try {
    const deviceIds = devices.map(device => device.id);
    for (const deviceId of deviceIds) {
      await checkDeviceStreamStatus(deviceId);
    }
  } catch (error) {
    console.error('检查设备流状态失败', error);
  }
};

// 获取表格操作按钮
const getTableActions = (record: DeviceInfo) => {
  const currentStatus = (deviceStreamStatuses.value && deviceStreamStatuses.value[record.id]) || 'unknown';
  
  const actions = [
    {
      icon: 'octicon:play-16',
      tooltip: '播放RTMP流',
      onClick: () => handlePlay(record)
    },
    {
      icon: 'ant-design:eye-filled',
      tooltip: '详情',
      onClick: () => handleView(record)
    },
    {
      icon: 'ant-design:edit-filled',
      tooltip: '编辑',
      onClick: () => handleEdit(record)
    },
  ];

  // 根据流状态添加不同的操作按钮
  if (currentStatus === 'running') {
    actions.splice(1, 0, {
      icon: 'ant-design:pause-circle-outlined',
      tooltip: '停止RTSP转发',
      onClick: () => handleDisableRtsp(record)
    });
  } else {
    actions.splice(1, 0, {
      icon: 'ant-design:swap-outline',
      tooltip: '启用RTSP转发',
      onClick: () => handleEnableRtsp(record)
    });
  }

  actions.push({
    icon: 'material-symbols:delete-outline-rounded',
    tooltip: '删除',
    popConfirm: {
      title: '确定删除此设备？',
      confirm: () => handleDelete(record)
    }
  });

  return actions;
};

// 启用RTSP转发
const handleEnableRtsp = async (record: DeviceInfo) => {
  try {
    if (!deviceStreamStatuses.value) {
      deviceStreamStatuses.value = {};
    }
    createMessage.loading({content: '正在启动RTSP转发...', key: 'rtsp'});

    const response = await startStreamForwarding(record.id);
    if (response.code === 0) {
      createMessage.success({content: 'RTSP转发已启动', key: 'rtsp'});
      deviceStreamStatuses.value[record.id] = 'running';
      reloadDeviceTable();
    } else {
      createMessage.error({content: `启动失败: ${response.data?.msg || '未知错误'}`, key: 'rtsp'});
      deviceStreamStatuses.value[record.id] = 'error';
    }
  } catch (error) {
    console.error('启动RTSP转发失败', error);
    createMessage.error({content: '启动RTSP转发失败', key: 'rtsp'});
    if (!deviceStreamStatuses.value) {
      deviceStreamStatuses.value = {};
    }
    deviceStreamStatuses.value[record.id] = 'error';
  }
};

// 停止RTSP转发
const handleDisableRtsp = async (record: DeviceInfo) => {
  try {
    if (!deviceStreamStatuses.value) {
      deviceStreamStatuses.value = {};
    }
    createMessage.loading({content: '正在停止RTSP转发...', key: 'rtsp'});

    const response = await stopStreamForwarding(record.id);
    if (response.code === 0) {
      createMessage.success({content: 'RTSP转发已停止', key: 'rtsp'});
      deviceStreamStatuses.value[record.id] = 'stopped';
      reloadDeviceTable();
    } else {
      createMessage.error({content: `停止失败: ${response.data?.msg || '未知错误'}`, key: 'rtsp'});
      deviceStreamStatuses.value[record.id] = 'error';
    }
  } catch (error) {
    console.error('停止RTSP转发失败', error);
    createMessage.error({content: '停止RTSP转发失败', key: 'rtsp'});
    if (!deviceStreamStatuses.value) {
      deviceStreamStatuses.value = {};
    }
    deviceStreamStatuses.value[record.id] = 'error';
  }
};

// 播放
const handlePlay = (record: DeviceInfo) => {
  emit('play', record);
};

// 查看
const handleView = (record: DeviceInfo) => {
  emit('view', record);
};

// 编辑
const handleEdit = (record: DeviceInfo) => {
  emit('edit', record);
};

// 删除
const handleDelete = async (record: DeviceInfo) => {
  emit('delete', record);
};

// 复制功能
async function handleCopy(text: string) {
  if (!text || text === '-') {
    return;
  }
  try {
    if (navigator.clipboard) {
      await navigator.clipboard.writeText(text);
    } else {
      const textarea = document.createElement('textarea');
      textarea.value = text;
      document.body.appendChild(textarea);
      textarea.select();
      document.execCommand('copy');
      document.body.removeChild(textarea);
    }
    createMessage.success('复制成功');
  } catch (error) {
    console.error('复制失败', error);
    createMessage.error('复制失败');
  }
}

// 添加目录或摄像头
const handleAddDirectoryOrDevice = () => {
  openAddModal(true);
};

// 目录操作成功回调
const handleDirectorySuccess = () => {
  loadDirectoryTree();
};

// 添加成功回调
const handleSuccess = () => {
  loadDirectoryTree();
  // 如果当前有选中的目录，刷新设备列表
  if (selectedDirectoryId.value) {
    reloadDeviceTable();
  }
};

// 暴露事件
const emit = defineEmits(['view', 'edit', 'delete', 'play', 'toggleStream']);

// 暴露刷新方法
defineExpose({
  refresh: () => {
    loadDirectoryTree();
    if (selectedDirectoryId.value) {
      reloadDeviceTable();
    }
  },
});

// 组件挂载时加载目录树
onMounted(() => {
  loadDirectoryTree();
});
</script>

<style lang="less" scoped>
.directory-manage-wrapper {
  padding: 16px;
  background: #f0f2f5;
  min-height: calc(100vh - 200px);
  height: 100%;
}

.directory-layout {
  display: flex;
  gap: 16px;
  height: 100%;
}

.directory-sidebar {
  width: 300px;
  background: #fff;
  border-radius: 4px;
  display: flex;
  flex-direction: column;
  overflow: hidden;

  .sidebar-header {
    padding: 16px;
    border-bottom: 1px solid #f0f0f0;
  }

  .sidebar-tree {
    flex: 1;
    overflow-y: auto;
    padding: 8px;

    :deep(.directory-tree) {
      .ant-tree-node-content-wrapper {
        padding: 4px 8px;
      }
    }
  }
}

.device-content {
  flex: 1;
  background: #fff;
  border-radius: 4px;
  padding: 16px;
  overflow: hidden;
  display: flex;
  flex-direction: column;

  .directory-title {
    font-size: 16px;
    font-weight: 500;
    color: #1890ff;
  }

  .directory-title-empty {
    font-size: 14px;
    color: #999;
  }
}
</style>
