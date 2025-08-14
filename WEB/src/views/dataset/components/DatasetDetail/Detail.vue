<template>
  <div>
    <!-- 进度条卡片：添加分隔线和悬停效果 -->
    <a-card
      :bordered="false"
      class="progress-card"
      :class="{ 'card-hover': isHovered }"
      @mouseover="isHovered = true"
      @mouseleave="isHovered = false"
    >
      <div class="progress-header">
        <h2 class="section-title">标注进度</h2>
        <a-progress
          type="circle"
          :percent="calculateAnnotationProgress"
          :stroke-color="progressStrokeColor"
          :width="110"
          :stroke-width="10"
          class="progress-circle"
        >
          <template #format>
            <div class="progress-stats">
              <div class="progress-value">{{ calculateAnnotationProgress }}%</div>
              <div class="progress-text">
                {{ description.annotatedImages || 0 }}/{{ description.totalImages || 0 }}
              </div>
            </div>
          </template>
        </a-progress>
      </div>
    </a-card>

    <!-- 详情卡片：添加标题和分隔线 -->
    <a-card :bordered="false" style="margin-top: 20px">
      <h2 class="section-title">数据集详情</h2>
      <a-divider style="margin: 12px 0 20px" />
      <Description
        layout="vertical"
        :column="2"
        :data="description"
        :schema="enhancedSchema"
      />
    </a-card>
  </div>
</template>

<script lang="ts" setup>
import { computed, onMounted, reactive, ref } from 'vue';
import { Description } from '@/components/Description/index';
import { useMessage } from '@/hooks/web/useMessage';
import { useRoute } from "vue-router";
import { getDataset } from "@/api/device/dataset";
import { Card as ACard, Progress as AProgress, Divider as ADivider } from 'ant-design-vue';

const route = useRoute()
const { createMessage } = useMessage();
const isHovered = ref(false);

// 响应式数据对象
const description = reactive({
  id: '',
  datasetCode: '',
  name: '',
  coverPath: '',
  description: '',
  datasetType: '',
  audit: '',
  reason: '',
  totalImages: 0,      // 总图片数
  annotatedImages: 0,  // 已标注图片数
});

// 增强的schema包含统计字段
const enhancedSchema = [
  {
    field: 'name',
    label: '数据集名称',
  },
  {
    field: 'datasetCode',
    label: '数据集编码',
  },
  {
    field: 'description',
    label: '数据集描述',
  },
  {
    field: 'datasetType',
    label: '数据集分类',
    render: (value) => (value === 0 ? '图片' : '文本'),
  },
  {
    field: 'audit',
    label: '审批状态',
    render: (value) => (value === 0 ? '待审批' : value === 1 ? '审批通过' : '审批驳回'),
  },
  {
    field: 'reason',
    label: '驳回原因',
  },
  {
    field: 'totalImages',
    label: '总图片数',
    render: val => val || 0
  },
  {
    field: 'annotatedImages',
    label: '已标注图片',
    render: val => val || 0
  }
];

// 计算标注进度百分比
const calculateAnnotationProgress = computed(() => {
  if (!description.totalImages || description.totalImages === 0) return 0;
  const progress = (description.annotatedImages / description.totalImages) * 100;
  return Math.round(progress);
});

// 动态进度条颜色（带透明度变化）
const progressStrokeColor = computed(() => {
  const percent = calculateAnnotationProgress.value;
  if (percent < 30) return 'rgba(255, 77, 79, 0.85)'; // 红色，进度低
  if (percent < 70) return 'rgba(250, 173, 20, 0.85)'; // 橙色，中等进度
  return 'rgba(82, 196, 26, 0.85)'; // 绿色，高进度
});

// 初始化数据集详情
async function initDeviceDetail(record) {
  try {
    const info = await getDataset(record);
    Object.keys(description).forEach((item) => {
      // 处理可能的命名差异（驼峰/蛇形）
      const value = info[item] ?? info[item.replace('_', '')] ?? 0;
      description[item] = value !== null && value !== undefined ? value : '--';
    });
  } catch (error) {
    createMessage.error('获取数据集详情失败');
    console.error('Error fetching dataset details:', error);
  }
}

onMounted(() => {
  initDeviceDetail(route.params);
});
</script>

<style lang="less" scoped>
// 进度条卡片动画
.progress-card {
  transition: all 0.3s ease;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.09);

  &.card-hover {
    transform: translateY(-3px);
    box-shadow: 0 5px 15px rgba(24, 144, 255, 0.2);

    .progress-circle {
      transform: scale(1.05);
      transition: transform 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
    }
  }
}

.section-title {
  font-size: 18px;
  font-weight: 600;
  color: #1f1f1f;
  margin-bottom: 0;
}

.progress-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 24px;
}

.progress-stats {
  text-align: center;

  .progress-value {
    font-size: 22px;
    font-weight: 600;
    color: #1890ff;
    line-height: 1.2;
  }

  .progress-text {
    font-size: 13px;
    color: #595959;
    margin-top: 4px;
  }
}

/* 原有样式保持不变 */
:deep(.copy-warpper) {
  display: flex;
  align-items: center;

  .copy {
    margin-left: 10px;
    opacity: 0;
  }
}

:deep(.copy-warpper):hover .copy {
  opacity: 1;
}
</style>
