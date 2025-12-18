<template>
  <div class="auto-label-container">
    <!-- 顶部导航栏 -->
    <div class="header-bar">
      <div class="header-left">
        <h1 class="app-title">自动化标注</h1>
      </div>
      <div class="header-right">
        <a-space>
          <a-button @click="handleImportDataset">
            <template #icon><Icon icon="ant-design:upload-outlined" /></template>
            导入数据集
          </a-button>
          <a-button type="primary" class="ai-label-btn" @click="handleAILabel">
            <template #icon><Icon icon="ant-design:robot-outlined" /></template>
            AI自动标注
          </a-button>
          <a-button @click="handleClear">
            <template #icon><Icon icon="ant-design:clear-outlined" /></template>
            清除
          </a-button>
          <a-button @click="handleSave">
            <template #icon><Icon icon="ant-design:save-outlined" /></template>
            保存
          </a-button>
          <a-button @click="handleExport">
            <template #icon><Icon icon="ant-design:export-outlined" /></template>
            导出数据集
          </a-button>
          <a-button @click="handleSettings">
            <template #icon><Icon icon="ant-design:setting-outlined" /></template>
            设置
          </a-button>
        </a-space>
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
          <a-space>
            <a-button type="text" size="small" @click="toggleSelectMode">
              <Icon :icon="selectMode === 'multiple' ? 'ant-design:check-square-outlined' : 'ant-design:border-outlined'" />
            </a-button>
            <span class="image-count">共 {{ filteredImageList.length }} 张图片</span>
            <a-checkbox v-model:checked="selectAll" @change="handleSelectAll">全选</a-checkbox>
            <a-button type="text" danger size="small" @click="handleDeleteSelected">
              <template #icon><Icon icon="ant-design:delete-outlined" /></template>
            </a-button>
          </a-space>
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
            <a-button type="primary" @click="handleAddLabel">+ 添加</a-button>
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
                <a-button type="text" size="small" @click="handleEditLabel(label)">
                  <Icon icon="ant-design:edit-outlined" />
                </a-button>
                <a-button type="text" size="small" danger @click="handleDeleteLabel(label.id)">
                  <Icon icon="ant-design:close-outlined" />
                </a-button>
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
              <a-button
                type="text"
                size="small"
                danger
                @click="handleDeleteAnnotation(annotation.id || index)"
              >
                <Icon icon="ant-design:delete-outlined" />
              </a-button>
            </div>
            <div v-if="currentAnnotations.length === 0" class="empty-annotations">
              暂无标注
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- AI自动标注设置模态框 -->
    <a-modal
      v-model:open="aiLabelModalVisible"
      :title="null"
      width="600px"
      :footer="null"
      :closable="true"
      :mask-closable="false"
      class="ai-auto-label-modal"
    >
      <template #title>
        <div class="modal-title">
          <Icon icon="ant-design:robot-outlined" class="title-icon" />
          <span>AI自动标注设置</span>
        </div>
      </template>
      
      <a-form
        :model="aiLabelForm"
        :label-col="{ span: 6 }"
        :wrapper-col="{ span: 18 }"
        :rules="aiLabelFormRules"
        ref="aiLabelFormRef"
        class="ai-label-form"
      >
        <a-form-item label="选择模型:" name="model_service_id" required>
          <a-select
            v-model:value="aiLabelForm.model_service_id"
            placeholder="-- 请选择模型 --"
            :loading="serviceLoading"
            show-search
            :filter-option="filterServiceOption"
            allow-clear
          >
            <a-select-option
              v-for="service in aiServiceList"
              :key="service.id"
              :value="service.id"
            >
              {{ service.service_name }}
            </a-select-option>
          </a-select>
          <div class="form-hint">
            请先在设置中安装YOLO11并下载或上传模型
          </div>
        </a-form-item>
        
        <a-form-item label="置信度阈值:" name="confidence_threshold" required>
          <div class="confidence-slider-wrapper">
            <a-slider
              v-model:value="aiLabelForm.confidence_threshold"
              :min="0.1"
              :max="0.9"
              :step="0.05"
              :marks="{ 0.1: '0.1', 0.5: '0.5', 0.9: '0.9' }"
            />
            <div class="confidence-value">{{ aiLabelForm.confidence_threshold }}</div>
          </div>
          <div class="form-hint">
            置信度越高,检测越严格,框越少
          </div>
        </a-form-item>
        
        <a-form-item :wrapper-col="{ offset: 6, span: 18 }">
          <a-checkbox v-model:checked="aiLabelForm.autoSwitchNext">
            保存后自动切换到下一张图片
          </a-checkbox>
        </a-form-item>
      </a-form>
      
      <template #footer>
        <div class="modal-footer">
          <a-button @click="handleCancelAILabel">取消</a-button>
          <a-button 
            type="primary" 
            :loading="aiLabelLoading"
            @click="handleStartAILabel"
            class="start-ai-label-btn"
          >
            <template #icon><Icon icon="ant-design:play-circle-outlined" /></template>
            开启AI标注
          </a-button>
        </div>
      </template>
    </a-modal>

    <!-- 导入数据集模态框 -->
    <a-modal
      v-model:open="importModalVisible"
      title="导入数据集"
      width="500px"
      @ok="handleConfirmImport"
      @cancel="handleCancelImport"
      :confirm-loading="importLoading"
    >
      <a-upload
        v-model:file-list="importFileList"
        :before-upload="beforeImportUpload"
        accept=".zip"
        :max-count="1"
        :show-upload-list="true"
      >
        <a-button>
          <template #icon><Icon icon="ant-design:upload-outlined" /></template>
          选择ZIP文件
        </a-button>
      </a-upload>
      <div class="upload-hint">
        <p>支持ZIP格式压缩包，最大200MB</p>
        <p>压缩包内应包含图片文件（JPG/PNG/JPEG等格式）</p>
      </div>
    </a-modal>

    <!-- 导出数据集模态框 -->
    <a-modal
      v-model:open="exportModalVisible"
      title="导出数据集"
      width="500px"
      @ok="handleConfirmExport"
      @cancel="handleCancelExport"
      :confirm-loading="exportLoading"
    >
      <a-form
        :model="exportForm"
        :label-col="{ span: 8 }"
        :wrapper-col="{ span: 16 }"
      >
        <a-form-item label="导出格式:">
          <a-select v-model:value="exportForm.format" placeholder="请选择导出格式">
            <a-select-option value="yolo">YOLO格式</a-select-option>
            <a-select-option value="coco">COCO格式</a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="训练集比例:">
          <a-input-number
            v-model:value="exportForm.train_ratio"
            :min="0"
            :max="1"
            :step="0.1"
            :precision="2"
            style="width: 100%"
          />
        </a-form-item>
        <a-form-item label="验证集比例:">
          <a-input-number
            v-model:value="exportForm.val_ratio"
            :min="0"
            :max="1"
            :step="0.1"
            :precision="2"
            style="width: 100%"
          />
        </a-form-item>
        <a-form-item label="测试集比例:">
          <a-input-number
            v-model:value="exportForm.test_ratio"
            :min="0"
            :max="1"
            :step="0.1"
            :precision="2"
            style="width: 100%"
          />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script lang="ts" setup>
import { ref, reactive, computed, onMounted, onUnmounted, nextTick, watch } from 'vue';
import { useMessage } from '@/hooks/web/useMessage';
import { Icon } from '@/components/Icon';
import { useRoute } from 'vue-router';
import {
  startAutoLabel,
  getAIServiceList,
  exportLabeledDataset
} from '@/api/device/auto-label';
import { getDatasetImagePage, uploadDatasetImage } from '@/api/device/dataset';

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
const labels = ref<any[]>([
  { id: 1, name: 'safehat', color: '#52c41a' },
  { id: 2, name: 'head', color: '#ff4d4f' },
  { id: 3, name: 'person', color: '#1890ff' },
  { id: 4, name: 'tv', color: '#13c2c2' },
  { id: 5, name: 'hard hat', color: '#52c41a' },
]);
const newLabelName = ref('');
const newLabelColor = ref('#52c41a');

// 当前图片的标注
const currentAnnotations = ref<any[]>([]);

// 图像信息
const imageInfo = ref<{ label?: string; personCount?: number } | null>(null);

// Canvas相关
const imageElement = ref<HTMLImageElement | null>(null);
const annotationCanvas = ref<HTMLCanvasElement | null>(null);
let canvasContext: CanvasRenderingContext2D | null = null;

// AI自动标注模态框
const aiLabelModalVisible = ref(false);
const aiLabelLoading = ref(false);
const aiLabelFormRef = ref();
const aiLabelForm = reactive({
  model_service_id: undefined,
  confidence_threshold: 0.5,
  autoSwitchNext: false,
});
const aiLabelFormRules = {
  model_service_id: [{ required: true, message: '请选择模型', trigger: 'change' }],
  confidence_threshold: [{ required: true, message: '请设置置信度阈值', trigger: 'change' }],
};

// 导入数据集模态框
const importModalVisible = ref(false);
const importLoading = ref(false);
const importFileList = ref<any[]>([]);

// 导出数据集模态框
const exportModalVisible = ref(false);
const exportLoading = ref(false);
const exportForm = reactive({
  format: 'yolo',
  train_ratio: 0.7,
  val_ratio: 0.2,
  test_ratio: 0.1,
});

// AI服务列表
const aiServiceList = ref([]);
const serviceLoading = ref(false);

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
      imageList.value = res.data?.list || [];
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
  // TODO: 从API加载标注数据
  // 这里先使用模拟数据
  currentAnnotations.value = [
    { id: 1, label: 'safehat', color: '#52c41a' },
    { id: 2, label: 'safehat', color: '#52c41a' },
  ];
  
  // 绘制标注框
  nextTick(() => {
    drawAnnotations();
  });
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
    drawAnnotations();
  });
};

// 初始化Canvas
const initCanvas = () => {
  if (!annotationCanvas.value || !imageElement.value) return;
  
  const canvas = annotationCanvas.value;
  const img = imageElement.value;
  
  canvas.width = img.offsetWidth;
  canvas.height = img.offsetHeight;
  
  canvasContext = canvas.getContext('2d');
  if (canvasContext) {
    canvasContext.strokeStyle = '#52c41a';
    canvasContext.lineWidth = 2;
  }
};

// 绘制标注框
const drawAnnotations = () => {
  if (!canvasContext || !annotationCanvas.value) return;
  
  const ctx = canvasContext;
  const canvas = annotationCanvas.value;
  
  // 清空画布
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  
  // 绘制标注框（示例）
  // TODO: 根据实际标注数据绘制
  currentAnnotations.value.forEach((anno, index) => {
    // 示例：绘制一个矩形框
    const x = 50 + index * 100;
    const y = 50 + index * 80;
    const width = 150;
    const height = 100;
    
    ctx.strokeStyle = anno.color || '#52c41a';
    ctx.strokeRect(x, y, width, height);
    
    // 绘制标签文字
    ctx.fillStyle = anno.color || '#52c41a';
    ctx.font = '12px Arial';
    ctx.fillText(anno.label, x, y - 5);
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
const handleAddLabel = () => {
  if (!newLabelName.value.trim()) {
    createMessage.warning('请输入标签名称');
    return;
  }
  
  const newLabel = {
    id: Date.now(),
    name: newLabelName.value.trim(),
    color: newLabelColor.value,
  };
  
  labels.value.push(newLabel);
  newLabelName.value = '';
  newLabelColor.value = '#52c41a';
};

// 编辑标签
const handleEditLabel = (label: any) => {
  // TODO: 实现编辑标签逻辑
  createMessage.info('编辑功能待实现');
};

// 删除标签
const handleDeleteLabel = (labelId: number) => {
  const index = labels.value.findIndex(l => l.id === labelId);
  if (index > -1) {
    labels.value.splice(index, 1);
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
  importModalVisible.value = true;
  importFileList.value = [];
};

const handleAILabel = () => {
  aiLabelModalVisible.value = true;
  loadAIServiceList();
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
  // TODO: 实现保存标注逻辑
  createMessage.success('保存成功');
};

const handleExport = () => {
  exportModalVisible.value = true;
  // 重置导出表单
  exportForm.format = 'yolo';
  exportForm.train_ratio = 0.7;
  exportForm.val_ratio = 0.2;
  exportForm.test_ratio = 0.1;
};

const handleSettings = () => {
  createMessage.info('设置功能待实现');
};

// 加载AI服务列表
const loadAIServiceList = async () => {
  try {
    serviceLoading.value = true;
    const res = await getAIServiceList();
    
    if (res.code === 0) {
      aiServiceList.value = (res.data || []).filter((s: any) => s.status === 'running');
    } else {
      createMessage.error(res.msg || '加载AI服务列表失败');
    }
  } catch (error) {
    console.error('加载AI服务列表失败:', error);
    createMessage.error('加载AI服务列表失败');
  } finally {
    serviceLoading.value = false;
  }
};

// 开始AI自动标注
const handleStartAILabel = async () => {
  if (!aiLabelFormRef.value) return;
  
  try {
    await aiLabelFormRef.value.validate();
  } catch (error) {
    return;
  }
  
  if (!datasetId.value) {
    createMessage.warning('请先选择数据集');
    return;
  }
  
  try {
    aiLabelLoading.value = true;
    const res = await startAutoLabel(datasetId.value, {
      model_service_id: aiLabelForm.model_service_id,
      confidence_threshold: aiLabelForm.confidence_threshold,
    });
    
    if (res.code === 0) {
      createMessage.success('AI自动标注任务已启动');
      aiLabelModalVisible.value = false;
      // 如果设置了自动切换，在标注完成后自动切换到下一张
      if (aiLabelForm.autoSwitchNext) {
        // TODO: 监听标注完成事件，自动切换图片
      }
      // 刷新图片列表
      await loadDatasetImages();
    } else {
      createMessage.error(res.msg || '启动AI自动标注失败');
    }
  } catch (error) {
    console.error('启动AI自动标注失败:', error);
    createMessage.error('启动AI自动标注失败');
  } finally {
    aiLabelLoading.value = false;
  }
};

const handleCancelAILabel = () => {
  aiLabelModalVisible.value = false;
};

const filterServiceOption = (input: string, option: any) => {
  return option.children.toLowerCase().indexOf(input.toLowerCase()) >= 0;
};

// 导入数据集相关方法
const beforeImportUpload = (file: File) => {
  const isZip = file.type === 'application/zip' || file.name.endsWith('.zip');
  if (!isZip) {
    createMessage.error('只能上传ZIP格式文件');
    return false;
  }
  const isLt200M = file.size / 1024 / 1024 < 200;
  if (!isLt200M) {
    createMessage.error('文件大小不能超过200MB');
    return false;
  }
  return false; // 阻止自动上传
};

const handleConfirmImport = async () => {
  if (importFileList.value.length === 0) {
    createMessage.warning('请选择要导入的ZIP文件');
    return;
  }

  if (!datasetId.value) {
    createMessage.warning('请先选择数据集');
    return;
  }

  try {
    importLoading.value = true;
    const file = importFileList.value[0].originFileObj;
    const formData = new FormData();
    formData.append('file', file);
    formData.append('datasetId', datasetId.value.toString());
    formData.append('isZip', 'true');

    await uploadDatasetImage(formData);
    createMessage.success('导入成功');
    importModalVisible.value = false;
    importFileList.value = [];
    // 刷新图片列表
    await loadDatasetImages();
  } catch (error) {
    console.error('导入失败:', error);
    createMessage.error('导入失败');
  } finally {
    importLoading.value = false;
  }
};

const handleCancelImport = () => {
  importModalVisible.value = false;
  importFileList.value = [];
};

// 导出数据集相关方法
const handleConfirmExport = async () => {
  if (!datasetId.value) {
    createMessage.warning('请先选择数据集');
    return;
  }

  // 验证比例
  const total = exportForm.train_ratio + exportForm.val_ratio + exportForm.test_ratio;
  if (Math.abs(total - 1.0) > 0.01) {
    createMessage.warning('训练集、验证集、测试集比例之和必须为1');
    return;
  }

  try {
    exportLoading.value = true;
    const res = await exportLabeledDataset(datasetId.value, {
      format: exportForm.format,
      train_ratio: exportForm.train_ratio,
      val_ratio: exportForm.val_ratio,
      test_ratio: exportForm.test_ratio,
    });

    // 处理文件下载
    if (res instanceof Blob) {
      const url = window.URL.createObjectURL(res);
      const link = document.createElement('a');
      link.href = url;
      link.download = `dataset_${datasetId.value}_${Date.now()}.zip`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
      createMessage.success('导出成功');
      exportModalVisible.value = false;
    } else {
      createMessage.error('导出失败');
    }
  } catch (error) {
    console.error('导出失败:', error);
    createMessage.error('导出失败');
  } finally {
    exportLoading.value = false;
  }
};

const handleCancelExport = () => {
  exportModalVisible.value = false;
};

// 监听全选状态
watch(selectedImageIds, (newVal) => {
  selectAll.value = newVal.length === filteredImageList.value.length && filteredImageList.value.length > 0;
}, { deep: true });

// 组件挂载
onMounted(() => {
  // 从路由参数获取数据集ID
  const id = route.params.id;
  if (id) {
    datasetId.value = Number(id);
    loadDatasetImages();
  }
});

// 组件卸载
onUnmounted(() => {
  // 清理资源
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
      background: #ffc107;
      border-color: #ffc107;
      color: #000;
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
          background: #fff1f0;
          color: #ff4d4f;
          font-weight: 500;
          border-left-color: #ff4d4f;
          
          .image-checkbox {
            :deep(.ant-checkbox-checked .ant-checkbox-inner) {
              background-color: #ff4d4f;
              border-color: #ff4d4f;
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
      gap: 8px;
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

// AI自动标注弹窗样式
:deep(.ai-auto-label-modal) {
  .ant-modal-header {
    padding: 20px 24px;
    border-bottom: 1px solid #e8e8e8;
    
    .modal-title {
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 18px;
      font-weight: 600;
      color: #1f1f1f;
      
      .title-icon {
        font-size: 20px;
        color: #1890ff;
      }
    }
  }
  
  .ant-modal-body {
    padding: 24px;
  }
  
  .ant-modal-close {
    top: 20px;
    right: 24px;
  }
  
  .ai-label-form {
    .ant-form-item-label {
      > label {
        font-weight: 500;
        color: #333;
      }
    }
    
    .form-hint {
      margin-top: 8px;
      font-size: 12px;
      color: #999;
      line-height: 1.5;
    }
    
    .confidence-slider-wrapper {
      position: relative;
      
      .confidence-value {
        position: absolute;
        top: -8px;
        right: 0;
        font-size: 14px;
        font-weight: 600;
        color: #1890ff;
      }
    }
  }
  
  .modal-footer {
    display: flex;
    justify-content: flex-end;
    gap: 12px;
    padding: 16px 24px;
    border-top: 1px solid #e8e8e8;
    
    .start-ai-label-btn {
      background: #1890ff;
      border-color: #1890ff;
      
      &:hover {
        background: #40a9ff;
        border-color: #40a9ff;
      }
    }
  }
}

// 导入/导出模态框样式
.upload-hint {
  margin-top: 16px;
  padding: 12px;
  background: #f5f5f5;
  border-radius: 4px;
  
  p {
    margin: 4px 0;
    font-size: 12px;
    color: #666;
    line-height: 1.5;
  }
}
</style>