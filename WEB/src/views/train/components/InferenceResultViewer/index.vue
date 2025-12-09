<template>
  <BasicModal
    v-bind="$attrs"
    :title="`推理结果查看器 - ${record?.id || ''}`"
    :width="1200"
    :height="800"
    @register="registerModal"
  >
    <a-tabs v-model:activeKey="activeTab" class="result-tabs">
      <!-- 结果概览 -->
      <a-tab-pane key="overview" tab="结果概览">
        <div class="result-container">
          <div class="input-section">
            <h3>输入源</h3>
            <div v-if="isImage" class="media-preview">
              <img :src="getMediaUrl(record.input_source)" alt="输入图像" />
            </div>
            <div v-else-if="isVideo" class="media-preview">
              <video controls :src="getMediaUrl(record.input_source)" />
            </div>
            <div v-else class="media-preview">
              <a-alert type="warning" message="不支持的输入类型" />
            </div>
          </div>

          <a-divider type="vertical" style="height: 100%" />

          <div class="output-section">
            <h3>推理结果</h3>
            <div v-if="resultType === 'keypoints'" class="keypoint-result">
              <img :src="getMediaUrl(record.output_path)" alt="关键点结果" />
              <div class="metrics">
                <a-statistic title="处理帧数" :value="`${record.processed_frames}/${record.total_frames}`" />
                <a-statistic title="处理时间" :value="`${record.processing_time}s`" />
              </div>
            </div>

            <div v-else-if="resultType === 'detection'" class="detection-result">
              <img :src="getMediaUrl(record.output_path)" alt="检测结果" />
              <a-table
                :dataSource="detectionData"
                :columns="detectionColumns"
                size="small"
                class="detection-table"
              />
            </div>

            <div v-else-if="resultType === 'classification'" class="classification-result">
              <div class="class-grid">
                <div
                  v-for="(item, index) in classificationData"
                  :key="index"
                  class="class-item"
                  :class="{ 'top-item': index === 0 }"
                >
                  <div class="class-name">{{ item.class }}</div>
                  <a-progress
                    :percent="item.confidence * 100"
                    status="active"
                    stroke-color="#1890ff"
                  />
                  <div class="confidence">{{ (item.confidence * 100).toFixed(2) }}%</div>
                </div>
              </div>
            </div>

            <div v-else-if="resultType === 'video'" class="video-result">
              <video controls :src="getMediaUrl(record.output_path)" />
            </div>

            <div v-else-if="resultType === 'stream'" class="stream-result">
              <div class="stream-container">
                <video controls :src="record.stream_output_url" autoplay muted />
                <div class="stream-controls">
                  <a-button @click="toggleStream">
                    {{ isPlaying ? '暂停' : '播放' }}
                  </a-button>
                  <a-button @click="downloadResult">
                    <template #icon><DownloadOutlined /></template>
                    下载结果
                  </a-button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </a-tab-pane>

      <!-- 原始数据 -->
      <a-tab-pane key="rawData" tab="原始数据">
        <div class="raw-data-container">
          <a-collapse v-model:activeKey="collapseActiveKey" accordion>
            <a-collapse-panel key="predictions" header="预测数据">
              <pre>{{ JSON.stringify(record.predictions, null, 2) }}</pre>
            </a-collapse-panel>
            <a-collapse-panel key="params" header="推理参数">
              <pre>{{ JSON.stringify(record.params, null, 2) }}</pre>
            </a-collapse-panel>
            <a-collapse-panel key="metrics" header="性能指标">
              <a-descriptions bordered>
                <a-descriptions-item label="开始时间">
                  {{ formatDateTime(record.start_time) }}
                </a-descriptions-item>
                <a-descriptions-item label="结束时间">
                  {{ record.end_time ? formatDateTime(record.end_time) : '-' }}
                </a-descriptions-item>
                <a-descriptions-item label="处理时间">
                  {{ record.processing_time }}秒
                </a-descriptions-item>
                <a-descriptions-item label="内存峰值">
                  {{ record.memory_usage }} MB
                </a-descriptions-item>
              </a-descriptions>
            </a-collapse-panel>
          </a-collapse>
        </div>
      </a-tab-pane>
    </a-tabs>
  </BasicModal>
</template>

<script lang="ts" setup>
import { ref, computed, watch } from 'vue';
import { BasicModal, useModalInner } from '@/components/Modal';
import { DownloadOutlined } from '@ant-design/icons-vue';

const props = defineProps({
  record: {
    type: Object,
    required: true,
    default: () => ({})
  }
});

const [registerModal] = useModalInner();

// 响应式状态
const activeTab = ref('overview');
const collapseActiveKey = ref(['predictions']);
const isPlaying = ref(true);

// 计算属性
const isImage = computed(() => props.record?.inference_type === 'image');
const isVideo = computed(() => props.record?.inference_type === 'video');

const resultType = computed(() => {
  if (!props.record) return 'unknown';
  if (props.record.output_path?.includes('.json')) return 'keypoints';
  if (props.record.output_path?.includes('.mp4') || props.record.output_path?.includes('.avi')) return 'video';
  if (props.record.stream_output_url) return 'stream';
  if (props.record.detection_results) return 'detection';
  if (props.record.classification_results) return 'classification';
  return 'unknown';
});

const classificationData = computed(() => {
  if (!props.record?.classification_results) return [];
  return Object.entries(props.record.classification_results)
    .map(([className, confidence]) => ({
      class: className,
      confidence: parseFloat(confidence)
    }))
    .sort((a, b) => b.confidence - a.confidence)
    .slice(0, 5);
});

const detectionData = computed(() => {
  return props.record?.detection_results || [];
});

const detectionColumns = computed(() => [
  { title: '类别', dataIndex: 'class', key: 'class' },
  { title: '置信度', dataIndex: 'confidence', key: 'confidence',
    customRender: ({ text }) => text ? `${(text * 100).toFixed(2)}%` : '0%'
  },
  { title: '位置', dataIndex: 'bbox', key: 'bbox',
    customRender: ({ text }) => text ? `[${text[0]}, ${text[1]}, ${text[2]}, ${text[3]}]` : '[]'
  }
]);

// 方法
const getMediaUrl = (path: string) => {
  if (!path) return '';
  if (path.startsWith('http')) return path;
  return `/api/media/${encodeURIComponent(path)}`;
};

const formatDateTime = (dateString: string) => {
  if (!dateString) return '';
  return new Date(dateString).toLocaleString('zh-CN');
};

const toggleStream = () => {
  const video = document.querySelector('.stream-result video') as HTMLVideoElement;
  if (video) {
    if (video.paused) {
      video.play();
      isPlaying.value = true;
    } else {
      video.pause();
      isPlaying.value = false;
    }
  }
};

const downloadResult = () => {
  if (resultType.value === 'stream' && props.record.stream_output_url) {
    const link = document.createElement('a');
    link.href = props.record.stream_output_url;
    link.download = `inference_result_${props.record.id}.mp4`;
    link.click();
  } else if (props.record.output_path) {
    const link = document.createElement('a');
    link.href = getMediaUrl(props.record.output_path);
    link.download = `inference_result_${props.record.id}${getFileExtension(props.record.output_path)}`;
    link.click();
  }
};

const getFileExtension = (path: string) => {
  return path.substring(path.lastIndexOf('.'));
};

// 监听记录变化
watch(() => props.record, (newRecord) => {
  // 可以在这里添加其他监听逻辑
}, { immediate: true });
</script>

<style lang="less" scoped>
.result-tabs {
  height: 100%;

  :deep(.ant-tabs-content) {
    height: calc(100% - 45px);
    padding: 16px;
    overflow: auto;
  }
}

.result-container {
  display: flex;
  height: 600px;
  gap: 24px;

  .input-section, .output-section {
    flex: 1;
    display: flex;
    flex-direction: column;
    overflow: hidden;

    h3 {
      margin-bottom: 16px;
      color: #1890ff;
    }
  }

  .media-preview {
    flex: 1;
    border: 1px solid #e8e8e8;
    border-radius: 4px;
    overflow: hidden;
    display: flex;
    align-items: center;
    justify-content: center;
    background: #f9f9f9;

    img, video {
      max-width: 100%;
      max-height: 100%;
      object-fit: contain;
    }
  }
}

.keypoint-result {
  display: flex;
  flex-direction: column;
  height: 100%;

  img {
    flex: 1;
    max-height: 80%;
    object-fit: contain;
  }

  .metrics {
    display: flex;
    gap: 24px;
    margin-top: 16px;
  }
}

.detection-result {
  display: flex;
  flex-direction: column;
  height: 100%;

  img {
    flex: 1;
    max-height: 70%;
    object-fit: contain;
    margin-bottom: 16px;
  }

  .detection-table {
    flex: 0 0 auto;
    max-height: 30%;
    overflow: auto;
  }
}

.classification-result {
  height: 100%;

  .class-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 16px;

    .class-item {
      padding: 12px;
      border: 1px solid #e8e8e8;
      border-radius: 4px;
      background: #fafafa;

      &.top-item {
        background: #e6f7ff;
        border-color: #91d5ff;
      }

      .class-name {
        font-weight: 500;
        margin-bottom: 8px;
      }

      .confidence {
        margin-top: 8px;
        text-align: right;
        font-size: 12px;
        color: #666;
      }
    }
  }
}

.stream-result {
  height: 100%;
  display: flex;
  flex-direction: column;

  .stream-container {
    flex: 1;
    position: relative;

    video {
      width: 100%;
      height: 100%;
      object-fit: contain;
      background: #000;
    }
  }

  .stream-controls {
    margin-top: 16px;
    display: flex;
    justify-content: center;
    gap: 16px;
  }
}

.raw-data-container {
  pre {
    background: #f6f8fa;
    padding: 16px;
    border-radius: 4px;
    max-height: 500px;
    overflow: auto;
  }
}
</style>
