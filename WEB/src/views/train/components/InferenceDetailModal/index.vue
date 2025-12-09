<template>
  <BasicModal
    v-bind="$attrs"
    :title="`推理详情 - ${record?.id || ''}`"
    :width="800"
    @register="registerModal"
  >
    <a-descriptions bordered :column="2">
      <a-descriptions-item label="模型名称">
        {{ record?.model?.name || '-' }}
      </a-descriptions-item>
      <a-descriptions-item label="模型ID">
        {{ record?.model_id || '-' }}
      </a-descriptions-item>
      <a-descriptions-item label="推理类型">
        {{ inferenceTypeMap[record?.inference_type] || record?.inference_type || '-' }}
      </a-descriptions-item>
      <a-descriptions-item label="状态">
        <a-tag :color="getStatusColor(record?.status)">
          {{ statusMap[record?.status] || record?.status || '-' }}
        </a-tag>
      </a-descriptions-item>
      <a-descriptions-item label="输入源">
        <a v-if="record?.input_source" :href="record.input_source" target="_blank">{{ record.input_source }}</a>
        <span v-else>-</span>
      </a-descriptions-item>
      <a-descriptions-item label="输出路径">
        <a v-if="record?.output_path" :href="record.output_path" target="_blank">
          查看结果
        </a>
        <span v-else>-</span>
      </a-descriptions-item>
      <a-descriptions-item label="开始时间">
        {{ formatDateTime(record?.start_time) }}
      </a-descriptions-item>
      <a-descriptions-item label="结束时间">
        {{ record?.end_time ? formatDateTime(record.end_time) : '-' }}
      </a-descriptions-item>
      <a-descriptions-item label="处理时间">
        {{ record?.processing_time ? `${record.processing_time}秒` : '-' }}
      </a-descriptions-item>
      <a-descriptions-item label="处理帧数" :span="2">
        {{ record?.processed_frames || 0 }}/{{ record?.total_frames || 0 }}
      </a-descriptions-item>
      <a-descriptions-item label="错误信息" :span="2" v-if="record?.error_message">
        <a-alert type="error" :message="record.error_message" show-icon />
      </a-descriptions-item>
    </a-descriptions>

    <div class="mt-6" v-if="record?.params">
      <h3 class="text-lg font-medium mb-2">推理参数</h3>
      <pre class="bg-gray-100 p-4 rounded">{{ JSON.stringify(record.params, null, 2) }}</pre>
    </div>
  </BasicModal>
</template>

<script lang="ts" setup>
import { defineProps } from 'vue';
import { BasicModal, useModalInner } from '@/components/Modal';

const props = defineProps({
  record: {
    type: Object,
    required: true,
    default: () => ({}),
  },
});

const [registerModal] = useModalInner();

const statusMap = {
  PROCESSING: '处理中',
  COMPLETED: '已完成',
  FAILED: '失败',
};

const inferenceTypeMap = {
  image: '图片推理',
  video: '视频推理',
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
  return new Date(dateString).toLocaleString('zh-CN');
};
</script>
