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
          <Icon icon="ant-design:search-outlined" />
        </template>
      </a-input>
    </div>
    
    <!-- 设备树 -->
    <div class="sidebar-tree">
      <a-tree
        v-model:expandedKeys="expandedKeys"
        v-model:selectedKeys="selectedKeys"
        :tree-data="treeData"
        :field-names="{ children: 'children', title: 'title', key: 'key' }"
        @select="handleSelect"
        class="device-tree"
      />
    </div>
  </div>
</template>

<script lang="ts" setup>
import { ref, computed, watch } from 'vue'
import { Input as AInput, Tree } from 'ant-design-vue'
import { Icon } from '@/components/Icon'

defineOptions({
  name: 'MonitorSidebar'
})

const props = defineProps<{
  selectedDevice?: any
}>()

const emit = defineEmits<{
  (e: 'device-change', device: any): void
}>()

const tabs = [
  { key: 'directory', label: '目录' },
  { key: 'ai', label: 'AI能力' },
  { key: 'tag', label: '标签' }
]

const activeTab = ref('directory')
const searchText = ref('')
const expandedKeys = ref(['kaifaqu'])
const selectedKeys = ref(['kaifaqu-1'])

// 设备树数据
const treeData = ref([
  {
    key: 'kaifaqu',
    title: '开发区',
    children: [
      { key: 'kaifaqu-1', title: '华南小区西四路23号' },
      { key: 'kaifaqu-2', title: '华南小区西四路24号' },
      { key: 'kaifaqu-3', title: '华南小区西四路25号' },
      { key: 'kaifaqu-4', title: '华南小区西四路26号' }
    ]
  },
  {
    key: 'jinshaqu',
    title: '金沙区',
    children: []
  },
  {
    key: 'xigangqu',
    title: '西岗区',
    children: []
  },
  {
    key: 'zhongshanqu',
    title: '中山区',
    children: []
  },
  {
    key: 'shangmaoquan',
    title: '商贸圈',
    children: []
  },
  {
    key: 'zhongsanfuxiao',
    title: '中三附小',
    children: []
  },
  {
    key: 'zhongxinyiyuan',
    title: '中心医院',
    children: []
  },
  {
    key: 'minglixiaoqu',
    title: '明丽小区',
    children: []
  },
  {
    key: 'jianshequ',
    title: '建设区',
    children: []
  }
])

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
const handleSelect = (selectedKeys: any[], info: any) => {
  if (selectedKeys.length > 0 && info.node) {
    const device = {
      id: info.node.key,
      name: info.node.title,
      location: getFullPath(info.node)
    }
    emit('device-change', device)
  }
}

// 获取完整路径
const getFullPath = (node: any): string => {
  const path = [node.title]
  let parent = node.parent
  
  while (parent) {
    path.unshift(parent.title)
    parent = parent.parent
  }
  
  return path.join('')
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
