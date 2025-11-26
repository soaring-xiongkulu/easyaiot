<template>
  <div class="directory-manage-wrapper">
    <div class="directory-layout">
      <!-- 左侧目录树 -->
      <div class="directory-tree-panel">
        <div class="tree-header">
          <span class="title">设备目录</span>
          <a-button type="primary" size="small" @click="handleCreateDirectory(null)">
            <template #icon>
              <PlusOutlined />
            </template>
            新建目录
          </a-button>
        </div>
        <div class="tree-content">
          <a-spin :spinning="treeLoading">
            <a-tree
              v-if="directoryTree.length > 0"
              :tree-data="directoryTree"
              :selected-keys="selectedKeys"
              :expanded-keys="expandedKeys"
              :auto-expand-parent="autoExpandParent"
              @select="handleTreeSelect"
              @expand="handleTreeExpand"
              :block-node="true"
            >
              <template #title="{ title, key, dataRef }">
                <div class="tree-node-title">
                  <span class="node-name">{{ title }}</span>
                  <span class="node-info">
                    <a-tag size="small" color="blue">{{ dataRef.device_count || 0 }}个设备</a-tag>
                  </span>
                  <div class="node-actions" @click.stop>
                    <a-button
                      type="text"
                      size="small"
                      @click="handleCreateDirectory(dataRef.id)"
                      title="新建子目录"
                    >
                      <template #icon>
                        <FolderAddOutlined />
                      </template>
                    </a-button>
                    <a-button
                      type="text"
                      size="small"
                      @click="handleEditDirectory(dataRef)"
                      title="编辑"
                    >
                      <template #icon>
                        <EditOutlined />
                      </template>
                    </a-button>
                    <a-popconfirm
                      title="确定删除此目录吗？"
                      ok-text="确定"
                      cancel-text="取消"
                      @confirm="handleDeleteDirectory(dataRef.id)"
                    >
                      <a-button
                        type="text"
                        size="small"
                        danger
                        title="删除"
                      >
                        <template #icon>
                          <DeleteOutlined />
                        </template>
                      </a-button>
                    </a-popconfirm>
                  </div>
                </div>
              </template>
            </a-tree>
            <a-empty v-else description="暂无目录，请创建目录" />
          </a-spin>
        </div>
      </div>

      <!-- 右侧设备列表 -->
      <div class="device-list-panel">
        <div class="device-list-header">
          <span class="title">
            {{ currentDirectory ? `目录：${currentDirectory.name}` : '所有设备' }}
          </span>
          <div class="header-actions">
            <a-button @click="handleShowAllDevices">查看全部设备</a-button>
            <a-button type="primary" @click="handleMoveDevices" :disabled="!currentDirectory">
              移动设备到此目录
            </a-button>
          </div>
        </div>
        <div class="device-list-content">
          <VideoCardList
            ref="cardListRef"
            :api="getDeviceListApi"
            :params="deviceListParams"
            @view="handleView"
            @edit="handleEdit"
            @delete="handleDelete"
            @play="handlePlay"
            @toggleStream="handleToggleStream"
          />
        </div>
      </div>
    </div>

    <!-- 目录编辑/创建模态框 -->
    <DirectoryModal
      @register="registerDirectoryModal"
      @success="handleDirectorySuccess"
    />
  </div>
</template>

<script lang="ts" setup>
import { ref, reactive, computed, onMounted } from 'vue';
import { useMessage } from '@/hooks/web/useMessage';
import { useModal } from '@/components/Modal';
import {
  getDirectoryList,
  deleteDirectory,
  getDirectoryDevices,
  getDeviceList,
  type DeviceDirectory,
} from '@/api/device/camera';
import VideoCardList from '../VideoCardList/index.vue';
import DirectoryModal from './DirectoryModal.vue';
import {
  PlusOutlined,
  FolderAddOutlined,
  EditOutlined,
  DeleteOutlined,
} from '@ant-design/icons-vue';
import type { DeviceInfo } from '@/api/device/camera';

const { createMessage } = useMessage();
const [registerDirectoryModal, { openModal }] = useModal();

// 目录树相关
const directoryTree = ref<any[]>([]);
const treeLoading = ref(false);
const selectedKeys = ref<number[]>([]);
const expandedKeys = ref<number[]>([]);
const autoExpandParent = ref(true);
const currentDirectory = ref<DeviceDirectory | null>(null);

// 设备列表相关
const cardListRef = ref();
const deviceListParams = reactive({
  directory_id: null as number | null,
});

// 将目录数据转换为树形结构
const convertToTreeData = (directories: DeviceDirectory[]): any[] => {
  return directories.map((dir) => ({
    title: dir.name,
    key: dir.id,
    device_count: dir.device_count || 0,
    id: dir.id,
    parent_id: dir.parent_id,
    description: dir.description,
    sort_order: dir.sort_order,
    children: dir.children ? convertToTreeData(dir.children) : [],
  }));
};

// 加载目录树
const loadDirectoryTree = async () => {
  try {
    treeLoading.value = true;
    const response = await getDirectoryList();
    // API返回格式: { code: 0, data: [...], msg: 'success' }
    // 如果isTransformResponse=true，则返回data；如果false，则返回整个response
    const data = response.code !== undefined ? response.data : response;
    if (data && Array.isArray(data)) {
      directoryTree.value = convertToTreeData(data);
      // 默认展开所有节点
      const getAllKeys = (nodes: any[]): number[] => {
        let keys: number[] = [];
        nodes.forEach((node) => {
          keys.push(node.key);
          if (node.children && node.children.length > 0) {
            keys = keys.concat(getAllKeys(node.children));
          }
        });
        return keys;
      };
      expandedKeys.value = getAllKeys(directoryTree.value);
    } else {
      directoryTree.value = [];
    }
  } catch (error) {
    console.error('加载目录树失败', error);
    createMessage.error('加载目录树失败');
    directoryTree.value = [];
  } finally {
    treeLoading.value = false;
  }
};

// 树节点选择
const handleTreeSelect = (selectedKeysValue: number[]) => {
  selectedKeys.value = selectedKeysValue;
  if (selectedKeysValue.length > 0) {
    const directoryId = selectedKeysValue[0];
    // 查找选中的目录
    const findDirectory = (nodes: any[], id: number): any => {
      for (const node of nodes) {
        if (node.id === id) {
          return node;
        }
        if (node.children && node.children.length > 0) {
          const found = findDirectory(node.children, id);
          if (found) return found;
        }
      }
      return null;
    };
    const dir = findDirectory(directoryTree.value, directoryId);
    if (dir) {
      currentDirectory.value = {
        id: dir.id,
        name: dir.title,
        parent_id: dir.parent_id,
        description: dir.description,
        sort_order: dir.sort_order,
        device_count: dir.device_count,
      };
      deviceListParams.directory_id = directoryId;
    }
  } else {
    currentDirectory.value = null;
    deviceListParams.directory_id = null;
  }
  // 刷新设备列表
  if (cardListRef.value) {
    cardListRef.value.fetch();
  }
};

// 树节点展开
const handleTreeExpand = (expandedKeysValue: number[]) => {
  expandedKeys.value = expandedKeysValue;
  autoExpandParent.value = false;
};

// 创建目录
const handleCreateDirectory = (parentId: number | null = null) => {
  openModal(true, {
    type: 'create',
    parent_id: parentId,
  });
};

// 编辑目录
const handleEditDirectory = (directory: any) => {
  openModal(true, {
    type: 'edit',
    record: {
      id: directory.id,
      name: directory.title,
      parent_id: directory.parent_id,
      description: directory.description,
      sort_order: directory.sort_order,
    },
  });
};

// 删除目录
const handleDeleteDirectory = async (directoryId: number) => {
  try {
    const response = await deleteDirectory(directoryId);
    // API返回格式: { code: 0, msg: '...' } 或直接返回data（如果isTransformResponse=true）
    const result = response.code !== undefined ? response : { code: 0, msg: '删除成功' };
    if (result.code === 0) {
      createMessage.success('删除成功');
      // 如果删除的是当前选中的目录，清空选择
      if (currentDirectory.value?.id === directoryId) {
        selectedKeys.value = [];
        currentDirectory.value = null;
        deviceListParams.directory_id = null;
      }
      await loadDirectoryTree();
      // 刷新设备列表
      if (cardListRef.value) {
        cardListRef.value.fetch();
      }
    } else {
      createMessage.error(result.msg || '删除失败');
    }
  } catch (error) {
    console.error('删除目录失败', error);
    createMessage.error('删除目录失败');
  }
};

// 目录操作成功回调
const handleDirectorySuccess = () => {
  loadDirectoryTree();
};

// 查看全部设备
const handleShowAllDevices = () => {
  selectedKeys.value = [];
  currentDirectory.value = null;
  deviceListParams.directory_id = null;
  if (cardListRef.value) {
    cardListRef.value.fetch();
  }
};

// 移动设备到目录
const handleMoveDevices = () => {
  // 这里可以打开一个模态框，让用户选择要移动的设备
  createMessage.info('移动设备功能待实现');
};

// 设备列表API（根据是否有目录ID选择不同的API）
const getDeviceListApi = (params: any) => {
  if (params.directory_id) {
    return getDirectoryDevices(params.directory_id, {
      pageNo: params.pageNo,
      pageSize: params.pageSize,
      search: params.search,
    });
  } else {
    return getDeviceList({
      pageNo: params.pageNo,
      pageSize: params.pageSize,
      search: params.search,
    });
  }
};

// 设备操作事件
const handleView = (record: DeviceInfo) => {
  emit('view', record);
};

const handleEdit = (record: DeviceInfo) => {
  emit('edit', record);
};

const handleDelete = (record: DeviceInfo) => {
  emit('delete', record);
};

const handlePlay = (record: DeviceInfo) => {
  emit('play', record);
};

const handleToggleStream = (record: DeviceInfo) => {
  emit('toggleStream', record);
};

// 暴露事件
const emit = defineEmits(['view', 'edit', 'delete', 'play', 'toggleStream']);

// 暴露刷新方法
defineExpose({
  refresh: () => {
    loadDirectoryTree();
    if (cardListRef.value) {
      cardListRef.value.fetch();
    }
  },
});

// 组件挂载时加载数据
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

  .directory-layout {
    display: flex;
    gap: 16px;
    height: calc(100vh - 250px);
    min-height: 600px;

    .directory-tree-panel {
      width: 320px;
      min-width: 280px;
      background: #fff;
      border-radius: 8px;
      display: flex;
      flex-direction: column;
      overflow: hidden;
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);

      .tree-header {
        padding: 16px;
        border-bottom: 1px solid #f0f0f0;
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-shrink: 0;

        .title {
          font-size: 16px;
          font-weight: 600;
          color: #262626;
        }
      }

      .tree-content {
        flex: 1;
        overflow: auto;
        padding: 12px;

        :deep(.ant-tree) {
          .ant-tree-node-content-wrapper {
            width: 100%;
            padding: 4px 8px;
            border-radius: 4px;
            transition: all 0.2s;

            &:hover {
              background-color: #f5f5f5;
            }
          }

          .tree-node-title {
            display: flex;
            align-items: center;
            justify-content: space-between;
            width: 100%;
            padding-right: 8px;
            gap: 8px;

            .node-name {
              flex: 1;
              overflow: hidden;
              text-overflow: ellipsis;
              white-space: nowrap;
              font-size: 14px;
            }

            .node-info {
              margin: 0 4px;
              flex-shrink: 0;
            }

            .node-actions {
              display: flex;
              gap: 4px;
              opacity: 0;
              transition: opacity 0.2s;
              flex-shrink: 0;
            }

            &:hover .node-actions {
              opacity: 1;
            }
          }
        }
      }
    }

    .device-list-panel {
      flex: 1;
      min-width: 0;
      background: #fff;
      border-radius: 8px;
      display: flex;
      flex-direction: column;
      overflow: hidden;
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);

      .device-list-header {
        padding: 16px;
        border-bottom: 1px solid #f0f0f0;
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-shrink: 0;

        .title {
          font-size: 16px;
          font-weight: 600;
          color: #262626;
        }

        .header-actions {
          display: flex;
          gap: 8px;
        }
      }

      .device-list-content {
        flex: 1;
        overflow: auto;
        padding: 16px;
      }
    }
  }
}
</style>

