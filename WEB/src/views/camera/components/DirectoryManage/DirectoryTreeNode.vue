<template>
  <div class="directory-tree-node">
    <div
      class="node-content"
      :class="{ 'node-selected': isSelected, 'node-level-0': level === 0, 'node-level-1': level === 1, 'node-level-2': level === 2 }"
      @click="handleSelect"
    >
      <div class="node-left">
        <!-- 折叠/展开图标 -->
        <span
          v-if="hasChildren && level < 2"
          class="expand-icon"
          @click.stop="handleToggle"
        >
          <Icon
            :icon="isExpanded ? 'ant-design:down-outlined' : 'ant-design:right-outlined'"
            :style="{ fontSize: '12px', color: '#666' }"
          />
        </span>
        <span v-else class="expand-placeholder"></span>
        
        <!-- 文件夹图标 -->
        <Icon
          icon="ant-design:folder-outlined"
          :style="{ fontSize: '16px', color: '#1890ff', marginRight: '8px' }"
        />
        
        <!-- 目录名称 -->
        <span class="node-name">{{ directory.name }}</span>
      </div>
      
      <!-- 操作按钮 -->
      <div class="node-actions" @click.stop>
        <a-button
          type="text"
          size="small"
          @click="handleEdit"
          title="编辑"
        >
          <template #icon>
            <Icon icon="ant-design:edit-filled" :style="{ color: '#1890ff' }" />
          </template>
        </a-button>
        <a-popconfirm
          title="确定删除此目录？"
          @confirm="handleDelete"
        >
          <a-button
            type="text"
            size="small"
            danger
            title="删除"
          >
            <template #icon>
              <Icon icon="material-symbols:delete-outline-rounded" />
            </template>
          </a-button>
        </a-popconfirm>
      </div>
    </div>
    
    <!-- 子节点 -->
    <div
      v-if="hasChildren && isExpanded && level < 2"
      class="node-children"
    >
      <DirectoryTreeNode
        v-for="child in directory.children"
        :key="child.id"
        :directory="child"
        :level="level + 1"
        :expanded-keys="expandedKeys"
        :selected-id="selectedId"
        @toggle="$emit('toggle', $event, level + 1)"
        @select="$emit('select', $event)"
        @edit="$emit('edit', $event)"
        @delete="$emit('delete', $event)"
      />
    </div>
  </div>
</template>

<script lang="ts" setup>
import { computed } from 'vue';
import { Icon } from '@/components/Icon';
import { Button as AButton, Popconfirm as APopconfirm } from 'ant-design-vue';
import type { DeviceDirectory } from '@/api/device/camera';

interface Props {
  directory: DeviceDirectory;
  level: number;
  expandedKeys: Set<number>;
  selectedId: number | null;
}

const props = defineProps<Props>();

const emit = defineEmits<{
  toggle: [directoryId: number, level: number];
  select: [directory: DeviceDirectory];
  edit: [directory: DeviceDirectory];
  delete: [directory: DeviceDirectory];
}>();

const hasChildren = computed(() => {
  return props.directory.children && props.directory.children.length > 0;
});

const isExpanded = computed(() => {
  return props.expandedKeys.has(props.directory.id);
});

const isSelected = computed(() => {
  return props.selectedId === props.directory.id;
});

const handleToggle = () => {
  emit('toggle', props.directory.id, props.level);
};

const handleSelect = () => {
  emit('select', props.directory);
};

const handleEdit = () => {
  emit('edit', props.directory);
};

const handleDelete = () => {
  emit('delete', props.directory);
};
</script>

<style lang="less" scoped>
.directory-tree-node {
  user-select: none;
}

.node-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  cursor: pointer;
  transition: background-color 0.2s;
  border-radius: 4px;
  margin: 2px 0;
  
  &:hover {
    background-color: #f5f5f5;
    
    .node-actions {
      opacity: 1;
    }
  }
  
  &.node-selected {
    background-color: #e6f7ff;
    border-left: 3px solid #1890ff;
  }
  
  &.node-level-0 {
    font-weight: 500;
  }
  
  &.node-level-1 {
    padding-left: 32px;
    font-size: 14px;
  }
  
  &.node-level-2 {
    padding-left: 56px;
    font-size: 13px;
    color: #666;
  }
}

.node-left {
  display: flex;
  align-items: center;
  flex: 1;
  min-width: 0;
}

.expand-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  margin-right: 4px;
  cursor: pointer;
  transition: transform 0.2s;
  
  &:hover {
    color: #1890ff !important;
  }
}

.expand-placeholder {
  width: 20px;
  margin-right: 4px;
}

.node-name {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.node-actions {
  display: flex;
  align-items: center;
  gap: 4px;
  opacity: 0;
  transition: opacity 0.2s;
  
  :deep(.ant-btn) {
    padding: 0 4px;
    height: 24px;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    border-radius: 4px;
    transition: all 0.2s;
    
    &:hover {
      background-color: #f0f0f0;
      transform: scale(1.1);
    }
    
    &:active {
      transform: scale(0.95);
    }
  }
}

.node-children {
  margin-left: 0;
}
</style>

