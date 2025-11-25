<template>
  <div ref="container" class="region-drawer-container">
    <!-- 工具栏 -->
    <div class="toolbar">
      <a-button type="primary" @click="handleCapture" :loading="capturing">
        <template #icon>
          <CameraOutlined />
        </template>
        抓拍图片
      </a-button>
      <a-button @click="handleClear" :disabled="!currentImage">
        <template #icon>
          <ClearOutlined />
        </template>
        清空画布
      </a-button>
      <a-button @click="handleSave" :disabled="regions.length === 0 || !currentImage">
        <template #icon>
          <SaveOutlined />
        </template>
        保存区域
      </a-button>
    </div>

    <!-- 主内容区 -->
    <div class="main-content">
      <!-- 左侧区域列表 -->
      <div class="region-panel">
        <div class="panel-header">
          <span>检测区域 ({{ regions.length }})</span>
        </div>
        <div class="region-list">
          <div
            v-for="(region, index) in regions"
            :key="region.id || index"
            class="region-item"
            :class="{ active: selectedRegionId === (region.id || index) }"
            @click="selectRegion(region.id || index)"
          >
            <div class="region-color" :style="{ backgroundColor: region.color }"></div>
            <div class="region-name">{{ region.region_name || `区域 ${index + 1}` }}</div>
            <div class="region-actions">
              <a-button
                type="text"
                size="small"
                danger
                @click.stop="deleteRegion(region.id || index)"
              >
                <template #icon>
                  <DeleteOutlined />
                </template>
              </a-button>
            </div>
          </div>
          <a-empty v-if="regions.length === 0" description="暂无区域" :image="false" />
        </div>
      </div>

      <!-- 画布区域 -->
      <div class="canvas-area">
        <div v-if="!currentImage" class="empty-state">
          <a-empty description="请先抓拍一张图片作为绘制基准">
            <template #image>
              <CameraOutlined style="font-size: 48px; color: #ccc" />
            </template>
          </a-empty>
        </div>
        <div v-else class="canvas-wrapper">
          <canvas
            ref="canvas"
            class="draw-canvas"
            @mousedown="handleMouseDown"
            @mousemove="handleMouseMove"
            @mouseup="handleMouseUp"
            @dblclick="handleDoubleClick"
          ></canvas>
        </div>
      </div>

      <!-- 右侧配置面板 -->
      <div class="config-panel">
        <div class="panel-header">
          <span>区域配置</span>
        </div>
        <div v-if="selectedRegion" class="config-content">
          <a-form :model="selectedRegion" layout="vertical" size="small">
            <a-form-item label="区域名称">
              <a-input v-model:value="selectedRegion.region_name" placeholder="请输入区域名称" />
            </a-form-item>
            <a-form-item label="算法类型">
              <a-select v-model:value="selectedRegion.algorithm_type" placeholder="请选择算法类型">
                <a-select-option value="FIRE">火焰烟雾检测</a-select-option>
                <a-select-option value="CROWD">人群聚集计数</a-select-option>
                <a-select-option value="SMOKE">吸烟检测</a-select-option>
              </a-select>
            </a-form-item>
            <a-form-item label="算法模型ID">
              <a-input-number
                v-model:value="selectedRegion.algorithm_model_id"
                placeholder="请输入算法模型ID"
                :min="1"
                style="width: 100%"
              />
            </a-form-item>
            <a-form-item label="算法阈值">
              <a-input-number
                v-model:value="selectedRegion.algorithm_threshold"
                placeholder="请输入算法阈值"
                :min="0"
                :max="1"
                :step="0.1"
                style="width: 100%"
              />
            </a-form-item>
            <a-form-item label="区域颜色">
              <input
                type="color"
                v-model="selectedRegion.color"
                @change="handleColorChange"
                style="width: 100%; height: 32px; border: 1px solid #d9d9d9; border-radius: 4px; cursor: pointer"
              />
            </a-form-item>
            <a-form-item label="透明度">
              <a-slider
                v-model:value="selectedRegion.opacity"
                :min="0"
                :max="1"
                :step="0.1"
              />
            </a-form-item>
            <a-form-item label="启用算法">
              <a-switch v-model:checked="selectedRegion.algorithm_enabled" />
            </a-form-item>
            <a-form-item label="启用区域">
              <a-switch v-model:checked="selectedRegion.is_enabled" />
            </a-form-item>
          </a-form>
        </div>
        <div v-else class="empty-config">
          <a-empty description="请选择一个区域进行配置" :image="false" />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue';
import { CameraOutlined, ClearOutlined, SaveOutlined, DeleteOutlined } from '@ant-design/icons-vue';
import { useMessage } from '@/hooks/web/useMessage';
import { captureSnapshot } from '@/api/device/camera';
import type { DetectionRegion } from '@/api/device/snap';

defineOptions({ name: 'RegionDrawer' });

const props = defineProps<{
  deviceId: string;
  taskId?: number;
  initialRegions?: DetectionRegion[];
  initialImageId?: number;
  initialImagePath?: string;
}>();

const emit = defineEmits<{
  (e: 'save', regions: DetectionRegion[]): void;
  (e: 'image-captured', imageId: number, imagePath: string): void;
}>();

const { createMessage } = useMessage();

// 状态
const capturing = ref(false);
const currentImage = ref<HTMLImageElement | null>(null);
const currentImageId = ref<number | null>(props.initialImageId || null);
const currentImagePath = ref<string | null>(props.initialImagePath || null);
const imageLoaded = ref(false);

// 区域数据
const regions = ref<DetectionRegion[]>(props.initialRegions || []);
const selectedRegionId = ref<number | string | null>(null);

// Canvas状态
const canvas = ref<HTMLCanvasElement | null>(null);
const ctx = ref<CanvasRenderingContext2D | null>(null);
const isDrawing = ref(false);
const currentPoints = ref<Array<{ x: number; y: number }>>([]);
const imageDisplaySize = ref({ x: 0, y: 0, width: 0, height: 0 });

// 计算属性
const selectedRegion = computed(() => {
  if (selectedRegionId.value === null) return null;
  return regions.value.find(r => (r.id || regions.value.indexOf(r)) === selectedRegionId.value) || null;
});

// 加载图片
const loadImage = (src: string) => {
  imageLoaded.value = false;
  const img = new Image();
  img.crossOrigin = 'Anonymous';
  img.onload = () => {
    currentImage.value = img;
    imageLoaded.value = true;
    resizeCanvas();
    draw();
  };
  img.src = src;
};

// 初始化画布
const initCanvas = () => {
  if (!canvas.value) return;
  ctx.value = canvas.value.getContext('2d');
  resizeCanvas();
  if (currentImage.value) {
    draw();
  }
};

// 调整画布大小
const resizeCanvas = () => {
  if (!canvas.value) return;
  const container = canvas.value.parentElement;
  if (!container) return;

  canvas.value.width = container.clientWidth;
  canvas.value.height = container.clientHeight;
  draw();
};

// 绘制
const draw = () => {
  if (!ctx.value || !canvas.value) return;

  ctx.value.clearRect(0, 0, canvas.value.width, canvas.value.height);

  if (currentImage.value && imageLoaded.value) {
    const img = currentImage.value;
    const scaleX = canvas.value.width / img.width;
    const scaleY = canvas.value.height / img.height;
    const scale = Math.min(scaleX, scaleY);

    const scaledWidth = img.width * scale;
    const scaledHeight = img.height * scale;
    const x = (canvas.value.width - scaledWidth) / 2;
    const y = (canvas.value.height - scaledHeight) / 2;

    imageDisplaySize.value = { x, y, width: scaledWidth, height: scaledHeight };

    ctx.value.drawImage(img, x, y, scaledWidth, scaledHeight);
  }

  // 绘制已保存的区域
  regions.value.forEach(region => {
    drawRegion(region);
  });

  // 绘制当前正在绘制的区域
  if (isDrawing.value && currentPoints.value.length > 0) {
    drawCurrentRegion();
  }
};

// 绘制单个区域
const drawRegion = (region: DetectionRegion) => {
  if (!ctx.value || !imageDisplaySize.value) return;

  const { x: imgX, y: imgY, width: imgWidth, height: imgHeight } = imageDisplaySize.value;

  const toCanvasCoords = (point: { x: number; y: number }) => ({
    x: imgX + point.x * imgWidth,
    y: imgY + point.y * imgHeight,
  });

  ctx.value.save();
  ctx.value.strokeStyle = region.color;
  ctx.value.lineWidth = 2;
  ctx.value.fillStyle = region.color + Math.round(region.opacity * 255).toString(16).padStart(2, '0');

  const isSelected = (region.id || regions.value.indexOf(region)) === selectedRegionId.value;
  if (isSelected) {
    ctx.value.strokeStyle = '#ffffff';
    ctx.value.lineWidth = 3;
  }

  if (region.points && region.points.length > 0) {
    const startPoint = toCanvasCoords(region.points[0]);
    ctx.value.beginPath();
    ctx.value.moveTo(startPoint.x, startPoint.y);

    for (let i = 1; i < region.points.length; i++) {
      const point = toCanvasCoords(region.points[i]);
      ctx.value.lineTo(point.x, point.y);
    }

    ctx.value.closePath();
    ctx.value.fill();
    ctx.value.stroke();

    // 绘制区域名称
    if (region.region_name) {
      ctx.value.fillStyle = region.color;
      ctx.value.font = '14px Inter';
      ctx.value.fillText(region.region_name, startPoint.x + 5, startPoint.y - 5);
    }
  }

  ctx.value.restore();
};

// 绘制当前正在创建的区域
const drawCurrentRegion = () => {
  if (!ctx.value || !imageDisplaySize.value || currentPoints.value.length === 0) return;

  const { x: imgX, y: imgY, width: imgWidth, height: imgHeight } = imageDisplaySize.value;

  const toCanvasCoords = (point: { x: number; y: number }) => ({
    x: imgX + point.x * imgWidth,
    y: imgY + point.y * imgHeight,
  });

  ctx.value.save();
  ctx.value.strokeStyle = '#FF5252';
  ctx.value.lineWidth = 2;
  ctx.value.fillStyle = '#FF525250';

  if (currentPoints.value.length > 0) {
    ctx.value.beginPath();
    const firstPoint = toCanvasCoords(currentPoints.value[0]);
    ctx.value.moveTo(firstPoint.x, firstPoint.y);

    for (let i = 1; i < currentPoints.value.length; i++) {
      const point = toCanvasCoords(currentPoints.value[i]);
      ctx.value.lineTo(point.x, point.y);
    }

    ctx.value.stroke();

    // 绘制点
    currentPoints.value.forEach(point => {
      const canvasPoint = toCanvasCoords(point);
      ctx.value.beginPath();
      ctx.value.arc(canvasPoint.x, canvasPoint.y, 4, 0, Math.PI * 2);
      ctx.value.fill();
    });
  }

  ctx.value.restore();
};

// 鼠标事件处理
const handleMouseDown = (e: MouseEvent) => {
  if (!canvas.value || !imageDisplaySize.value || !currentImage.value) return;

  const rect = canvas.value.getBoundingClientRect();
  const canvasX = e.clientX - rect.left;
  const canvasY = e.clientY - rect.top;

  const { x: imgX, y: imgY, width: imgWidth, height: imgHeight } = imageDisplaySize.value;

  const x = (canvasX - imgX) / imgWidth;
  const y = (canvasY - imgY) / imgHeight;

  if (x < 0 || x > 1 || y < 0 || y > 1) return;

  isDrawing.value = true;
  currentPoints.value.push({ x, y });
  draw();
};

const handleMouseMove = (e: MouseEvent) => {
  if (!isDrawing.value || !canvas.value) return;
  draw();
};

const handleMouseUp = () => {
  // 多边形绘制在双击时完成
};

const handleDoubleClick = () => {
  if (isDrawing.value && currentPoints.value.length >= 3) {
    // 创建新区域
    const newRegion: DetectionRegion = {
      id: Date.now(), // 临时ID
      task_id: props.taskId || 0,
      region_name: `区域 ${regions.value.length + 1}`,
      region_type: 'polygon',
      points: [...currentPoints.value],
      image_id: currentImageId.value || undefined,
      algorithm_type: undefined,
      algorithm_model_id: undefined,
      algorithm_threshold: undefined,
      algorithm_enabled: true,
      color: '#FF5252',
      opacity: 0.3,
      is_enabled: true,
      sort_order: regions.value.length,
    };

    regions.value.push(newRegion);
    selectedRegionId.value = newRegion.id;
    isDrawing.value = false;
    currentPoints.value = [];
    draw();
  }
};

// 选择区域
const selectRegion = (id: number | string) => {
  selectedRegionId.value = id;
  draw();
};

// 删除区域
const deleteRegion = (id: number | string) => {
  const index = regions.value.findIndex(r => (r.id || regions.value.indexOf(r)) === id);
  if (index !== -1) {
    regions.value.splice(index, 1);
    if (selectedRegionId.value === id) {
      selectedRegionId.value = null;
    }
    draw();
  }
};

// 颜色变化
const handleColorChange = () => {
  draw();
};

// 抓拍图片
const handleCapture = async () => {
  if (!props.deviceId) {
    createMessage.error('设备ID不能为空');
    return;
  }

  try {
    capturing.value = true;
    const response = await captureSnapshot(props.deviceId);
    if (response.code === 0 && response.data) {
      currentImageId.value = response.data.image_id;
      currentImagePath.value = response.data.image_url;
      loadImage(response.data.image_url);
      createMessage.success('抓拍成功');
      emit('image-captured', response.data.image_id, response.data.image_url);
    } else {
      createMessage.error(response.msg || '抓拍失败');
    }
  } catch (error) {
    console.error('抓拍失败', error);
    createMessage.error('抓拍失败');
  } finally {
    capturing.value = false;
  }
};

// 清空画布
const handleClear = () => {
  regions.value = [];
  selectedRegionId.value = null;
  currentPoints.value = [];
  isDrawing.value = false;
  draw();
};

// 保存区域
const handleSave = () => {
  if (regions.value.length === 0) {
    createMessage.warning('请至少绘制一个区域');
    return;
  }
  emit('save', regions.value);
};

// 监听区域变化
watch(
  () => selectedRegion.value,
  () => {
    if (selectedRegion.value) {
      draw();
    }
  },
  { deep: true }
);

// 初始化
onMounted(() => {
  initCanvas();
  window.addEventListener('resize', resizeCanvas);

  // 如果有初始图片，加载它
  if (props.initialImagePath) {
    loadImage(props.initialImagePath);
  }
});

onUnmounted(() => {
  window.removeEventListener('resize', resizeCanvas);
});
</script>

<style lang="less" scoped>
.region-drawer-container {
  height: 600px;
  display: flex;
  flex-direction: column;
  background: #f5f5f5;

  .toolbar {
    padding: 12px;
    background: white;
    border-bottom: 1px solid #e8e8e8;
    display: flex;
    gap: 8px;
  }

  .main-content {
    flex: 1;
    display: flex;
    overflow: hidden;

    .region-panel {
      width: 250px;
      background: white;
      border-right: 1px solid #e8e8e8;
      display: flex;
      flex-direction: column;

      .panel-header {
        padding: 12px;
        font-weight: 600;
        border-bottom: 1px solid #e8e8e8;
      }

      .region-list {
        flex: 1;
        overflow-y: auto;
        padding: 8px;

        .region-item {
          display: flex;
          align-items: center;
          padding: 8px;
          margin-bottom: 8px;
          border: 1px solid #e8e8e8;
          border-radius: 4px;
          cursor: pointer;
          transition: all 0.2s;

          &:hover {
            background: #f5f5f5;
          }

          &.active {
            border-color: #1890ff;
            background: #e6f7ff;
          }

          .region-color {
            width: 20px;
            height: 20px;
            border-radius: 4px;
            margin-right: 8px;
          }

          .region-name {
            flex: 1;
            font-size: 14px;
          }

          .region-actions {
            margin-left: 8px;
          }
        }
      }
    }

    .canvas-area {
      flex: 1;
      display: flex;
      align-items: center;
      justify-content: center;
      background: #2d3748;
      overflow: auto;

      .empty-state {
        width: 100%;
        height: 100%;
        display: flex;
        align-items: center;
        justify-content: center;
      }

      .canvas-wrapper {
        width: 100%;
        height: 100%;
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 20px;

        .draw-canvas {
          max-width: 100%;
          max-height: 100%;
          box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
          background: #2d3748;
          border-radius: 4px;
        }
      }
    }

    .config-panel {
      width: 300px;
      background: white;
      border-left: 1px solid #e8e8e8;
      display: flex;
      flex-direction: column;

      .panel-header {
        padding: 12px;
        font-weight: 600;
        border-bottom: 1px solid #e8e8e8;
      }

      .config-content {
        flex: 1;
        overflow-y: auto;
        padding: 16px;
      }

      .empty-config {
        flex: 1;
        display: flex;
        align-items: center;
        justify-content: center;
      }
    }
  }
}
</style>

