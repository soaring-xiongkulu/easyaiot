<template>
  <div class="inference-card-list">
    <template v-if="records.length > 0">
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <div
          v-for="record in records"
          :key="record.id"
          class="card-item bg-white rounded-lg shadow-md overflow-hidden transition-all hover:shadow-lg"
          :class="{
            'border-blue-500 border-2': record.status === 'PROCESSING',
            'border-green-500': record.status === 'COMPLETED',
            'border-red-500': record.status === 'FAILED'
          }"
        >
          <div class="card-header bg-gray-50 px-4 py-3 border-b">
            <div class="flex justify-between items-center">
              <span class="font-medium text-gray-900">#{{ record.id || '-' }}</span>
              <a-tag :color="getStatusColor(record.status)">
                {{ getStatusText(record.status) }}
              </a-tag>
            </div>
            <div class="text-sm text-gray-500 mt-1">
              {{ formatDateTime(record.start_time) }}
            </div>
          </div>

          <div class="card-body p-4">
            <div class="flex items-center mb-3">
              <span class="text-gray-600 mr-2">模型:</span>
              <span class="font-medium">{{ record.model?.name || '未知模型' }}</span>
            </div>

            <div class="mb-3">
              <div class="text-gray-600 mb-1">输入源</div>
              <div class="truncate text-sm">{{ record.input_source || '-' }}</div>
            </div>

            <div class="mb-3" v-if="record.processed_frames">
              <div class="text-gray-600 mb-1">处理进度</div>
              <a-progress
                :percent="calculateProgress(record)"
                status="active"
                size="small"
              />
              <div class="text-xs text-gray-500 mt-1 text-right">
                {{ record.processed_frames || 0 }}/{{ record.total_frames || 0 }} 帧
              </div>
            </div>
          </div>

          <div class="card-footer bg-gray-50 px-4 py-3 border-t flex justify-end space-x-2">
            <a-button
              size="small"
              @click="emit('view', record)"
              preIcon="ant-design:eye-outlined"
            >
              详情
            </a-button>
            <a-button
              size="small"
              type="primary"
              ghost
              @click="emit('result', record)"
              preIcon="ant-design:file-image-outlined"
              :disabled="record.status !== 'COMPLETED'"
            >
              结果
            </a-button>
            <a-button
              size="small"
              danger
              @click="emit('delete', record)"
              preIcon="ant-design:delete-outlined"
            >
              删除
            </a-button>
          </div>
        </div>
      </div>
    </template>

    <a-empty v-else description="暂无推理记录" class="py-12" />
  </div>
</template>

<script lang="ts" setup>
import { defineEmits, defineProps } from 'vue';

const props = defineProps({
  records: {
    type: Array as () => any[],
    required: true,
    default: () => [],
  },
});

const emit = defineEmits(['view', 'result', 'delete']);

const getStatusText = (status: string) => {
  const statusMap = {
    PROCESSING: '处理中',
    COMPLETED: '已完成',
    FAILED: '失败',
  };
  return statusMap[status] || status;
};

const getStatusColor = (status: string) => {
  const colors = {
    PROCESSING: 'blue',
    COMPLETED: 'green',
    FAILED: 'red',
  };
  return colors[status] || 'gray';
};

const formatDateTime = (dateString: string) => {
  if (!dateString) return '';
  return new Date(dateString).toLocaleString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  });
};

const calculateProgress = (record: any) => {
  if (!record.processed_frames || !record.total_frames) return 0;
  return Math.round((record.processed_frames / record.total_frames) * 100);
};
</script>

<style scoped>
.card-item {
  transition: transform 0.2s, box-shadow 0.2s;
}
.card-item:hover {
  transform: translateY(-4px);
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.1);
}
</style>
