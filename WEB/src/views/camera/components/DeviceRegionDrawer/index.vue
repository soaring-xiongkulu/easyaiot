<template>
  <div ref="container" class="device-region-drawer-container">
    <!-- 工具栏 -->
    <div class="toolbar">
      <div class="toolbar-buttons">
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
        <a-button type="primary" @click="handleSave" :disabled="!currentImage" :loading="saving">
          <template #icon>
            <SaveOutlined />
          </template>
          保存区域
        </a-button>
        <a-button @click="handleDeleteSelected" :disabled="selectedRegionId === null" danger>
          <template #icon>
            <DeleteOutlined />
          </template>
          Del 删除选中
        </a-button>
      </div>
      <!-- 快捷键提示 -->
      <div v-if="currentImage" class="shortcut-hint">
        <div v-for="hint in shortcutHints" :key="hint.key" class="hint-item">
          <span class="key">{{ hint.key }}</span>
          <span class="text">{{ hint.text }}</span>
        </div>
      </div>
    </div>

    <!-- 主内容区 -->
    <div class="main-content">
      <!-- 左侧绘制工具 -->
      <div class="tool-panel">
        <div class="panel-header">
          <span>绘制工具</span>
        </div>
        <div class="tool-list">
          <div
            v-for="tool in tools"
            :key="tool.id"
            class="tool-item"
            :class="{ active: activeTool === tool.id }"
            @click="setActiveTool(tool.id)"
          >
            <Icon :icon="tool.icon"/>
            <span>{{ tool.name }}</span>
          </div>
        </div>
        
        <!-- 算法模型选择 -->
        <div class="model-selector-panel">
          <div class="panel-header">
            <span>算法模型</span>
          </div>
          <div class="model-selector-content">
            <a-spin :spinning="modelListLoading">
              <div v-if="modelList.length > 0" class="model-list">
                <div
                  v-for="model in modelList"
                  :key="model.id"
                  class="model-item"
                  :class="{ 
                    selected: selectedModelIds.includes(model.id),
                    disabled: !selectedRegion
                  }"
                  @click="!isModelListDisabled && toggleModelSelection(model.id)"
                >
                  <a-checkbox
                    :checked="selectedModelIds.includes(model.id)"
                    :disabled="isModelListDisabled"
                    @change="(e) => !isModelListDisabled && handleModelCheckboxChange(model.id, e.target.checked)"
                    @click.stop
                  />
                  <span class="model-name" :class="{ disabled: isModelListDisabled }">
                    {{ model.name }}{{ model.version ? ` (v${model.version})` : '' }}
                  </span>
                </div>
              </div>
              <a-empty v-else-if="!modelListLoading" description="暂无算法模型" :image="false" style="padding: 20px 0;" />
            </a-spin>
          </div>
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
            @contextmenu="handleContextMenu"
          ></canvas>
        </div>
      </div>

      <!-- 右侧区域列表和配置面板 -->
      <div class="region-list-panel">
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
            <div class="region-name">{{ getDisplayRegionName(region, index) }}</div>
            <div class="region-type">{{ getRegionTypeName(region.region_type) }}</div>
            <div class="region-models" :class="{ 'no-models': !region.model_ids || region.model_ids.length === 0 }">
              <span class="models-label">绑定模型：</span>
              <span v-if="region.model_ids && region.model_ids.length > 0" class="models-value">
                {{ getSelectedModelNames(region.model_ids) }}
              </span>
              <span v-else class="models-empty">未绑定</span>
            </div>
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
        
        <!-- 区域配置面板 -->
        <div v-if="selectedRegion" class="region-config-panel">
          <div class="panel-header">
            <span>区域配置</span>
          </div>
          <div class="config-content">
            <a-form :model="selectedRegion" layout="vertical" size="small">
              <a-form-item label="区域名称">
                <a-input 
                  v-model:value="selectedRegion.region_name" 
                  placeholder="请输入区域名称"
                  @blur="handleRegionNameChange"
                />
              </a-form-item>
            </a-form>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue';
import { CameraOutlined, ClearOutlined, SaveOutlined, DeleteOutlined } from '@ant-design/icons-vue';
import { Icon } from '@/components/Icon';
import { useMessage } from '@/hooks/web/useMessage';
import {
  captureDeviceSnapshot,
  updateDeviceCoverImage,
  getDeviceRegions,
  createDeviceRegion,
  updateDeviceRegion,
  deleteDeviceRegion,
  type DeviceDetectionRegion,
} from '@/api/device/device_detection_region';
import { getModelPage } from '@/api/device/model';

defineOptions({ name: 'DeviceRegionDrawer' });

const props = defineProps<{
  deviceId: string;
  initialRegions?: DeviceDetectionRegion[];
  initialImageId?: number;
  initialImagePath?: string;
  modelIds?: number[]; // 可选的模型ID列表，如果提供则只显示这些模型
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
}

const tools = ref<Tool[]>([
  { id: ToolType.SELECT, name: '默认', icon: 'mage:mouse-pointer' },
  { id: ToolType.RECTANGLE, name: '四边形', icon: 'uil:vector-square' },
  { id: ToolType.POLYGON, name: '多边形', icon: 'fa-solid:draw-polygon' }
]);

// 状态
const activeTool = ref<string>(ToolType.SELECT);
const capturing = ref(false);
const saving = ref(false);
const currentImage = ref<HTMLImageElement | null>(null);
const currentImageId = ref<number | null>(props.initialImageId || null);
const currentImagePath = ref<string | null>(props.initialImagePath || null);
const imageLoaded = ref(false);

// 区域数据
const regions = ref<DeviceDetectionRegion[]>((props.initialRegions || []).map(region => ({
  ...region,
  color: region.color || generateRandomColor(),
  model_ids: region.model_ids || []
})));
const selectedRegionId = ref<number | string | null>(null);

// 算法模型相关
const modelList = ref<Array<{ id: number; name: string; version?: string }>>([]);
const selectedModelIds = ref<number[]>([]);
const modelListLoading = ref(false);

// 快捷键提示
const shortcutHints = ref<{ key: string, text: string }[]>([
  { key: 'Del', text: '删除选中' },
  { key: 'V', text: '选择工具' },
  { key: 'R', text: '四边形' },
  { key: 'P', text: '多边形' },
  { key: 'Esc', text: '取消绘制' },
  { key: '右键', text: '封闭多边形' }
]);

// Canvas状态
const canvas = ref<HTMLCanvasElement | null>(null);
const ctx = ref<CanvasRenderingContext2D | null>(null);
const isDrawing = ref(false);
const startX = ref<number>(0);
const startY = ref<number>(0);
const currentPoints = ref<Array<{ x: number; y: number }>>([]);
const imageDisplaySize = ref({ x: 0, y: 0, width: 0, height: 0 });

// 计算属性
const selectedRegion = computed(() => {
  if (selectedRegionId.value === null) return null;
  return regions.value.find(r => (r.id || regions.value.indexOf(r)) === selectedRegionId.value) || null;
});

// 计算属性：是否禁用模型列表（没有选中区域框时禁用）
const isModelListDisabled = computed(() => {
  return selectedRegionId.value === null;
});

// 获取已选模型的名称（英文逗号分隔）
const getSelectedModelNames = (modelIds: number[]): string => {
  if (!modelIds || modelIds.length === 0) return '';
  const names = modelIds
    .map(id => {
      const model = modelList.value.find(m => m.id === id);
      return model ? model.name : '';
    })
    .filter(name => name !== '');
  return names.join(', ');
};

// 加载算法模型列表
const loadModelList = async () => {
  try {
    modelListLoading.value = true;
    
    // 先查询所有模型
    const response = await getModelPage({ pageNo: 1, pageSize: 1000 });
    console.log('模型列表API响应:', response);
    
    // 处理响应数据，兼容不同的响应格式
    let models = [];
    if (response && response.code === 0) {
      models = response.data || [];
    } else if (Array.isArray(response)) {
      // 如果直接返回数组
      models = response;
    } else if (response && response.data && Array.isArray(response.data)) {
      models = response.data;
    }
    
    // 添加特殊模型（-1 和 -2）
    const specialModels = [
      {
        id: -1,
        name: 'yolo11n.pt',
        version: undefined
      },
      {
        id: -2,
        name: 'yolov8n.pt',
        version: undefined
      }
    ];
    
    // 合并数据库模型和特殊模型
    const allModels = [...specialModels, ...models];
    
    if (allModels.length > 0) {
      let filteredModels = allModels;
      
      // 如果提供了 modelIds，则只显示这些模型（包括特殊模型）
      if (props.modelIds && Array.isArray(props.modelIds) && props.modelIds.length > 0) {
        const modelIdSet = new Set(props.modelIds);
        filteredModels = allModels.filter((model: any) => modelIdSet.has(model.id));
        console.log('过滤模型列表，任务关联的模型ID:', props.modelIds, '过滤前数量:', allModels.length, '过滤后数量:', filteredModels.length);
      }
      
      modelList.value = filteredModels.map((model: any) => ({
        id: model.id,
        name: model.name,
        version: model.version
      }));
      console.log('加载模型列表成功，数量:', modelList.value.length, '模型列表:', modelList.value);
    } else {
      console.warn('模型列表为空或格式异常:', response);
      modelList.value = [];
      if (response && response.code !== 0) {
        createMessage.warning(response.msg || '加载算法模型列表失败');
      }
    }
  } catch (error) {
    console.error('加载算法模型列表失败', error);
    createMessage.error('加载算法模型列表失败: ' + (error as Error).message);
    modelList.value = [];
  } finally {
    modelListLoading.value = false;
  }
};

// 切换模型选择
const toggleModelSelection = (modelId: number) => {
  // 如果没有选中区域框，不允许选择模型
  if (isModelListDisabled.value) {
    return;
  }
  const index = selectedModelIds.value.indexOf(modelId);
  if (index > -1) {
    selectedModelIds.value.splice(index, 1);
  } else {
    selectedModelIds.value.push(modelId);
  }
  handleModelChange();
};

// 处理模型复选框变化
const handleModelCheckboxChange = (modelId: number, checked: boolean) => {
  // 如果没有选中区域框，不允许选择模型
  if (isModelListDisabled.value) {
    return;
  }
  if (checked) {
    if (!selectedModelIds.value.includes(modelId)) {
      selectedModelIds.value.push(modelId);
    }
  } else {
    const index = selectedModelIds.value.indexOf(modelId);
    if (index > -1) {
      selectedModelIds.value.splice(index, 1);
    }
  }
  handleModelChange();
};

// 处理模型选择变化
const handleModelChange = () => {
  if (selectedRegion.value) {
    const regionIndex = regions.value.findIndex(r => 
      (r.id || regions.value.indexOf(r)) === selectedRegionId.value
    );
    if (regionIndex !== -1) {
      regions.value[regionIndex].model_ids = [...selectedModelIds.value];
      draw();
    }
  }
};

// 获取区域类型名称
const getRegionTypeName = (type: string) => {
  if (type === 'rectangle') return '四边形';
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
  // 切换到任何工具时，都清空区域选择和模型选择（失去全部焦点）
  selectedRegionId.value = null;
  selectedModelIds.value = [];
  currentPoints.value = [];
  isDrawing.value = false;
};

// 构建完整的图片URL
const buildImageUrl = (src: string): string => {
  if (!src) return '';
  
  // 如果已经是完整的URL（以 http:// 或 https:// 开头），直接返回
  if (src.startsWith('http://') || src.startsWith('https://')) {
    return src;
  }
  
  // 如果是MinIO路径（以/api/v1/buckets开头），使用前端启动地址前缀
  if (src.startsWith('/api/v1/buckets')) {
    return `${window.location.origin}${src}`;
  }
  
  // 如果是相对路径（以/api开头），使用前端启动地址前缀
  if (src.startsWith('/api/')) {
    return `${window.location.origin}${src}`;
  }
  
  // 其他相对路径，添加API基础URL
  const apiUrl = import.meta.env.VITE_GLOB_API_URL || '';
  // 确保路径以 / 开头
  const path = src.startsWith('/') ? src : `/${src}`;
  return `${apiUrl}${path}`;
};

// 加载图片
const loadImage = (src: string) => {
  if (!src) {
    console.error('图片路径为空');
    createMessage.error('图片路径为空');
    return;
  }

  const fullUrl = buildImageUrl(src);
  console.log('加载图片，原始路径:', src, '完整URL:', fullUrl);

  imageLoaded.value = false;
  const img = new Image();
  
  // 处理图片加载成功
  img.onload = () => {
    console.log('图片加载成功:', fullUrl, '尺寸:', img.width, 'x', img.height);
    currentImage.value = img;
    imageLoaded.value = true;
    // 确保canvas已初始化
    if (!ctx.value) {
      initCanvas();
    }
    resizeCanvas();
    draw();
  };
  
  // 处理图片加载失败
  img.onerror = (error) => {
    console.error('图片加载失败:', fullUrl, error);
    imageLoaded.value = false;
    currentImage.value = null;
    
    // 尝试不使用 crossOrigin 重新加载
    if (img.crossOrigin) {
      console.log('尝试不使用 crossOrigin 重新加载图片');
      const retryImg = new Image();
      retryImg.onload = () => {
        console.log('图片重新加载成功（不使用 crossOrigin）');
        currentImage.value = retryImg;
        imageLoaded.value = true;
        if (!ctx.value) {
          initCanvas();
        }
        resizeCanvas();
        draw();
      };
      retryImg.onerror = () => {
        console.error('图片重新加载仍然失败:', fullUrl);
        createMessage.error('图片加载失败，请检查网络连接或图片路径');
      };
      retryImg.src = fullUrl;
    } else {
      createMessage.error('图片加载失败，请检查图片路径是否正确');
    }
  };
  
  // 设置 crossOrigin，但如果失败会重试不使用它
  img.crossOrigin = 'Anonymous';
  img.src = fullUrl;
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
  if (!ctx.value || !canvas.value) {
    console.log('draw: canvas 未初始化');
    return;
  }

  ctx.value.clearRect(0, 0, canvas.value.width, canvas.value.height);

  if (currentImage.value && imageLoaded.value) {
    const img = currentImage.value;
    const scaleX = canvas.value.width / img.width;
    const scaleY = canvas.value.height / img.height;
    // 使用 Math.max 让图片撑满canvas（可能会裁剪部分内容）
    const scale = Math.max(scaleX, scaleY);

    const scaledWidth = img.width * scale;
    const scaledHeight = img.height * scale;
    // 居中显示，超出部分会被裁剪
    const x = (canvas.value.width - scaledWidth) / 2;
    const y = (canvas.value.height - scaledHeight) / 2;

    imageDisplaySize.value = { x, y, width: scaledWidth, height: scaledHeight };

    ctx.value.drawImage(img, x, y, scaledWidth, scaledHeight);
  }

  // 绘制已保存的区域
  console.log('draw: 准备绘制区域，区域数量:', regions.value.length, '图片已加载:', imageLoaded.value, 'imageDisplaySize:', imageDisplaySize.value);
  console.log('draw: regions.value 详情:', JSON.parse(JSON.stringify(regions.value)));
  
  if (regions.value.length === 0) {
    console.warn('draw: 区域列表为空，无法绘制');
  }
  
  regions.value.forEach((region, index) => {
    console.log(`draw: 绘制区域 ${index + 1}:`, {
      id: region.id,
      name: region.region_name,
      type: region.region_type,
      points: region.points?.length || 0,
      pointsData: region.points
    });
    
    if (!region.points || region.points.length === 0) {
      console.warn(`draw: 区域 ${index + 1} (${region.region_name}) 没有点数据，跳过绘制`);
      return;
    }
    
    drawRegion(region);
  });

  // 绘制当前正在绘制的区域
  if (isDrawing.value && currentPoints.value.length > 0) {
    drawCurrentRegion();
  }
};

// 绘制单个区域
const drawRegion = (region: DeviceDetectionRegion) => {
  if (!ctx.value) {
    console.log('drawRegion: ctx 未初始化');
    return;
  }
  if (!imageDisplaySize.value) {
    console.log('drawRegion: imageDisplaySize 未初始化，区域:', region.region_name);
    return;
  }

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

    // 绘制区域名称
    if (region.region_name) {
      ctx.value.fillStyle = redColor;
      ctx.value.font = '14px Inter';
      ctx.value.fillText(region.region_name, startPoint.x + 5, startPoint.y - 5);
    }
    
    // 如果有模型配置，在区域中心绘制模型名称（英文逗号分隔）
    if (region.model_ids && region.model_ids.length > 0) {
      const modelNames = getSelectedModelNames(region.model_ids);
      if (modelNames) {
        // 计算区域的中心点
        let centerX = 0;
        let centerY = 0;
        if (region.points && region.points.length > 0) {
          // 计算所有点的平均值作为中心点
          region.points.forEach(point => {
            const canvasPoint = toCanvasCoords(point);
            centerX += canvasPoint.x;
            centerY += canvasPoint.y;
          });
          centerX = centerX / region.points.length;
          centerY = centerY / region.points.length;
        }
        
        // 测量文字宽度，用于绘制背景框
        ctx.value.font = 'bold 14px Inter';
        ctx.value.textAlign = 'center';
        ctx.value.textBaseline = 'middle';
        const textMetrics = ctx.value.measureText(modelNames);
        const textWidth = textMetrics.width;
        const textHeight = 18; // 文字高度
        const padding = 8; // 内边距
        
        // 绘制背景框（半透明白色背景）
        ctx.value.fillStyle = 'rgba(255, 255, 255, 0.9)';
        ctx.value.strokeStyle = '#2C3E50';
        ctx.value.lineWidth = 2;
        const bgX = centerX - textWidth / 2 - padding;
        const bgY = centerY - textHeight / 2 - padding;
        const bgWidth = textWidth + padding * 2;
        const bgHeight = textHeight + padding * 2;
        ctx.value.fillRect(bgX, bgY, bgWidth, bgHeight);
        ctx.value.strokeRect(bgX, bgY, bgWidth, bgHeight);
        
        // 绘制模型名称文字
        ctx.value.fillStyle = '#2C3E50';
        ctx.value.font = 'bold 14px Inter';
        ctx.value.textAlign = 'center';
        ctx.value.textBaseline = 'middle';
        ctx.value.fillText(modelNames, centerX, centerY);
        
        // 恢复默认对齐方式
        ctx.value.textAlign = 'left';
        ctx.value.textBaseline = 'alphabetic';
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
        // 选中区域框后，加载该区域框关联的模型ID
        if (region.model_ids && Array.isArray(region.model_ids) && region.model_ids.length > 0) {
          selectedModelIds.value = [...region.model_ids];
        } else {
          selectedModelIds.value = [];
        }
        break;
      }
    }
    if (!clickedRegion) {
      // 点击空白处，失焦区域框，清空模型选择并禁用
      selectedRegionId.value = null;
      selectedModelIds.value = [];
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

const handleMouseMove = (e: MouseEvent) => {
  if (!canvas.value || !imageDisplaySize.value) return;

  const rect = canvas.value.getBoundingClientRect();
  const canvasX = e.clientX - rect.left;
  const canvasY = e.clientY - rect.top;

  const { x: imgX, y: imgY, width: imgWidth, height: imgHeight } = imageDisplaySize.value;

  // 转换为归一化坐标 (0-1)
  const x = (canvasX - imgX) / imgWidth;
  const y = (canvasY - imgY) / imgHeight;

  startX.value = x;
  startY.value = y;

  if (isDrawing.value) {
    draw();
  }
};

const handleMouseUp = () => {
  if (isDrawing.value && currentPoints.value.length > 0) {
    if (activeTool.value === ToolType.RECTANGLE) {
      const width = startX.value - currentPoints.value[0].x;
      const height = startY.value - currentPoints.value[0].y;

      if (Math.abs(width) > 0.01 && Math.abs(height) > 0.01) {
        const newRegion: DeviceDetectionRegion = {
          id: Date.now(),
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
          model_ids: [], // 新创建的区域默认不关联模型
        };

        regions.value.push(newRegion);
        selectedRegionId.value = newRegion.id;
        // 选中新区域后，清空模型选择（因为新区域还没有关联模型）
        selectedModelIds.value = [];
        draw();
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
      id: Date.now(),
      device_id: props.deviceId,
      region_name: generateDefaultRegionName(),
      region_type: 'polygon',
      points: [...currentPoints.value],
      image_id: currentImageId.value || undefined,
      color: generateRandomColor(),
      opacity: 0.3,
      is_enabled: true,
      sort_order: regions.value.length,
      model_ids: [], // 新创建的区域默认不关联模型
    };

    regions.value.push(newRegion);
    selectedRegionId.value = newRegion.id;
    // 选中新区域后，清空模型选择（因为新区域还没有关联模型）
    selectedModelIds.value = [];
    draw();

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
  // 选中区域框后，加载该区域框关联的模型ID
  const region = regions.value.find(r => (r.id || regions.value.indexOf(r)) === id);
  if (region && region.model_ids && Array.isArray(region.model_ids) && region.model_ids.length > 0) {
    selectedModelIds.value = [...region.model_ids];
  } else {
    selectedModelIds.value = [];
  }
  draw();
};

// 删除区域
const deleteRegion = async (id: number | string) => {
  const index = regions.value.findIndex(r => (r.id || regions.value.indexOf(r)) === id);
  if (index !== -1) {
    const region = regions.value[index];
    // 如果是有效的数据库ID（大于0的数字），调用API删除服务器上的区域
    const isValidDbId = region.id && typeof region.id === 'number' && region.id > 0;
    if (isValidDbId) {
      try {
        await deleteDeviceRegion(region.id);
        console.log('已删除服务器上的区域:', region.id);
      } catch (error) {
        console.error('删除区域失败:', region.id, error);
        createMessage.error('删除区域失败');
        return; // 如果删除失败，不从前端移除
      }
    }
    // 从前端数组中移除
    regions.value.splice(index, 1);
    if (selectedRegionId.value === id) {
      selectedRegionId.value = null;
      selectedModelIds.value = [];
    }
    draw();
  }
};

// 删除选中的区域
const handleDeleteSelected = () => {
  if (selectedRegionId.value !== null) {
    deleteRegion(selectedRegionId.value);
  }
};


// 抓拍图片
const handleCapture = async () => {
  if (!props.deviceId) {
    createMessage.error('设备ID不能为空');
    return;
  }

  try {
    capturing.value = true;
    const response = await captureDeviceSnapshot(props.deviceId);
    // 当isTransformResponse为false时，返回的是AxiosResponse对象，需要访问response.data
    const result = (response as any).data || response;
    if (result.code === 0 && result.data) {
      currentImageId.value = result.data.image_id;
      currentImagePath.value = result.data.image_url;
      loadImage(result.data.image_url);
      createMessage.success('抓拍成功');
      emit('image-captured', result.data.image_id, result.data.image_url);
      
      // 抓拍成功后，自动更新设备封面图
      try {
        const coverResponse = await updateDeviceCoverImage(props.deviceId);
        const coverResult = (coverResponse as any).data || coverResponse;
        if (coverResult.code === 0 && coverResult.data) {
          emit('cover-updated', coverResult.data.image_url);
        } else {
          console.warn('自动更新封面图失败:', coverResult.msg);
        }
      } catch (coverError) {
        console.error('自动更新封面图失败', coverError);
        // 不显示错误提示，因为抓拍已经成功了
      }
    } else {
      createMessage.error(result.msg || '抓拍失败');
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
  selectedModelIds.value = [];
  currentPoints.value = [];
  isDrawing.value = false;
  draw();
};

// 保存区域
const handleSave = async () => {
  // 验证所有区域都有名称，并确保唯一性（仅当有区域时）
  if (regions.value.length > 0) {
    const usedNames = new Set<string>();
    for (let i = 0; i < regions.value.length; i++) {
      const region = regions.value[i];
      if (!region.region_name || region.region_name.trim() === '') {
        // 如果名称为空，使用默认名称
        region.region_name = `区域 ${i + 1}`;
      }
      // 确保名称唯一性：如果名称已存在，添加后缀
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

  try {
    saving.value = true;
    
    // 先获取现有区域列表
    const existingRegionsResponse = await getDeviceRegions(props.deviceId);
    const existingRegions = existingRegionsResponse.data || [];
    const existingRegionIds = new Set(existingRegions.map(r => r.id));
    const currentRegionIds = new Set(regions.value.map(r => r.id).filter(id => id && typeof id === 'number' && id > 0));

    // 保存或更新每个区域
    for (const region of regions.value) {
      // 确保区域名称不为空
      const regionName = region.region_name && region.region_name.trim() !== '' 
        ? region.region_name.trim() 
        : `区域 ${regions.value.indexOf(region) + 1}`;
      
      // 判断是否为有效的数据库ID（大于0的数字）
      const isValidDbId = region.id && typeof region.id === 'number' && region.id > 0;
      
      if (isValidDbId && existingRegionIds.has(region.id)) {
        // 更新现有区域
        const updateResponse = await updateDeviceRegion(region.id, {
          region_name: regionName,
          region_type: region.region_type,
          points: region.points,
          color: region.color,
          opacity: region.opacity,
          is_enabled: region.is_enabled,
          sort_order: region.sort_order,
          model_ids: region.model_ids || [],
        });
        // 更新前端区域的ID（确保使用服务器返回的最新ID）
        if (updateResponse.code === 0 && updateResponse.data) {
          const index = regions.value.findIndex(r => r.id === region.id);
          if (index !== -1) {
            regions.value[index] = {
              ...regions.value[index],
              ...updateResponse.data,
              color: region.color || updateResponse.data.color || generateRandomColor(),
              model_ids: region.model_ids || updateResponse.data.model_ids || []
            };
          }
        }
      } else {
        // 创建新区域
        const createResponse = await createDeviceRegion(props.deviceId, {
          region_name: regionName,
          region_type: region.region_type,
          points: region.points,
          image_id: currentImageId.value || undefined,
          color: region.color,
          opacity: region.opacity,
          is_enabled: region.is_enabled,
          sort_order: region.sort_order,
          model_ids: region.model_ids || [],
        });
        // 更新前端区域的ID（使用服务器返回的新ID）
        if (createResponse.code === 0 && createResponse.data) {
          const index = regions.value.findIndex(r => r === region);
          if (index !== -1) {
            // 使用服务器返回的完整数据更新前端区域，确保ID正确
            regions.value[index] = {
              ...createResponse.data,
              color: region.color || createResponse.data.color || generateRandomColor(),
              model_ids: region.model_ids || createResponse.data.model_ids || []
            };
            // 更新 existingRegionIds，避免重复创建
            existingRegionIds.add(createResponse.data.id);
            currentRegionIds.add(createResponse.data.id);
          }
        }
      }
    }

    // 删除服务器上存在但前端不存在的区域
    const regionsToDelete = existingRegions.filter(r => !currentRegionIds.has(r.id));
    for (const regionToDelete of regionsToDelete) {
      try {
        await deleteDeviceRegion(regionToDelete.id);
        console.log('已删除服务器上的区域:', regionToDelete.id);
      } catch (error) {
        console.error('删除区域失败:', regionToDelete.id, error);
        // 继续删除其他区域，不中断流程
      }
    }

    createMessage.success('保存成功');
    emit('save', regions.value);
    
    // 重新加载区域列表（确保数据同步）
    const response = await getDeviceRegions(props.deviceId);
    if (response.code === 0 && response.data) {
      // 为没有颜色的区域分配随机颜色，保留model_ids
      regions.value = response.data.map(region => ({
        ...region,
        color: region.color || generateRandomColor(),
        model_ids: region.model_ids || []
      }));
      // 规范化区域名称，确保唯一性
      normalizeRegionNames(regions.value);
      // 重新绘制
      draw();
    }
  } catch (error) {
    console.error('保存失败', error);
    createMessage.error('保存失败');
  } finally {
    saving.value = false;
  }
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

// 监听 modelIds prop 变化，重新加载模型列表
watch(
  () => props.modelIds,
  () => {
    loadModelList();
  },
  { immediate: false }
);

// 监听初始区域配置变化
watch(
  () => props.initialRegions,
  (newRegions, oldRegions) => {
    console.log('watch initialRegions: 新值:', newRegions, '新值长度:', newRegions?.length, '旧值:', oldRegions, '旧值长度:', oldRegions?.length);
    
    // 处理 undefined 或 null 的情况
    const newRegionsArray = Array.isArray(newRegions) ? newRegions : [];
    const oldRegionsArray = Array.isArray(oldRegions) ? oldRegions : [];
    
    // 检查数据是否真的变化了（通过比较长度和ID）
    const newIds = newRegionsArray.map(r => r.id).filter(id => id != null).sort();
    const oldIds = oldRegionsArray.map(r => r.id).filter(id => id != null).sort();
    const idsChanged = JSON.stringify(newIds) !== JSON.stringify(oldIds);
    const lengthChanged = (newRegionsArray.length !== oldRegionsArray.length);
    
    console.log('watch initialRegions: idsChanged:', idsChanged, 'lengthChanged:', lengthChanged, 'newLength:', newRegionsArray.length, 'oldLength:', oldRegionsArray.length);
    
    // 如果数据有变化，更新区域列表
    if (idsChanged || lengthChanged || oldRegions === undefined) {
      if (newRegionsArray.length > 0) {
        // 当初始区域配置变化时，更新区域列表
        regions.value = newRegionsArray.map(region => ({
          ...region,
          color: region.color || generateRandomColor(),
          model_ids: region.model_ids || []
        }));
        // 规范化区域名称，确保唯一性
        normalizeRegionNames(regions.value);
        console.log('watch: 区域配置已更新，区域数量:', regions.value.length, '图片已加载:', imageLoaded.value, 'imageDisplaySize:', imageDisplaySize.value);
        console.log('watch: 区域数据详情:', regions.value);
        
        // 重新绘制画布（无论图片是否已加载，都会尝试绘制）
        // 如果图片还没加载，等图片加载完成后会自动调用 draw()
        if (imageLoaded.value && imageDisplaySize.value && imageDisplaySize.value.width > 0) {
          console.log('watch: 立即绘制区域');
          draw();
        } else {
          console.log('watch: 图片未加载或 imageDisplaySize 未初始化，等待图片加载完成后自动绘制');
        }
      } else {
        // 如果传入空数组，清空区域
        console.log('watch: 清空区域');
        regions.value = [];
        selectedRegionId.value = null;
        if (imageLoaded.value && imageDisplaySize.value && imageDisplaySize.value.width > 0) {
          draw();
        }
      }
    } else {
      console.log('watch: 区域数据未变化，跳过更新');
    }
  },
  { deep: true, immediate: true } // 改为 immediate: true，确保初始值也能触发
);

// 监听初始图片路径变化
watch(
  () => props.initialImagePath,
  (newPath, oldPath) => {
    // 如果路径发生变化，或者路径存在但图片未加载，都重新加载
    if (newPath) {
      if (newPath !== currentImagePath.value || !currentImage.value) {
        console.log('检测到新的图片路径:', newPath, '旧路径:', oldPath, '当前图片:', !!currentImage.value);
        currentImagePath.value = newPath;
        loadImage(newPath);
      }
    } else if (oldPath && !newPath) {
      // 如果路径被清空，清空当前图片
      console.log('图片路径被清空');
      currentImage.value = null;
      currentImagePath.value = null;
      imageLoaded.value = false;
      if (ctx.value && canvas.value) {
        ctx.value.clearRect(0, 0, canvas.value.width, canvas.value.height);
      }
    }
  },
  { immediate: true } // 改为 immediate: true，确保初始值也能触发
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
  initCanvas();
  window.addEventListener('resize', resizeCanvas);
  window.addEventListener('keydown', handleKeyDown);
  
  // 加载算法模型列表
  await loadModelList();

  // 如果有初始图片，加载它
  if (props.initialImagePath) {
    loadImage(props.initialImagePath);
  }

  // 加载现有区域
  // 优先使用 props.initialRegions，如果没有则从服务器加载
  console.log('onMounted: props.initialRegions:', props.initialRegions, 'length:', props.initialRegions?.length);
  if (props.deviceId) {
    // 如果已经有初始区域配置，优先使用它（即使为空数组也要检查，因为可能是异步传入的）
    if (props.initialRegions && Array.isArray(props.initialRegions)) {
      if (props.initialRegions.length > 0) {
        // 使用初始区域配置，但确保有颜色和model_ids
        regions.value = props.initialRegions.map(region => ({
          ...region,
          color: region.color || generateRandomColor(),
          model_ids: region.model_ids || []
        }));
        // 规范化区域名称，确保唯一性
        normalizeRegionNames(regions.value);
        console.log('onMounted: 使用 props.initialRegions，区域数量:', regions.value.length);
        // 如果有区域，尝试加载对应的图片（优先使用区域图片）
        if (props.initialRegions[0].image_path) {
          currentImagePath.value = props.initialRegions[0].image_path;
          loadImage(props.initialRegions[0].image_path);
        } else if (props.initialImagePath && !currentImage.value) {
          // 如果没有区域图片，但有初始图片（封面图），使用封面图
          currentImagePath.value = props.initialImagePath;
          loadImage(props.initialImagePath);
        }
      } else {
        // 如果 initialRegions 是空数组，说明已经加载过了但没有数据，不需要从服务器加载
        console.log('onMounted: props.initialRegions 是空数组，不重新加载');
        regions.value = [];
        // 如果有初始图片，加载它
        if (props.initialImagePath && !currentImage.value) {
          currentImagePath.value = props.initialImagePath;
          loadImage(props.initialImagePath);
        }
      }
    } else {
      // 如果没有初始区域配置，从服务器加载
      console.log('onMounted: 从服务器加载区域配置');
      try {
        const response = await getDeviceRegions(props.deviceId);
        console.log('onMounted: 服务器返回的区域数据:', response);
        if (response.code === 0 && response.data) {
          // 为没有颜色的区域分配随机颜色，保留model_ids
          regions.value = response.data.map(region => ({
            ...region,
            color: region.color || generateRandomColor(),
            model_ids: region.model_ids || []
          }));
          // 规范化区域名称，确保唯一性
          normalizeRegionNames(regions.value);
          console.log('onMounted: 从服务器加载区域成功，区域数量:', regions.value.length);
          // 如果有区域，尝试加载对应的图片（优先使用区域图片）
          if (response.data.length > 0 && response.data[0].image_path) {
            currentImagePath.value = response.data[0].image_path;
            loadImage(response.data[0].image_path);
          } else if (props.initialImagePath && !currentImage.value) {
            // 如果没有区域图片，但有初始图片（封面图），使用封面图
            currentImagePath.value = props.initialImagePath;
            loadImage(props.initialImagePath);
          }
        } else if (props.initialImagePath && !currentImage.value) {
          // 如果没有区域，但有初始图片（封面图），使用封面图
          currentImagePath.value = props.initialImagePath;
          loadImage(props.initialImagePath);
        }
      } catch (error) {
        console.error('加载区域失败', error);
        // 如果加载区域失败，但有初始图片（封面图），使用封面图
        if (props.initialImagePath && !currentImage.value) {
          currentImagePath.value = props.initialImagePath;
          loadImage(props.initialImagePath);
        }
      }
    }
  } else if (props.initialImagePath && !currentImage.value) {
    // 如果没有设备ID，但有初始图片（封面图），使用封面图
    currentImagePath.value = props.initialImagePath;
    loadImage(props.initialImagePath);
  }
});

onUnmounted(() => {
  window.removeEventListener('resize', resizeCanvas);
  window.removeEventListener('keydown', handleKeyDown);
});
</script>

<style lang="less" scoped>
// 变量定义 - 专业简洁配色方案（与 train 模型推理界面保持一致）
@primary-color: #2C3E50;
@secondary-color: #34495E;
@accent-color: #495057;
@success-color: #28A745;
@warning-color: #FFC107;
@error-color: #DC3545;
@light-bg: #F8F9FA;
@light-text: #212529;
@text-secondary: #6C757D;
@text-muted: #868E96;
@gray-color: #ADB5BD;
@border-color: #DEE2E6;
@border-hover: #CED4DA;
@shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
@shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
@shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
@shadow-xl: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);

.device-region-drawer-container {
  height: calc(100vh - 200px);
  min-height: 800px;
  display: flex;
  flex-direction: column;
  background: @light-bg;

  .toolbar {
    padding: 16px 20px;
    background: #ffffff;
    box-shadow: @shadow-sm;
    display: flex;
    flex-direction: column;
    gap: 12px;
    border-bottom: 1px solid @border-color;

    .toolbar-buttons {
      display: flex;
      gap: 10px;
      align-items: center;
      flex-wrap: wrap;

      :deep(.ant-btn) {
        height: 36px;
        padding: 0 16px;
        border-radius: 6px;
        font-weight: 500;
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
        transition: all 0.2s ease;
        border: 1px solid #d9d9d9;

        &:hover {
          box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        }

        &.ant-btn-primary {
          background: @primary-color;
          border-color: @primary-color;
          color: #ffffff;

          &:hover {
            background: @secondary-color;
            border-color: @secondary-color;
          }
        }
      }
    }

    .shortcut-hint {
      display: flex;
      gap: 12px;
      align-items: center;
      justify-content: center;
      padding: 8px 16px;
      background: @light-bg;
      border-radius: 6px;
      font-size: 12px;
      border: 1px solid @border-color;

      .hint-item {
        display: flex;
        align-items: center;
        gap: 6px;

        .key {
          background: #ffffff;
          padding: 4px 8px;
          border-radius: 4px;
          font-weight: 600;
          font-size: 11px;
          border: 1px solid @border-color;
          color: @primary-color;
          box-shadow: @shadow-sm;
        }

        .text {
          font-size: 12px;
          color: @text-secondary;
          font-weight: 500;
        }
      }
    }
  }

  .main-content {
    flex: 1;
    display: flex;
    overflow: hidden;
    gap: 16px;
    padding: 16px;
    background: transparent;

    .tool-panel {
      width: 280px;
      background: #ffffff;
      border-radius: 12px;
      box-shadow: @shadow-md;
      display: flex;
      flex-direction: column;
      overflow: hidden;
      border: 1px solid @border-color;

      .panel-header {
        padding: 16px 20px;
        font-weight: 600;
        font-size: 15px;
        color: @light-text;
        border-bottom: 1px solid @border-color;
        background: @light-bg;
        position: relative;

        &::after {
          content: '';
          position: absolute;
          bottom: 0;
          left: 0;
          width: 40px;
          height: 2px;
          background: @primary-color;
        }
      }

      .tool-list {
        padding: 12px;
        border-bottom: 1px solid @border-color;

        .tool-item {
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 8px;
          padding: 16px;
          margin-bottom: 10px;
          border: 2px solid @border-color;
          border-radius: 10px;
          cursor: pointer;
          transition: all 0.3s ease;
          color: @text-secondary;
          background: #ffffff;

          &:hover {
            background: @light-bg;
            border-color: @border-hover;
            box-shadow: @shadow-sm;
          }

          &.active {
            border-color: @primary-color;
            background: @light-bg;
            color: @light-text;
            box-shadow: @shadow-sm;
          }

          span {
            font-size: 13px;
            font-weight: 500;
          }

          :deep(.iconify) {
            font-size: 24px;
          }
        }
      }

      .model-selector-panel {
        border-top: 1px solid @border-color;
        display: flex;
        flex-direction: column;
        flex: 1;
        min-height: 0;

        .panel-header {
          padding: 16px 20px;
          font-weight: 600;
          font-size: 15px;
          color: @light-text;
          border-bottom: 1px solid @border-color;
          background: @light-bg;
          position: relative;

          &::after {
            content: '';
            position: absolute;
            bottom: 0;
            left: 0;
            width: 40px;
            height: 2px;
            background: @primary-color;
          }
        }

        .model-selector-content {
          flex: 1;
          overflow-y: auto;
          padding: 12px;

          &::-webkit-scrollbar {
            width: 6px;
          }

          &::-webkit-scrollbar-track {
            background: @light-bg;
            border-radius: 3px;
          }

          &::-webkit-scrollbar-thumb {
            background: @gray-color;
            border-radius: 3px;

            &:hover {
              background: @border-hover;
            }
          }

          .model-list {
            display: flex;
            flex-direction: column;
            gap: 8px;

            .model-item {
              display: flex;
              align-items: center;
              gap: 10px;
              padding: 12px;
              border: 2px solid @border-color;
              border-radius: 8px;
              cursor: pointer;
              transition: all 0.3s ease;
              background: #ffffff;

              &:hover:not(.disabled) {
                background: @light-bg;
                border-color: @border-hover;
                box-shadow: @shadow-sm;
              }

              &.selected {
                background: @light-bg;
                border-color: @primary-color;
                box-shadow: @shadow-sm;
              }

              &.disabled {
                cursor: not-allowed;
                opacity: 0.5;
                background: @light-bg;

                &:hover {
                  background: @light-bg;
                  border-color: @border-color;
                  transform: none;
                  box-shadow: none;
                }

                .model-name.disabled {
                  color: @text-muted;
                }
              }

              .model-name {
                flex: 1;
                font-size: 13px;
                color: @light-text;
                word-break: break-all;
                font-weight: 500;

                &.disabled {
                  color: @text-muted;
                }
              }
            }
          }
        }
      }
    }

    .canvas-area {
      flex: 1;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      background: @light-bg;
      overflow: auto;
      position: relative;
      border-radius: 8px;
      box-shadow: @shadow-sm;
      border: 1px solid @border-color;

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
        padding: 24px;

        .draw-canvas {
          max-width: 100%;
          max-height: 100%;
          box-shadow: @shadow-md;
          background: #ffffff;
          border-radius: 6px;
          border: 1px solid @border-color;
        }
      }
    }

    .region-list-panel {
      width: 320px;
      background: #ffffff;
      border-radius: 12px;
      box-shadow: @shadow-md;
      display: flex;
      flex-direction: column;
      overflow: hidden;
      border: 1px solid @border-color;

      .panel-header {
        padding: 16px 20px;
        font-weight: 600;
        font-size: 15px;
        color: @light-text;
        border-bottom: 1px solid @border-color;
        background: @light-bg;
        position: relative;

        &::after {
          content: '';
          position: absolute;
          bottom: 0;
          left: 0;
          width: 40px;
          height: 2px;
          background: @primary-color;
        }
      }

        .region-list {
        flex: 1;
        overflow-y: auto;
        padding: 12px;
        border-bottom: 1px solid @border-color;

        &::-webkit-scrollbar {
          width: 6px;
        }

        &::-webkit-scrollbar-track {
          background: @light-bg;
          border-radius: 3px;
        }

        &::-webkit-scrollbar-thumb {
          background: @gray-color;
          border-radius: 3px;

          &:hover {
            background: @border-hover;
          }
        }

        .region-item {
          display: flex;
          flex-direction: column;
          padding: 14px;
          margin-bottom: 10px;
          border: 2px solid @border-color;
          border-radius: 10px;
          cursor: pointer;
          transition: all 0.3s ease;
          background: #ffffff;
          position: relative;
          overflow: hidden;

          &::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 4px;
            height: 100%;
            background: transparent;
            transition: all 0.3s ease;
          }

          &:hover {
            background: @light-bg;
            border-color: @border-hover;
            box-shadow: @shadow-sm;

            &::before {
              background: @border-hover;
            }
          }

          &.active {
            border-color: @primary-color;
            background: @light-bg;
            box-shadow: @shadow-sm;

            &::before {
              background: @primary-color;
            }
          }

          .region-name {
            font-size: 14px;
            font-weight: 600;
            margin-bottom: 6px;
            color: @light-text;
          }

          .region-type {
            font-size: 12px;
            color: @text-secondary;
            margin-bottom: 8px;
            padding: 4px 8px;
            background: @light-bg;
            border-radius: 4px;
            display: inline-block;
            width: fit-content;
          }

          .region-models {
            font-size: 12px;
            color: @primary-color;
            margin-bottom: 8px;
            word-break: break-all;
            padding: 6px 10px;
            background: @light-bg;
            border-radius: 6px;
            border-left: 3px solid @border-hover;

            &.no-models {
              border-left-color: @text-muted;
            }

            .models-label {
              color: @text-secondary;
              font-weight: 500;
            }

            .models-value {
              color: @light-text;
              font-weight: 600;
            }

            .models-empty {
              color: @text-muted;
              font-weight: 500;
              font-style: italic;
            }
          }

          .region-actions {
            display: flex;
            justify-content: flex-end;
            margin-top: 8px;

            :deep(.ant-btn) {
              border-radius: 6px;
              transition: all 0.3s ease;

              &:hover {
                transform: scale(1.1);
              }
            }
          }
        }
      }

      .region-config-panel {
        border-top: 1px solid @border-color;
        background: #ffffff;

        .panel-header {
          padding: 16px 20px;
          font-weight: 600;
          font-size: 15px;
          color: @light-text;
          border-bottom: 1px solid @border-color;
          background: @light-bg;
          position: relative;

          &::after {
            content: '';
            position: absolute;
            bottom: 0;
            left: 0;
            width: 40px;
            height: 2px;
            background: @primary-color;
          }
        }

        .config-content {
          padding: 16px 20px;

          :deep(.ant-form-item) {
            margin-bottom: 16px;

            .ant-form-item-label {
              label {
                font-weight: 500;
                color: @light-text;
              }
            }

            .ant-input {
              border-radius: 6px;
              border: 1px solid @border-color;
              transition: all 0.2s ease;

              &:focus {
                border-color: @primary-color;
                box-shadow: 0 0 0 2px rgba(44, 62, 80, 0.1);
              }
            }
          }
        }
      }
    }
  }
}
</style>

