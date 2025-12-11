<template>
  <div class="monitor-sidebar">
    <!-- 全局总览 -->
    <div class="sidebar-section overview-section">
      <div class="section-header">
        <Icon icon="ant-design:dashboard-outlined" :size="16" class="header-icon" />
        <span class="section-title">全局总览</span>
      </div>
      <div class="statistics-cards">
        <div class="stat-card">
          <div class="stat-icon alarm">
            <Icon icon="ant-design:warning-outlined" :size="24" />
          </div>
          <div class="stat-content">
            <div class="stat-label">告警数量</div>
            <div class="stat-value">{{ statistics.alarmCount }}</div>
          </div>
        </div>
        <div class="stat-card">
          <div class="stat-icon camera">
            <Icon icon="ant-design:video-camera-outlined" :size="24" />
          </div>
          <div class="stat-content">
            <div class="stat-label">摄像头数量</div>
            <div class="stat-value">{{ statistics.cameraCount }}</div>
          </div>
        </div>
        <div class="stat-card">
          <div class="stat-icon algorithm">
            <Icon icon="ant-design:code-outlined" :size="24" />
          </div>
          <div class="stat-content">
            <div class="stat-label">算法数量</div>
            <div class="stat-value">{{ statistics.algorithmCount }}</div>
          </div>
        </div>
        <div class="stat-card">
          <div class="stat-icon model">
            <Icon icon="ant-design:database-outlined" :size="24" />
          </div>
          <div class="stat-content">
            <div class="stat-label">模型数量</div>
            <div class="stat-value">{{ statistics.modelCount }}</div>
          </div>
        </div>
      </div>
    </div>

    <!-- 设备目录 -->
    <div class="sidebar-section directory-section">
      <div class="section-header">
        <Icon icon="ant-design:folder-outlined" :size="16" class="header-icon" />
        <span class="section-title">设备目录</span>
        <div class="header-actions">
          <span class="device-count" v-if="!loading && treeData.length > 0">
            {{ getTotalDeviceCount(treeData) }} 个设备
          </span>
        </div>
      </div>
      <!-- 设备树 -->
      <div class="sidebar-tree">
        <BasicTree
          :tree-data="treeData"
          :expanded-keys="expandedKeys"
          :selected-keys="selectedKeys"
          :loading="loading"
          search
          :default-expand-all="true"
          :click-row-to-expand="false"
          :render-icon="renderTreeIcon"
          tree-wrapper-class-name="sidebar-tree-wrapper"
          @update:expanded-keys="handleExpandedKeysChange"
          @select="handleTreeSelect"
        />
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
import {computed, ref, watch, onMounted, onUnmounted, h} from 'vue'
import {Icon} from '@/components/Icon'
import {BasicTree} from '@/components/Tree'
import type {TreeItem} from '@/components/Tree'
import {getDirectoryList, getDirectoryDevices, getDeviceList, type DeviceDirectory, type DeviceInfo} from '@/api/device/camera'
import {queryAlarmList, getDashboardStatistics} from '@/api/device/calculate'
import {useMessage} from '@/hooks/web/useMessage'

defineOptions({
  name: 'MonitorSidebar'
})

const props = defineProps<{
  selectedDevice?: any
}>()

const emit = defineEmits<{
  (e: 'device-change', device: any): void
  (e: 'device-play', device: any): void
}>()

const {createMessage} = useMessage()

const expandedKeys = ref<string[]>([])
const selectedKeys = ref<string[]>([])
const treeData = ref<TreeItem[]>([])
const loading = ref(false)

// 统计数据
const statistics = ref({
  alarmCount: 0,
  cameraCount: 0,
  algorithmCount: 0,
  modelCount: 0
})

// 将目录和设备转换为树形结构
const convertToTreeData = (directories: DeviceDirectory[], devices: DeviceInfo[]): TreeItem[] => {
  return directories.map((dir) => {
    const directoryKey = `dir_${dir.id}`
    const children: TreeItem[] = []
    
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
        icon: 'ant-design:camera-filled',
      } as TreeItem)
    })
    
    return {
      key: directoryKey,
      title: dir.name,
      isDirectory: true,
      directory: dir,
      icon: 'ant-design:folder-outlined',
      children: children.length > 0 ? children : undefined,
    } as TreeItem
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
    
    // 处理设备数据 - 可能是数组或包含list/records的对象
    let deviceData: any[] = []
    if (deviceResponse) {
      if (Array.isArray(deviceResponse)) {
        deviceData = deviceResponse
      } else if (deviceResponse.code !== undefined) {
        deviceData = deviceResponse.data?.list || deviceResponse.data?.records || deviceResponse.data || []
      } else if (deviceResponse.list) {
        deviceData = deviceResponse.list
      } else if (deviceResponse.records) {
        deviceData = deviceResponse.records
      } else if (Array.isArray(deviceResponse.data)) {
        deviceData = deviceResponse.data
      }
    }
    
    console.log('目录数据:', dirData)
    console.log('设备数据:', deviceData)
    
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
            icon: 'ant-design:camera-filled',
          } as TreeItem)
        })
      }
      
      treeData.value = tree
      console.log('树形数据:', treeData.value)
      
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
      
      // 摄像头数量会在loadStatistics中统一更新，这里不需要单独设置
    } else {
      console.warn('数据格式不正确:', { dirData, deviceData })
      treeData.value = []
      // 如果至少有一些数据，显示提示
      if (!dirData || !Array.isArray(dirData)) {
        createMessage.warning('目录数据格式不正确')
      }
      if (!deviceData || !Array.isArray(deviceData)) {
        createMessage.warning('设备数据格式不正确')
      }
    }
  } catch (error) {
    console.error('加载设备目录失败', error)
    createMessage.error('加载设备目录失败: ' + (error as Error).message)
    treeData.value = []
  } finally {
    loading.value = false
  }
}

// 加载统计数据
const loadStatistics = async () => {
  try {
    // 调用统一的统计接口
    const statsResponse = await getDashboardStatistics()
    if (statsResponse) {
      statistics.value.alarmCount = statsResponse.alarm_count || 0
      statistics.value.cameraCount = statsResponse.camera_count || 0
      statistics.value.algorithmCount = statsResponse.algorithm_count || 0
      statistics.value.modelCount = statsResponse.model_count || 0
    }
  } catch (error) {
    console.error('加载统计数据失败', error)
    // 发生错误时使用默认值
    statistics.value.alarmCount = 0
    statistics.value.cameraCount = 0
    statistics.value.algorithmCount = 0
    statistics.value.modelCount = 0
  }
}

// 处理展开/收起变化
const handleExpandedKeysChange = (keys: string[]) => {
  expandedKeys.value = keys
}

// 处理树节点选择
const handleTreeSelect = (keys: string[], info: any) => {
  if (keys.length === 0) {
    return
  }
  
  const selectedKey = keys[0]
  const node = findNodeByKey(treeData.value, selectedKey)
  
  if (node && node.isDevice && node.device) {
    const device = {
      id: node.device.id,
      name: node.device.name || node.device.id,
      location: getFullPath(node, treeData.value),
      device: node.device,
    }
    selectedKeys.value = [selectedKey]
    emit('device-change', device)
    
    // 检查是否有流地址，优先使用http_stream（大屏地址使用摄像头的http地址）
    if (node.device.http_stream || node.device.rtmp_stream) {
      emit('device-play', {
        ...device,
        http_stream: node.device.http_stream, // 优先传递http_stream
        rtmp_stream: node.device.rtmp_stream,
      })
    }
  }
}

// 根据key查找节点
const findNodeByKey = (nodes: TreeItem[], key: string): TreeItem | null => {
  for (const node of nodes) {
    if (node.key === key) {
      return node as TreeItem
    }
    if (node.children && node.children.length > 0) {
      const found = findNodeByKey(node.children as TreeItem[], key)
      if (found) {
        return found
      }
    }
  }
  return null
}

// 渲染树节点图标
const renderTreeIcon = (node: TreeItem) => {
  if (node.isDirectory) {
    return 'ant-design:folder-outlined'
  } else if (node.isDevice) {
    return 'ant-design:camera-filled'
  }
  return ''
}

// 获取完整路径
const getFullPath = (node: TreeItem, treeNodes: TreeItem[]): string => {
  const path: string[] = [node.title as string]

  // 递归查找父节点路径
  const findPath = (nodes: TreeItem[], targetKey: string, currentPath: string[] = []): string[] | null => {
    for (const n of nodes) {
      const newPath = [...currentPath, n.title as string]
      if (n.key === targetKey) {
        return newPath
      }
      if (n.children && n.children.length > 0) {
        const found = findPath(n.children as TreeItem[], targetKey, newPath)
        if (found) {
          return found
        }
      }
    }
    return null
  }

  const fullPath = findPath(treeNodes, node.key as string)
  return fullPath ? fullPath.join(' / ') : (node.title as string)
}

// 获取设备总数
const getTotalDeviceCount = (nodes: TreeItem[]): number => {
  let count = 0
  const countDevices = (nodes: TreeItem[]) => {
    nodes.forEach(node => {
      if (node.isDevice) {
        count++
      }
      if (node.children && node.children.length > 0) {
        countDevices(node.children as TreeItem[])
      }
    })
  }
  countDevices(nodes)
  return count
}

// 刷新定时器
let statisticsTimer: any = null
let delayTimer: any = null
let isMounted = false

// 组件挂载时加载数据
onMounted(() => {
  isMounted = true
  
  loadTreeData()
  // 初始加载统计数据
  loadStatistics()
  
  // 错峰刷新：延迟1秒开始，每5秒刷新一次统计数据（1秒、6秒、11秒...）
  delayTimer = setTimeout(() => {
    // 检查组件是否仍然挂载
    if (!isMounted) return
    
    loadStatistics()
    
    // 再次检查组件是否仍然挂载
    if (!isMounted) return
    
    statisticsTimer = setInterval(() => {
      // 每次执行前检查组件是否仍然挂载
      if (!isMounted) {
        if (statisticsTimer) {
          clearInterval(statisticsTimer)
          statisticsTimer = null
        }
        return
      }
      
      loadStatistics()
    }, 5000)
  }, 1000)
})

// 组件卸载时清理定时器
onUnmounted(() => {
  isMounted = false
  
  // 清理延迟定时器
  if (delayTimer) {
    clearTimeout(delayTimer)
    delayTimer = null
  }
  
  // 清理定时器
  if (statisticsTimer) {
    clearInterval(statisticsTimer)
    statisticsTimer = null
  }
})
</script>

<style lang="less" scoped>
.monitor-sidebar {
  width: 280px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  overflow: hidden;
}

.sidebar-section {
  background: linear-gradient(135deg, rgba(15, 34, 73, 0.8), rgba(24, 46, 90, 0.6));
  border-radius: 8px;
  border: 1px solid rgba(52, 134, 218, 0.3);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3), inset 0 0 30px rgba(52, 134, 218, 0.1);
  position: relative;
  overflow: hidden;
  display: flex;
  flex-direction: column;

  &::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: 
      linear-gradient(90deg, transparent 0%, rgba(52, 134, 218, 0.05) 50%, transparent 100%),
      radial-gradient(circle at top left, rgba(52, 134, 218, 0.1), transparent 50%);
    pointer-events: none;
    border-radius: 8px;
  }
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding: 12px 16px;
  border-bottom: 1px solid rgba(52, 134, 218, 0.3);
  background: rgba(52, 134, 218, 0.08);
  position: relative;
  z-index: 1;

  .header-icon {
    color: #3486da;
    filter: drop-shadow(0 0 4px rgba(52, 134, 218, 0.6));
  }

  .section-title {
    font-size: 15px;
    font-weight: 600;
    color: #ffffff;
    text-shadow: 0 0 8px rgba(52, 134, 218, 0.5);
    letter-spacing: 0.5px;
    flex: 1;
  }

  .header-actions {
    display: flex;
    align-items: center;
    gap: 8px;

    .device-count {
      font-size: 12px;
      color: rgba(200, 220, 255, 0.7);
      padding: 2px 8px;
      background: rgba(52, 134, 218, 0.15);
      border-radius: 4px;
      border: 1px solid rgba(52, 134, 218, 0.3);
    }
  }
}

.overview-section {
  flex-shrink: 0;
}

.directory-section {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
}

.statistics-cards {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  grid-template-rows: repeat(2, 1fr);
  gap: 8px;
  padding: 12px;
  position: relative;
  z-index: 1;
}

.stat-card {
  background: linear-gradient(135deg, rgba(52, 134, 218, 0.15), rgba(48, 82, 174, 0.1));
  border: 1px solid rgba(52, 134, 218, 0.3);
  border-radius: 8px;
  padding: 12px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  transition: all 0.3s;
  position: relative;
  overflow: hidden;
  cursor: pointer;

  &::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: linear-gradient(135deg, rgba(52, 134, 218, 0.1), transparent);
    opacity: 0;
    transition: opacity 0.3s;
  }

  &:hover {
    border-color: rgba(52, 134, 218, 0.6);
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(52, 134, 218, 0.2);

    &::before {
      opacity: 1;
    }

    .stat-icon {
      transform: scale(1.1);
    }
  }

  .stat-icon {
    width: 48px;
    height: 48px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all 0.3s;
    position: relative;
    z-index: 1;

    &.alarm {
      background: linear-gradient(135deg, rgba(255, 77, 79, 0.2), rgba(255, 77, 79, 0.1));
      color: #ff4d4f;
      border: 1px solid rgba(255, 77, 79, 0.3);
    }

    &.camera {
      background: linear-gradient(135deg, rgba(52, 134, 218, 0.2), rgba(52, 134, 218, 0.1));
      color: #3486da;
      border: 1px solid rgba(52, 134, 218, 0.3);
    }

    &.algorithm {
      background: linear-gradient(135deg, rgba(82, 196, 26, 0.2), rgba(82, 196, 26, 0.1));
      color: #52c41a;
      border: 1px solid rgba(82, 196, 26, 0.3);
    }

    &.model {
      background: linear-gradient(135deg, rgba(250, 173, 20, 0.2), rgba(250, 173, 20, 0.1));
      color: #faad14;
      border: 1px solid rgba(250, 173, 20, 0.3);
    }
  }

  .stat-content {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 4px;
    position: relative;
    z-index: 1;

    .stat-label {
      font-size: 11px;
      color: rgba(255, 255, 255, 0.6);
      white-space: nowrap;
    }

    .stat-value {
      font-size: 20px;
      font-weight: 700;
      color: #ffffff;
      line-height: 1;
      text-shadow: 0 0 8px rgba(52, 134, 218, 0.5);
    }
  }
}

.sidebar-tree {
  flex: 1;
  min-height: 0;
  padding: 8px;
  position: relative;
  z-index: 1;
  display: flex;
  flex-direction: column;
  background: linear-gradient(to bottom, rgba(15, 34, 73, 0.4), rgba(24, 46, 90, 0.3));

  // 覆盖 BasicTree 的所有背景色
  :deep(.tree) {
    background: transparent !important;
    height: 100%;
    display: flex;
    flex-direction: column;
  }

  // 覆盖 xingyuv-tree 类的背景色
  :deep(.xingyuv-tree) {
    background: transparent !important;
  }

  // 隐藏 BasicTree 的标题栏，只保留搜索框
  :deep(.tree-header) {
    padding: 8px 0;
    border-bottom: none !important;
    background: rgba(15, 34, 73, 0.3) !important;
    margin-bottom: 8px;

    .tree-header-title {
      display: none; // 隐藏标题
    }
  }

  // 去掉搜索框下方的所有边框
  :deep(.tree-header-search) {
    border-bottom: none !important;
  }

  // 增大 xingyuv-tree-header 下方的间距
  :deep(.xingyuv-tree-header) {
    margin-bottom: 12px !important;
    border-bottom: none !important;
  }

  // 覆盖 Spin 组件的背景
  :deep(.ant-spin-container) {
    background: transparent !important;
  }

  // 覆盖 ScrollContainer 的背景
  :deep(.scroll-container) {
    background: transparent !important;
  }

  :deep(.ant-tree) {
    background: transparent !important;
    color: rgba(200, 220, 255, 0.9);
  }

  // 覆盖树节点的背景
  :deep(.ant-tree-list) {
    background: transparent !important;
  }

  :deep(.ant-tree-list-holder) {
    background: transparent !important;
  }

  :deep(.ant-tree-list-holder-inner) {
    background: transparent !important;
  }

  :deep(.ant-tree-treenode) {
    background: transparent !important;
  }

  :deep(.ant-tree-node-content-wrapper) {
    background: transparent !important;
    color: rgba(200, 220, 255, 0.9);
    transition: all 0.25s;

    &:hover {
      background: rgba(52, 134, 218, 0.12) !important;
      color: #ffffff;
    }
  }

  :deep(.ant-tree-node-selected) {
    .ant-tree-node-content-wrapper {
      background: linear-gradient(90deg, rgba(52, 134, 218, 0.3), rgba(52, 134, 218, 0.15)) !important;
      color: #6bb3ff !important;
    }
  }

  :deep(.ant-tree-switcher) {
    color: rgba(52, 134, 218, 0.8);
    background: transparent !important;
  }

  :deep(.ant-tree-title) {
    color: inherit;
  }

  // 覆盖 Empty 组件的背景
  :deep(.ant-empty) {
    background: transparent !important;
  }

  // 搜索框样式
  :deep(.tree-header-search) {
    .ant-input {
      background: rgba(52, 134, 218, 0.15) !important;
      border: 1px solid rgba(52, 134, 218, 0.4);
      border-radius: 6px;
      color: rgba(200, 220, 255, 0.95);

      &::placeholder {
        color: rgba(200, 220, 255, 0.5);
      }

      &:hover {
        border-color: rgba(52, 134, 218, 0.6);
        background: rgba(52, 134, 218, 0.2) !important;
      }

      &:focus {
        border-color: #3486da;
        box-shadow: 0 0 12px rgba(52, 134, 218, 0.5);
        background: rgba(52, 134, 218, 0.25) !important;
      }
    }
  }
}

.sidebar-tree-wrapper {
  height: 100%;
  overflow-y: auto;
  overflow-x: hidden;
  background: transparent !important;

  // 自定义滚动条
  &::-webkit-scrollbar {
    width: 6px;
  }

  &::-webkit-scrollbar-track {
    background: rgba(52, 134, 218, 0.1);
    border-radius: 3px;
  }

  &::-webkit-scrollbar-thumb {
    background: rgba(52, 134, 218, 0.5);
    border-radius: 3px;
    transition: all 0.3s;

    &:hover {
      background: rgba(52, 134, 218, 0.7);
    }
  }
}
</style>
