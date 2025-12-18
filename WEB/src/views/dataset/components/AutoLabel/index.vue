<template>
  <div class="auto-label-container">
    <!-- 顶部导航栏 -->
    <div class="header-bar">
      <div class="header-left">
        <h1 class="app-title">自动化标注</h1>
      </div>
      <div class="header-right">
        <Space size="small">
          <Button @click="handleImportDataset">
            <template #icon><Icon icon="ant-design:upload-outlined" /></template>
            添加数据集
          </Button>
          <Button type="primary" class="ai-label-btn" @click="handleAILabel">
            <template #icon><Icon icon="ant-design:robot-outlined" /></template>
            AI标注
          </Button>
          <Button 
            type="primary" 
            :disabled="!currentImageId"
            :loading="aiLabelLoading"
            @click="handleLabelCurrentImage"
          >
            <template #icon><Icon icon="ant-design:robot-outlined" /></template>
            AI标注当前图片
          </Button>
          <a-badge v-if="taskProgress" :count="taskProgress.processed_images" :number-style="{ backgroundColor: '#52c41a' }">
            <span style="margin-right: 8px;">任务进度: {{ taskProgress.processed_images }}/{{ taskProgress.total_images }}</span>
          </a-badge>
          <Button @click="handleClear">
            <template #icon><Icon icon="ant-design:clear-outlined" /></template>
            清除
          </Button>
          <Button @click="handleSave">
            <template #icon><Icon icon="ant-design:save-outlined" /></template>
            保存
          </Button>
          <Button @click="handleExport">
            <template #icon><Icon icon="ant-design:download-outlined" /></template>
            导出数据集
          </Button>
          <Button @click="handleSettings">
            <template #icon><Icon icon="ant-design:setting-outlined" /></template>
            设置
          </Button>
        </Space>
      </div>
    </div>

    <!-- 主内容区域：三列布局 -->
    <div class="main-layout">
      <!-- 左侧边栏：图片列表 -->
      <div class="left-sidebar">
        <!-- 搜索框 -->
        <div class="search-section">
          <a-input
            v-model:value="searchKeyword"
            placeholder="搜索图片..."
            allow-clear
            @change="handleSearch"
          >
            <template #prefix>
              <Icon icon="ant-design:search-outlined" />
            </template>
          </a-input>
        </div>

        <!-- 操作按钮 -->
        <div class="action-section">
          <Space size="small">
            <Button type="text" size="small" @click="toggleSelectMode">
              <template #icon>
                <Icon :icon="selectMode === 'multiple' ? 'ant-design:check-square-outlined' : 'ant-design:border-outlined'" />
              </template>
            </Button>
            <span class="image-count">共 {{ filteredImageList.length }} 张图片</span>
            <a-checkbox v-model:checked="selectAll" @change="handleSelectAll">全选</a-checkbox>
            <Button type="text" size="small" @click="handleDeleteSelected">
              <template #icon><Icon icon="ant-design:delete-outlined" /></template>
            </Button>
          </Space>
        </div>

        <!-- 图片列表 -->
        <div class="image-list">
          <div
            v-for="(image, index) in filteredImageList"
            :key="image.id"
            class="image-item"
            :class="{
              'active': currentImageId === image.id,
              'selected': selectedImageIds.includes(image.id),
              'annotated': image.completed === 1
            }"
            @click="selectImage(image)"
          >
            <a-checkbox
              :checked="selectedImageIds.includes(image.id)"
              @click.stop="toggleImageSelect(image.id)"
              class="image-checkbox"
            />
            <div class="image-index">{{ index + 1 }}</div>
            <div class="image-name" :title="image.name">{{ image.name }}</div>
          </div>
        </div>
      </div>

      <!-- 中间主内容区域：图像显示和标注 -->
      <div class="center-content">
        <!-- 标注工具栏 -->
        <div class="annotation-toolbar">
          <div
            v-for="tool in annotationTools"
            :key="tool.id"
            class="tool-button"
            :class="{ active: activeTool === tool.id }"
            @click="setActiveTool(tool.id)"
            :title="tool.name"
          >
            <Icon :icon="tool.icon" />
          </div>
        </div>

        <!-- 图像显示区域 -->
        <div class="image-display-area" v-if="currentImage">
          <div class="image-wrapper">
            <img
              ref="imageElement"
              :src="currentImage.path"
              alt="标注图片"
              @load="handleImageLoad"
            />
            <!-- 标注框叠加层 -->
            <canvas
              ref="annotationCanvas"
              class="annotation-overlay"
              @mousedown="handleCanvasMouseDown"
              @mousemove="handleCanvasMouseMove"
              @mouseup="handleCanvasMouseUp"
              @resize="handleImageLoad"
            ></canvas>
          </div>
          <!-- 图像信息叠加 -->
          <div class="image-info-overlay" v-if="imageInfo">
            <div class="info-item" style="color: #52c41a">{{ imageInfo.label }}</div>
            <div class="info-item" style="color: #52c41a">人数: {{ imageInfo.personCount || 0 }}</div>
          </div>
        </div>
        <div v-else class="empty-image">
          <a-empty description="请从左侧选择一张图片" />
        </div>
      </div>

      <!-- 右侧边栏：标签管理和标注列表 -->
      <div class="right-sidebar">
        <!-- 标签管理 -->
        <div class="label-management">
          <div class="section-title">标签管理</div>
          <div class="add-label-form">
            <a-input
              v-model:value="newLabelName"
              placeholder="新标签"
              @pressEnter="handleAddLabel"
            />
            <div class="color-picker-wrapper">
              <input
                type="color"
                v-model="newLabelColor"
                class="color-picker"
              />
            </div>
            <Button type="primary" class="add-label-btn" @click="handleAddLabel">+ 添加</Button>
          </div>
          <div class="label-list">
            <div
              v-for="label in labels"
              :key="label.id"
              class="label-item"
            >
              <div class="label-color" :style="{ backgroundColor: label.color }"></div>
              <span class="label-name">{{ label.name }}</span>
              <div class="label-actions">
                <Button type="text" size="small" @click="handleEditLabel(label)">
                  <template #icon><Icon icon="ant-design:edit-outlined" /></template>
                </Button>
                <Button type="text" size="small" @click="handleDeleteLabel(label.id)">
                  <template #icon><Icon icon="ant-design:close-outlined" /></template>
                </Button>
              </div>
            </div>
          </div>
        </div>

        <!-- 标注列表 -->
        <div class="annotation-list">
          <div class="section-title">标注列表</div>
          <div class="annotation-items">
            <div
              v-for="(annotation, index) in currentAnnotations"
              :key="annotation.id || index"
              class="annotation-item"
            >
              <div class="annotation-dot" :style="{ backgroundColor: annotation.color || '#52c41a' }"></div>
              <span class="annotation-label">{{ annotation.label }}</span>
              <Button
                type="text"
                size="small"
                @click="handleDeleteAnnotation(annotation.id || index)"
              >
                <template #icon><Icon icon="ant-design:delete-outlined" /></template>
              </Button>
            </div>
            <div v-if="currentAnnotations.length === 0" class="empty-annotations">
              暂无标注
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 模态框组件 -->
    <AILabelModal ref="aiLabelModalRef" @success="handleAILabelSuccess" />
    <ImportDatasetModal ref="importModalRef" @success="handleImportSuccess" />
    <ExportDatasetModal ref="exportModalRef" @success="handleExportSuccess" />
    <SettingsModal ref="settingsModalRef" />
  </div>
</template>

<script lang="ts" setup>
import { ref, reactive, computed, onMounted, onUnmounted, nextTick, watch } from 'vue';
import { useMessage } from '@/hooks/web/useMessage';
import { Icon } from '@/components/Icon';
import { useRoute } from 'vue-router';
import { Button, Space } from 'ant-design-vue';
import {
  getAutoLabelTask,
  labelSingleImage,
} from '@/api/device/auto-label';
import { 
  getDatasetImagePage, 
  getDatasetTagPage,
  createDatasetTag,
  updateDatasetTag,
  deleteDatasetTag,
  getDatasetImage,
  updateDatasetImage
} from '@/api/device/dataset';
import AILabelModal from './AILabelModal/index.vue';
import ImportDatasetModal from './ImportDatasetModal/index.vue';
import ExportDatasetModal from './ExportDatasetModal/index.vue';
import SettingsModal from './SettingsModal/index.vue';

defineOptions({ name: 'AutoLabel' });

const { createMessage } = useMessage();
const route = useRoute();

// 数据集ID
const datasetId = ref<number | undefined>(undefined);

// 搜索关键词
const searchKeyword = ref('');

// 图片列表
const imageList = ref<any[]>([]);
const filteredImageList = computed(() => {
  if (!searchKeyword.value) return imageList.value;
  return imageList.value.filter(img => 
    img.name?.toLowerCase().includes(searchKeyword.value.toLowerCase())
  );
});

// 当前选中的图片
const currentImageId = ref<number | undefined>(undefined);
const currentImage = computed(() => {
  return imageList.value.find(img => img.id === currentImageId.value);
});

// 选择模式
const selectMode = ref<'single' | 'multiple'>('multiple');
const selectAll = ref(false);
const selectedImageIds = ref<number[]>([]);

// 标注工具
const annotationTools = [
  { id: 'rect', name: '矩形框', icon: 'ant-design:border-outlined' },
  { id: 'polygon', name: '多边形', icon: 'ant-design:appstore-outlined' },
  { id: 'crop', name: '裁剪', icon: 'ant-design:scissor-outlined' },
  { id: 'pan', name: '拖动', icon: 'ant-design:drag-outlined' },
];
const activeTool = ref('rect');

// 标签管理
const labels = ref<any[]>([]);
const newLabelName = ref('');
const newLabelColor = ref('#52c41a');
const editingLabel = ref<any>(null);

// 当前图片的标注
const currentAnnotations = ref<any[]>([]);

// 图像信息
const imageInfo = ref<{ label?: string; personCount?: number } | null>(null);

// Canvas相关
const imageElement = ref<HTMLImageElement | null>(null);
const annotationCanvas = ref<HTMLCanvasElement | null>(null);
let canvasContext: CanvasRenderingContext2D | null = null;

// 模态框引用
const aiLabelModalRef = ref();
const importModalRef = ref();
const exportModalRef = ref();
const settingsModalRef = ref();

// AI标注表单
const aiLabelForm = reactive({
  model_service_id: undefined,
  confidence_threshold: 0.5,
  autoSwitchNext: false,
});

// 批量标注任务相关
const currentTaskId = ref<number | undefined>(undefined);
const taskProgressTimer = ref<any>(null);
const taskProgress = ref<any>(null);

// 加载数据集图片
const loadDatasetImages = async () => {
  if (!datasetId.value) return;
  
  try {
    const res = await getDatasetImagePage({
      datasetId: datasetId.value,
      pageNo: 1,
      pageSize: 1000,
    });
    
    if (res.code === 0) {
      imageList.value = (res.data?.list || []).map((img: any) => ({
        ...img,
        annotations: img.annotations ? (typeof img.annotations === 'string' ? JSON.parse(img.annotations) : img.annotations) : []
      }));
      // 如果有图片，默认选中第一张
      if (imageList.value.length > 0 && !currentImageId.value) {
        selectImage(imageList.value[0]);
      }
    }
  } catch (error) {
    console.error('加载图片列表失败:', error);
    createMessage.error('加载图片列表失败');
  }
};

// 加载标签列表
const loadLabels = async () => {
  if (!datasetId.value) return;
  
  try {
    const res = await getDatasetTagPage({
      datasetId: datasetId.value,
      pageNo: 1,
      pageSize: 1000,
    });
    
    if (res.code === 0) {
      labels.value = (res.data?.list || []).map((tag: any) => ({
        id: tag.id,
        name: tag.name,
        color: tag.color || '#52c41a',
        shortcut: tag.shortcut,
        description: tag.description
      }));
    }
  } catch (error) {
    console.error('加载标签列表失败:', error);
    createMessage.error('加载标签列表失败');
  }
};

// 搜索处理
const handleSearch = () => {
  // 搜索逻辑已在computed中实现
};

// 切换选择模式
const toggleSelectMode = () => {
  selectMode.value = selectMode.value === 'multiple' ? 'single' : 'multiple';
};

// 全选/取消全选
const handleSelectAll = (e: any) => {
  if (e.target.checked) {
    selectedImageIds.value = filteredImageList.value.map(img => img.id);
  } else {
    selectedImageIds.value = [];
  }
};

// 切换图片选择
const toggleImageSelect = (imageId: number) => {
  const index = selectedImageIds.value.indexOf(imageId);
  if (index > -1) {
    selectedImageIds.value.splice(index, 1);
  } else {
    if (selectMode.value === 'single') {
      selectedImageIds.value = [imageId];
    } else {
      selectedImageIds.value.push(imageId);
    }
  }
};

// 选择图片
const selectImage = (image: any) => {
  currentImageId.value = image.id;
  // 加载该图片的标注
  loadImageAnnotations(image.id);
  // 更新图像信息
  updateImageInfo(image);
};

// 加载图片标注
const loadImageAnnotations = async (imageId: number) => {
  try {
    const res = await getDatasetImage({ id: imageId });
    if (res.code === 0 && res.data) {
      const image = res.data;
      let annotations: any[] = [];
      if (image.annotations) {
        try {
          annotations = typeof image.annotations === 'string' 
            ? JSON.parse(image.annotations) 
            : image.annotations;
        } catch (e) {
          console.error('解析标注数据失败:', e);
          annotations = [];
        }
      }
      
      // 将标注数据转换为显示格式
      currentAnnotations.value = annotations.map((ann: any, index: number) => {
        const label = labels.value.find(l => l.name === ann.class || l.id === ann.labelId);
        return {
          id: ann.id || index,
          label: ann.class || ann.label || '',
          labelId: ann.labelId,
          color: label?.color || '#52c41a',
          points: ann.points || [],
          confidence: ann.confidence,
          bbox: ann.bbox,
          type: ann.type || 'rectangle'
        };
      });
      
      // 绘制标注框
      nextTick(() => {
        drawAnnotations();
      });
    }
  } catch (error) {
    console.error('加载图片标注失败:', error);
    currentAnnotations.value = [];
  }
};

// 更新图像信息
const updateImageInfo = (image: any) => {
  // TODO: 从API获取图像信息
  imageInfo.value = {
    label: '上罐',
    personCount: 0,
  };
};

// 图像加载完成
const handleImageLoad = () => {
  nextTick(() => {
    initCanvas();
    // 延迟一下确保图片完全加载
    setTimeout(() => {
      drawAnnotations();
    }, 100);
  });
};

// 初始化Canvas
const initCanvas = () => {
  if (!annotationCanvas.value || !imageElement.value) return;
  
  const canvas = annotationCanvas.value;
  const img = imageElement.value;
  
  // 使用图片的实际显示尺寸
  const rect = img.getBoundingClientRect();
  canvas.width = rect.width;
  canvas.height = rect.height;
  
  // 设置canvas样式以匹配图片位置
  canvas.style.width = `${rect.width}px`;
  canvas.style.height = `${rect.height}px`;
  
  canvasContext = canvas.getContext('2d');
  if (canvasContext) {
    canvasContext.strokeStyle = '#52c41a';
    canvasContext.lineWidth = 2;
    canvasContext.textBaseline = 'top';
  }
};

// 绘制标注框
const drawAnnotations = () => {
  if (!canvasContext || !annotationCanvas.value || !imageElement.value) return;
  
  const ctx = canvasContext;
  const canvas = annotationCanvas.value;
  const img = imageElement.value;
  
  // 清空画布
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  
  // 获取图片的实际显示尺寸和原始尺寸
  const displayWidth = img.offsetWidth || img.clientWidth;
  const displayHeight = img.offsetHeight || img.clientHeight;
  const naturalWidth = img.naturalWidth || displayWidth;
  const naturalHeight = img.naturalHeight || displayHeight;
  
  // 计算缩放比例
  const scaleX = displayWidth / naturalWidth;
  const scaleY = displayHeight / naturalHeight;
  
  // 绘制标注框
  currentAnnotations.value.forEach((anno) => {
    if (!anno.points || anno.points.length === 0) {
      // 如果有bbox，转换为points
      if (anno.bbox && Array.isArray(anno.bbox) && anno.bbox.length >= 4) {
        const [x1, y1, x2, y2] = anno.bbox;
        anno.points = [[x1, y1], [x2, y1], [x2, y2], [x1, y2]];
      } else {
        return;
      }
    }
    
    ctx.strokeStyle = anno.color || '#52c41a';
    ctx.lineWidth = 2;
    ctx.font = 'bold 12px Arial';
    
    if (anno.type === 'rectangle' && anno.points.length >= 4) {
      // 矩形框
      const xs = anno.points.map((p: number[]) => p[0] * scaleX);
      const ys = anno.points.map((p: number[]) => p[1] * scaleY);
      const x = Math.min(...xs);
      const y = Math.min(...ys);
      const width = Math.max(...xs) - x;
      const height = Math.max(...ys) - y;
      
      // 绘制矩形框
      ctx.strokeRect(x, y, width, height);
      
      // 绘制标签文字背景
      const labelText = anno.label || '';
      const confidenceText = anno.confidence ? ` (${(anno.confidence * 100).toFixed(1)}%)` : '';
      const fullText = labelText + confidenceText;
      const textMetrics = ctx.measureText(fullText);
      const textHeight = 16;
      const textPadding = 4;
      
      ctx.fillStyle = anno.color || '#52c41a';
      ctx.fillRect(x, y - textHeight, textMetrics.width + textPadding * 2, textHeight);
      
      // 绘制标签文字
      ctx.fillStyle = '#fff';
      ctx.fillText(fullText, x + textPadding, y - textHeight + 3);
    } else if (anno.points.length >= 2) {
      // 多边形
      ctx.beginPath();
      anno.points.forEach((point: number[], index: number) => {
        const x = point[0] * scaleX;
        const y = point[1] * scaleY;
        if (index === 0) {
          ctx.moveTo(x, y);
        } else {
          ctx.lineTo(x, y);
        }
      });
      ctx.closePath();
      ctx.stroke();
      
      // 绘制标签文字
      if (anno.points.length > 0) {
        const firstPoint = anno.points[0];
        const x = firstPoint[0] * scaleX;
        const y = firstPoint[1] * scaleY;
        const labelText = anno.label || '';
        const textMetrics = ctx.measureText(labelText);
        
        ctx.fillStyle = anno.color || '#52c41a';
        ctx.fillRect(x, y - 16, textMetrics.width + 8, 16);
        
        ctx.fillStyle = '#fff';
        ctx.fillText(labelText, x + 4, y - 13);
      }
    }
  });
};

// Canvas鼠标事件
const handleCanvasMouseDown = (e: MouseEvent) => {
  // TODO: 实现标注绘制逻辑
};

const handleCanvasMouseMove = (e: MouseEvent) => {
  // TODO: 实现标注绘制逻辑
};

const handleCanvasMouseUp = (e: MouseEvent) => {
  // TODO: 实现标注绘制逻辑
};

// 设置活动工具
const setActiveTool = (toolId: string) => {
  activeTool.value = toolId;
};

// 添加标签
const handleAddLabel = async () => {
  if (!newLabelName.value.trim()) {
    createMessage.warning('请输入标签名称');
    return;
  }
  
  if (!datasetId.value) {
    createMessage.warning('请先选择数据集');
    return;
  }
  
  try {
    // 生成快捷键（使用下一个可用的数字）
    const maxShortcut = labels.value.length > 0 
      ? Math.max(...labels.value.map(l => l.shortcut || 0))
      : 0;
    
    const res = await createDatasetTag({
      datasetId: datasetId.value,
      name: newLabelName.value.trim(),
      color: newLabelColor.value,
      shortcut: maxShortcut + 1,
      description: `标签: ${newLabelName.value.trim()}`
    });
    
    if (res.code === 0) {
      createMessage.success('标签添加成功');
      newLabelName.value = '';
      newLabelColor.value = '#52c41a';
      await loadLabels();
    } else {
      createMessage.error(res.msg || '标签添加失败');
    }
  } catch (error) {
    console.error('添加标签失败:', error);
    createMessage.error('添加标签失败');
  }
};

// 编辑标签
const handleEditLabel = async (label: any) => {
  editingLabel.value = { ...label };
  newLabelName.value = label.name;
  newLabelColor.value = label.color;
  
  // 使用模态框或直接编辑
  // 这里简化处理，直接更新
  try {
    const res = await updateDatasetTag({
      id: label.id,
      datasetId: datasetId.value,
      name: newLabelName.value,
      color: newLabelColor.value,
      shortcut: label.shortcut,
      description: label.description || ''
    });
    
    if (res.code === 0) {
      createMessage.success('标签更新成功');
      await loadLabels();
      editingLabel.value = null;
      newLabelName.value = '';
      newLabelColor.value = '#52c41a';
    } else {
      createMessage.error(res.msg || '标签更新失败');
    }
  } catch (error) {
    console.error('更新标签失败:', error);
    createMessage.error('更新标签失败');
  }
};

// 删除标签
const handleDeleteLabel = async (labelId: number) => {
  try {
    const res = await deleteDatasetTag(labelId);
    if (res.code === 0) {
      createMessage.success('标签删除成功');
      await loadLabels();
    } else {
      createMessage.error(res.msg || '标签删除失败');
    }
  } catch (error) {
    console.error('删除标签失败:', error);
    createMessage.error('删除标签失败');
  }
};

// 删除标注
const handleDeleteAnnotation = (annotationId: number | string) => {
  const index = currentAnnotations.value.findIndex(a => (a.id || 0) === annotationId);
  if (index > -1) {
    currentAnnotations.value.splice(index, 1);
    drawAnnotations();
  }
};

// 删除选中的图片
const handleDeleteSelected = () => {
  if (selectedImageIds.value.length === 0) {
    createMessage.warning('请先选择要删除的图片');
    return;
  }
  // TODO: 实现删除逻辑
  createMessage.info('删除功能待实现');
};

// 顶部按钮处理
const handleImportDataset = () => {
  (window as any).__currentDatasetId__ = datasetId.value;
  importModalRef.value?.openModal();
};

const handleAILabel = () => {
  (window as any).__currentDatasetId__ = datasetId.value;
  aiLabelModalRef.value?.openModal();
};

const handleClear = () => {
  currentAnnotations.value = [];
  drawAnnotations();
  createMessage.success('已清除当前标注');
};

const handleSave = async () => {
  if (!currentImageId.value) {
    createMessage.warning('请先选择一张图片');
    return;
  }
  
  if (!datasetId.value) {
    createMessage.warning('请先选择数据集');
    return;
  }
  
  try {
    // 将标注数据转换为后端格式
    const annotationsData = currentAnnotations.value.map(ann => ({
      class: ann.label,
      labelId: ann.labelId,
      points: ann.points,
      confidence: ann.confidence,
      bbox: ann.bbox,
      type: ann.type || 'rectangle',
      auto: ann.auto || false
    }));
    
    const res = await updateDatasetImage({
      id: currentImageId.value,
      datasetId: datasetId.value,
      annotations: JSON.stringify(annotationsData),
      completed: currentAnnotations.value.length > 0 ? 1 : 0,
      modificationCount: (currentImage.value?.modificationCount || 0) + 1
    });
    
    if (res.code === 0) {
      createMessage.success('保存成功');
      // 更新图片列表中的标注状态
      const imageIndex = imageList.value.findIndex(img => img.id === currentImageId.value);
      if (imageIndex > -1) {
        imageList.value[imageIndex].annotations = annotationsData;
        imageList.value[imageIndex].completed = currentAnnotations.value.length > 0 ? 1 : 0;
      }
      
      // 如果设置了自动切换，切换到下一张
      if (aiLabelForm.autoSwitchNext) {
        switchToNextImage();
      }
      
      // 更新全局表单数据
      (window as any).__currentAILabelForm__ = aiLabelForm;
    } else {
      createMessage.error(res.msg || '保存失败');
    }
  } catch (error) {
    console.error('保存标注失败:', error);
    createMessage.error('保存标注失败');
  }
};

// 切换到下一张图片
const switchToNextImage = () => {
  const currentIndex = imageList.value.findIndex(img => img.id === currentImageId.value);
  if (currentIndex >= 0 && currentIndex < imageList.value.length - 1) {
    selectImage(imageList.value[currentIndex + 1]);
  } else {
    createMessage.info('已经是最后一张图片');
  }
};

const handleExport = () => {
  (window as any).__currentDatasetId__ = datasetId.value;
  (window as any).__currentLabels__ = labels.value;
  const exportForm = exportModalRef.value?.form;
  if (exportForm) {
    exportForm.format = 'yolo';
    exportForm.train_ratio = 0.7;
    exportForm.val_ratio = 0.2;
    exportForm.test_ratio = 0.1;
    exportForm.sampleType = 'all';
    exportForm.selectedClasses = labels.value.map(l => l.name);
    exportForm.filePrefix = '';
  }
  // 使用 nextTick 确保 labels 已更新
  nextTick(() => {
    exportModalRef.value?.openModal();
  });
};

// 设置模态框
const handleSettings = () => {
  settingsModalRef.value?.loadInstalledModels();
  settingsModalRef.value?.loadYOLO11Config();
  settingsModalRef.value?.openModal();
};

// AI标注成功回调
const handleAILabelSuccess = (data: any) => {
  if (data?.taskId) {
    currentTaskId.value = data.taskId;
    // 开始监听任务进度
    startTaskProgressMonitoring(data.taskId);
  }
  // 更新表单数据
  if (data?.form) {
    Object.assign(aiLabelForm, data.form);
  }
  // 刷新图片列表
  loadDatasetImages();
};

// 单张图片AI标注
const handleLabelCurrentImage = async () => {
  if (!currentImageId.value) {
    createMessage.warning('请先选择一张图片');
    return;
  }
  
  if (!datasetId.value) {
    createMessage.warning('请先选择数据集');
    return;
  }
  
  // 如果没有选择模型，先打开AI标注模态框
  if (!aiLabelForm.model_service_id) {
    (window as any).__currentDatasetId__ = datasetId.value;
    aiLabelModalRef.value?.loadAIServiceList();
    aiLabelModalRef.value?.openModal();
    return;
  }
  
  try {
    aiLabelLoading.value = true;
    const res = await labelSingleImage(datasetId.value, currentImageId.value, {
      model_service_id: aiLabelForm.model_service_id,
      confidence_threshold: aiLabelForm.confidence_threshold,
    });
    
    if (res.code === 0) {
      createMessage.success(`AI标注完成，检测到 ${res.data?.count || 0} 个对象`);
      
      // 将AI标注结果转换为显示格式
      if (res.data?.annotations && Array.isArray(res.data.annotations)) {
        const aiAnnotations = res.data.annotations.map((ann: any, index: number) => {
          const label = labels.value.find(l => l.name === ann.class);
          return {
            id: ann.id || Date.now() + index,
            label: ann.class || '',
            labelId: ann.labelId,
            color: label?.color || '#52c41a',
            points: ann.points || [],
            confidence: ann.confidence,
            bbox: ann.bbox,
            type: ann.type || 'rectangle',
            auto: true
          };
        });
        
        // 合并现有标注和AI标注（避免重复）
        const existingLabels = currentAnnotations.value.map(a => a.label);
        const newAnnotations = aiAnnotations.filter((a: any) => !existingLabels.includes(a.label));
        currentAnnotations.value = [...currentAnnotations.value, ...newAnnotations];
        
        // 重新绘制标注框
        nextTick(() => {
          drawAnnotations();
        });
      }
      
      // 刷新图片列表
      await loadDatasetImages();
    } else {
      createMessage.error(res.msg || 'AI标注失败');
    }
  } catch (error) {
    console.error('AI标注失败:', error);
    createMessage.error('AI标注失败');
  } finally {
    aiLabelLoading.value = false;
  }
};

// 监听任务进度
const startTaskProgressMonitoring = (taskId: number) => {
  if (taskProgressTimer.value) {
    clearInterval(taskProgressTimer.value);
  }
  
  taskProgressTimer.value = setInterval(async () => {
    try {
      const res = await getAutoLabelTask(datasetId.value!, taskId);
      if (res.code === 0) {
        taskProgress.value = res.data;
        
        // 如果任务完成，停止监听
        if (res.data.status === 'COMPLETED' || res.data.status === 'FAILED') {
          if (taskProgressTimer.value) {
            clearInterval(taskProgressTimer.value);
            taskProgressTimer.value = null;
          }
          
          if (res.data.status === 'COMPLETED') {
            createMessage.success(`标注任务完成！成功: ${res.data.success_count}, 失败: ${res.data.failed_count}`);
          } else {
            createMessage.error(`标注任务失败: ${res.data.error_message || '未知错误'}`);
          }
          
          // 刷新图片列表
          await loadDatasetImages();
        }
      }
    } catch (error) {
      console.error('获取任务进度失败:', error);
    }
  }, 2000); // 每2秒刷新一次
};

// 导入成功回调
const handleImportSuccess = () => {
  loadDatasetImages();
  loadLabels();
};

// 导出成功回调
const handleExportSuccess = () => {
  // 导出成功后的处理
};

// 监听全选状态
watch(selectedImageIds, (newVal) => {
  selectAll.value = newVal.length === filteredImageList.value.length && filteredImageList.value.length > 0;
}, { deep: true });

// 窗口大小变化时重新绘制
const handleResize = () => {
  nextTick(() => {
    initCanvas();
    drawAnnotations();
  });
};

// 组件挂载
onMounted(() => {
  // 从路由参数获取数据集ID
  const id = route.params.id;
  if (id) {
    datasetId.value = Number(id);
    (window as any).__currentDatasetId__ = datasetId.value;
    loadDatasetImages();
    loadLabels();
  }
  
  // 恢复AI标注表单数据
  if ((window as any).__currentAILabelForm__) {
    Object.assign(aiLabelForm, (window as any).__currentAILabelForm__);
  }
  
  // 监听窗口大小变化
  window.addEventListener('resize', handleResize);
});

// 组件卸载
onUnmounted(() => {
  // 清理资源
  if (taskProgressTimer.value) {
    clearInterval(taskProgressTimer.value);
    taskProgressTimer.value = null;
  }
  
  // 移除事件监听
  window.removeEventListener('resize', handleResize);
});
</script>

<style lang="less" scoped>
.auto-label-container {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: #f0f2f5;
  overflow: hidden;
}

// 顶部导航栏
.header-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 24px;
  background: #fff;
  border-bottom: 1px solid #e8e8e8;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);

  .header-left {
    .app-title {
      margin: 0;
      font-size: 20px;
      font-weight: 600;
      color: #1890ff;
    }
  }

  .header-right {
    .ai-label-btn {
      background: #1890ff;
      border-color: #1890ff;
      color: #fff;
      
      &:hover {
        background: #40a9ff;
        border-color: #40a9ff;
      }
    }
  }
}

// 主布局：三列
.main-layout {
  display: flex;
  flex: 1;
  overflow: hidden;
}

// 左侧边栏
.left-sidebar {
  width: 280px;
  background: #fff;
  border-right: 1px solid #e8e8e8;
  display: flex;
  flex-direction: column;
  overflow: hidden;

  .search-section {
    padding: 16px;
    border-bottom: 1px solid #e8e8e8;
  }

  .action-section {
    padding: 12px 16px;
    border-bottom: 1px solid #e8e8e8;
    display: flex;
    align-items: center;

    .image-count {
      font-size: 14px;
      color: #666;
      margin: 0 8px;
    }
  }

  .image-list {
    flex: 1;
    overflow-y: auto;
    padding: 8px 0;

      .image-item {
        display: flex;
        align-items: center;
        padding: 8px 16px;
        cursor: pointer;
        transition: all 0.2s;
        position: relative;
        border-left: 3px solid transparent;

        &:hover {
          background: #f5f5f5;
        }

        &.active {
          background: #e6f7ff;
          color: #1890ff;
          font-weight: 500;
          border-left-color: #1890ff;
          
          .image-checkbox {
            :deep(.ant-checkbox-checked .ant-checkbox-inner) {
              background-color: #1890ff;
              border-color: #1890ff;
            }
          }
        }

        &.selected {
          background: #f0f0f0;
        }

        &.annotated {
          .image-name::after {
            content: ' ✓';
            color: #52c41a;
            font-weight: bold;
          }
        }

      .image-checkbox {
        margin-right: 8px;
        
        :deep(.ant-checkbox-inner) {
          border-radius: 4px;
        }
      }

      .image-index {
        min-width: 30px;
        font-size: 14px;
        color: #666;
        margin-right: 8px;
      }

      .image-name {
        flex: 1;
        font-size: 14px;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
      }

      .annotated-badge {
        display: none;
      }
    }
  }
}

// 中间主内容区域
.center-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: #f5f5f5;
  position: relative;
  overflow: hidden;

  .annotation-toolbar {
    position: absolute;
    top: 16px;
    left: 16px;
    z-index: 10;
    display: flex;
    flex-direction: column;
    gap: 4px;
    background: rgba(255, 255, 255, 0.95);
    padding: 4px;
    border-radius: 4px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);

    .tool-button {
      width: 36px;
      height: 36px;
      display: flex;
      align-items: center;
      justify-content: center;
      cursor: pointer;
      border-radius: 4px;
      transition: all 0.2s;
      font-size: 16px;
      color: #666;

      &:hover {
        background: #f0f0f0;
      }

      &.active {
        background: #1890ff;
        color: #fff;
      }
    }
  }

  .image-display-area {
    flex: 1;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 20px;
    position: relative;
    overflow: auto;

    .image-wrapper {
      position: relative;
      display: inline-block;
      max-width: 100%;
      max-height: 100%;

      img {
        max-width: 100%;
        max-height: 100%;
        display: block;
      }

      .annotation-overlay {
        position: absolute;
        top: 0;
        left: 0;
        pointer-events: auto;
        cursor: crosshair;
        image-rendering: -webkit-optimize-contrast;
        image-rendering: crisp-edges;
      }
    }

    .image-info-overlay {
      position: absolute;
      top: 20px;
      left: 20px;
      z-index: 5;
      background: transparent;
      padding: 0;
      font-size: 14px;
      font-weight: 500;

      .info-item {
        margin-bottom: 4px;
        color: #52c41a;
        text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.5);
      }
    }
  }

  .empty-image {
    flex: 1;
    display: flex;
    align-items: center;
    justify-content: center;
  }
}

// 右侧边栏
.right-sidebar {
  width: 320px;
  background: #fff;
  border-left: 1px solid #e8e8e8;
  display: flex;
  flex-direction: column;
  overflow: hidden;

  .section-title {
    padding: 16px;
    font-size: 16px;
    font-weight: 600;
    border-bottom: 1px solid #e8e8e8;
    background: #fafafa;
  }

  .label-management {
    border-bottom: 1px solid #e8e8e8;

    .add-label-form {
      padding: 16px;
      display: flex;
      gap: 4px;
      align-items: center;

      .color-picker-wrapper {
        .color-picker {
          width: 40px;
          height: 32px;
          border: 1px solid #d9d9d9;
          border-radius: 4px;
          cursor: pointer;
        }
      }

      .add-label-btn {
        margin-left: 4px;
      }
    }

    .label-list {
      max-height: 300px;
      overflow-y: auto;
      padding: 8px 0;

      .label-item {
        display: flex;
        align-items: center;
        padding: 8px 16px;
        transition: background 0.2s;

        &:hover {
          background: #f5f5f5;
        }

        .label-color {
          width: 20px;
          height: 20px;
          border-radius: 4px;
          margin-right: 8px;
          border: 1px solid #e8e8e8;
        }

        .label-name {
          flex: 1;
          font-size: 14px;
        }

        .label-actions {
          display: flex;
          gap: 4px;
        }
      }
    }
  }

  .annotation-list {
    flex: 1;
    display: flex;
    flex-direction: column;
    overflow: hidden;

    .annotation-items {
      flex: 1;
      overflow-y: auto;
      padding: 8px 0;

      .annotation-item {
        display: flex;
        align-items: center;
        padding: 8px 16px;
        transition: background 0.2s;

        &:hover {
          background: #f5f5f5;
        }

        .annotation-dot {
          width: 8px;
          height: 8px;
          border-radius: 50%;
          margin-right: 8px;
        }

        .annotation-label {
          flex: 1;
          font-size: 14px;
        }

        :deep(.ant-btn) {
          margin-left: 4px;
        }
      }

      .empty-annotations {
        padding: 40px 16px;
        text-align: center;
        color: #999;
        font-size: 14px;
      }
    }
  }
}

</style>