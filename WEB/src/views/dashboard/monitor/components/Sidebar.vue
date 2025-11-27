<template>
  <div class="monitor-sidebar">
    <!-- 标签页 -->
    <div class="sidebar-tabs">
      <div
        v-for="tab in tabs"
        :key="tab.key"
        :class="['tab-item', { active: activeTab === tab.key }]"
        @click="activeTab = tab.key"
      >
        {{ tab.label }}
      </div>
    </div>

    <!-- 搜索框 -->
    <div class="sidebar-search">
      <a-input
        v-model:value="searchText"
        placeholder="请输入设备名称"
        allow-clear
        class="search-input"
      >
        <template #prefix>
          <Icon icon="ant-design:search-outlined"/>
        </template>
      </a-input>
    </div>

    <!-- 设备树 -->
    <div class="sidebar-tree">
      <a-spin :spinning="loading">
        <a-tree
          v-if="filteredTreeData.length > 0"
          v-model:expandedKeys="expandedKeys"
          v-model:selectedKeys="selectedKeys"
          :tree-data="filteredTreeData"
          :field-names="{ children: 'children', title: 'title', key: 'key', icon: 'icon' }"
          @select="handleSelect"
          class="device-tree"
        />
        <a-empty v-else description="暂无设备目录" />
      </a-spin>
    </div>
  </div>
</template>

<script lang="ts" setup>
import {computed, ref, watch, onMounted, h} from 'vue'
import {Input as AInput} from 'ant-design-vue'
import {Icon} from '@/components/Icon'
import {getDirectoryList, getDirectoryDevices, getDeviceList, type DeviceDirectory, type DeviceInfo} from '@/api/device/camera'
import {useMessage} from '@/hooks/web/useMessage'

defineOptions({
  name: 'MonitorSidebar'
})

const props = defineProps<{
  selectedDevice?: any
}>()

const emit = defineEmits<{
  (e: 'device-change', device: any): void
}>()

const {createMessage} = useMessage()

const tabs = [
  {key: 'directory', label: '设备目录'},
  {key: 'ai', label: '智能分析'},
  {key: 'tag', label: '预置点位'}
]

const activeTab = ref('directory')
const searchText = ref('')
const expandedKeys = ref<string[]>([])
const selectedKeys = ref<string[]>([])
const treeData = ref<any[]>([])
const loading = ref(false)

// 将目录和设备转换为树形结构
const convertToTreeData = (directories: DeviceDirectory[], devices: DeviceInfo[]): any[] => {
  return directories.map((dir) => {
    const directoryKey = `dir_${dir.id}`
    const children: any[] = []
    
    // 添加子目录
    if (dir.children && dir.children.length > 0) {
      const subTree = convertToTreeData(dir.children, devices)
      children.push(...subTree)
    }
    
    // 添加该目录下的设备
    const dirDevices = devices.filter(device => device.directory_id === dir.id)
    dirDevices.forEach(device => {
      children.push({
        key: `device_${device.id}`,
        title: device.name || device.id,
        isDevice: true,
        isDirectory: false,
        device: device,
        icon: () => h(Icon, { icon: 'ant-design:video-camera-outlined' }),
      })
    })
    
    return {
      key: directoryKey,
      title: dir.name,
      isDirectory: true,
      directory: dir,
      children: children.length > 0 ? children : undefined,
      icon: () => h(Icon, { icon: 'ant-design:folder-outlined' }),
    }
  })
}

// 加载目录和设备数据
const loadTreeData = async () => {
  try {
    loading.value = true
    // 获取目录列表
    const dirResponse = await getDirectoryList()
    const dirData = dirResponse.code !== undefined ? dirResponse.data : dirResponse
    
    // 获取所有设备（不分页，获取全部）
    const deviceResponse = await getDeviceList({
      pageNo: 1,
      pageSize: 10000, // 获取所有设备
    })
    const deviceData = deviceResponse.code !== undefined ? deviceResponse.data : deviceResponse
    
    if (dirData && Array.isArray(dirData) && deviceData && Array.isArray(deviceData)) {
      // 获取没有目录的设备
      const devicesWithoutDir = deviceData.filter((device: DeviceInfo) => !device.directory_id)
      
      // 转换目录树
      const tree = convertToTreeData(dirData, deviceData)
      
      // 如果有未分配目录的设备，添加到根节点
      if (devicesWithoutDir.length > 0) {
        devicesWithoutDir.forEach((device: DeviceInfo) => {
          tree.push({
            key: `device_${device.id}`,
            title: device.name || device.id,
            isDevice: true,
            isDirectory: false,
            device: device,
            icon: () => h(Icon, { icon: 'ant-design:video-camera-outlined' }),
          })
        })
      }
      
      treeData.value = tree
      
      // 默认展开所有目录节点
      const getAllKeys = (nodes: any[]): string[] => {
        let keys: string[] = []
        nodes.forEach((node) => {
          if (node.isDirectory) {
            keys.push(node.key)
          }
          if (node.children && node.children.length > 0) {
            keys = keys.concat(getAllKeys(node.children))
          }
        })
        return keys
      }
      expandedKeys.value = getAllKeys(treeData.value)
    } else {
      treeData.value = []
    }
  } catch (error) {
    console.error('加载设备目录失败', error)
    createMessage.error('加载设备目录失败')
    treeData.value = []
  } finally {
    loading.value = false
  }
}

// 过滤后的树数据
const filteredTreeData = computed(() => {
  if (!searchText.value) {
    return treeData.value
  }

  const filterTree = (nodes: any[]): any[] => {
    return nodes
      .map(node => {
        const match = node.title.toLowerCase().includes(searchText.value.toLowerCase())
        const filteredChildren = node.children ? filterTree(node.children) : []

        if (match || filteredChildren.length > 0) {
          return {
            ...node,
            children: filteredChildren.length > 0 ? filteredChildren : node.children
          }
        }
        return null
      })
      .filter(Boolean)
  }

  return filterTree(treeData.value)
})

// 选择设备
const handleSelect = (selectedKeysValue: any[], info: any) => {
  if (selectedKeysValue.length > 0 && info.node) {
    const node = info.node
    // 只处理设备节点，忽略目录节点
    if (node.isDevice && node.device) {
      const device = {
        id: node.device.id,
        name: node.device.name || node.device.id,
        location: getFullPath(node, treeData.value),
        device: node.device,
      }
      emit('device-change', device)
    }
  }
}

// 获取完整路径
const getFullPath = (node: any, treeNodes: any[]): string => {
  const path: string[] = [node.title]

  // 递归查找父节点路径
  const findPath = (nodes: any[], targetKey: string, currentPath: string[] = []): string[] | null => {
    for (const n of nodes) {
      const newPath = [...currentPath, n.title]
      if (n.key === targetKey) {
        return newPath
      }
      if (n.children && n.children.length > 0) {
        const found = findPath(n.children, targetKey, newPath)
        if (found) {
          return found
        }
      }
    }
    return null
  }

  const fullPath = findPath(treeNodes, node.key)
  return fullPath ? fullPath.join(' / ') : node.title
}

// 监听搜索文本变化，自动展开匹配的节点
watch(searchText, (newVal) => {
  if (newVal) {
    const expandKeys: string[] = []
    const findKeys = (nodes: any[]) => {
      nodes.forEach(node => {
        if (node.title.toLowerCase().includes(newVal.toLowerCase())) {
          expandKeys.push(node.key)
        }
        if (node.children) {
          findKeys(node.children)
        }
      })
    }
    findKeys(treeData.value)
    expandedKeys.value = [...new Set([...expandedKeys.value, ...expandKeys])]
  }
})

// 组件挂载时加载数据
onMounted(() => {
  loadTreeData()
})
</script>

<style lang="less" scoped>
.monitor-sidebar {
  width: 280px;
  background: rgba(0, 0, 0, 0.3);
  border-radius: 8px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.sidebar-tabs {
  display: flex;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  padding: 0 12px;

  .tab-item {
    flex: 1;
    padding: 12px 8px;
    text-align: center;
    cursor: pointer;
    color: rgba(255, 255, 255, 0.6);
    font-size: 14px;
    transition: all 0.3s;
    border-bottom: 2px solid transparent;

    &:hover {
      color: rgba(255, 255, 255, 0.9);
    }

    &.active {
      color: #1890ff;
      border-bottom-color: #1890ff;
      font-weight: 500;
    }
  }
}

.sidebar-search {
  padding: 12px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);

  .search-input {
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.1);

    :deep(.ant-input) {
      background: transparent;
      color: #ffffff;
      border: none;

      &::placeholder {
        color: rgba(255, 255, 255, 0.4);
      }
    }

    :deep(.ant-input-prefix) {
      color: rgba(255, 255, 255, 0.6);
    }
  }
}

.sidebar-tree {
  flex: 1;
  overflow-y: auto;
  padding: 8px;

  .device-tree {
    background: transparent;
    color: #ffffff;

    :deep(.ant-tree-node-selected) {
      background: rgba(24, 144, 255, 0.2) !important;
    }

    :deep(.ant-tree-title) {
      color: rgba(255, 255, 255, 0.8);

      &:hover {
        color: #ffffff;
      }
    }

    :deep(.ant-tree-node-selected .ant-tree-title) {
      color: #1890ff;
    }

    :deep(.ant-tree-switcher) {
      color: rgba(255, 255, 255, 0.6);
    }

    :deep(.ant-tree-iconEle) {
      color: rgba(255, 255, 255, 0.6);
    }
  }
}
</style>
