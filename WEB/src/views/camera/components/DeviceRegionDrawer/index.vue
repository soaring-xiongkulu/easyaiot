<template>
  <div ref="container" class="region-editor">
    <!-- 主画布区 -->
    <section class="region-editor__main">
      <header class="region-editor__toolbar">
        <div class="region-editor__tool-group">
          <button
            v-for="tool in tools"
            :key="tool.id"
            type="button"
            class="region-tool-btn"
            :class="{ 'is-active': activeTool === tool.id }"
            :title="tool.tip"
            @click="setActiveTool(tool.id)"
          >
            <Icon :icon="tool.icon" :size="14" />
            <span>{{ tool.name }}</span>
          </button>
        </div>

        <div class="region-editor__toolbar-divider" />

        <div class="region-editor__action-group">
          <button
            type="button"
            class="region-action-btn"
            :disabled="capturing"
            @click="onRefreshCapture"
          >
            <Icon
              :icon="capturing ? 'ant-design:loading-outlined' : 'ant-design:camera-outlined'"
              :size="14"
              :spin="capturing"
            />
            <span>刷新抓图</span>
          </button>

          <a-popconfirm
            placement="topRight"
            title="确定清空所有检测区域？"
            :disabled="!currentImage || regions.length === 0"
            @confirm="handleClear"
          >
            <button
              type="button"
              class="region-action-btn"
              :disabled="!currentImage || regions.length === 0"
            >
              <Icon icon="ant-design:clear-outlined" :size="14" />
              <span>清空</span>
            </button>
          </a-popconfirm>

          <a-popconfirm
            placement="topRight"
            title="确定删除当前选中的区域？"
            :disabled="selectedRegionId === null"
            @confirm="handleDeleteSelected"
          >
            <button type="button" class="region-action-btn" :disabled="selectedRegionId === null">
              <Icon icon="ant-design:delete-outlined" :size="14" />
              <span>删除</span>
            </button>
          </a-popconfirm>
        </div>
      </header>

      <div class="region-editor__viewport">
        <canvas
          ref="canvas"
          class="region-editor__canvas"
          @mousedown="handleMouseDown"
          @mousemove="handleMouseMove"
          @mouseup="handleMouseUp"
          @dblclick="handleDoubleClick"
          @contextmenu="handleContextMenu"
        />

        <div v-if="!currentImage && !imageLoading" class="region-editor__empty">
          <a-empty description="正在抓取摄像头画面…">
            <template #image>
              <Icon icon="ant-design:camera-outlined" :size="48" color="rgba(0,0,0,0.25)" />
            </template>
          </a-empty>
        </div>

        <div
          v-if="imageLoading"
          class="region-editor__loading"
          :class="{ 'region-editor__loading--passive': !!currentImage }"
        >
          <a-spin :tip="loadingTip" size="large" />
        </div>
      </div>

      <footer v-if="drawHint && currentImage" class="region-editor__status">
        <span>{{ drawHint }}</span>
      </footer>
    </section>

    <!-- 区域列表侧栏 -->
    <aside class="region-editor__aside">
      <div class="region-editor__aside-head">
        <div class="region-editor__aside-head-main">
          <span class="region-editor__aside-title">区域</span>
          <a-badge
            :count="regions.length"
            :number-style="{ backgroundColor: 'rgba(0, 0, 0, 0.25)', fontSize: '11px' }"
            :show-zero="true"
          />
        </div>
        <span v-if="saving" class="region-editor__sync">
          <Icon icon="ant-design:loading-outlined" :size="12" spin />
        </span>
      </div>

      <div class="region-editor__aside-body">
        <div v-if="regions.length" class="region-list">
          <div
            v-for="(region, index) in regions"
            :key="getRegionKey(region, index)"
            class="region-item"
            :class="{ 'is-selected': selectedRegionId === getRegionKey(region, index) }"
            @click="selectRegion(getRegionKey(region, index))"
          >
            <span class="region-item__swatch" />
            <span class="region-item__name">{{ getDisplayRegionName(region, index) }}</span>
            <span class="region-item__type">{{ getRegionTypeName(region.region_type) }}</span>
            <a-popconfirm
              title="确定删除该区域？"
              placement="topRight"
              @confirm="deleteRegion(getRegionKey(region, index))"
            >
              <button type="button" class="region-item__delete" title="删除" @click.stop>
                <Icon icon="ant-design:delete-outlined" :size="14" />
              </button>
            </a-popconfirm>
          </div>
        </div>
        <div v-else class="region-editor__aside-empty">
          <p>暂无区域</p>
          <p class="region-editor__aside-empty-hint">在画面绘制后将自动保存</p>
        </div>
      </div>

      <div v-if="selectedRegion" class="region-editor__aside-foot">
        <label class="region-editor__field-label">区域名称</label>
        <Input
          v-model:value="selectedRegion.region_name"
          placeholder="输入名称"
          allow-clear
          size="small"
          @blur="handleRegionNameChange"
          @press-enter="handleRegionNameChange"
        />
      </div>
    </aside>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue';
import { Input } from 'ant-design-vue';
import { Icon } from '@/components/Icon';
import { useMessage } from '@/hooks/web/useMessage';
import {
  listDeviceRegionsSafe,
  createDeviceRegion,
  updateDeviceRegion,
  deleteDeviceRegion,
  type DeviceDetectionRegion,
} from '@/api/device/device_detection_region';
import type { DeviceInfo } from '@/api/device/camera';
import { resolveAlertImageDisplayUrl } from '@/utils/alertMinioImage';
import { formatApiErrorMessage } from '@/views/camera/utils/apiErrorMessage';
import { captureSnapshotWithQuality } from '@/views/camera/utils/deviceSnapshotCapture';
import { isGb28181Device, verifySnapshotQuality } from '@/views/camera/utils/snapshotQuality';
defineOptions({ name: 'DeviceRegionDrawer' });

function parseRegionsList(response: unknown): DeviceDetectionRegion[] {
  if (Array.isArray(response)) return response as DeviceDetectionRegion[];
  if (response && typeof response === 'object') {
    const obj = response as Record<string, unknown>;
    if (Array.isArray(obj.data)) return obj.data as DeviceDetectionRegion[];
  }
  return [];
}

function parseRegionEntity(response: unknown): DeviceDetectionRegion | null {
  if (!response || typeof response !== 'object') return null;
  const obj = response as Record<string, unknown>;
  if (obj.id != null && (obj.region_name != null || obj.points != null)) {
    return obj as DeviceDetectionRegion;
  }
  if (obj.data && typeof obj.data === 'object' && (obj.data as DeviceDetectionRegion).id != null) {
    return obj.data as DeviceDetectionRegion;
  }
  return null;
}

function markRegionsDirty() {
  regionsDirty.value = true;
}

function getRegionKey(region: DeviceDetectionRegion, index: number): number | string {
  return region.id ?? index;
}

let persistTimer: ReturnType<typeof setTimeout> | null = null;
let persistQueue: Promise<void> = Promise.resolve();

function schedulePersist(delay = 400) {
  if (persistTimer) clearTimeout(persistTimer);
  persistTimer = setTimeout(() => {
    persistTimer = null;
    void persistRegions({ silent: true }).catch(() => {});
  }, delay);
}

const props = defineProps<{
  taskId: number;
  deviceId: string;
  deviceMeta?: Pick<DeviceInfo, 'id' | 'name' | 'source' | 'device_kind'> | null;
  initialRegions?: DeviceDetectionRegion[];
  initialImageId?: number;
  initialImagePath?: string;
  /** 无基准图时自动抓图 */
  autoCapture?: boolean;
}>();

const emit = defineEmits<{
  (e: 'save', regions: DeviceDetectionRegion[]): void;
  (e: 'image-captured', imageId: number, imagePath: string): void;
  (e: 'cover-updated', imagePath: string): void;
}>();

const { createMessage } = useMessage();

// 工具类型定义
const ToolType = {
  SELECT: 'select',
  RECTANGLE: 'rectangle',
  POLYGON: 'polygon'
};

// 工具列表
interface Tool {
  id: string;
  name: string;
  icon: string;
  tip: string;
}

const tools = ref<Tool[]>([
  {
    id: ToolType.SELECT,
    name: '选择',
    icon: 'ant-design:drag-outlined',
    tip: '点击选中已有区域，可在右侧编辑名称',
  },
  {
    id: ToolType.RECTANGLE,
    name: '矩形',
    icon: 'ant-design:border-outlined',
    tip: '按住鼠标拖拽绘制矩形检测区域',
  },
  {
    id: ToolType.POLYGON,
    name: '多边形',
    icon: 'ant-design:node-index-outlined',
    tip: '依次点击顶点，双击或右键完成封闭',
  },
]);

// 状态
const activeTool = ref<string>(ToolType.SELECT);
const capturing = ref(false);
const saving = ref(false);
const imageLoading = ref(false);
const captureRetryOnLoadFail = ref(0);
const greyRecaptureAttempt = ref(0);
const currentImage = ref<HTMLImageElement | null>(null);
const currentImageId = ref<number | null>(props.initialImageId || null);
const currentImagePath = ref<string | null>(props.initialImagePath || null);
const imageLoaded = ref(false);

// 区域数据
const regions = ref<DeviceDetectionRegion[]>((props.initialRegions || []).map(region => ({
  ...region,
  color: region.color || generateRandomColor(),
})));
const selectedRegionId = ref<number | string | null>(null);
/** 本地有未同步到 props 的编辑（绘制/删除/改名）时，避免被 initialRegions 覆盖 */
const regionsDirty = ref(false);

// 画布上下文提示（随当前工具变化，替代快捷键条）
const drawHint = computed(() => {
  if (!currentImage.value) return '';
  switch (activeTool.value) {
    case ToolType.SELECT:
      return regions.value.length
        ? '点击区域选中后可编辑名称或删除'
        : '选择「矩形」或「多边形」工具开始绘制';
    case ToolType.RECTANGLE:
      return '在画面上按住拖拽，松开完成矩形绘制';
    case ToolType.POLYGON:
      return isDrawing.value
        ? '继续点击添加顶点，双击或右键完成封闭'
        : '依次点击顶点绘制多边形，至少三个点';
    default:
      return '';
  }
});

// Canvas状态
const canvas = ref<HTMLCanvasElement | null>(null);
const ctx = ref<CanvasRenderingContext2D | null>(null);
const isDrawing = ref(false);
const startX = ref<number>(0);
const startY = ref<number>(0);
const currentPoints = ref<Array<{ x: number; y: number }>>([]);
const imageDisplaySize = ref({ x: 0, y: 0, width: 0, height: 0 });

const isGbDevice = computed(() => isGb28181Device(props.deviceMeta ?? { id: props.deviceId }));

const loadingTip = computed(() =>
  capturing.value && isGbDevice.value
    ? 'GB 设备出图中，请稍候…'
    : imageLoading.value && isGbDevice.value
      ? 'GB 设备画面加载中…'
      : '正在加载画面…',
);

// 计算属性
const selectedRegion = computed(() => {
  if (selectedRegionId.value === null) return null;
  return regions.value.find((r, index) => getRegionKey(r, index) === selectedRegionId.value) || null;
});

// 获取区域类型名称
const getRegionTypeName = (type: string) => {
  if (type === 'rectangle') return '矩形';
  if (type === 'polygon') return '多边形';
  return type;
};

// 生成默认区域名称
const generateDefaultRegionName = (): string => {
  const count = regions.value.length + 1;
  return `区域 ${count}`;
};

// 获取显示用的区域名称（确保唯一性）
const getDisplayRegionName = (region: DeviceDetectionRegion, index: number): string => {
  // 如果区域有名称且不为空，直接使用
  if (region.region_name && region.region_name.trim() !== '') {
    return region.region_name;
  }
  // 否则使用基于索引的默认名称
  return `区域 ${index + 1}`;
};

// 规范化区域名称，确保唯一性
const normalizeRegionNames = (regionsList: DeviceDetectionRegion[]) => {
  const usedNames = new Set<string>();
  regionsList.forEach((region, index) => {
    // 如果名称为空，使用默认名称
    if (!region.region_name || region.region_name.trim() === '') {
      region.region_name = `区域 ${index + 1}`;
    }
    // 确保名称唯一性：如果名称已存在，添加后缀
    let finalName = region.region_name.trim();
    let suffix = 1;
    while (usedNames.has(finalName)) {
      finalName = `${region.region_name.trim()} (${suffix})`;
      suffix++;
    }
    region.region_name = finalName;
    usedNames.add(finalName);
  });
};

// 处理区域名称变化
const handleRegionNameChange = () => {
  if (selectedRegion.value) {
    // 如果名称为空，使用默认名称
    if (!selectedRegion.value.region_name || selectedRegion.value.region_name.trim() === '') {
      const index = regions.value.findIndex(r => 
        (r.id || regions.value.indexOf(r)) === selectedRegionId.value
      );
      if (index !== -1) {
        regions.value[index].region_name = `区域 ${index + 1}`;
      }
    }
    draw();
    markRegionsDirty();
    schedulePersist();
  }
};

// 生成随机颜色（专业灰色系）
const generateRandomColor = (): string => {
  const colors = [
    '#8c8c8c', '#a6a6a6', '#bfbfbf', '#d9d9d9', '#737373',
    '#595959', '#434343', '#262626', '#707070', '#909090',
    '#808080', '#6b6b6b', '#5a5a5a', '#4a4a4a', '#3a3a3a',
    '#9a9a9a', '#b3b3b3', '#cccccc', '#e0e0e0', '#f0f0f0',
    '#7a7a7a', '#6a6a6a', '#5c5c5c', '#4d4d4d', '#3d3d3d',
    '#8a8a8a', '#9f9f9f', '#b8b8b8', '#d1d1d1', '#e8e8e8'
  ];
  return colors[Math.floor(Math.random() * colors.length)];
};

// 设置活动工具
const setActiveTool = (toolId: string): void => {
  activeTool.value = toolId;
  onToolChange();
};

const onToolChange = (): void => {
  selectedRegionId.value = null;
  currentPoints.value = [];
  isDrawing.value = false;
};

function onRefreshCapture() {
  void handleCapture(false, true);
}

// 构建可访问的图片 URL（MinIO / VIDEO 本地路径 / 直链）
const buildImageUrl = (src: string): string => resolveAlertImageDisplayUrl(src);

// 加载图片（刷新时保留旧图，画布不卸载）
const loadImage = (
  src: string,
  options?: { retryCaptureOnFail?: boolean; bustCache?: boolean; checkQuality?: boolean },
) => {
  if (!src) {
    console.error('图片路径为空');
    return;
  }

  const fullUrl = buildImageUrl(src);
  if (!fullUrl) {
    console.error('无法解析图片地址:', src);
    if (options?.retryCaptureOnFail && captureRetryOnLoadFail.value < 1) {
      captureRetryOnLoadFail.value += 1;
      void handleCapture(true, true);
    } else if (!options?.retryCaptureOnFail) {
      createMessage.error('图片地址无效，请点击「刷新抓图」');
    }
    return;
  }

  const requestUrl = options?.bustCache
    ? `${fullUrl}${fullUrl.includes('?') ? '&' : '?'}_t=${Date.now()}`
    : fullUrl;

  const keepCurrentFrame = !!currentImage.value;
  if (!keepCurrentFrame) {
    imageLoaded.value = false;
  }
  imageLoading.value = true;

  const finishLoad = (img: HTMLImageElement) => {
    if (!img.naturalWidth || !img.naturalHeight) {
      imageLoading.value = false;
      if (options?.retryCaptureOnFail && captureRetryOnLoadFail.value < 1) {
        captureRetryOnLoadFail.value += 1;
        void handleCapture(true, true);
        return;
      }
      failLoad();
      return;
    }
    currentImage.value = img;
    imageLoaded.value = true;
    imageLoading.value = false;
    void nextTick(() => {
      initCanvas();
    });

    if (options?.checkQuality !== false) {
      void verifySnapshotQuality(src, { bustCache: true }).then(async (quality) => {
        if (quality.valid || !quality.isGrey) return;
        if (greyRecaptureAttempt.value >= 1) return;
        greyRecaptureAttempt.value += 1;
        await handleCapture(true, true);
      });
    }
  };

  const failLoad = () => {
    imageLoading.value = false;
    if (currentImage.value) {
      imageLoaded.value = true;
      void nextTick(() => {
        initCanvas();
      });
    } else {
      imageLoaded.value = false;
      currentImage.value = null;
    }
    if (options?.retryCaptureOnFail) {
      if (captureRetryOnLoadFail.value < 1) {
        captureRetryOnLoadFail.value += 1;
        void handleCapture(true, true);
      }
      return;
    }
    createMessage.error('图片加载失败，请点击「刷新抓图」重试');
  };

  const tryLoad = (useCors: boolean) => {
    const img = new Image();
    if (useCors) {
      img.crossOrigin = 'anonymous';
    }
    img.onload = () => finishLoad(img);
    img.onerror = () => {
      if (useCors) {
        tryLoad(false);
      } else {
        failLoad();
      }
    };
    img.src = requestUrl;
  };

  tryLoad(true);
};

// 初始化画布
const initCanvas = () => {
  if (!canvas.value) return;
  ctx.value = canvas.value.getContext('2d');
  resizeCanvas();
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

  regions.value.forEach((region) => {
    if (!region.points || region.points.length === 0) return;
    drawRegion(region);
  });

  if (isDrawing.value && currentPoints.value.length > 0) {
    drawCurrentRegion();
  }
};

function getPolygonCentroidNorm(points: Array<{ x: number; y: number }>): { x: number; y: number } {
  if (points.length === 0) return { x: 0, y: 0 };
  if (points.length < 3) {
    const sum = points.reduce(
      (acc, p) => ({ x: acc.x + p.x, y: acc.y + p.y }),
      { x: 0, y: 0 },
    );
    return { x: sum.x / points.length, y: sum.y / points.length };
  }

  let area = 0;
  let cx = 0;
  let cy = 0;
  for (let i = 0; i < points.length; i++) {
    const j = (i + 1) % points.length;
    const cross = points[i].x * points[j].y - points[j].x * points[i].y;
    area += cross;
    cx += (points[i].x + points[j].x) * cross;
    cy += (points[i].y + points[j].y) * cross;
  }
  area *= 0.5;
  if (Math.abs(area) < 1e-8) {
    const sum = points.reduce(
      (acc, p) => ({ x: acc.x + p.x, y: acc.y + p.y }),
      { x: 0, y: 0 },
    );
    return { x: sum.x / points.length, y: sum.y / points.length };
  }
  return { x: cx / (6 * area), y: cy / (6 * area) };
}

function getRegionLabelAnchor(
  region: DeviceDetectionRegion,
  toCanvasCoords: (point: { x: number; y: number }) => { x: number; y: number },
): { x: number; y: number; bounds: { minX: number; maxX: number; minY: number; maxY: number } } | null {
  if (!region.points?.length) return null;

  const canvasPoints = region.points.map(toCanvasCoords);
  const bounds = {
    minX: Math.min(...canvasPoints.map(p => p.x)),
    maxX: Math.max(...canvasPoints.map(p => p.x)),
    minY: Math.min(...canvasPoints.map(p => p.y)),
    maxY: Math.max(...canvasPoints.map(p => p.y)),
  };

  let normPoint = getPolygonCentroidNorm(region.points);
  if (!isPointInRegion(region, normPoint.x, normPoint.y)) {
    const sum = region.points.reduce(
      (acc, p) => ({ x: acc.x + p.x, y: acc.y + p.y }),
      { x: 0, y: 0 },
    );
    normPoint = { x: sum.x / region.points.length, y: sum.y / region.points.length };
  }

  const canvasPoint = toCanvasCoords(normPoint);
  return { x: canvasPoint.x, y: canvasPoint.y, bounds };
}

function drawRegionNameLabel(
  ctx: CanvasRenderingContext2D,
  text: string,
  x: number,
  y: number,
  bounds: { minX: number; maxX: number; minY: number; maxY: number },
) {
  const font = '500 12px Inter, -apple-system, BlinkMacSystemFont, sans-serif';
  const padX = 7;
  const boxH = 20;
  const inset = 4;
  ctx.font = font;
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';

  const metrics = ctx.measureText(text);
  let boxW = metrics.width + padX * 2;
  let boxX = x - boxW / 2;
  let boxY = y - boxH / 2;

  const maxW = bounds.maxX - bounds.minX - inset * 2;
  const maxH = bounds.maxY - bounds.minY - inset * 2;
  if (maxW <= 8 || maxH <= 8 || boxH > maxH) return;

  if (boxW > maxW) {
    boxW = maxW;
  }

  boxX = Math.max(bounds.minX + inset, Math.min(boxX, bounds.maxX - boxW - inset));
  boxY = Math.max(bounds.minY + inset, Math.min(boxY, bounds.maxY - boxH - inset));

  if (
    boxX < bounds.minX
    || boxY < bounds.minY
    || boxX + boxW > bounds.maxX
    || boxY + boxH > bounds.maxY
  ) {
    return;
  }

  x = boxX + boxW / 2;
  y = boxY + boxH / 2;
  const radius = 3;

  ctx.fillStyle = 'rgba(0, 0, 0, 0.68)';
  ctx.beginPath();
  if (typeof ctx.roundRect === 'function') {
    ctx.roundRect(boxX, boxY, boxW, boxH, radius);
  } else {
    ctx.rect(boxX, boxY, boxW, boxH);
  }
  ctx.fill();

  ctx.save();
  ctx.beginPath();
  if (typeof ctx.roundRect === 'function') {
    ctx.roundRect(boxX, boxY, boxW, boxH, radius);
  } else {
    ctx.rect(boxX, boxY, boxW, boxH);
  }
  ctx.clip();
  ctx.fillStyle = '#ffffff';
  ctx.fillText(text, x, y);
  ctx.restore();
}

// 绘制单个区域
const drawRegion = (region: DeviceDetectionRegion) => {
  if (!ctx.value || !imageDisplaySize.value) return;

  const { x: imgX, y: imgY, width: imgWidth, height: imgHeight } = imageDisplaySize.value;

  const toCanvasCoords = (point: { x: number; y: number }) => ({
    x: imgX + point.x * imgWidth,
    y: imgY + point.y * imgHeight,
  });

  ctx.value.save();
  // 所有区域框统一使用红色
  const redColor = '#DC3545';
  const darkRedColor = '#B02A37'; // 深一点的红色，用于选中区域边框
  ctx.value.strokeStyle = redColor;
  ctx.value.lineWidth = 1.5; // 边框更细
  const opacityHex = Math.round((region.opacity || 0.3) * 255).toString(16).padStart(2, '0');
  ctx.value.fillStyle = redColor + opacityHex;

  const isSelected = (region.id || regions.value.indexOf(region)) === selectedRegionId.value;
  if (isSelected) {
    ctx.value.strokeStyle = darkRedColor; // 使用深一点的红色
    ctx.value.lineWidth = 2; // 选中时稍微粗一点，但仍然较细
  }

  if (region.points && region.points.length > 0) {
    const startPoint = toCanvasCoords(region.points[0]);
    ctx.value.beginPath();
    ctx.value.moveTo(startPoint.x, startPoint.y);

    for (let i = 1; i < region.points.length; i++) {
      const point = toCanvasCoords(region.points[i]);
      ctx.value.lineTo(point.x, point.y);
    }

    // 如果是矩形或多边形，闭合路径并填充
    if (region.region_type === 'rectangle' || region.region_type === 'polygon') {
      ctx.value.closePath();
      ctx.value.fill();
    }
    
    ctx.value.stroke();

    if (region.region_name) {
      const anchor = getRegionLabelAnchor(region, toCanvasCoords);
      if (anchor) {
        drawRegionNameLabel(ctx.value, region.region_name, anchor.x, anchor.y, anchor.bounds);
      }
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
  // 所有区域框统一使用红色
  const redColor = '#DC3545';
  ctx.value.strokeStyle = redColor;
  ctx.value.lineWidth = 1.5; // 边框更细
  ctx.value.fillStyle = redColor + '50';

  switch (activeTool.value) {
    case ToolType.RECTANGLE:
      if (currentPoints.value.length > 0) {
        const rectStart = toCanvasCoords(currentPoints.value[0]);
        const rectEnd = toCanvasCoords({ x: startX.value, y: startY.value });
        const width = rectEnd.x - rectStart.x;
        const height = rectEnd.y - rectStart.y;

        ctx.value.beginPath();
        ctx.value.rect(rectStart.x, rectStart.y, width, height);
        ctx.value.fill();
        ctx.value.stroke();
      }
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

        const currentPoint = toCanvasCoords({ x: startX.value, y: startY.value });
        ctx.value.lineTo(currentPoint.x, currentPoint.y);
        ctx.value.stroke();

        // 绘制点
        currentPoints.value.forEach(point => {
          const canvasPoint = toCanvasCoords(point);
          ctx.value.fillStyle = redColor;
          ctx.value.beginPath();
          ctx.value.arc(canvasPoint.x, canvasPoint.y, 4, 0, Math.PI * 2);
          ctx.value.fill();
        });
      }
      break;
  }

  ctx.value.restore();
};

// 检查点是否在区域内
const isPointInRegion = (region: DeviceDetectionRegion, x: number, y: number): boolean => {
  if (region.region_type === 'rectangle' && region.points && region.points.length >= 4) {
    const [p1, p2, p3, p4] = region.points;
    const minX = Math.min(p1.x, p2.x, p3.x, p4.x);
    const maxX = Math.max(p1.x, p2.x, p3.x, p4.x);
    const minY = Math.min(p1.y, p2.y, p3.y, p4.y);
    const maxY = Math.max(p1.y, p2.y, p3.y, p4.y);
    return x >= minX && x <= maxX && y >= minY && y <= maxY;
  } else if (region.region_type === 'polygon' && region.points && region.points.length > 0) {
    let inside = false;
    for (let i = 0, j = region.points.length - 1; i < region.points.length; j = i++) {
      const xi = region.points[i].x;
      const yi = region.points[i].y;
      const xj = region.points[j].x;
      const yj = region.points[j].y;
      const crossY = (yi > y) !== (yj > y);
      const crossX = (xj - xi) * (y - yi) / (yj - yi) + xi;
      const intersect = crossY && (x < crossX);
      if (intersect) inside = !inside;
    }
    return inside;
  }
  return false;
};

// 鼠标事件处理
const handleMouseDown = (e: MouseEvent) => {
  if (!canvas.value || !imageDisplaySize.value || !currentImage.value) return;

  const rect = canvas.value.getBoundingClientRect();
  const canvasX = e.clientX - rect.left;
  const canvasY = e.clientY - rect.top;

  const { x: imgX, y: imgY, width: imgWidth, height: imgHeight } = imageDisplaySize.value;

  // 将canvas坐标转换为图片归一化坐标（0-1之间）
  const x = (canvasX - imgX) / imgWidth;
  const y = (canvasY - imgY) / imgHeight;

  // 确保坐标在图片范围内
  if (x < 0 || x > 1 || y < 0 || y > 1) return;

  startX.value = x;
  startY.value = y;

  if (activeTool.value === ToolType.SELECT) {
    // 选择模式：检查点击是否在某个区域内
    let clickedRegion = false;
    for (let i = regions.value.length - 1; i >= 0; i--) {
      const region = regions.value[i];
      if (isPointInRegion(region, x, y)) {
        selectedRegionId.value = region.id || i;
        clickedRegion = true;
        break;
      }
    }
    if (!clickedRegion) {
      selectedRegionId.value = null;
    }
    draw();
    return;
  }

  if ([ToolType.RECTANGLE, ToolType.POLYGON].includes(activeTool.value)) {
    isDrawing.value = true;

    if (activeTool.value === ToolType.POLYGON && currentPoints.value.length === 0) {
      currentPoints.value.push({ x, y });
    } else if (activeTool.value === ToolType.RECTANGLE) {
      currentPoints.value = [{ x, y }];
    }
    draw();
  }
};

const getCanvasNormalizedPoint = (e: MouseEvent): { x: number; y: number } | null => {
  if (!canvas.value || !imageDisplaySize.value) return null;

  const rect = canvas.value.getBoundingClientRect();
  const canvasX = e.clientX - rect.left;
  const canvasY = e.clientY - rect.top;
  const { x: imgX, y: imgY, width: imgWidth, height: imgHeight } = imageDisplaySize.value;

  const x = (canvasX - imgX) / imgWidth;
  const y = (canvasY - imgY) / imgHeight;
  return { x, y };
};

const handleMouseMove = (e: MouseEvent) => {
  const point = getCanvasNormalizedPoint(e);
  if (!point) return;

  startX.value = point.x;
  startY.value = point.y;

  if (isDrawing.value) {
    draw();
  }
};

const onWindowMouseMove = (e: MouseEvent) => {
  if (isDrawing.value) {
    handleMouseMove(e);
  }
};

const onWindowMouseUp = () => {
  if (isDrawing.value) {
    handleMouseUp();
  }
};

const handleMouseUp = () => {
  if (isDrawing.value && currentPoints.value.length > 0) {
    if (activeTool.value === ToolType.RECTANGLE) {
      const width = startX.value - currentPoints.value[0].x;
      const height = startY.value - currentPoints.value[0].y;

      if (Math.abs(width) > 0.01 && Math.abs(height) > 0.01) {
        const newRegion: DeviceDetectionRegion = {
          id: -Date.now(),  // 负数=前端未保存的临时区域，区别于数据库正整数 id（删除/保存据此判断）
          device_id: props.deviceId,
          region_name: generateDefaultRegionName(),
          region_type: 'rectangle',
          points: [
            { x: currentPoints.value[0].x, y: currentPoints.value[0].y },
            { x: currentPoints.value[0].x + width, y: currentPoints.value[0].y },
            { x: currentPoints.value[0].x + width, y: currentPoints.value[0].y + height },
            { x: currentPoints.value[0].x, y: currentPoints.value[0].y + height }
          ],
          image_id: currentImageId.value || undefined,
          color: generateRandomColor(),
          opacity: 0.3,
          is_enabled: true,
          sort_order: regions.value.length,
        };

        regions.value.push(newRegion);
        selectedRegionId.value = getRegionKey(newRegion, regions.value.length - 1);
        markRegionsDirty();
        draw();
        void persistRegions({ silent: true }).catch(() => {});
      }
    } else if (activeTool.value === ToolType.POLYGON) {
      currentPoints.value.push({ x: startX.value, y: startY.value });
      return;
    }

    isDrawing.value = false;
    currentPoints.value = [];
  }
};

const handleDoubleClick = () => {
  if (activeTool.value === ToolType.POLYGON && currentPoints.value.length > 2) {
    finishPolygon();
  }
};

// 完成多边形绘制（封闭并结束）
const finishPolygon = () => {
  if (activeTool.value === ToolType.POLYGON && currentPoints.value.length >= 2) {
    const newRegion: DeviceDetectionRegion = {
      id: -Date.now(),  // 负数=前端未保存的临时区域，区别于数据库正整数 id（删除/保存据此判断）
      device_id: props.deviceId,
      region_name: generateDefaultRegionName(),
      region_type: 'polygon',
      points: [...currentPoints.value],
      image_id: currentImageId.value || undefined,
      color: generateRandomColor(),
      opacity: 0.3,
      is_enabled: true,
      sort_order: regions.value.length,
    };

    regions.value.push(newRegion);
    selectedRegionId.value = getRegionKey(newRegion, regions.value.length - 1);
    markRegionsDirty();
    draw();
    void persistRegions({ silent: true }).catch(() => {});

    isDrawing.value = false;
    currentPoints.value = [];
  }
};

// 处理右键点击事件
const handleContextMenu = (e: MouseEvent) => {
  // 阻止默认右键菜单
  e.preventDefault();
  
  // 如果正在绘制多边形，右键点击时自动封闭并结束绘制
  if (activeTool.value === ToolType.POLYGON && isDrawing.value && currentPoints.value.length >= 2) {
    finishPolygon();
  }
};

// 选择区域
const selectRegion = (id: number | string) => {
  selectedRegionId.value = id;
  draw();
};

// 删除区域
const deleteRegion = async (id: number | string) => {
  const index = regions.value.findIndex((r, idx) => getRegionKey(r, idx) === id);
  if (index !== -1) {
    const region = regions.value[index];
    regions.value.splice(index, 1);
    markRegionsDirty();
    if (selectedRegionId.value === id) {
      selectedRegionId.value = null;
    }
    draw();
    void persistRegions({ silent: true }).catch(() => {});
  }
};

// 删除选中的区域
const handleDeleteSelected = () => {
  if (selectedRegionId.value !== null) {
    deleteRegion(selectedRegionId.value);
  }
};

// 抓拍图片（含 GB 灰图重试；刷新/灰图重抓跳过 5s 预热）
const handleCapture = async (silent = false, skipPreWait = false) => {
  if (!props.deviceId) {
    if (!silent) createMessage.error('设备ID不能为空');
    return;
  }

  try {
    capturing.value = true;
    imageLoading.value = true;
    const result = await captureSnapshotWithQuality(props.deviceId, {
      silent,
      skipPreWait,
      device: props.deviceMeta ?? { id: props.deviceId },
    });
    if (result.ok && result.imageUrl) {
      captureRetryOnLoadFail.value = 0;
      currentImageId.value = result.imageId!;
      currentImagePath.value = result.imageUrl;
      loadImage(result.imageUrl, { bustCache: true });
      if (!silent) {
        createMessage.success('抓图成功');
      }
      emit('image-captured', result.imageId!, result.imageUrl);
      emit('cover-updated', result.imageUrl);
    } else if (!silent) {
      createMessage.error(
        isGbDevice.value
          ? '抓图失败或画面未就绪（GB 设备出图较慢，请稍后重试）'
          : '抓图失败，请稍后重试',
      );
    }
  } catch (error) {
    console.error('抓图失败', error);
    if (!silent) createMessage.error('抓图失败');
  } finally {
    capturing.value = false;
    if (!currentImage.value) {
      imageLoading.value = false;
    }
  }
};

// 清空画布
const handleClear = () => {
  regions.value = [];
  selectedRegionId.value = null;
  currentPoints.value = [];
  isDrawing.value = false;
  markRegionsDirty();
  draw();
  void persistRegions({ silent: true }).catch(() => {});
};

async function persistRegions(options: { silent?: boolean } = {}) {
  if (!props.deviceId || !props.taskId) return;

  const run = async () => {
    if (regions.value.length > 0) {
      const usedNames = new Set<string>();
      for (let i = 0; i < regions.value.length; i++) {
        const region = regions.value[i];
        if (!region.region_name || region.region_name.trim() === '') {
          region.region_name = `区域 ${i + 1}`;
        }
        let finalName = region.region_name;
        let suffix = 1;
        while (usedNames.has(finalName)) {
          finalName = `${region.region_name} (${suffix})`;
          suffix++;
        }
        region.region_name = finalName;
        usedNames.add(finalName);
      }
    }

    const previousSelectedId = selectedRegionId.value;

    try {
      saving.value = true;

      const existingRegions = await listDeviceRegionsSafe(props.deviceId, props.taskId);
      const existingRegionIds = new Set(existingRegions.map(r => r.id));
      const currentRegionIds = new Set(
        regions.value.map(r => r.id).filter(id => id && typeof id === 'number' && id > 0),
      );

      for (const region of regions.value) {
        const regionName =
          region.region_name && region.region_name.trim() !== ''
            ? region.region_name.trim()
            : `区域 ${regions.value.indexOf(region) + 1}`;
        const isValidDbId = region.id && typeof region.id === 'number' && region.id > 0;

        if (isValidDbId && existingRegionIds.has(region.id)) {
          const updateResponse = await updateDeviceRegion(region.id, {
            region_name: regionName,
            region_type: region.region_type,
            points: region.points,
            color: region.color,
            opacity: region.opacity,
            is_enabled: region.is_enabled,
            sort_order: region.sort_order,
            model_ids: [],
          });
          const updated = parseRegionEntity(updateResponse);
          if (updated) {
            const index = regions.value.findIndex(r => r.id === region.id);
            if (index !== -1) {
              regions.value[index] = {
                ...regions.value[index],
                ...updated,
                color: region.color || updated.color || generateRandomColor(),
              };
            }
          }
        } else {
          const createResponse = await createDeviceRegion(props.deviceId, props.taskId, {
            region_name: regionName,
            region_type: region.region_type,
            points: region.points,
            image_id: currentImageId.value || undefined,
            color: region.color,
            opacity: region.opacity,
            is_enabled: region.is_enabled,
            sort_order: region.sort_order,
            model_ids: [],
          });
          const created = parseRegionEntity(createResponse);
          if (created) {
            const index = regions.value.findIndex(r => r === region);
            if (index !== -1) {
              regions.value[index] = {
                ...created,
                color: region.color || created.color || generateRandomColor(),
              };
              existingRegionIds.add(created.id);
              currentRegionIds.add(created.id);
            }
          }
        }
      }

      const regionsToDelete = existingRegions.filter(r => !currentRegionIds.has(r.id));
      for (const regionToDelete of regionsToDelete) {
        try {
          await deleteDeviceRegion(regionToDelete.id);
        } catch (error) {
          console.error('删除区域失败:', regionToDelete.id, error);
        }
      }

      const list = await listDeviceRegionsSafe(props.deviceId, props.taskId);
      regions.value = list.map(region => ({
        ...region,
        color: region.color || generateRandomColor(),
      }));
      normalizeRegionNames(regions.value);

      if (previousSelectedId != null) {
        const matched = regions.value.find((r, index) => getRegionKey(r, index) === previousSelectedId);
        if (matched) {
          selectedRegionId.value = getRegionKey(matched, regions.value.indexOf(matched));
        } else if (regions.value.length > 0) {
          selectedRegionId.value = getRegionKey(regions.value[regions.value.length - 1], regions.value.length - 1);
        } else {
          selectedRegionId.value = null;
        }
      }

      regionsDirty.value = false;
      emit('save', regions.value);
      draw();

      if (!options.silent) {
        createMessage.success('区域已保存');
      }
    } catch (error) {
      console.error('保存失败', error);
      if (!options.silent) {
        createMessage.error(formatApiErrorMessage(error, '区域保存失败，请稍后重试'));
      }
    } finally {
      saving.value = false;
    }
  };

  persistQueue = persistQueue.then(run, run);
  await persistQueue;
}

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

// 监听初始区域配置变化
watch(
  () => props.initialRegions,
  (newRegions, oldRegions) => {
    if (regionsDirty.value) {
      return;
    }

    // 处理 undefined 或 null 的情况
    const newRegionsArray = Array.isArray(newRegions) ? newRegions : [];
    const oldRegionsArray = Array.isArray(oldRegions) ? oldRegions : [];
    
    // 检查数据是否真的变化了（通过比较长度和ID）
    const newIds = newRegionsArray.map(r => r.id).filter(id => id != null).sort();
    const oldIds = oldRegionsArray.map(r => r.id).filter(id => id != null).sort();
    const idsChanged = JSON.stringify(newIds) !== JSON.stringify(oldIds);
    const lengthChanged = (newRegionsArray.length !== oldRegionsArray.length);
    
    // 如果数据有变化，更新区域列表
    if (idsChanged || lengthChanged || oldRegions === undefined) {
      if (newRegionsArray.length > 0) {
        regions.value = newRegionsArray.map(region => ({
          ...region,
          color: region.color || generateRandomColor(),
        }));
        normalizeRegionNames(regions.value);
        
        if (imageLoaded.value && imageDisplaySize.value && imageDisplaySize.value.width > 0) {
          draw();
        }
      } else {
        regions.value = [];
        selectedRegionId.value = null;
        if (imageLoaded.value && imageDisplaySize.value && imageDisplaySize.value.width > 0) {
          draw();
        }
      }
    }
  },
  { deep: true, immediate: true }
);

// 监听初始图片路径变化
watch(
  () => props.initialImagePath,
  (newPath, oldPath) => {
    if (newPath) {
      if (newPath !== currentImagePath.value || !currentImage.value) {
        currentImagePath.value = newPath;
        loadImage(newPath, {
          retryCaptureOnFail: true,
          bustCache: Boolean(oldPath && newPath !== oldPath),
        });
      }
    } else if (oldPath && !newPath) {
      currentImage.value = null;
      currentImagePath.value = null;
      imageLoaded.value = false;
      if (ctx.value && canvas.value) {
        ctx.value.clearRect(0, 0, canvas.value.width, canvas.value.height);
      }
    }
  },
  { immediate: true },
);

// 键盘快捷键处理
const handleKeyDown = (e: KeyboardEvent): void => {
  // 如果焦点在输入框等元素上，不处理快捷键
  if ((e.target as HTMLElement).tagName === 'INPUT' || (e.target as HTMLElement).tagName === 'TEXTAREA') {
    return;
  }

  switch (e.key) {
    case 'Delete':
    case 'Backspace':
      if (selectedRegionId.value !== null) {
        deleteRegion(selectedRegionId.value);
      }
      break;
    case 'v':
    case 'V':
      setActiveTool(ToolType.SELECT);
      break;
    case 'r':
    case 'R':
      setActiveTool(ToolType.RECTANGLE);
      break;
    case 'p':
    case 'P':
      setActiveTool(ToolType.POLYGON);
      break;
    case 'Escape':
      if (isDrawing.value && activeTool.value === ToolType.POLYGON) {
        isDrawing.value = false;
        currentPoints.value = [];
        draw();
      }
      break;
  }
};

// 初始化
onMounted(async () => {
  await nextTick();
  initCanvas();
  window.addEventListener('resize', resizeCanvas);
  window.addEventListener('keydown', handleKeyDown);
  window.addEventListener('mousemove', onWindowMouseMove);
  window.addEventListener('mouseup', onWindowMouseUp);

  // 如果有初始图片，加载它
  if (props.initialImagePath) {
    loadImage(props.initialImagePath, { retryCaptureOnFail: !!props.autoCapture });
  }

  // 加载现有区域：优先使用 props.initialRegions，否则从服务器加载
  if (props.deviceId) {
    if (props.initialRegions && Array.isArray(props.initialRegions)) {
      if (props.initialRegions.length > 0) {
        regions.value = props.initialRegions.map(region => ({
          ...region,
          color: region.color || generateRandomColor(),
        }));
        normalizeRegionNames(regions.value);
        if (props.initialRegions[0].image_path) {
          currentImagePath.value = props.initialRegions[0].image_path;
          loadImage(props.initialRegions[0].image_path, { retryCaptureOnFail: true });
        } else if (props.initialImagePath && !currentImage.value) {
          currentImagePath.value = props.initialImagePath;
          loadImage(props.initialImagePath, { retryCaptureOnFail: true });
        }
      } else {
        regions.value = [];
        if (props.initialImagePath && !currentImage.value) {
          currentImagePath.value = props.initialImagePath;
          loadImage(props.initialImagePath, { retryCaptureOnFail: true });
        }
      }
    } else {
      try {
        const list = await listDeviceRegionsSafe(props.deviceId, props.taskId);
        if (list.length > 0) {
          regions.value = list.map(region => ({
            ...region,
            color: region.color || generateRandomColor(),
          }));
          normalizeRegionNames(regions.value);
          if (list[0].image_path) {
            currentImagePath.value = list[0].image_path;
            loadImage(list[0].image_path, { retryCaptureOnFail: true });
          } else if (props.initialImagePath && !currentImage.value) {
            currentImagePath.value = props.initialImagePath;
            loadImage(props.initialImagePath, { retryCaptureOnFail: true });
          }
        } else if (props.initialImagePath && !currentImage.value) {
          currentImagePath.value = props.initialImagePath;
          loadImage(props.initialImagePath, { retryCaptureOnFail: true });
        }
      } catch (error) {
        console.warn('加载区域失败', error);
        if (props.initialImagePath && !currentImage.value) {
          currentImagePath.value = props.initialImagePath;
          loadImage(props.initialImagePath, { retryCaptureOnFail: true });
        }
      }
    }
  } else if (props.initialImagePath && !currentImage.value) {
    currentImagePath.value = props.initialImagePath;
    loadImage(props.initialImagePath, { retryCaptureOnFail: true });
  }

  if (props.autoCapture && !props.initialImagePath && !currentImage.value) {
    await handleCapture(true);
  }
});

onUnmounted(() => {
  if (persistTimer) clearTimeout(persistTimer);
  window.removeEventListener('resize', resizeCanvas);
  window.removeEventListener('keydown', handleKeyDown);
  window.removeEventListener('mousemove', onWindowMouseMove);
  window.removeEventListener('mouseup', onWindowMouseUp);
});
</script>

<style lang="less" scoped>
@text: rgba(0, 0, 0, 0.65);
@text-muted: rgba(0, 0, 0, 0.45);
@primary: #1677ff;
@canvas-bg: #1a1a1a;
@aside-width: 260px;
@border: #f0f0f0;

.region-editor {
  display: flex;
  align-items: stretch;
  height: 100%;
  min-height: 0;
  background: #fff;
}

.region-editor__main {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  background: #fff;
}

.region-editor__toolbar {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
  padding: 12px 16px;
  background: #fff;
  border-bottom: 1px solid @border;
  flex-shrink: 0;
}

.region-editor__tool-group,
.region-editor__action-group {
  display: inline-flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 6px;
}

.region-editor__toolbar-divider {
  width: 1px;
  height: 22px;
  background: #e8e8e8;
  margin: 0 2px;
  flex-shrink: 0;
}

.region-tool-btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 6px 10px;
  border-radius: 6px;
  border: 1px solid #d9d9d9;
  background: #fff;
  font-size: 13px;
  color: @text;
  cursor: pointer;
  transition: all 0.2s;

  &:hover {
    border-color: @primary;
    color: @primary;
  }

  &.is-active {
    background: fade(@primary, 10%);
    border-color: @primary;
    color: @primary;
  }
}

.region-action-btn {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 6px 12px;
  border-radius: 6px;
  border: 1px solid #d9d9d9;
  background: #fff;
  font-size: 13px;
  color: @text;
  cursor: pointer;
  transition: all 0.2s;

  &:hover:not(:disabled) {
    border-color: @primary;
    color: @primary;
  }

  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  &--primary {
    background: @primary;
    border-color: @primary;
    color: #fff;
    font-weight: 500;

    &:hover:not(:disabled) {
      opacity: 0.92;
      border-color: @primary;
      color: #fff;
    }
  }
}

.region-editor__viewport {
  flex: 1;
  position: relative;
  min-height: 0;
  overflow: hidden;
  background: @canvas-bg;
  margin: 0 12px;
  border-radius: 4px;
}

.region-editor__canvas {
  display: block;
  width: 100%;
  height: 100%;
}

.region-editor__empty,
.region-editor__loading {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2;
  border-radius: 6px;
}

.region-editor__empty {
  background: @canvas-bg;

  :deep(.ant-empty-description) {
    color: @text-muted;
  }
}

.region-editor__loading {
  background: rgba(26, 26, 26, 0.6);
  backdrop-filter: blur(2px);

  &--passive {
    pointer-events: none;
    background: rgba(26, 26, 26, 0.28);
  }

  :deep(.ant-spin-text) {
    color: @text-muted;
    font-size: 13px;
  }

  :deep(.ant-spin-dot-item) {
    background-color: rgba(255, 255, 255, 0.35);
  }
}

.region-editor__status {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 36px;
  padding: 0 16px;
  font-size: 12px;
  color: @text-muted;
  background: #fff;
  border-top: 1px solid @border;
  flex-shrink: 0;
}

.region-editor__aside {
  width: @aside-width;
  flex-shrink: 0;
  min-height: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: #fff;
  border-left: 1px solid @border;
}

.region-editor__aside-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 52px;
  padding: 0 12px;
  border-bottom: 1px solid @border;
  flex-shrink: 0;
}

.region-editor__aside-head-main {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.region-editor__sync {
  display: inline-flex;
  align-items: center;
  color: @primary;
}

.region-editor__aside-title {
  font-size: 13px;
  font-weight: 500;
  color: @text;
}

.region-editor__aside-body {
  flex: 1 1 0;
  min-height: 0;
  width: 100%;
  padding: 10px 12px;
  overflow-x: hidden;
  overflow-y: auto;
  box-sizing: border-box;
}

.region-list {
  width: 100%;
  box-sizing: border-box;
  border: 1px solid #eee;
  border-radius: 6px;
  padding: 4px;
  background: #fff;
}

.region-editor__aside-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  width: 100%;
  box-sizing: border-box;
  min-height: 120px;
  padding: 24px 16px;
  border: 1px dashed #e8e8e8;
  border-radius: 6px;
  text-align: center;

  p {
    margin: 0;
    font-size: 13px;
    color: @text-muted;
  }
}

.region-editor__aside-empty-hint {
  margin-top: 6px !important;
  font-size: 12px !important;
  color: rgba(0, 0, 0, 0.35) !important;
}

.region-editor__aside-foot {
  flex-shrink: 0;
  padding: 12px;
  border-top: 1px solid @border;
  background: #fafafa;
}

.region-editor__field-label {
  display: block;
  margin-bottom: 6px;
  font-size: 12px;
  font-weight: 500;
  color: @text-muted;
  line-height: 1;
}

.region-item {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  box-sizing: border-box;
  min-height: 36px;
  padding: 7px 10px;
  border-radius: 4px;
  cursor: pointer;
  transition: background 0.15s;

  & + & {
    margin-top: 2px;
  }

  &:hover {
    background: #f5f7fa;

    .region-item__delete {
      opacity: 1;
    }
  }

  &.is-selected {
    background: fade(@primary, 10%);
    box-shadow: inset 3px 0 0 @primary;

    .region-item__name {
      color: @primary;
      font-weight: 500;
    }

    .region-item__delete {
      opacity: 1;
    }
  }

  &__swatch {
    width: 14px;
    height: 14px;
    border-radius: 3px;
    background: #dc3545;
    flex-shrink: 0;
  }

  &__name {
    flex: 1;
    min-width: 0;
    font-size: 13px;
    color: @text;
    line-height: 1.3;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  &__type {
    flex-shrink: 0;
    font-size: 11px;
    color: @text-muted;
    line-height: 1;
  }

  &__delete {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 24px;
    height: 24px;
    padding: 0;
    border: none;
    border-radius: 4px;
    background: transparent;
    color: rgba(0, 0, 0, 0.35);
    cursor: pointer;
    opacity: 0;
    flex-shrink: 0;
    transition: opacity 0.15s, background 0.15s, color 0.15s;

    &:hover {
      background: #fff1f0;
      color: #ff4d4f;
    }
  }
}
</style>

