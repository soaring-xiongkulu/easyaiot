<template>
  <div class="directory-manage-wrapper">
    <div class="directory-layout">
      <!-- 左侧：目录树 -->
      <div class="directory-sidebar">
        <div class="sidebar-tree">
          <div class="tree-header">
            <div class="tree-header-button">
              <a-button type="primary" @click="handleAddDirectory">
                <template #icon>
                  <PlusOutlined />
                </template>
                添加目录
              </a-button>
            </div>
            <a-input
              v-model:value="directorySearchText"
              placeholder="请输入目录名称"
              allow-clear
              style="margin-top: 12px;"
            >
              <template #prefix>
                <Icon icon="ant-design:search-outlined" />
              </template>
            </a-input>
          </div>
          <div class="tree-content">
            <div
              v-for="dir in filteredDirectoryTree"
              :key="dir.id"
              class="tree-node"
            >
              <DirectoryTreeNode
                :directory="dir"
                :level="0"
                :expanded-keys="expandedKeys"
                :selected-id="selectedDirectoryId"
                @toggle="handleToggleNode"
                @select="handleSelectDirectory"
                @edit="handleEditDirectory"
                @delete="handleDeleteDirectory"
              />
            </div>
            <a-empty v-if="filteredDirectoryTree.length === 0" description="暂无目录" />
          </div>
        </div>
      </div>

      <!-- 右侧：设备列表 -->
      <div class="device-content">
        <div class="device-button-group">
          <a-button type="primary" @click="handleAddDevice" :disabled="!selectedDirectoryId">
            <template #icon>
              <PlusOutlined />
            </template>
            添加摄像头
          </a-button>
        </div>
        <BasicTable @register="registerTable">
          <template #bodyCell="{ column, record }">
            <!-- 统一复制功能组件 -->
            <template
              v-if="['id', 'name', 'model'].includes(column.key)">
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
import { ref, onMounted, computed } from 'vue';
import { useMessage } from '@/hooks/web/useMessage';
import { useModal } from '@/components/Modal';
import { BasicTable, TableAction, useTable } from '@/components/Table';
import { Icon } from '@/components/Icon';
import { Tag as ATag, Input as AInput, Empty as AEmpty } from 'ant-design-vue';
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
import DirectoryTreeNode from './DirectoryTreeNode.vue';
import {
  PlusOutlined,
} from '@ant-design/icons-vue';

const { createMessage } = useMessage();
const [registerDirectoryModal, { openModal: openDirectoryModal }] = useModal();
const [registerAddModal, { openModal: openAddModal }] = useModal();

// 目录相关
const selectedDirectoryId = ref<number | null>(null);
const selectedDirectoryName = ref<string>('');
const directoryTree = ref<DeviceDirectory[]>([]);
const expandedKeys = ref<Set<number>>(new Set());
const directorySearchText = ref<string>('');

// 设备流状态映射
const deviceStreamStatuses = ref<Record<string, string>>({});

// 过滤目录树（根据搜索文本）
const filteredDirectoryTree = computed(() => {
  if (!directorySearchText.value) {
    return directoryTree.value;
  }
  
  const searchLower = directorySearchText.value.toLowerCase();
  
  const filterTree = (nodes: DeviceDirectory[]): DeviceDirectory[] => {
    return nodes
      .map(node => {
        const matches = node.name.toLowerCase().includes(searchLower);
        const filteredChildren = node.children ? filterTree(node.children) : [];
        
        if (matches || filteredChildren.length > 0) {
          return {
            ...node,
            children: filteredChildren.length > 0 ? filteredChildren : node.children,
          };
        }
        return null;
      })
      .filter((node): node is DeviceDirectory => node !== null);
  };
  
  return filterTree(directoryTree.value);
});

// 加载目录列表
const loadDirectoryList = async () => {
  try {
    const response = await getDirectoryList();
    const data = response.code !== undefined ? response.data : response;
    
    if (data && Array.isArray(data)) {
      directoryTree.value = data;
      // 默认只展开一级目录（不自动展开）
      expandedKeys.value = new Set();
    } else {
      directoryTree.value = [];
    }
  } catch (error) {
    console.error('加载目录列表失败', error);
    directoryTree.value = [];
  }
};

// 切换节点展开/折叠（手风琴效果）
const handleToggleNode = (directoryId: number, level: number) => {
  const newExpandedKeys = new Set(expandedKeys.value);
  
  if (newExpandedKeys.has(directoryId)) {
    // 折叠：移除当前节点及其所有子节点
    newExpandedKeys.delete(directoryId);
    removeChildrenKeys(directoryId, newExpandedKeys);
  } else {
    // 展开：如果是同一级的其他节点已展开，先折叠它们（手风琴效果）
    if (level === 0) {
      // 一级目录：折叠所有其他一级目录
      directoryTree.value.forEach(dir => {
        if (dir.id !== directoryId && newExpandedKeys.has(dir.id)) {
          newExpandedKeys.delete(dir.id);
          removeChildrenKeys(dir.id, newExpandedKeys);
        }
      });
    } else {
      // 二级或三级目录：找到同级节点并折叠
      const parent = findParentDirectory(directoryId, directoryTree.value);
      if (parent) {
        const siblings = parent.children || [];
        siblings.forEach(sibling => {
          if (sibling.id !== directoryId && newExpandedKeys.has(sibling.id)) {
            newExpandedKeys.delete(sibling.id);
            removeChildrenKeys(sibling.id, newExpandedKeys);
          }
        });
      }
    }
    
    // 展开当前节点
    newExpandedKeys.add(directoryId);
  }
  
  expandedKeys.value = newExpandedKeys;
};

// 移除节点的所有子节点的展开状态
const removeChildrenKeys = (parentId: number, keys: Set<number>) => {
  // 递归查找并移除所有子节点的展开状态
  const removeFromNode = (node: DeviceDirectory) => {
    if (node.children && node.children.length > 0) {
      node.children.forEach(child => {
        keys.delete(child.id);
        removeFromNode(child);
      });
    }
  };
  
  // 查找目标节点
  const findNode = (nodes: DeviceDirectory[], targetId: number): DeviceDirectory | null => {
    for (const node of nodes) {
      if (node.id === targetId) {
        return node;
      }
      if (node.children && node.children.length > 0) {
        const found = findNode(node.children, targetId);
        if (found) {
          return found;
        }
      }
    }
    return null;
  };
  
  const targetNode = findNode(directoryTree.value, parentId);
  if (targetNode) {
    removeFromNode(targetNode);
  }
};

// 查找父目录
const findParentDirectory = (childId: number, nodes: DeviceDirectory[]): DeviceDirectory | null => {
  for (const node of nodes) {
    if (node.children) {
      const found = node.children.find(child => child.id === childId);
      if (found) {
        return node;
      }
      const parent = findParentDirectory(childId, node.children);
      if (parent) {
        return parent;
      }
    }
  }
  return null;
};

// 选择目录
const handleSelectDirectory = (directory: DeviceDirectory) => {
  selectedDirectoryId.value = directory.id;
  selectedDirectoryName.value = directory.name;
  reloadDeviceTable();
};

// 编辑目录
const handleEditDirectory = (directory: DeviceDirectory) => {
  openDirectoryModal(true, {
    type: 'edit',
    record: directory,
  });
};

// 删除目录
const handleDeleteDirectory = async (directory: DeviceDirectory) => {
  try {
    const response = await deleteDirectory(directory.id);
    const result = response.code !== undefined ? response : { code: 0, msg: '删除成功' };
    if (result.code === 0) {
      createMessage.success('删除成功');
      loadDirectoryList();
      // 如果删除的是当前选中的目录，清空选择
      if (selectedDirectoryId.value === directory.id) {
        selectedDirectoryId.value = null;
        selectedDirectoryName.value = '';
        reloadDeviceTable();
      }
      // 移除展开状态
      expandedKeys.value.delete(directory.id);
    } else {
      createMessage.error(result.msg || '删除失败');
    }
  } catch (error) {
    console.error('删除目录失败', error);
    createMessage.error('删除失败');
  }
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
        name: params.name || '',
        online: params.online !== undefined ? params.online : undefined,
        model: params.model || '',
      });
      
      const data = response.code !== undefined ? response.data : response;
      const total = response.code !== undefined ? response.total : (Array.isArray(data) ? data.length : 0);
      
      if (data && Array.isArray(data)) {
        // 应用筛选条件
        let filteredData = data;
        
        if (params.name) {
          filteredData = filteredData.filter((device: DeviceInfo) => 
            device.name && device.name.toLowerCase().includes(params.name.toLowerCase())
          );
        }
        
        if (params.online !== undefined && params.online !== '') {
          filteredData = filteredData.filter((device: DeviceInfo) => 
            device.online === params.online
          );
        }
        
        if (params.model) {
          filteredData = filteredData.filter((device: DeviceInfo) => 
            device.model && device.model.toLowerCase().includes(params.model.toLowerCase())
          );
        }
        
        // 初始化设备流状态
        const devicesWithStatus = filteredData.map((device: DeviceInfo) => {
          if (!deviceStreamStatuses.value[device.id]) {
            deviceStreamStatuses.value[device.id] = 'unknown';
          }
          return {
            ...device,
            stream_status: deviceStreamStatuses.value[device.id] || 'unknown',
          };
        });
        
        // 检查设备流状态
        checkAllDevicesStreamStatus(filteredData);
        
        return {
          data: devicesWithStatus,
          total: devicesWithStatus.length,
        };
      }
      return { data: [], total: 0 };
    } catch (error) {
      console.error('加载设备列表失败', error);
      return { data: [], total: 0 };
    }
  },
  fetchSetting: {
    listField: 'data',
    totalField: 'total',
  },
  columns: getDeviceColumns(),
  useSearchForm: true,
  formConfig: {
    labelWidth: 80,
    baseColProps: { span: 6 },
    actionColOptions: {
      span: 6,
      style: { textAlign: 'right' }
    },
    schemas: [
      {
        field: 'name',
        label: '设备名称',
        component: 'Input',
        componentProps: {
          placeholder: '请输入设备名称',
        },
      },
      {
        field: 'online',
        label: '在线状态',
        component: 'Select',
        componentProps: {
          placeholder: '请选择在线状态',
          allowClear: true,
          options: [
            { label: '在线', value: true },
            { label: '离线', value: false },
          ],
        },
      },
      {
        field: 'model',
        label: '设备型号',
        component: 'Input',
        componentProps: {
          placeholder: '请输入设备型号',
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

// 添加目录
const handleAddDirectory = () => {
  openDirectoryModal(true, {
    type: 'create',
  });
};

// 添加摄像头
const handleAddDevice = () => {
  if (!selectedDirectoryId.value) {
    createMessage.warning('请先选择目录');
    return;
  }
  openAddModal(true, {
    defaultType: 'device',
    defaultParentId: selectedDirectoryId.value,
  });
};

// 目录操作成功回调
const handleDirectorySuccess = () => {
  loadDirectoryList();
  if (selectedDirectoryId.value) {
    reloadDeviceTable();
  }
};

// 添加成功回调
const handleSuccess = () => {
  loadDirectoryList();
  if (selectedDirectoryId.value) {
    reloadDeviceTable();
  }
};

// 暴露事件
const emit = defineEmits(['view', 'edit', 'delete', 'play', 'toggleStream']);

// 暴露刷新方法
defineExpose({
  refresh: () => {
    loadDirectoryList();
    if (selectedDirectoryId.value) {
      reloadDeviceTable();
    }
  },
});

// 组件挂载时加载目录列表
onMounted(() => {
  loadDirectoryList();
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
  flex-shrink: 0;
  background: #fff;
  border-radius: 4px;
  display: flex;
  flex-direction: column;
  overflow: hidden;

  .sidebar-tree {
    flex: 1;
    overflow: hidden;
    display: flex;
    flex-direction: column;
    padding: 16px;
    
    .tree-header {
      margin-bottom: 16px;
      
      .tree-header-button {
        display: flex;
        justify-content: flex-end;
      }
    }
    
    .tree-content {
      flex: 1;
      overflow-y: auto;
      overflow-x: hidden;
      
      .tree-node {
        margin-bottom: 0;
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
}

.device-button-group {
  margin-bottom: 16px;
  display: flex;
  justify-content: flex-end;
}
</style>
