<template>
  <div ref="container" class="annotation-container">
    <!-- 全屏标题 -->
    <div v-show="isFullscreen" class="fullscreen-title">
      <div class="title-content">
        <i class="fas fa-database"></i>
        <span>图像数据集标注</span>
      </div>
    </div>
    <!-- 主内容区 -->
    <div class="main-content">
      <!-- 左侧工具栏 -->
      <div class="toolbar">
        <div
          v-for="tool in tools"
          :key="tool.id"
          class="tool-button"
          :class="{ active: activeTool === tool.id }"
          @click="setActiveTool(tool.id)"
        >
          <Icon :icon="tool.icon"/>
          <span>{{ tool.name }} ({{ tool.shortcut }})</span>
        </div>
      </div>

      <!-- 画布区域 -->
      <div class="canvas-area">
        <div class="image-position-indicator">
          <div class="position-text">
            当前图片: <span class="current-index">{{ globalImageIndex + 1 }}</span> /
            <span class="total-count">{{ totalImages }}</span> <!-- 修改为 totalImages -->
          </div>
        </div>
        <div class="canvas-wrapper">
          <canvas
            ref="canvas"
            class="annotation-canvas"
            @mousedown="handleMouseDown"
            @mousemove="handleMouseMove"
            @mouseup="handleMouseUp"
            @dblclick="handleDoubleClick"
          ></canvas>
        </div>

        <div class="status-indicator">
          <div class="status-header">
            <div class="completion-status" :class="{ completed: currentImage.completed === 1 }">
              {{ currentImage.completed === 1 ? '✅ 已完成标注' : '⏳ 标注中' }}
            </div>
            <div v-if="currentImage.completed === 1" class="modification-info">
              <div>修改次数: {{ currentImage.modificationCount || 0 }}</div>
              <div>最后修改: {{ formatDateTime(currentImage.lastModified) }}</div>
            </div>
          </div>
          <div class="annotation-count">
            <div class="status-dot"></div>
            <span>{{ statusText }}</span>
            <div v-if="!isSaved" class="unsaved-indicator">(未保存)</div>
          </div>
        </div>

        <div class="fullscreen-control" @click="toggleFullscreen">
          <Icon :icon="isFullscreen ? 'fa:compress' : 'fa:expand'"/>
          <span>{{ isFullscreen ? '退出全屏' : '全屏标注' }}</span>
        </div>

        <div class="shortcut-hint">
          <div v-for="hint in shortcutHints" :key="hint.key" class="hint-item">
            <span class="key">{{ hint.key }}</span>
            <span class="text">{{ hint.text }}</span>
          </div>
        </div>
      </div>

      <!-- 右侧标签栏 -->
      <div class="label-panel">
        <!-- 筛选开关部分保持不变 -->
        <div class="filter-section">
          <div class="filter-toggle">
            <label>
              <input type="checkbox" v-model="showOnlyUnannotated">
              <span class="toggle-slider"></span>
            </label>
            <span>仅未标注</span>
            <span class="filter-indicator" v-if="showOnlyUnannotated">
              ({{ filteredImageCount }}张)
            </span>
          </div>
        </div>

        <!-- 修改后的panel-header部分 -->
        <div class="panel-header">
          <span>标签管理</span>
        </div>

        <div class="label-list">
          <div
            v-for="(label, index) in labels"
            :key="label.id"
            class="label-item"
            :class="{ active: currentLabelIndex === index }"
            @click="setCurrentLabel(index)"
          >
            <div class="color-badge" :style="{ backgroundColor: label.color }"></div>
            <div class="label-name">{{ label.name }}</div>
            <div class="label-shortcut">{{ label.shortcut }}</div>
          </div>
        </div>

        <div class="object-layer-section">
          <div class="panel-header">
            <i class="fas fa-layer-group"></i>
            <span>对象图层 ({{ annotations.length }})</span>
          </div>
          <div class="object-list">
            <div
              v-for="(anno, index) in annotations"
              :key="anno.id"
              class="object-item"
              :class="{ selected: selectedAnnotationId === anno.id }"
              @click="selectAnnotation(anno.id)"
            >
              <div class="object-color" :style="{ backgroundColor: anno.color }"></div>
              <div class="object-name">{{ getLabelName(anno.label) }} #{{ index + 1 }}</div>
              <div class="object-actions">
                <button class="delete-btn" @click.stop="deleteAnnotation(anno.id)">
                  <Icon icon="fa:trash"/>
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 图片预览列表 -->
    <div class="image-preview-container">
      <button class="nav-btn prev-btn" @click="changePage(-1)"
              :disabled="currentPage === 1">
        <Icon icon="fa:chevron-left"/>
      </button>
      <div class="preview-list-wrapper">
        <div class="preview-list">
          <div
            v-for="(img, index) in visiblePreviewImages"
            :key="img.id"
            class="preview-item"
            :class="{
            active: globalImageIndex === (currentPage - 1) * previewCount + index,
            annotated: hasAnnotations(img),
            completed: img.completed === 1
          }"
            @click="selectImage((currentPage - 1) * previewCount + index)"
          >
            <img :src="img.path" alt="预览图" class="preview-image"/>
            <div class="preview-status">
              {{ hasAnnotations(img) ? '已标注' : '待标注' }}
            </div>
            <div v-if="img.completed === 1" class="completed-badge">已完成</div>
          </div>
        </div>
      </div>
      <button
        class="nav-btn next-btn"
        @click="changePage(1)"
        :disabled="currentPage >= totalPages"
      >
        <Icon icon="fa:chevron-right"/>
      </button>

      <div class="pagination-control">
        <span class="page-indicator">第 {{ currentPage }} 页 / 共 {{ totalPages }} 页</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import {computed, onMounted, onUnmounted, ref, watch} from 'vue';
import {Icon} from '@/components/Icon';
import {useMessage} from "@/hooks/web/useMessage";
import {useRoute} from "vue-router";
import { debounce } from 'lodash-es';
import {getDatasetImagePage, getDatasetTagPage, updateDatasetImage} from "@/api/device/dataset";

defineOptions({name: 'AnnotationTool'});

const {createMessage} = useMessage();
const route = useRoute();

// 添加事件绑定标志
let eventBound = false;

// 标注数据
const annotations = ref<Annotation[]>([]);
const selectedAnnotationId = ref<number | null>(null);
const annotationCount = computed<number>(() => annotations.value.length);
const statusText = computed<string>(() => `已标注 ${annotationCount.value} 个对象`);
const isSaved = ref(true);

// 新增筛选状态变量
const showOnlyUnannotated = ref(false);
const filteredImageCount = ref(0);

// 添加保存状态锁
const saving = ref(false);

// 分页相关状态
const currentPage = ref(1);
const previewCount = 16; // 每页显示的图片数量
const totalImages = ref(0); // 总图片数量

// 计算总页数
const totalPages = computed(() => {
  return Math.ceil(totalImages.value / previewCount);
});

// 计算全局图片索引
const globalImageIndex = computed(() => {
  return (currentPage.value - 1) * previewCount + currentImageIndex.value;
});

// 更新可见预览图片
const visiblePreviewImages = computed(() => {
  return images.value;
});

// 分页方法
const changePage = (direction: number) => {
  const newPage = currentPage.value + direction;
  if (newPage >= 1 && newPage <= totalPages.value) {
    currentPage.value = newPage;
    fetchImages(newPage);
  }
};

// 更新当前页的起始索引
const startPreviewIndex = computed(() => {
  return (currentPage.value - 1) * previewCount;
});

// 快捷键提示
const shortcutHints = ref<{ key: string, text: string }[]>([
  {key: 'Del', text: '删除选中'},
  {key: 'Ctrl+S', text: '保存标注'},
  {key: '← →', text: '切换图片'},
  {key: '1-5', text: '切换标签'},
  {key: 'Ctrl+Z', text: '撤销操作'}
]);

// 操作历史记录
const historyStack = ref<Annotation[][]>([]);

// Canvas 状态
const canvas = ref<HTMLCanvasElement | null>(null);
const ctx = ref<CanvasRenderingContext2D | null>(null);
const isDrawing = ref<boolean>(false);
const startX = ref<number>(0);
const startY = ref<number>(0);
const currentPoints = ref<Point[]>([]);
const zoomLevel = ref<number>(1.0);
const offsetX = ref<number>(0);
const offsetY = ref<number>(0);

// 全屏状态
const isFullscreen = ref(false);
const container = ref<HTMLElement | null>(null);

// 定义 TypeScript 类型
const ToolType = {
  SELECT: 'select',
  RECTANGLE: 'rectangle',
  POLYGON: 'polygon'
};

const AnnotationType = {
  RECTANGLE: 'rectangle',
  POLYGON: 'polygon'
};

// 工具类型
interface Tool {
  id: string;
  name: string;
  icon: string;
  shortcut: string;
}

// 标签类型
interface Label {
  id: number;
  name: string;
  color: string;
  shortcut: string; // 确保定义为string类型
}

// 点类型
interface Point {
  x: number;
  y: number;
}

// 标注数据格式
interface Annotation {
  id: number;
  type: string;
  label: string; // 改为存储标签的 shortcut
  color: string;
  points: Point[];
}

// 图片类型
interface Image {
  id: number;
  name: string;
  path: string;
  annotations: Annotation[] | string;
  completed: 0 | 1;
  modificationCount: number;
  lastModified: Date | null;
}

// 保存标注请求类型
interface SaveAnnotationRequest {
  id: number;
  name: string;
  annotations: string;
  completed: 0 | 1;
  modificationCount: number;
  lastModified: Date | null;
}

// 工具状态
const activeTool = ref<string>(ToolType.SELECT);
const tools = ref<Tool[]>([
  {id: ToolType.SELECT, name: '选择', icon: 'mage:mouse-pointer', shortcut: 'V'},
  {id: ToolType.RECTANGLE, name: '矩形', icon: 'uil:vector-square', shortcut: 'R'},
  {id: ToolType.POLYGON, name: '多边形', icon: 'fa-solid:draw-polygon', shortcut: 'P'}
]);

// 图片显示尺寸
const imageDisplaySize = ref({
  x: 0,
  y: 0,
  width: 0,
  height: 0
});

// 标签状态
const currentLabelIndex = ref<number>(0);
const labels = ref<Label[]>([]);

const currentLabel = computed<Label>(() => labels.value[currentLabelIndex.value]);

// 图片数据
const images = ref<Image[]>([]);

// 图片标注状态存储
const imageAnnotations = ref<{ [key: number]: Annotation[] }>({});

const currentImageIndex = ref<number>(0);
const currentImage = computed<Image>(() => images.value[currentImageIndex.value] || {
  id: 0,
  name: '',
  path: '',
  annotations: [],
  completed: 0,
  modificationCount: 0,
  lastModified: null
});

// 图片对象引用
const currentImageObj = ref<HTMLImageElement | null>(null);
const imageLoaded = ref(false);

// 修改图片加载逻辑
const loadImage = (src: string) => {
  imageLoaded.value = false;
  const img = new Image();
  img.crossOrigin = "Anonymous";
  img.onload = () => {
    currentImageObj.value = img;
    imageLoaded.value = true;

    // 计算初始缩放比例和位置
    if (canvas.value) {
      const canvasWidth = canvas.value.width;
      const canvasHeight = canvas.value.height;

      // 确保图片不超过画布
      const scaleX = canvasWidth / img.width;
      const scaleY = canvasHeight / img.height;
      const initScale = Math.min(scaleX, scaleY);

      // 重置缩放和偏移
      zoomLevel.value = initScale;
      offsetX.value = 0;
      offsetY.value = 0;
    }

    draw();
  };
  img.src = src;
};

const getLabelName = (shortcut: string): string => {
  let label = labels.value.find(l => String(l.shortcut) === shortcut);
  if (label == null || label == undefined) {
    label = labels.value.find(l => String(l.name) === shortcut);
  }
  return label ? label.name : '未知标签';
};

// 添加对筛选状态的监听
watch(showOnlyUnannotated, (newVal) => {
  // 重置到第一页
  currentPage.value = 1;
  // 重新获取图片
  fetchImages(1);
});

// 监听当前图片变化
watch(currentImage, (newImage) => {
  if (newImage.path) {
    loadImage(newImage.path);

    // 加载当前图片的标注
    if (typeof newImage.annotations === 'string') {
      try {
        annotations.value = JSON.parse(newImage.annotations);
      } catch (e) {
        createMessage.error('标注解析失败');
        annotations.value = [];
      }
    } else {
      annotations.value = [...newImage.annotations];
    }
    isSaved.value = true;
  }
}, {immediate: true});

// 检查图片是否有标注
const hasAnnotations = (image: Image) => {
  if (typeof image.annotations === 'string') {
    try {
      const parsed = JSON.parse(image.annotations);
      return Array.isArray(parsed) && parsed.length > 0;
    } catch (e) {
      return false;
    }
  }
  return image.annotations && image.annotations.length > 0;
};

// 设置活动工具
const setActiveTool = (toolId: string): void => {
  activeTool.value = toolId;
  selectedAnnotationId.value = null;
  currentPoints.value = [];
};

// 设置当前标签
const setCurrentLabel = (index: number): void => {
  currentLabelIndex.value = index;
  console.log(`当前标签已设置为: ${labels.value[index].name} (shortcut: ${labels.value[index].shortcut})`);
};

// 选择图片
const selectImage = (index: number): void => {
  if (index >= 0 && index < totalImages.value) {
    // 计算目标页码
    const targetPage = Math.floor(index / previewCount) + 1;
    // 计算目标页的局部索引
    const targetIndex = index % previewCount;

    // 如果目标页码与当前页码不同，需要先切换页面
    if (targetPage !== currentPage.value) {
      currentPage.value = targetPage;
      fetchImages(targetPage).then(() => {
        // 页面切换完成后再选择图片
        currentImageIndex.value = targetIndex;
      });
    } else {
      // 如果已在同一页，直接选择图片
      currentImageIndex.value = targetIndex;
    }
  }
};

// 图片导航
const nextImage = (): void => {
  const newIndex = globalImageIndex.value + 1;
  if (newIndex < totalImages.value) {
    selectImage(newIndex);
  }
};

const prevImage = (): void => {
  const newIndex = globalImageIndex.value - 1;
  if (newIndex >= 0) {
    selectImage(newIndex);
  }
};


// 更新图片状态
const updateImageStatus = (modified: boolean = true) => {
  if (modified) {
    currentImage.value.modificationCount += 1;
    currentImage.value.lastModified = new Date();
    currentImage.value.completed = 0;
    isSaved.value = false;
  }
};

// 保存当前状态到历史记录
const saveToHistory = () => {
  historyStack.value.push(JSON.parse(JSON.stringify(annotations.value)));
  if (historyStack.value.length > 50) {
    historyStack.value.shift();
  }
  isSaved.value = false;
};

// 撤销操作
const undo = () => {
  if (historyStack.value.length > 0) {
    const prevState = historyStack.value.pop();
    if (prevState) {
      annotations.value = JSON.parse(JSON.stringify(prevState));
      draw();
      updateImageStatus();
    }
  }
};

// 从后端分页获取标签数据
const fetchLabels = async (): Promise<void> => {
  try {
    const pageSize = 100;
    let allLabels: Label[] = [];

    const res = await getDatasetTagPage({
      datasetId: route.params['id'],
      pageNo: 1,
      pageSize: pageSize
    });

    if (res?.list) {
      // 确保shortcut转换为字符串
      const pageLabels = res.list.map((tag: any) => ({
        id: tag.id,
        name: tag.name,
        color: tag.color,
        shortcut: String(tag.shortcut) // 关键转换
      }));
      allLabels = [...allLabels, ...pageLabels];
    }

    if (allLabels.length > 0) {
      labels.value = allLabels;
    } else {
      throw new Error("未获取到标签数据");
    }
  } catch (error) {
    // 默认标签也确保shortcut是字符串
    labels.value = [
      {id: 1, name: '人物', color: '#FF5252', shortcut: '1'},
      {id: 2, name: '车辆', color: '#4CAF50', shortcut: '2'},
      {id: 3, name: '动物', color: '#FFC107', shortcut: '3'},
    ];
    currentLabelIndex.value = 0;
  }
};

// 修改后的fetchImages函数
const fetchImages = async (pageNo: number = 1): Promise<void> => {
  try {
    const res = await getDatasetImagePage({
      datasetId: route.params['id'],
      pageNo: pageNo,
      pageSize: previewCount,
      // 新增筛选参数
      completed: showOnlyUnannotated.value ? 0 : undefined
    });

    if (res && res.list) {
      // 更新总图片数量
      totalImages.value = res.total || res.list.length;

      // 更新筛选后的图片数量
      filteredImageCount.value = res.total || 0;

      // 只更新当前页的图片
      images.value = res.list.map((img: any) => {
        // 处理标注数据
        let annotations: Annotation[] | string = [];
        if (img.annotations) {
          try {
            annotations = typeof img.annotations === 'string'
              ? JSON.parse(img.annotations)
              : img.annotations;
          } catch (e) {
            annotations = [];
          }
        }

        return {
          id: img.id,
          name: img.name,
          path: img.path,
          annotations,
          completed: img.completed || 0,
          modificationCount: img.modificationCount || 0,
          lastModified: img.lastModified ? new Date(img.lastModified) : null
        };
      });

      // 初始化后自动选择第一张图片
      if (images.value.length > 0 && currentImageIndex.value >= images.value.length) {
        currentImageIndex.value = 0;
      }
    }
  } catch (error) {
    createMessage.error('获取图片失败:' + error);
    images.value = [];
    totalImages.value = 0;
  }
};

// 保存标注到后端（简化版）
const saveAnnotationsToDB = async (requestData: SaveAnnotationRequest): Promise<void> => {
  try {
    requestData['datasetId'] = route.params['id'];
    await updateDatasetImage(requestData);
  } catch (error) {
    createMessage.error('保存到数据库失败:' + error);
    throw error; // 重新抛出错误
  }
};

// 格式化日期时间
const formatDateTime = (date: Date | null): string => {
  if (!date) return '从未修改';

  return new Intl.DateTimeFormat('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  }).format(date);
};

// 保存当前标注
const saveCurrentAnnotations = async (): Promise<void> => {
  if (saving.value) return;
  saving.value = true;

  if (annotations.value.length === 0) {
    createMessage.warning('请至少标注一个对象');
    saving.value = false;
    return;
  }

  saving.value = true; // 加锁

  try {
    const updatedStatus = {
      completed: 1 as 0 | 1,
      modificationCount: currentImage.value.modificationCount + 1,
      lastModified: new Date()
    };

    const requestData: SaveAnnotationRequest = {
      id: currentImage.value.id,
      name: currentImage.value.name,
      annotations: JSON.stringify(annotations.value),
      ...updatedStatus
    };

    // 使用单一await处理保存操作
    await saveAnnotationsToDB(requestData);

    // 更新当前图片状态
    const currentId = currentImage.value.id;
    const imageIndex = images.value.findIndex(img => img.id === currentId);
    if (imageIndex !== -1) {
      images.value[imageIndex] = {
        ...images.value[imageIndex],
        ...updatedStatus,
        annotations: requestData.annotations
      };
    }

    // 更新标注缓存
    try {
      imageAnnotations.value[currentId] = JSON.parse(requestData.annotations);
    } catch (e) {
      imageAnnotations.value[currentId] = [];
    }

    // 仅显示一次成功提示
    createMessage.success('标注保存成功');
    isSaved.value = true;
  } catch (error) {
    createMessage.error('保存失败:' + error);
  } finally {
    saving.value = false; // 解锁
  }
};

// 初始化画布
const initCanvas = (): void => {
  if (!canvas.value) return;

  ctx.value = canvas.value.getContext('2d');
  resizeCanvas();
  draw();
};

// 调整画布大小 - 优化版
const resizeCanvas = (): void => {
  if (!canvas.value) return;

  const container = canvas.value.parentElement;
  if (!container) return;

  // 保存当前状态
  const wasDrawing = isDrawing.value;
  const hadPoints = [...currentPoints.value];

  // 暂停绘制状态
  isDrawing.value = false;
  currentPoints.value = [];

  // 更新画布尺寸
  canvas.value.width = container.clientWidth;
  canvas.value.height = container.clientHeight;

  // 恢复状态
  requestAnimationFrame(() => {
    isDrawing.value = wasDrawing;
    currentPoints.value = hadPoints;
    draw();
  });
};

// 添加防抖处理 - 优化性能
let resizeTimeout: number | null = null;
const handleResize = () => {
  if (resizeTimeout) clearTimeout(resizeTimeout);
  resizeTimeout = setTimeout(() => {
    resizeCanvas();
  }, 100) as unknown as number;
};

// 绘制网格背景
const drawGridBackground = (): void => {
  if (!ctx.value || !canvas.value) return;

  ctx.value.fillStyle = '#2d3748';
  ctx.value.fillRect(0, 0, canvas.value.width, canvas.value.height);

  ctx.value.strokeStyle = '#3c4757';
  ctx.value.lineWidth = 1;

  for (let x = 0; x < canvas.value.width; x += 25) {
    ctx.value.beginPath();
    ctx.value.moveTo(x, 0);
    ctx.value.lineTo(x, canvas.value.height);
    ctx.value.stroke();
  }

  for (let y = 0; y < canvas.value.height; y += 25) {
    ctx.value.beginPath();
    ctx.value.moveTo(0, y);
    ctx.value.lineTo(canvas.value.width, y);
    ctx.value.stroke();
  }

  ctx.value.fillStyle = '#4cc9f0';
  ctx.value.beginPath();
  ctx.value.arc(canvas.value.width / 2, canvas.value.height / 2, 5, 0, Math.PI * 2);
  ctx.value.fill();
};

// 修改绘制逻辑
const draw = (): void => {
  if (!ctx.value || !canvas.value) return;

  // 清空画布
  ctx.value.clearRect(0, 0, canvas.value.width, canvas.value.height);

  // 绘制网格背景
  drawGridBackground();

  if (currentImageObj.value && imageLoaded.value) {
    const img = currentImageObj.value;

    // 计算缩放后的尺寸
    const scaledWidth = img.width * zoomLevel.value;
    const scaledHeight = img.height * zoomLevel.value;

    // 计算居中位置
    const x = (canvas.value.width - scaledWidth) / 2 + offsetX.value;
    const y = (canvas.value.height - scaledHeight) / 2 + offsetY.value;

    // 保存显示尺寸用于坐标转换
    imageDisplaySize.value = {
      x: x,
      y: y,
      width: scaledWidth,
      height: scaledHeight
    };

    // 绘制图片
    ctx.value.drawImage(img, x, y, scaledWidth, scaledHeight);
  }

  // 绘制标注
  annotations.value.forEach(annotation => {
    drawAnnotation(annotation);
  });

  // 绘制当前标注
  if (isDrawing.value && currentPoints.value.length > 0) {
    drawCurrentAnnotation();
  }
};

// 绘制单个标注
const drawAnnotation = (annotation: Annotation): void => {
  if (!ctx.value || !imageDisplaySize.value) return;

  const {x: imgX, y: imgY, width: imgWidth, height: imgHeight} = imageDisplaySize.value;

  // 转换归一化坐标为实际坐标
  const toCanvasCoords = (point: Point) => ({
    x: imgX + point.x * imgWidth,
    y: imgY + point.y * imgHeight
  });

  ctx.value.save();
  ctx.value.strokeStyle = annotation.color;
  ctx.value.lineWidth = 2;
  ctx.value.fillStyle = annotation.color + '20';

  const isSelected = annotation.id === selectedAnnotationId.value;

  if (isSelected) {
    ctx.value.strokeStyle = '#ffffff';
    ctx.value.lineWidth = 3;
  }

  if (annotation.points.length > 0) {
    const startPoint = toCanvasCoords(annotation.points[0]);
    ctx.value.beginPath();
    ctx.value.moveTo(startPoint.x, startPoint.y);

    for (let i = 1; i < annotation.points.length; i++) {
      const point = toCanvasCoords(annotation.points[i]);
      ctx.value.lineTo(point.x, point.y);
    }

    if (annotation.type === AnnotationType.RECTANGLE ||
      annotation.type === AnnotationType.POLYGON) {
      ctx.value.closePath();
    }

    ctx.value.fill();
    ctx.value.stroke();

    if (annotation.points.length > 0) {
      drawAnnotationLabel(
        annotation,
        annotation.points[0].x,
        annotation.points[0].y
      );
    }

    drawAnnotationLabel(annotation, startPoint.x, startPoint.y);
  }

  ctx.value.restore();
};

// 绘制当前正在创建的标注
const drawCurrentAnnotation = (): void => {
  if (!ctx.value || !imageDisplaySize.value || currentPoints.value.length === 0) return;

  const {x: imgX, y: imgY, width: imgWidth, height: imgHeight} = imageDisplaySize.value;

  // 转换归一化坐标为实际canvas坐标
  const toCanvasCoords = (point: Point) => ({
    x: imgX + point.x * imgWidth,
    y: imgY + point.y * imgHeight
  });

  ctx.value.save();
  ctx.value.strokeStyle = currentLabel.value.color;
  ctx.value.lineWidth = 2;
  ctx.value.fillStyle = currentLabel.value.color + '40';

  switch (activeTool.value) {
    case ToolType.RECTANGLE:
      const rectStart = toCanvasCoords(currentPoints.value[0]);
      const rectEnd = toCanvasCoords({x: startX.value, y: startY.value});
      const width = rectEnd.x - rectStart.x;
      const height = rectEnd.y - rectStart.y;

      ctx.value.beginPath();
      ctx.value.rect(rectStart.x, rectStart.y, width, height);
      ctx.value.fill();
      ctx.value.stroke();

      drawAnnotationLabel({
        id: 0,
        type: AnnotationType.RECTANGLE,
        label: currentLabel.value.name,
        color: currentLabel.value.color,
        points: [
          {x: currentPoints.value[0].x, y: currentPoints.value[0].y},
          {x: currentPoints.value[0].x + width / imgWidth, y: currentPoints.value[0].y},
          {
            x: currentPoints.value[0].x + width / imgWidth,
            y: currentPoints.value[0].y + height / imgHeight
          },
          {x: currentPoints.value[0].x, y: currentPoints.value[0].y + height / imgHeight}
        ]
      }, rectStart.x, rectStart.y);
      break;

    case ToolType.POLYGON:
      if (currentPoints.value.length > 0) {
        ctx.value.beginPath();
        const firstPoint = toCanvasCoords(currentPoints.value[0]);
        ctx.value.moveTo(firstPoint.x, firstPoint.y);

        for (let i = 1; i < currentPoints.value.length; i++) {
          const point = toCanvasCoords(currentPoints.value[i]);
          ctx.value.lineTo(point.x, point.y);
        }

        const currentPoint = toCanvasCoords({x: startX.value, y: startY.value});
        ctx.value.lineTo(currentPoint.x, currentPoint.y);
        ctx.value.stroke();

        ctx.value.fillStyle = currentLabel.value.color;
        currentPoints.value.forEach(point => {
          const canvasPoint = toCanvasCoords(point);
          ctx.value.beginPath();
          ctx.value.arc(canvasPoint.x, canvasPoint.y, 4, 0, Math.PI * 2);
          ctx.value.fill();
        });
      }
      break;
  }

  ctx.value.restore();
};

// 绘制标注
const drawAnnotationLabel = (annotation: Annotation, x: number, y: number): void => {
  if (!ctx.value) return;

  ctx.value.save();
  ctx.value.fillStyle = annotation.color;
  ctx.value.font = '14px Inter';

  // 使用getLabelName方法获取标签名称
  const labelName = getLabelName(annotation.label);
  const textWidth = ctx.value.measureText(labelName).width;

  ctx.value.fillRect(x - 2, y - 25, textWidth + 10, 20);
  ctx.value.fillStyle = 'white';
  ctx.value.fillText(labelName, x + 3, y - 10); // 使用标签名称显示

  ctx.value.restore();
};

// 检查点是否在标注内
const isPointInAnnotation = (annotation: Annotation, x: number, y: number): boolean => {
  if (annotation.type === AnnotationType.RECTANGLE) {
    const [p1, p2, p3, p4] = annotation.points;
    const minX = Math.min(p1.x, p2.x, p3.x, p4.x);
    const maxX = Math.max(p1.x, p2.x, p3.x, p4.x);
    const minY = Math.min(p1.y, p2.y, p3.y, p4.y);
    const maxY = Math.max(p1.y, p2.y, p3.y, p4.y);

    return x >= minX && x <= maxX && y >= minY && y <= maxY;
  } else if (annotation.type === AnnotationType.POLYGON) {
    let inside = false;
    for (let i = 0, j = annotation.points.length - 1; i < annotation.points.length; j = i++) {
      const xi = annotation.points[i].x;
      const yi = annotation.points[i].y;
      const xj = annotation.points[j].x;
      const yj = annotation.points[j].y;

      const intersect = ((yi > y) !== (yj > y)) &&
        (x < ((xj - xi) * (y - yi)) / (yj - yi) + xi);
      if (intersect) inside = !inside;
    }
    return inside;
  }
  return false;
};

// 选择标注
const selectAnnotation = (id: number): void => {
  selectedAnnotationId.value = id;
  draw();
};

// 删除标注
const deleteAnnotation = (id: number): void => {
  saveToHistory();
  annotations.value = annotations.value.filter(a => a.id !== id);
  if (selectedAnnotationId.value === id) {
    selectedAnnotationId.value = null;
  }
  draw();
  updateImageStatus();
};

// 鼠标事件处理
const handleMouseDown = (e: MouseEvent): void => {
  if (!canvas.value || !imageDisplaySize.value) return;

  const rect = canvas.value.getBoundingClientRect();
  const canvasX = e.clientX - rect.left;
  const canvasY = e.clientY - rect.top;

  const {x: imgX, y: imgY, width: imgWidth, height: imgHeight} = imageDisplaySize.value;

  // 转换为归一化坐标 (0-1)
  const x = (canvasX - imgX) / imgWidth;
  const y = (canvasY - imgY) / imgHeight;

  // 确保坐标在图片范围内
  if (x < 0 || x > 1 || y < 0 || y > 1) return;

  startX.value = x;
  startY.value = y;

  if (activeTool.value === ToolType.SELECT) {
    let clickedAnnotation = false;

    for (let i = annotations.value.length - 1; i >= 0; i--) {
      const annotation = annotations.value[i];
      if (isPointInAnnotation(annotation, x, y)) {
        selectedAnnotationId.value = annotation.id;
        clickedAnnotation = true;
        saveToHistory();
        break;
      }
    }

    if (!clickedAnnotation) {
      selectedAnnotationId.value = null;
    }
    draw();
    return;
  }

  if ([ToolType.RECTANGLE, ToolType.POLYGON].includes(activeTool.value)) {
    isDrawing.value = true;

    if (activeTool.value === ToolType.POLYGON && currentPoints.value.length === 0) {
      currentPoints.value.push({x, y});
    } else if (activeTool.value !== ToolType.POLYGON) {
      currentPoints.value = [{x, y}];
    }

    saveToHistory();
    updateImageStatus();
  }
};

const handleMouseMove = (e: MouseEvent): void => {
  if (!canvas.value || !imageDisplaySize.value) return;

  const rect = canvas.value.getBoundingClientRect();
  const canvasX = e.clientX - rect.left;
  const canvasY = e.clientY - rect.top;

  const {x: imgX, y: imgY, width: imgWidth, height: imgHeight} = imageDisplaySize.value;

  // 转换为归一化坐标 (0-1)
  const x = (canvasX - imgX) / imgWidth;
  const y = (canvasY - imgY) / imgHeight;

  startX.value = x;
  startY.value = y;

  if (isDrawing.value) {
    draw();
  }
};

const handleMouseUp = (): void => {
  if (isDrawing.value && currentPoints.value.length > 0) {
    if (activeTool.value === ToolType.RECTANGLE) {
      const width = startX.value - currentPoints.value[0].x;
      const height = startY.value - currentPoints.value[0].y;

      if (Math.abs(width) > 0.01 && Math.abs(height) > 0.01) {
        console.log(`创建矩形标注，使用标签: ${currentLabel.value.name} (shortcut: ${currentLabel.value.shortcut})`);

        const newAnnotation: Annotation = {
          id: Date.now(),
          type: AnnotationType.RECTANGLE,
          label: currentLabel.value.shortcut, // 确保使用 shortcut
          color: currentLabel.value.color,
          points: [
            {x: currentPoints.value[0].x, y: currentPoints.value[0].y},
            {x: currentPoints.value[0].x + width, y: currentPoints.value[0].y},
            {x: currentPoints.value[0].x + width, y: currentPoints.value[0].y + height},
            {x: currentPoints.value[0].x, y: currentPoints.value[0].y + height}
          ]
        };

        annotations.value.push(newAnnotation);
        selectedAnnotationId.value = newAnnotation.id;
        draw();
      }
    } else if (activeTool.value === ToolType.POLYGON) {
      currentPoints.value.push({x: startX.value, y: startY.value});
      return;
    }

    isDrawing.value = false;
    currentPoints.value = [];
  }
};

const handleDoubleClick = (): void => {
  if (activeTool.value === ToolType.POLYGON && currentPoints.value.length > 2) {
    console.log(`创建多边形标注，使用标签: ${currentLabel.value.name} (shortcut: ${currentLabel.value.shortcut})`);

    const newAnnotation: Annotation = {
      id: Date.now(),
      type: AnnotationType.POLYGON,
      label: currentLabel.value.shortcut, // 确保使用 shortcut
      color: currentLabel.value.color,
      points: [...currentPoints.value]
    };

    annotations.value.push(newAnnotation);
    selectedAnnotationId.value = newAnnotation.id;
    draw();

    isDrawing.value = false;
    currentPoints.value = [];
  }
};

// 全屏切换逻辑
const toggleFullscreen = () => {
  if (!container.value) return;

  if (!isFullscreen.value) {
    const element = container.value;
    if (element.requestFullscreen) {
      element.requestFullscreen();
    } else if ((element as any).webkitRequestFullscreen) {
      (element as any).webkitRequestFullscreen();
    } else if ((element as any).msRequestFullscreen) {
      (element as any).msRequestFullscreen();
    }
  } else {
    if (document.exitFullscreen) {
      document.exitFullscreen();
    } else if ((document as any).webkitExitFullscreen) {
      (document as any).webkitExitFullscreen();
    } else if ((document as any).msExitFullscreen) {
      (document as any).msExitFullscreen();
    }
  }
};

// 处理全屏变化
const handleFullscreenChange = () => {
  isFullscreen.value = Boolean(
    document.fullscreenElement ||
    (document as any).webkitFullscreenElement ||
    (document as any).msFullscreenElement
  );

  requestAnimationFrame(() => {
    resizeCanvas();
  });
};

// 键盘快捷键
const handleKeyDown = (e: KeyboardEvent): void => {
  if (e.ctrlKey) {
    if (e.key === 's') {
      e.preventDefault();
      saveCurrentAnnotations();
    } else if (e.key === 'z') {
      e.preventDefault();
      undo();
    }
  }

  switch (e.key) {
    case '1':
    case '2':
    case '3':
    case '4':
    case '5':
    case '6':
    case '7':
    case '8':
    case '9':
    case '0':
      const shortcut = e.key;
      const index = labels.value.findIndex(l => l.shortcut === shortcut);
      if (index !== -1) {
        setCurrentLabel(index);
      } else {
        console.warn(`未找到匹配的标签 shortcut: ${shortcut}`);
      }
      break;
    case 'r':
      setActiveTool(ToolType.RECTANGLE);
      break;
    case 'p':
      setActiveTool(ToolType.POLYGON);
      break;
    case 'v':
      setActiveTool(ToolType.SELECT);
      break;
    case 'ArrowRight':
      nextImage();
      break;
    case 'ArrowLeft':
      prevImage();
      break;
    case 'Delete':
      if (selectedAnnotationId.value !== null) {
        deleteAnnotation(selectedAnnotationId.value);
      }
      break;
    case 'Escape':
      if (isDrawing.value && activeTool.value === ToolType.POLYGON) {
        isDrawing.value = false;
        currentPoints.value = [];
        draw();
      }
      break;
    case 'f':
      toggleFullscreen();
      break;
  }
};

// 初始化
onMounted(() => {
  initCanvas();
  window.addEventListener('resize', handleResize);
  window.addEventListener('keydown', handleKeyDown);
  window.addEventListener('resize', resizeCanvas);

  document.addEventListener('fullscreenchange', handleFullscreenChange);
  document.addEventListener('webkitfullscreenchange', handleFullscreenChange);
  document.addEventListener('msfullscreenchange', handleFullscreenChange);

  fetchLabels();
  fetchImages(1);
});

// 组件卸载时移除事件监听
onUnmounted(() => {
  window.removeEventListener('resize', handleResize);
  document.removeEventListener('fullscreenchange', handleFullscreenChange);
  document.removeEventListener('webkitfullscreenchange', handleFullscreenChange);
  document.removeEventListener('msfullscreenchange', handleFullscreenChange);
});
</script>

<style lang="less">
// 定义LESS变量
@primary-color: #4361ee;
@success-color: #4cc9f0;
@warning-color: #f8961e;
@error-color: #f72585;
@dark-color: #1a1c2c;
@light-color: #f8f9fa;
@gray-color: #6c757d;
@border-color: #dee2e6;

// 更新全屏标题样式
.fullscreen-title {
  width: 100%;
  height: 64px; /* 固定高度避免覆盖内容 */
  background: linear-gradient(to right, #1a1c2c, #2d3748); /* 更专业的深色渐变 */
  color: white;
  font-weight: bold;
  font-size: 22px;
  display: flex;
  align-items: center;
  z-index: 1000;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.3); /* 添加阴影增强层次感 */
  padding: 0 20px; /* 左右留白 */

  .title-content {
    display: flex;
    align-items: center;
    gap: 12px;
    font-size: 22px;
    font-weight: 600;
    letter-spacing: 0.5px;

    i {
      font-size: 20px;
      color: #4cc9f0;
    }
  }
}

.annotation-container {
  height: 700px;
  display: flex;
  flex-direction: column;
  background: @dark-color;
  transition: all 0.3s ease;

  /* 在样式部分添加以下样式 */

  .filter-section {
    padding: 6px 0 20px 5px;
    border-bottom: 1px solid #eee;
    margin-bottom: 12px;

    .filter-toggle {
      display: flex;
      align-items: center;
      gap: 10px;
      font-size: 14px;

      label {
        position: relative;
        display: inline-block;
        width: 40px;
        height: 20px;

        input {
          opacity: 0;
          width: 0;
          height: 0;

          &:checked + .toggle-slider {
            background-color: @primary-color;

            &:before {
              transform: translateX(20px);
            }
          }
        }

        .toggle-slider {
          position: absolute;
          cursor: pointer;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          background-color: #ccc;
          transition: .3s;
          border-radius: 20px;

          &:before {
            position: absolute;
            content: "";
            height: 16px;
            width: 16px;
            left: 2px;
            bottom: 2px;
            background-color: white;
            transition: .3s;
            border-radius: 50%;
          }
        }
      }
    }

    .filter-indicator {
      color: @primary-color;
      font-weight: 500;
      font-size: 13px;
    }
  }

  .main-content {
    display: flex;
    flex: 1;
    height: calc(100% - 120px);
    min-width: 0;
  }

  .image-preview-container {
    height: 120px; /* 增加高度以适应分页控制器 */
    display: flex;
    justify-content: center;
    align-items: center;
    background: #f5f7fa;
    border-top: 1px solid #eaeaea;
    padding: 0 40px;
    position: relative;
    transition: opacity 0.3s ease;

    .pagination-control {
      position: absolute;
      bottom: 5px;
      left: 50%;
      transform: translateX(-50%);
      background: rgba(0, 0, 0, 0.7);
      color: white;
      padding: 4px 12px;
      border-radius: 20px;
      font-size: 12px;
      z-index: 10;

      .page-indicator {
        font-weight: 500;
      }
    }

    .nav-btn {
      top: 50%;
      transform: translateY(-50%);
      /* 其他按钮样式保持不变 */
    }

    .nav-btn {
      position: absolute;
      top: 50%;
      transform: translateY(-50%);
      width: 30px;
      height: 60px;
      background: rgba(0, 0, 0, 0.3);
      color: white;
      border: none;
      border-radius: 4px;
      cursor: pointer;
      z-index: 10;
      display: flex;
      align-items: center;
      justify-content: center;
      transition: background 0.3s;

      &:hover:not(:disabled) {
        background: rgba(0, 0, 0, 0.6);
      }

      &:disabled {
        opacity: 0.3;
        cursor: not-allowed;
      }

      &.prev-btn {
        left: 5px;
      }

      &.next-btn {
        right: 5px;
      }
    }

    .preview-list {
      display: flex;
      overflow-x: auto;
      width: 100%;
      padding: 0 10px;
      scrollbar-width: none;
      -ms-overflow-style: none;

      &::-webkit-scrollbar {
        display: none;
      }
    }

    .preview-item {
      width: 80px;
      height: 80px;
      margin: 0 8px;
      border: 2px solid transparent;
      border-radius: 4px;
      overflow: hidden;
      cursor: pointer;
      position: relative;
      flex-shrink: 0;
      transition: all 0.3s ease;

      &.active {
        border-color: @primary-color;
        box-shadow: 0 0 8px fade(@primary-color, 50%);
        transform: scale(1.1);
      }

      &.annotated {
        position: relative;

        &::after {
          content: '';
          position: absolute;
          top: 5px;
          right: 5px;
          width: 10px;
          height: 10px;
          background-color: @success-color;
          border-radius: 50%;
        }
      }

      &.completed {
        border: 2px solid @success-color;

        .completed-badge {
          position: absolute;
          top: 5px;
          left: 5px;
          background: @success-color;
          color: white;
          font-size: 10px;
          padding: 2px 5px;
          border-radius: 3px;
        }
      }

      .preview-image {
        width: 100%;
        height: 100%;
        object-fit: cover;
      }

      .preview-status {
        position: absolute;
        bottom: 0;
        left: 0;
        right: 0;
        background: rgba(0, 0, 0, 0.7);
        color: white;
        font-size: 12px;
        text-align: center;
        padding: 2px 0;
      }
    }
  }

  .toolbar {
    width: 80px;
    background: white;
    padding: 20px 0;
    box-shadow: 2px 0 10px rgba(0, 0, 0, 0.05);
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 24px;
    z-index: 5;

    .tool-button {
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 6px;
      width: 60px;
      padding: 10px 0;
      border-radius: 10px;
      cursor: pointer;
      transition: all 0.2s ease;
      color: @gray-color;

      &:hover {
        background: #e9ecef;
      }

      &.active {
        background: fade(@primary-color, 10%);
        color: @primary-color;
      }

      i {
        font-size: 20px;
      }

      span {
        font-size: 12px;
        font-weight: 500;
      }
    }
  }

  .canvas-area {
    flex: 1;
    display: flex;
    flex-direction: column;
    background: @dark-color;
    position: relative;
    min-width: 0;
    overflow: hidden;

    .image-position-indicator {
      position: absolute;
      top: 20px;
      left: 50%;
      transform: translateX(-50%);
      background: rgba(0, 0, 0, 0.85);
      color: white;
      padding: 8px 16px;
      border-radius: 30px;
      font-size: 16px;
      font-weight: 500;
      z-index: 20;
      display: flex;
      align-items: center;
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.25);

      .position-text {
        display: flex;
        align-items: center;

        .current-index {
          color: #4cc9f0;
          font-weight: bold;
          font-size: 18px;
          margin: 0 4px;
        }

        .total-count {
          color: #a0aec0;
          margin-left: 4px;
        }
      }
    }

    .canvas-wrapper {
      flex: 1;
      display: flex;
      align-items: center;
      justify-content: center;
      overflow: auto;
      padding: 20px;
      max-width: 100%;

      .annotation-canvas {
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
        background: #2d3748;
        border-radius: 8px;
      }
    }

    .shortcut-hint {
      position: absolute;
      bottom: 90px;
      left: 50%;
      transform: translateX(-50%);
      background: rgba(0, 0, 0, 0.7);
      color: white;
      padding: 8px 16px;
      border-radius: 30px;
      font-size: 14px;
      display: flex;
      gap: 12px;
      z-index: 10;

      .hint-item {
        display: flex;
        align-items: center;
        gap: 6px;

        .key {
          background: rgba(255, 255, 255, 0.2);
          padding: 2px 8px;
          border-radius: 4px;
          font-weight: 500;
        }
      }
    }

    .status-indicator {
      position: absolute;
      top: 20px;
      right: 20px;
      background: rgba(0, 0, 0, 0.85);
      color: white;
      padding: 12px;
      border-radius: 8px;
      font-size: 14px;
      min-width: 280px;
      z-index: 10;

      .status-header {
        display: flex;
        flex-direction: column;
        gap: 8px;
        padding-bottom: 10px;
        border-bottom: 1px solid rgba(255, 255, 255, 0.2);
        margin-bottom: 10px;

        .completion-status {
          font-weight: bold;
          font-size: 16px;

          &.completed {
            color: #4CAF50;
          }
        }

        .modification-info {
          display: flex;
          flex-direction: column;
          gap: 4px;
          font-size: 13px;
          color: #e0e0e0;
        }
      }

      .annotation-count {
        display: flex;
        align-items: center;
        gap: 8px;
        font-size: 14px;

        .status-dot {
          width: 10px;
          height: 10px;
          border-radius: 50%;
          background: #4CAF50;
        }

        .unsaved-indicator {
          color: #ff6b6b;
          font-weight: bold;
          margin-left: 8px;
        }
      }
    }

    .fullscreen-control {
      position: absolute;
      bottom: 20px;
      right: 20px;
      background: rgba(0, 0, 0, 0.7);
      color: white;
      padding: 10px 15px;
      border-radius: 30px;
      font-size: 14px;
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 8px;
      z-index: 10;
      transition: background 0.3s;

      &:hover {
        background: rgba(0, 0, 0, 0.9);
      }

      i {
        font-size: 16px;
      }
    }
  }

  .label-panel {
    width: 220px;
    background: white;
    padding: 20px 16px;
    box-shadow: -2px 0 10px rgba(0, 0, 0, 0.05);
    display: flex;
    flex-direction: column;
    z-index: 5;

    .panel-header {
      padding-left: 5px;
      font-size: 16px;
      font-weight: 600;
      margin-bottom: 16px;
      color: @dark-color;
      display: flex;
      align-items: center;
      gap: 8px;
      flex-wrap: wrap;

      i {
        color: @primary-color;
      }

      .annotation-stats {
        flex: 100%;
        font-size: 14px;
        font-weight: normal;
        margin-top: 8px;
        color: @gray-color;
      }
    }

    .label-list {
      display: flex;
      flex-direction: column;
      gap: 8px;
      overflow-y: auto;
      flex: 1;
      max-height: 200px;

      .label-item {
        display: flex;
        align-items: center;
        padding: 12px;
        border-radius: 8px;
        cursor: pointer;
        transition: all 0.2s;
        border: 1px solid @border-color;

        &:hover {
          transform: translateY(-2px);
          box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
        }

        &.active {
          border-color: @primary-color;
          background: fade(@primary-color, 5%);
        }

        .color-badge {
          width: 24px;
          height: 24px;
          border-radius: 6px;
          margin-right: 12px;
        }

        .label-name {
          flex: 1;
          font-weight: 500;
        }

        .label-shortcut {
          background: #e9ecef;
          padding: 2px 8px;
          border-radius: 4px;
          font-size: 12px;
          font-weight: 600;
          color: @gray-color;
        }
      }
    }

    .object-layer-section {
      margin-top: 20px;
      border-top: 1px solid #eee;
      padding-top: 15px;

      .panel-header {
        margin-bottom: 10px;
        font-size: 14px;
        color: #666;

        i {
          color: #666;
        }
      }

      .object-list {
        max-height: 250px;
        overflow-y: auto;
        border: 1px solid #eee;
        border-radius: 6px;
        padding: 5px;

        .object-item {
          display: flex;
          align-items: center;
          padding: 8px;
          border-radius: 4px;
          margin-bottom: 5px;
          cursor: pointer;
          transition: all 0.2s;

          &:hover {
            background-color: #f5f7fa;
          }

          &.selected {
            background-color: fade(@primary-color, 10%);
            border-left: 3px solid @primary-color;
          }

          .object-color {
            width: 16px;
            height: 16px;
            border-radius: 4px;
            margin-right: 10px;
          }

          .object-name {
            flex: 1;
            font-size: 13px;
            color: #333;
          }

          .object-actions {
            .delete-btn {
              background: none;
              border: none;
              color: #f44336;
              cursor: pointer;
              padding: 4px;
              border-radius: 4px;

              &:hover {
                background-color: #ffeeee;
              }
            }
          }
        }
      }
    }
  }
}

// 全屏模式下的样式调整
:fullscreen &,
&:-webkit-full-screen,
&:-moz-full-screen,
&:-ms-fullscreen {
  .image-position-indicator,
  .status-indicator {
    top: 54px; /* 为标题栏留出空间 */
  }

  .canvas-wrapper {
    top: 44px; /* 确保画布区域下移 */
  }
}

// 全屏模式下的样式调整
:fullscreen .annotation-container,
:-webkit-full-screen .annotation-container,
:-moz-full-screen .annotation-container,
:-ms-fullscreen .annotation-container {
  height: 100vh;
  width: 100vw;
  background: @dark-color;

  .main-content {
    height: calc(100% - 120px);
  }

  .image-preview-container {
    height: 120px; /* 增加高度以适应分页控制器 */
  }

  .toolbar {
    width: 80px;
  }

  .canvas-area {
    flex: 1;
  }

  .label-panel {
    width: 220px;
    min-width: 250px;
    max-width: 350px;
    transition: width 0.3s ease;
  }
}

@media (min-width: 1920px) {
  :fullscreen .label-panel {
    width: 220px;
  }
}
</style>
