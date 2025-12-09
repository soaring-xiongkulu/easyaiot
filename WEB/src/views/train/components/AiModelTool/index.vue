<template>
  <div class="model-workbench">
    <!-- 主内容区 -->
    <div class="main-content">
      <!-- 左侧配置面板 -->
      <div class="left-panel" :class="{ collapsed: state.leftPanelCollapsed }">
        <!-- 模型选择 -->
        <div class="config-section">
          <div class="section-title">
            <SettingOutlined class="icon" />
            <span>模型选择</span>
            <ReloadOutlined class="icon refresh-icon" @click="loadModels" :class="{ spinning: state.loading }" title="刷新模型列表" />
          </div>
          <div class="config-options">
            <div class="input-group">
              <select class="select-field" v-model="state.selectedModelId" @change="handleModelChange">
                <option value="">请选择模型</option>
                <option value="yolov8">Yolov8模型</option>
                <option value="yolov11">Yolov11模型</option>
                <option v-for="model in state.models" :key="model.id" :value="model.id">
                  {{ model.name }} (v{{ model.version }})
                </option>
              </select>
            </div>
          </div>
        </div>

        <!-- 模型服务选择（仅在图片推理时显示） -->
        <div class="config-section" v-if="state.activeSource === 'image'">
          <div class="section-title">
            <SettingOutlined class="icon" />
            <span>模型服务</span>
            <Tooltip title="推理用模型服务优先级高于模型选择">
              <QuestionCircleOutlined class="icon tip-icon" />
            </Tooltip>
            <ReloadOutlined class="icon refresh-icon" @click="loadDeployServices" :class="{ spinning: state.deployServicesLoading }" title="刷新服务列表" />
          </div>
          <div class="config-options">
            <div class="input-group">
              <select class="select-field" v-model="state.selectedDeployServiceId" @change="handleDeployServiceChange">
                <option :value="null">请选择模型服务</option>
                <option v-for="service in state.deployServices" :key="service.id" :value="service.id">
                  {{ service.model_name }}服务（v{{ service.model_version }}）
                </option>
              </select>
            </div>
          </div>
        </div>

        <!-- 历史推理记录 -->
        <div class="config-section">
          <div class="section-title">
            <HistoryOutlined class="icon" />
            <span>历史推理记录</span>
            <ReloadOutlined class="icon refresh-icon" @click="loadInferenceHistory" :class="{ spinning: state.historyLoading }" title="刷新历史记录" />
          </div>
          <div class="config-options">
            <div class="input-group">
              <select class="select-field" v-model="state.selectedHistoryRecordId" @change="handleHistoryRecordChange">
                <option value="">请选择历史记录</option>
                <option v-for="record in state.inferenceHistory" :key="record.id" :value="record.id">
                  {{ formatHistoryRecordLabel(record) }}
                </option>
              </select>
            </div>
          </div>
        </div>

        <!-- 输入源选择 -->
        <div class="config-section">
          <div class="section-title">
            <UploadOutlined class="icon" />
            <span>输入源选择</span>
          </div>
          <div class="config-options">
            <div class="input-group">
              <select class="select-field" v-model="state.activeSource" @change="handleSourceChange">
                <option v-for="option in sourceOptions" :key="option.value" :value="option.value">
                  {{ option.label }}
                </option>
              </select>
            </div>

            <!-- 动态内容区域 -->
            <div class="source-content" v-if="state.activeSource === 'image'">
              <div class="file-upload-wrapper">
                <input
                  type="file"
                  class="file-input"
                  accept="image/*"
                  @change="handleImageUpload"
                  ref="imageInput"
                  id="image-upload-input"
                >
                <label for="image-upload-input" class="file-upload-label">
                  <PictureOutlined class="icon" />
                  <span>{{ state.uploadedImageFile ? state.uploadedImageFile.name : '选择图片文件' }}</span>
                </label>
              </div>
            </div>
            <div class="source-content" v-else-if="state.activeSource === 'video'">
              <div class="file-upload-wrapper">
                <input
                  type="file"
                  class="file-input"
                  accept="video/*"
                  @change="handleVideoUpload"
                  ref="videoInput"
                  id="video-upload-input"
                >
                <label for="video-upload-input" class="file-upload-label">
                  <VideoCameraOutlined class="icon" />
                  <span>{{ state.uploadedVideoFile ? state.uploadedVideoFile.name : '选择视频文件' }}</span>
                </label>
              </div>
            </div>
          </div>
        </div>

        <!-- 控制操作 -->
        <div class="config-section">
          <div class="section-title">
            <ControlOutlined class="icon" />
            <span>控制操作</span>
          </div>
          <div class="config-options">
            <div class="button-group">
              <button class="btn btn-primary" @click="startDetection" :disabled="state.inferenceLoading || !state.selectedModelId">
                <PlayCircleOutlined class="icon" />
                <span v-if="state.inferenceLoading">推理中...</span>
                <span v-else>开始检测</span>
              </button>
              <button class="btn btn-success" @click="state.showOriginal = true" v-if="!state.showOriginal">
                <EyeOutlined class="icon" />
                <span>显示原始对照</span>
              </button>
              <button class="btn btn-white" @click="state.showOriginal = false" v-if="state.showOriginal">
                <CloseOutlined class="icon" />
                <span>关闭原始对照</span>
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- 左侧面板切换按钮 -->
      <div class="panel-toggle"
           :class="{ collapsed: state.leftPanelCollapsed }"
           @click="toggleLeftPanel">
        <LeftOutlined v-if="!state.leftPanelCollapsed" class="icon" />
        <RightOutlined v-else class="icon" />
      </div>

      <!-- 右侧视频显示区域 -->
      <div class="video-area">
        <div class="video-container">
          <!-- 图片模式 -->
          <div v-if="state.activeSource === 'image'">
            <div v-if="state.showOriginal" class="dual-video">
              <div class="video-wrapper">
                <div class="video-title">
                  <span>原始输入源</span>
                </div>
                <div class="video-content">
                  <div v-if="state.uploadedImage" class="image-preview">
                    <img :src="state.uploadedImage" alt="原始图片" class="preview-image">
                  </div>
                  <div v-else class="video-placeholder">
                    <PictureOutlined class="icon" />
                    <span>等待图片上传</span>
                  </div>
                </div>
              </div>
              <div class="video-wrapper">
                <div class="video-title">
                  <span>检测结果</span>
                </div>
                <div class="video-content">
                  <div v-if="state.detectionResult" class="detection-result">
                    <img :src="state.detectionResult" alt="检测结果" class="preview-image" @error="handleImageError">
                    <div class="detection-overlay">
                      <div class="detection-info">
                        <div class="detection-count">检测到 {{ state.detectionCount }} 个目标</div>
                        <div class="confidence">平均置信度: {{ state.averageConfidence }}%</div>
                      </div>
                    </div>
                  </div>
                  <div v-else class="video-placeholder">
                    <ExperimentOutlined class="icon" />
                    <span>检测结果将显示在这里</span>
                  </div>
                </div>
              </div>
            </div>
            <div v-else class="single-video">
              <div class="video-wrapper">
                <div class="video-title">
                  <span>检测结果</span>
                </div>
                <div class="video-content">
                  <div v-if="state.detectionResult" class="detection-result">
                    <img :src="state.detectionResult" alt="检测结果" class="preview-image" @error="handleImageError">
                    <div class="detection-overlay">
                      <div class="detection-info">
                        <div class="detection-count">检测到 {{ state.detectionCount }} 个目标</div>
                        <div class="confidence">平均置信度: {{ state.averageConfidence }}%</div>
                      </div>
                    </div>
                  </div>
                  <div v-else class="video-placeholder">
                    <ExperimentOutlined class="icon" />
                    <span>检测结果将显示在这里</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- 视频模式 -->
          <div v-else>
            <div v-if="state.showOriginal" class="dual-video">
              <div class="video-wrapper">
                <div class="video-title">
                  <span>原始输入源</span>
                </div>
                <div class="video-content">
                  <div v-if="state.uploadedVideoUrl" class="video-preview">
                    <video
                      ref="inputVideoRef"
                      :src="state.uploadedVideoUrl"
                      controls
                      preload="auto"
                      playsinline
                      class="preview-video"
                      @click="handleVideoClick"
                      @error="handleInputVideoError"
                      @loadedmetadata="handleInputVideoLoaded"
                      @loadstart="handleInputVideoLoadStart"
                      @canplay="handleInputVideoCanPlay"
                      @canplaythrough="handleInputVideoCanPlayThrough"
                      @stalled="handleInputVideoStalled"
                      @suspend="handleInputVideoSuspend"
                    ></video>
                    <div v-if="state.videoLoadError" class="video-error-info">
                      <div class="error-title">视频加载错误</div>
                      <div class="error-message">{{ state.videoLoadError }}</div>
                      <div class="error-details" v-if="state.videoErrorDetails">
                        <div>文件类型: {{ state.videoErrorDetails.type }}</div>
                        <div>文件大小: {{ formatFileSize(state.videoErrorDetails.size) }}</div>
                        <div>错误代码: {{ state.videoErrorDetails.errorCode }}</div>
                      </div>
                    </div>
                  </div>
                  <div v-else class="video-placeholder">
                    <VideoCameraOutlined class="icon" />
                    <span>等待视频输入</span>
                  </div>
                </div>
              </div>
              <div class="video-wrapper">
                <div class="video-title">
                  <span>检测结果</span>
                </div>
                <div class="video-content">
                  <div v-if="state.detectionResult" class="video-preview">
                    <video
                      ref="resultVideoRef"
                      :src="getMediaUrl(state.detectionResult)"
                      controls
                      autoplay
                      class="preview-video"
                      @error="handleVideoError"
                      @loadedmetadata="() => console.log('视频元数据加载成功')"
                    ></video>
                  </div>
                  <div v-else-if="state.inferenceLoading" class="video-placeholder">
                    <SearchOutlined class="icon" />
                    <span>推理处理中，请稍候...</span>
                  </div>
                  <div v-else class="video-placeholder">
                    <SearchOutlined class="icon" />
                    <span>检测结果将显示在这里</span>
                  </div>
                </div>
              </div>
            </div>
            <div v-else class="single-video">
              <div class="video-wrapper">
                <div class="video-title">
                  <span>检测结果</span>
                </div>
                <div class="video-content">
                  <div v-if="state.detectionResult" class="video-preview">
                    <video
                      ref="resultVideoRef"
                      :src="getMediaUrl(state.detectionResult)"
                      controls
                      autoplay
                      class="preview-video"
                      @error="handleVideoError"
                      @loadedmetadata="() => console.log('视频元数据加载成功')"
                    ></video>
                  </div>
                  <div v-else-if="state.inferenceLoading" class="video-placeholder">
                    <SearchOutlined class="icon" />
                    <span>推理处理中，请稍候...</span>
                  </div>
                  <div v-else class="video-placeholder">
                    <SearchOutlined class="icon" />
                    <span>检测结果将显示在这里</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, reactive, ref, onMounted, onUnmounted, nextTick } from "vue";
import { useRoute, useRouter } from "vue-router";
import { getModelPage, runInference, runClusterInference, uploadInputFile, getInferenceTaskDetail, getInferenceTasks, getDeployServicePage } from "@/api/device/model";
import { useMessage } from '@/hooks/web/useMessage';
import { Tooltip } from 'ant-design-vue';
import {
  SettingOutlined,
  UploadOutlined,
  ControlOutlined,
  PlayCircleOutlined,
  EyeOutlined,
  CloseOutlined,
  PictureOutlined,
  VideoCameraOutlined,
  LeftOutlined,
  RightOutlined,
  ExperimentOutlined,
  SearchOutlined,
  ReloadOutlined,
  HistoryOutlined,
  QuestionCircleOutlined
} from '@ant-design/icons-vue';

const { createMessage } = useMessage();

// 类型定义

interface Model {
  id: number;
  name: string;
  version: string;
  status: number;
}

interface InferenceHistoryRecord {
  id: number;
  model_id: number | null;
  inference_type?: string;
  status: string;
  input_source: string;
  start_time: string;
  processing_time: number | null;
}

interface DeployService {
  id: number;
  service_name: string;
  model_id: number;
  model_name: string;
  model_version: string;
  status: string;
}

interface AppState {
  activeSource: string;
  confidenceThreshold: number;
  cooldownTime: number;
  showOriginal: boolean;
  detectionStatus: string;
  statusText: string;
  leftPanelCollapsed: boolean;
  showAdvancedSettings: boolean;
  uploadedImage: string | null;
  uploadedImageFile: File | null;
  uploadedVideoFile: File | null;
  uploadedVideoUrl: string | null;
  detectionResult: string | null;
  detectionCount: number;
  averageConfidence: number;
  selectedModelId: number | string | null;
  models: Model[];
  loading: boolean;
  inferenceLoading: boolean;
  currentInferenceRecordId: number | null;
  pollingTimer: number | null;
  pollingStartTime: number | null;
  videoLoadError: string | null;
  videoErrorDetails: {
    type: string;
    size: number;
    errorCode: number | null;
  } | null;
  inferenceHistory: InferenceHistoryRecord[];
  historyLoading: boolean;
  selectedHistoryRecordId: string;
  historyInputSource: string | null; // 保存历史记录的 input_source URL
  deployServices: DeployService[]; // 部署服务列表
  selectedDeployServiceId: number | null; // 选中的部署服务ID
  deployServicesLoading: boolean; // 部署服务加载状态
}

// 状态管理
const state = reactive<AppState>({
  activeSource: 'image',
  confidenceThreshold: 70,
  cooldownTime: 5,
  showOriginal: true,
  detectionStatus: 'idle',
  statusText: '就绪 - 等待输入源',
  leftPanelCollapsed: false,
  showAdvancedSettings: false,
  uploadedImage: null,
  uploadedImageFile: null,
  uploadedVideoFile: null,
  uploadedVideoUrl: null,
  detectionResult: null,
  detectionCount: 0,
  averageConfidence: 0,
  selectedModelId: 'yolov11',
  models: [],
  loading: false,
  inferenceLoading: false,
  currentInferenceRecordId: null,
  pollingTimer: null,
  pollingStartTime: null,
  videoLoadError: null,
  videoErrorDetails: null,
  inferenceHistory: [],
  historyLoading: false,
  selectedHistoryRecordId: '',
  historyInputSource: null,
  deployServices: [],
  selectedDeployServiceId: null,
  deployServicesLoading: false
});

// 轮询超时时间（5分钟）
const POLLING_TIMEOUT = 5 * 60 * 1000;
// 轮询间隔（1秒）
const POLLING_INTERVAL = 1000;

const sourceOptions = [
  { value: 'image', label: '图片上传' },
  { value: 'video', label: '视频上传' }
];

const imageInput = ref<HTMLInputElement | null>(null);
const videoInput = ref<HTMLInputElement | null>(null);
const inputVideoRef = ref<HTMLVideoElement | null>(null);
const resultVideoRef = ref<HTMLVideoElement | null>(null);

const selectedSource = computed(() => {
  return sourceOptions.find(option => option.value === state.activeSource);
});

const setActiveSource = (source: string) => {
  state.activeSource = source;
};


const loadDetectionParams = async () => {
  try {
    // 模拟API调用
    const params = await new Promise<any>(resolve => setTimeout(() => resolve({
      confidenceThreshold: 70,
      cooldownTime: 5,
      showOriginal: true
    }), 300));

    // 更新状态
    state.confidenceThreshold = params.confidenceThreshold;
    state.cooldownTime = params.cooldownTime;
    state.showOriginal = params.showOriginal;
  } catch (error) {
    console.error('加载参数失败:', error);
    alert('加载参数失败，请重试');
  }
};

const startDetection = async () => {
  if (!state.selectedModelId) {
    createMessage.warning('请先选择模型');
    return;
  }

  if (state.activeSource === 'image' && !state.uploadedImageFile && !state.historyInputSource) {
    createMessage.warning('请先上传图片');
    return;
  }

  if (state.activeSource === 'video' && !state.uploadedVideoFile && !state.historyInputSource) {
    createMessage.warning('请先上传视频');
    return;
  }

  state.inferenceLoading = true;
  state.detectionStatus = 'running';
  state.statusText = '推理中...';

  try {
    const formData = new FormData();
    
    // 设置推理类型
    formData.append('inference_type', state.activeSource);
    
    // 设置推理参数
    const parameters = {
      conf_thres: state.confidenceThreshold / 100,
      iou_thres: 0.45
    };
    formData.append('parameters', JSON.stringify(parameters));

    // 如果是默认模型，添加模型文件路径参数
    if (state.selectedModelId === 'yolov8') {
      formData.append('model_file_path', 'yolov8n.pt');
    } else if (state.selectedModelId === 'yolov11') {
      formData.append('model_file_path', 'yolo11n.pt');
    }
    // 注意：用户上传的模型不需要传递 model_file_path，后端会根据 model_id 从 MinIO 下载

    // 根据输入源类型添加文件或URL
    if (state.activeSource === 'image' && state.uploadedImageFile) {
      formData.append('file', state.uploadedImageFile);
    } else if (state.activeSource === 'image' && state.historyInputSource) {
      // 从历史记录还原的图片，使用 input_source URL
      formData.append('input_source', state.historyInputSource);
    } else if (state.activeSource === 'video' && state.uploadedVideoFile) {
      formData.append('file', state.uploadedVideoFile);
    } else if (state.activeSource === 'video' && state.historyInputSource) {
      // 从历史记录还原的视频，使用 input_source URL
      formData.append('input_source', state.historyInputSource);
    }

    // 判断使用哪个接口：优先使用模型服务接口（集群接口）
    let response;
    let useClusterService = false;
    
    if (state.selectedDeployServiceId && state.activeSource === 'image') {
      // 使用模型服务接口（集群接口）
      const selectedService = state.deployServices.find(s => s.id === state.selectedDeployServiceId);
      if (selectedService && selectedService.model_id) {
        useClusterService = true;
        const clusterModelId = selectedService.model_id;
        response = await runClusterInference(clusterModelId, formData);
      } else {
        createMessage.warning('选中的模型服务无效，将使用模型列表接口');
        useClusterService = false;
      }
    }
    
    // 如果未选择模型服务或模型服务无效，使用模型列表接口
    if (!useClusterService) {
      // 调用推理接口
      // 重要：用户上传的模型应该传递实际的 model_id（数字），而不是转换为 0
      // 只有默认模型（yolov8/yolov11）才传递 0
      let modelId: number;
      if (state.selectedModelId === 'yolov8' || state.selectedModelId === 'yolov11') {
        modelId = 0; // 默认模型使用 0
      } else if (typeof state.selectedModelId === 'number') {
        modelId = state.selectedModelId; // 用户上传的模型使用实际的 ID
      } else if (typeof state.selectedModelId === 'string' && state.selectedModelId !== '') {
        // 如果 selectedModelId 是字符串且不是空字符串，尝试转换为数字
        const parsedId = parseInt(state.selectedModelId, 10);
        modelId = isNaN(parsedId) ? 0 : parsedId;
      } else {
        modelId = 0; // 默认值
      }
      
      response = await runInference(modelId, formData);
    }
    
    // 当 isTransformResponse: false 时，返回的是整个 Axios 响应对象，需要访问 response.data 获取实际响应
    const responseData = response.data || response;
    
    if (responseData.code === 0) {
      const result = responseData.data.result;
      
      // 处理结果
      if (state.activeSource === 'image') {
        // 优先使用 result_url（检测结果图片），如果没有则使用 image_url（原始图片作为后备）
        let imagePath = '';
        if (result.result_url) {
          // result_url 是检测结果图片的URL，直接使用
          imagePath = result.result_url;
        } else if (result.image_url) {
          // image_url 是原始输入图片，不是检测结果，但可以作为后备
          imagePath = result.image_url;
        }
        
        // 使用 getMediaUrl 处理路径，确保可以正确访问
        state.detectionResult = imagePath ? getMediaUrl(imagePath) : null;
        
        // 设置检测数量
        state.detectionCount = result.detection_count || 0;
        
        // 计算平均置信度（从 detections 数组中计算）
        if (result.detections && Array.isArray(result.detections) && result.detections.length > 0) {
          const totalConfidence = result.detections.reduce((sum: number, det: any) => {
            return sum + (det.confidence || 0);
          }, 0);
          state.averageConfidence = Math.round((totalConfidence / result.detections.length) * 100);
        } else {
          state.averageConfidence = result.average_confidence ? Math.round(result.average_confidence * 100) : 0;
        }
      } else if (state.activeSource === 'video') {
        // 视频推理是异步的，需要轮询获取结果
        if (responseData.data?.record_id) {
          state.currentInferenceRecordId = responseData.data.record_id;
          startPollingInferenceResult(responseData.data.record_id);
          createMessage.success('视频推理任务已提交，处理中...');
          // 视频推理是异步的，不在这里设置完成状态，由轮询函数处理
          // 也不在这里设置 inferenceLoading = false，保持加载状态直到轮询完成
          return; // 提前返回，不执行后面的完成状态设置
        } else if (result.output_path) {
          // 如果立即返回了结果路径，直接使用
          state.detectionResult = result.output_path;
          state.detectionStatus = 'completed';
          state.statusText = '推理完成';
          createMessage.success('视频推理完成');
        } else {
          createMessage.warning('视频推理任务已提交，但无法获取任务ID');
          state.inferenceLoading = false;
          state.detectionStatus = 'failed';
          state.statusText = '推理失败';
          return;
        }
      }
      
      // 图片推理在这里设置完成状态
      state.detectionStatus = 'completed';
      state.statusText = '推理完成';
      createMessage.success('推理执行成功');
    } else {
      throw new Error(responseData.msg || '推理失败');
    }
  } catch (error: any) {
    console.error('推理失败:', error);
    state.detectionStatus = 'failed';
    state.statusText = '推理失败';
    createMessage.error(error.message || '推理执行失败，请重试');
  } finally {
    state.inferenceLoading = false;
  }
};

const toggleLeftPanel = () => {
  state.leftPanelCollapsed = !state.leftPanelCollapsed;
};

const triggerImageUpload = () => {
  imageInput.value?.click();
};

const triggerVideoUpload = () => {
  videoInput.value?.click();
};

const handleImageUpload = (event: Event) => {
  const target = event.target as HTMLInputElement;
  const file = target.files?.[0];
  if (file) {
    // 清理之前的视频URL和历史记录
    cleanupVideoUrl();
    state.historyInputSource = null; // 清除历史记录的 input_source
    state.uploadedImageFile = file;
    const reader = new FileReader();
    reader.onload = (e) => {
      state.uploadedImage = e.target?.result as string;
      state.detectionResult = null; // 清除之前的检测结果
    };
    reader.readAsDataURL(file);
  }
};

const handleVideoUpload = (event: Event) => {
  const target = event.target as HTMLInputElement;
  const file = target.files?.[0];
  if (file) {
    // 清理之前的视频URL和历史记录
    cleanupVideoUrl();
    state.historyInputSource = null; // 清除历史记录的 input_source
    
    // 清除之前的错误状态
    state.videoLoadError = null;
    state.videoErrorDetails = null;
    
    // 验证文件类型
    if (!file.type.startsWith('video/')) {
      createMessage.warning('请选择有效的视频文件');
      // 清空输入
      if (target) {
        target.value = '';
      }
      return;
    }
    
    // 检查文件大小（限制为 2GB）
    const maxSize = 2 * 1024 * 1024 * 1024; // 2GB
    if (file.size > maxSize) {
      createMessage.warning('视频文件过大，请选择小于 2GB 的文件');
      if (target) {
        target.value = '';
      }
      return;
    }
    
    state.uploadedVideoFile = file;
    state.detectionResult = null; // 清除之前的检测结果
    
    try {
      // 创建视频预览URL
      state.uploadedVideoUrl = URL.createObjectURL(file);
      console.log('视频文件已加载:', {
        name: file.name,
        size: file.size,
        type: file.type || '未知类型',
        url: state.uploadedVideoUrl,
        lastModified: new Date(file.lastModified).toLocaleString()
      });
      
      // 检查视频格式支持
      if (!file.type) {
        console.warn('文件类型未知，可能无法正常播放');
        createMessage.warning('文件类型未知，如果无法播放，请尝试使用 MP4 格式（H.264 编码）');
      } else if (!file.type.includes('mp4') && !file.type.includes('webm') && !file.type.includes('ogg')) {
        console.warn('视频格式可能不被浏览器支持:', file.type);
        createMessage.warning(`视频格式 ${file.type} 可能不被浏览器支持，建议使用 MP4 格式（H.264 编码）`);
      }
    } catch (error) {
      console.error('创建视频预览URL失败:', error);
      createMessage.error('视频文件加载失败，请重试');
      state.uploadedVideoFile = null;
      state.uploadedVideoUrl = null;
    }
  }
};



// 加载模型列表
const loadModels = async () => {
  state.loading = true;
  try {
    const response = await getModelPage({ page: 1, size: 100 });
    if (response.code === 0) {
      state.models = response.data || [];
      if (state.models.length > 0 && !state.selectedModelId) {
        state.selectedModelId = state.models[0].id;
      }
    }
  } catch (error: any) {
    console.error('加载模型列表失败:', error);
    createMessage.error('加载模型列表失败');
  } finally {
    state.loading = false;
  }
};

// 加载部署服务列表
const loadDeployServices = async () => {
  state.deployServicesLoading = true;
  try {
    const response = await getDeployServicePage({ pageNo: 1, pageSize: 100 });
    if (response.code === 0) {
      // 只显示运行中的服务
      state.deployServices = (response.data || []).filter((service: DeployService) => 
        service.status === 'running' && service.model_id
      );
    }
  } catch (error: any) {
    console.error('加载部署服务列表失败:', error);
    createMessage.error('加载部署服务列表失败');
  } finally {
    state.deployServicesLoading = false;
  }
};

// 处理部署服务选择变化
const handleDeployServiceChange = () => {
  state.detectionResult = null;
  state.detectionCount = 0;
  state.averageConfidence = 0;
  stopPollingInferenceResult();
};

const handleModelChange = () => {
  state.detectionResult = null;
  state.detectionCount = 0;
  state.averageConfidence = 0;
  // 停止轮询
  stopPollingInferenceResult();
};

// 切换输入源时清理
const handleSourceChange = () => {
  stopPollingInferenceResult();
  cleanupVideoUrl();
  state.historyInputSource = null; // 清除历史记录的 input_source
  state.detectionResult = null;
  
  // 如果切换到图片推理，加载部署服务列表；否则清空选择
  if (state.activeSource === 'image') {
    loadDeployServices();
  } else {
    // 非图片推理时，清空模型服务选择（因为模型服务只支持图片推理）
    state.selectedDeployServiceId = null;
  }
};

// 处理图片加载错误
const handleImageError = (event: Event) => {
  const img = event.target as HTMLImageElement;
  console.error('图片加载失败:', img.src);
  createMessage.error('图片加载失败，请检查图片路径');
};

// 处理视频加载错误（检测结果视频）
const handleVideoError = (event: Event) => {
  const video = event.target as HTMLVideoElement;
  console.error('视频加载失败:', {
    src: video.src,
    error: video.error,
    networkState: video.networkState,
    readyState: video.readyState
  });
  
  if (video.error) {
    const errorCode = video.error.code;
    let errorMsg = '视频加载失败';
    switch (errorCode) {
      case MediaError.MEDIA_ERR_ABORTED:
        errorMsg = '视频加载被中止';
        break;
      case MediaError.MEDIA_ERR_NETWORK:
        errorMsg = '视频网络错误，请检查网络连接';
        break;
      case MediaError.MEDIA_ERR_DECODE:
        errorMsg = '视频解码失败，视频格式可能不支持';
        break;
      case MediaError.MEDIA_ERR_SRC_NOT_SUPPORTED:
        errorMsg = '视频格式不支持，请检查视频编码格式';
        break;
      default:
        errorMsg = `视频加载失败 (错误代码: ${errorCode})`;
    }
    createMessage.error(errorMsg);
  } else {
    createMessage.error('视频加载失败，请检查视频路径或格式');
  }
};

// 处理原始输入视频的错误
const handleInputVideoError = (event: Event) => {
  const video = event.target as HTMLVideoElement;
  const errorInfo = {
    src: video.src,
    error: video.error,
    networkState: video.networkState,
    readyState: video.readyState,
    currentSrc: video.currentSrc,
    videoWidth: video.videoWidth,
    videoHeight: video.videoHeight,
    duration: video.duration
  };
  
  console.error('原始视频加载失败:', errorInfo);
  
  let errorMsg = '视频加载失败';
  let errorCode: number | null = null;
  
  if (video.error) {
    errorCode = video.error.code;
    switch (errorCode) {
      case MediaError.MEDIA_ERR_ABORTED:
        errorMsg = '视频加载被中止，可能是文件损坏或格式不支持';
        break;
      case MediaError.MEDIA_ERR_NETWORK:
        errorMsg = '视频网络错误，请检查文件是否完整';
        break;
      case MediaError.MEDIA_ERR_DECODE:
        errorMsg = '视频解码失败，视频编码格式可能不被浏览器支持（建议使用 H.264 编码的 MP4 格式）';
        break;
      case MediaError.MEDIA_ERR_SRC_NOT_SUPPORTED:
        errorMsg = '视频格式不支持，请检查视频编码格式（建议使用 MP4/H.264）';
        break;
      default:
        errorMsg = `视频加载失败 (错误代码: ${errorCode})`;
    }
  } else {
    errorMsg = '视频加载失败，请检查视频文件是否损坏或格式是否正确';
  }
  
  // 设置错误状态
  state.videoLoadError = errorMsg;
  if (state.uploadedVideoFile) {
    state.videoErrorDetails = {
      type: state.uploadedVideoFile.type || '未知',
      size: state.uploadedVideoFile.size,
      errorCode: errorCode
    };
  }
  
  createMessage.error(errorMsg);
  console.error('视频详细信息:', {
    file: state.uploadedVideoFile,
    errorInfo: errorInfo
  });
};

// 处理原始视频元数据加载
const handleInputVideoLoaded = (event: Event) => {
  const video = event.target as HTMLVideoElement;
  console.log('原始视频元数据加载成功:', {
    duration: video.duration,
    videoWidth: video.videoWidth,
    videoHeight: video.videoHeight,
    readyState: video.readyState,
    networkState: video.networkState
  });
  // 清除错误状态
  state.videoLoadError = null;
  state.videoErrorDetails = null;
};

// 处理原始视频开始加载
const handleInputVideoLoadStart = (event: Event) => {
  console.log('原始视频开始加载');
  state.videoLoadError = null;
  state.videoErrorDetails = null;
};

// 处理原始视频可以播放
const handleInputVideoCanPlay = (event: Event) => {
  const video = event.target as HTMLVideoElement;
  console.log('原始视频可以播放:', {
    duration: video.duration,
    readyState: video.readyState
  });
};

// 处理原始视频可以完整播放
const handleInputVideoCanPlayThrough = (event: Event) => {
  console.log('原始视频可以完整播放');
};

// 处理原始视频加载停滞
const handleInputVideoStalled = (event: Event) => {
  console.warn('原始视频加载停滞');
  createMessage.warning('视频加载缓慢，请检查网络连接或文件大小');
};

// 处理原始视频加载暂停
const handleInputVideoSuspend = (event: Event) => {
  console.warn('原始视频加载暂停');
};

const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

// 获取媒体文件的访问URL
const getMediaUrl = (path: string): string => {
  if (!path) return '';
  // 如果已经是完整的HTTP/HTTPS URL，直接返回
  if (path.startsWith('http://') || path.startsWith('https://')) {
    return path;
  }
  // 如果是相对路径（以 / 开头），直接返回（假设可以通过API服务器直接访问）
  if (path.startsWith('/')) {
    return path;
  }
  // 其他情况，通过 /api/media/ 访问
  return `/api/media/${encodeURIComponent(path)}`;
};

// 处理视频点击播放
const handleVideoClick = (event: Event) => {
  const video = event.target as HTMLVideoElement;
  if (video.paused) {
    video.play().catch(err => {
      console.error('视频播放失败:', err);
    });
  }
};

// 开始轮询推理结果
const startPollingInferenceResult = (recordId: number) => {
  // 清除之前的轮询
  stopPollingInferenceResult();
  
  state.currentInferenceRecordId = recordId;
  state.pollingStartTime = Date.now();
  
  // 立即查询一次
  pollInferenceResult(recordId);
  
  // 设置定时轮询
  state.pollingTimer = window.setInterval(() => {
    // 检查超时
    if (state.pollingStartTime && Date.now() - state.pollingStartTime > POLLING_TIMEOUT) {
      stopPollingInferenceResult();
      createMessage.warning('推理任务超时，请刷新页面重试');
      state.inferenceLoading = false;
      state.statusText = '推理超时';
      return;
    }
    
    pollInferenceResult(recordId);
  }, POLLING_INTERVAL);
};

// 轮询查询推理结果
const pollInferenceResult = async (recordId: number) => {
  try {
    const response = await getInferenceTaskDetail(recordId);
    
    // 处理响应数据：isTransformResponse: true 时，response 直接是任务数据对象
    // 否则 response 可能是 {code: 0, data: {...}, msg: "success"} 格式
    let taskData;
    if (response && typeof response === 'object') {
      if ('code' in response && 'data' in response) {
        // 响应是包装格式 {code: 0, data: {...}, msg: "success"}
        if (response.code === 0) {
          taskData = response.data;
        } else {
          console.error('查询推理结果失败:', response.msg || '未知错误');
          return;
        }
      } else if ('status' in response) {
        // 响应直接是任务数据对象 {status: "COMPLETED", ...}
        taskData = response;
      } else {
        console.error('无法解析响应数据格式:', response);
        return;
      }
    } else {
      console.error('响应数据格式错误:', response);
      return;
    }
    
    if (!taskData) {
      console.error('无法获取任务数据');
      return;
    }
    
    const status = taskData.status;
    
    // 确保状态匹配（不区分大小写）
    const normalizedStatus = status?.toUpperCase();
    
    if (normalizedStatus === 'COMPLETED') {
      // 推理完成，立即停止轮询
      stopPollingInferenceResult();
      state.inferenceLoading = false;
      state.detectionStatus = 'completed';
      state.statusText = '推理完成';
      
      // 获取结果路径并显示
      const outputPath = taskData.output_path;
      if (outputPath) {
        state.detectionResult = outputPath;
        createMessage.success('视频推理完成');
        
        // 自动播放结果视频
        nextTick(() => {
          if (resultVideoRef.value) {
            resultVideoRef.value.play().catch(err => {
              console.error('结果视频自动播放失败:', err);
            });
          }
        });
      } else {
        // 状态是完成但没有输出路径
        console.warn('推理任务已完成但未找到输出路径');
        createMessage.warning('推理任务已完成，但未找到输出路径');
      }
    } else if (normalizedStatus === 'FAILED') {
      // 推理失败
      stopPollingInferenceResult();
      state.inferenceLoading = false;
      state.detectionStatus = 'failed';
      state.statusText = '推理失败';
      const errorMsg = taskData.error_message || '推理任务失败';
      createMessage.error(errorMsg);
    } else if (normalizedStatus === 'PROCESSING' || normalizedStatus === 'PENDING') {
      // 仍在处理中，继续轮询
      state.statusText = `推理处理中... (已处理 ${taskData.processed_frames || 0} 帧)`;
    }
  } catch (error: any) {
    console.error('查询推理结果失败:', error);
    // 查询失败不停止轮询，继续尝试
  }
};

// 停止轮询
const stopPollingInferenceResult = () => {
  if (state.pollingTimer !== null) {
    clearInterval(state.pollingTimer);
    state.pollingTimer = null;
  }
  state.currentInferenceRecordId = null;
  state.pollingStartTime = null;
};

// 清理视频URL
const cleanupVideoUrl = () => {
  if (state.uploadedVideoUrl) {
    URL.revokeObjectURL(state.uploadedVideoUrl);
    state.uploadedVideoUrl = null;
  }
};

// 加载历史推理记录
const loadInferenceHistory = async () => {
  state.historyLoading = true;
  try {
    const response = await getInferenceTasks({
      pageNo: 1,
      pageSize: 50
    });
    if (response.code === 0) {
      state.inferenceHistory = response.data || [];
    }
  } catch (error: any) {
    console.error('加载历史推理记录失败:', error);
    createMessage.error('加载历史推理记录失败');
  } finally {
    state.historyLoading = false;
  }
};

// 格式化历史记录标签
const formatHistoryRecordLabel = (record: InferenceHistoryRecord): string => {
  const date = new Date(record.start_time);
  const dateStr = date.toLocaleString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  });
  const statusMap: Record<string, string> = {
    'COMPLETED': '已完成',
    'PROCESSING': '处理中',
    'FAILED': '失败'
  };
  const status = statusMap[record.status] || record.status;
  return `${dateStr} - ${status}`;
};

// 处理历史记录选择
const handleHistoryRecordChange = async () => {
  if (!state.selectedHistoryRecordId) {
    // 清空选择时，清理状态
    state.detectionResult = null;
    state.detectionCount = 0;
    state.averageConfidence = 0;
    state.historyInputSource = null;
    return;
  }

  const recordId = parseInt(state.selectedHistoryRecordId, 10);
  if (isNaN(recordId)) {
    return;
  }

  try {
    // 停止当前的轮询
    stopPollingInferenceResult();
    
    // 清理之前的状态
    cleanupVideoUrl();
    state.uploadedImage = null;
    state.uploadedImageFile = null;
    state.uploadedVideoFile = null;
    state.uploadedVideoUrl = null;
    state.historyInputSource = null;
    state.detectionResult = null;
    state.detectionCount = 0;
    state.averageConfidence = 0;
    state.inferenceLoading = false;
    
    // 获取推理任务详情
    const response = await getInferenceTaskDetail(recordId);
    
    // 处理响应数据
    let taskData;
    if (response && typeof response === 'object') {
      if ('code' in response && 'data' in response) {
        if (response.code === 0) {
          taskData = response.data;
        } else {
          createMessage.error(response.msg || '获取历史记录详情失败');
          return;
        }
      } else if ('id' in response) {
        taskData = response;
      } else {
        createMessage.error('无法解析响应数据格式');
        return;
      }
    } else {
      createMessage.error('响应数据格式错误');
      return;
    }

    if (!taskData) {
      createMessage.error('无法获取任务数据');
      return;
    }

    // 还原模型选择
    if (taskData.model_id) {
      // 检查是否是默认模型（model_id 为 null 或 0 表示默认模型）
      // 这里需要根据实际情况判断，如果 model_id 存在且大于0，则使用该模型
      const modelExists = state.models.find(m => m.id === taskData.model_id);
      if (modelExists) {
        state.selectedModelId = taskData.model_id;
      } else {
        // 如果模型不存在，可能是默认模型，保持当前选择或设置为默认
        state.selectedModelId = 'yolov11';
      }
    } else {
      // model_id 为 null，使用默认模型
      state.selectedModelId = 'yolov11';
    }

    // 根据 inference_type 和 input_source 还原输入源
    const inferenceType = taskData.inference_type || '';
    const inputSource = taskData.input_source || '';
    
    // 保存历史记录的 input_source，用于后续推理
    if (inputSource) {
      state.historyInputSource = inputSource;
    }
    
    if (inferenceType === 'image') {
      // 图片
      state.activeSource = 'image';
      // 如果 input_source 是 URL，可以直接使用
      if (inputSource && (inputSource.startsWith('http://') || inputSource.startsWith('https://') || inputSource.startsWith('/'))) {
        state.uploadedImage = getMediaUrl(inputSource);
      }
    } else if (inferenceType === 'video') {
      // 视频
      state.activeSource = 'video';
      // 如果 input_source 是 URL，可以直接使用
      if (inputSource && (inputSource.startsWith('http://') || inputSource.startsWith('https://') || inputSource.startsWith('/'))) {
        state.uploadedVideoUrl = getMediaUrl(inputSource);
      }
    } else if (inputSource) {
      // 如果没有 inference_type，尝试根据 input_source 推断
      const lowerSource = inputSource.toLowerCase();
      if (lowerSource.match(/\.(jpg|jpeg|png|gif|bmp|webp)$/)) {
        state.activeSource = 'image';
        if (inputSource.startsWith('http://') || inputSource.startsWith('https://') || inputSource.startsWith('/')) {
          state.uploadedImage = getMediaUrl(inputSource);
        }
      } else if (lowerSource.match(/\.(mp4|avi|mov|mkv|webm|flv)$/)) {
        state.activeSource = 'video';
        if (inputSource.startsWith('http://') || inputSource.startsWith('https://') || inputSource.startsWith('/')) {
          state.uploadedVideoUrl = getMediaUrl(inputSource);
        }
      }
    }

    // 还原检测结果
    if (taskData.output_path) {
      state.detectionResult = getMediaUrl(taskData.output_path);
    } else if (taskData.stream_output_url) {
      state.detectionResult = taskData.stream_output_url;
    }

    // 还原状态信息
    if (taskData.status === 'COMPLETED') {
      state.detectionStatus = 'completed';
      state.statusText = '推理完成';
    } else if (taskData.status === 'FAILED') {
      state.detectionStatus = 'failed';
      state.statusText = '推理失败';
    } else if (taskData.status === 'PROCESSING') {
      state.detectionStatus = 'running';
      state.statusText = '推理处理中';
    } else {
      state.detectionStatus = 'idle';
      state.statusText = '已加载历史记录';
    }

    createMessage.success('历史记录已还原');
  } catch (error: any) {
    console.error('还原历史记录失败:', error);
    createMessage.error(error.message || '还原历史记录失败');
    // 还原失败时，清空选择
    state.selectedHistoryRecordId = '';
  }
};

// 初始化
onMounted(() => {
  loadDetectionParams();
  loadModels();
  loadInferenceHistory();
  
  // 如果是图片推理，加载部署服务列表
  if (state.activeSource === 'image') {
    loadDeployServices();
  }
});

// 组件卸载时清理
onUnmounted(() => {
  stopPollingInferenceResult();
  cleanupVideoUrl();
});
</script>

<style scoped lang="less">
// 变量定义 - 专业简洁配色方案
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
@sidebar-width: 320px;
@header-height: 60px;
@panel-transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
@shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
@shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
@shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
@shadow-xl: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}

body {
  background-color: #f5f5f5;
  color: #333;
  overflow: hidden;
}

.model-workbench {
  display: flex;
  flex-direction: column;
  height: 100vh;
  width: 100%;
  overflow: hidden;
  margin: 0;
  padding: 0;
}

/* 主内容区 */
.main-content {
  display: flex;
  flex: 1;
  overflow: hidden;
  position: relative;
  min-width: 0; /* 防止 flex 子元素溢出 */
  height: 100%;
  margin: 0;
  padding: 0;
}

/* 左侧配置面板 */
.left-panel {
  width: @sidebar-width;
  min-width: @sidebar-width;
  max-width: @sidebar-width;
  display: flex;
  flex-direction: column;
  background: #ffffff;
  border-right: none;
  overflow: hidden;
  transition: @panel-transition;
  flex-shrink: 0;
  height: 100%;
  padding: 0;
  position: relative;
  
  &::after {
    content: '';
    position: absolute;
    right: 0;
    top: 0;
    bottom: 0;
    width: 1px;
    background: linear-gradient(to bottom, 
      rgba(0, 0, 0, 0) 0%,
      rgba(0, 0, 0, 0.2) 20%,
      rgba(0, 0, 0, 0.3) 50%,
      rgba(0, 0, 0, 0.2) 80%,
      rgba(0, 0, 0, 0) 100%
    );
    box-shadow: 2px 0 8px rgba(0, 0, 0, 0.1), 
                -2px 0 8px rgba(0, 0, 0, 0.05);
  }

  &.collapsed {
    width: 0;
    min-width: 0;
    max-width: 0;
    overflow: hidden;
    border-right: none;
  }

  .config-section {
    padding: 20px;
    border-bottom: none;
    background: transparent;
    margin: 0;
    border-radius: 0;
    transition: @panel-transition;
    flex-shrink: 1;
    overflow: hidden;
    display: flex;
    flex-direction: column;
    min-height: 0;

    &:not(:last-child) {
      border-bottom: none;
    }

      .section-title {
      display: flex;
      align-items: center;
      gap: 12px;
      margin-bottom: 18px;
      font-weight: 600;
      font-size: 16px;
      color: @light-text;

      .icon {
        font-size: 18px;
        color: @primary-color;
      }

      .tip-icon {
        cursor: help;
        transition: color 0.3s ease;
        color: @text-secondary;
        font-size: 14px;
        margin-left: 4px;

        &:hover {
          color: @primary-color;
        }
      }

      .refresh-icon {
        margin-left: auto;
        cursor: pointer;
        transition: transform 0.3s ease;
        color: @text-secondary;
        font-size: 16px;

        &:hover {
          color: @primary-color;
          transform: rotate(180deg);
        }

        &.spinning {
          animation: spin 1s linear infinite;
        }
      }
    }

    .config-options {
      display: flex;
      flex-direction: column;
      gap: 15px;
      overflow: hidden;
      flex: 1;
      min-height: 0;

      .source-content {
        display: flex;
        flex-direction: column;
        gap: 12px;

        .file-upload-wrapper {
          position: relative;
          width: 100%;

          .file-input {
            position: absolute;
            width: 0;
            height: 0;
            opacity: 0;
            overflow: hidden;
            z-index: -1;
          }

          .file-upload-label {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
            padding: 12px 20px;
            border: 1px solid @border-color;
            border-radius: 6px;
            background: #FFFFFF;
            cursor: pointer;
            transition: all 0.2s ease;
            font-size: 14px;
            color: @light-text;
            font-weight: 500;
            min-height: 44px;
            box-shadow: @shadow-sm;

            .icon {
              font-size: 16px;
              color: @text-secondary;
              flex-shrink: 0;
            }

            span {
              text-align: center;
              overflow: hidden;
              text-overflow: ellipsis;
              white-space: nowrap;
            }

            &:hover {
              border-color: @primary-color;
              background: @light-bg;
              box-shadow: @shadow-md;
            }

            &:active {
              box-shadow: @shadow-sm;
            }
          }
        }

        .upload-preview {
          margin-top: 10px;
          text-align: center;
          width: 100%;
          max-width: 100%;
          overflow: hidden;
          display: flex;
          align-items: center;
          justify-content: center;

          .preview-image {
            max-width: 100%;
            max-height: 150px;
            width: auto;
            height: auto;
            object-fit: contain;
            border-radius: 6px;
            border: 1px solid @border-color;
            transition: @panel-transition;
            box-shadow: @shadow-sm;
            display: block;

            &:hover {
              border-color: @border-hover;
              box-shadow: @shadow-md;
            }
          }

          .file-info {
            display: flex;
            flex-direction: column;
            gap: 8px;
            padding: 14px;
            background: @light-bg;
            border-radius: 6px;
            font-size: 13px;
            color: @light-text;
            border: 1px solid @border-color;
            transition: @panel-transition;

            .file-name {
              font-weight: 500;
              color: @accent-color;
            }

            .file-size {
              color: @text-secondary;
            }

            &:hover {
              border-color: @border-hover;
              background: #FFFFFF;
            }
          }
        }
      }

      .option-group {
        display: flex;
        flex-direction: column;
        gap: 10px;

        .option-title {
          font-weight: 500;
          font-size: 14px;
          color: @light-text;
        }
      }

      .button-group {
        display: flex;
        flex-direction: column;
        gap: 12px;

        .btn {
          padding: 11px 20px;
          border: 1px solid @border-color;
          border-radius: 6px;
          background: #FFFFFF;
          cursor: pointer;
          transition: all 0.2s ease;
          font-size: 14px;
          width: 100%;
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 8px;
          font-weight: 500;
          position: relative;
          box-shadow: @shadow-sm;

          .icon {
            font-size: 16px;
          }

          &-primary {
            background: @primary-color;
            color: #FFFFFF;
            border-color: @primary-color;

            &:hover {
              background: @primary-color;
              border-color: @primary-color;
              box-shadow: @shadow-sm;
            }

            &:active {
              box-shadow: @shadow-sm;
            }
          }

          &-outline {
            background: #FFFFFF;
            color: @accent-color;
            border-color: @accent-color;

            &:hover {
              background: @light-bg;
              border-color: @border-hover;
              box-shadow: @shadow-md;
            }
          }

          &-success {
            background: @success-color;
            color: #FFFFFF;
            border-color: @success-color;

            &:hover {
              background: darken(@success-color, 5%);
              border-color: darken(@success-color, 5%);
              box-shadow: @shadow-md;
              transform: translateY(-1px);
            }

            &:active {
              transform: translateY(0);
              box-shadow: @shadow-sm;
            }
          }

          &-warning {
            background: @warning-color;
            color: #212529;
            border-color: @warning-color;

            &:hover {
              background: darken(@warning-color, 5%);
              border-color: darken(@warning-color, 5%);
              box-shadow: @shadow-md;
              transform: translateY(-1px);
            }

            &:active {
              transform: translateY(0);
              box-shadow: @shadow-sm;
            }
          }

          &-white {
            background: #FFFFFF;
            color: @light-text;
            border-color: @border-color;

            &:hover {
              background: #FFFFFF;
              border-color: @border-color;
              box-shadow: @shadow-sm;
            }

            &:active {
              box-shadow: @shadow-sm;
            }
          }

          &:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            background: @light-bg;
            color: @text-muted;
            border-color: @border-color;

            &:hover {
              transform: none;
              box-shadow: @shadow-sm;
            }
          }
        }
      }

      .input-group {
        display: flex;
        flex-direction: column;
        gap: 5px;

        .input-label {
          font-size: 13px;
          color: @gray-color;
        }

        .input-field {
          padding: 11px 14px;
          border: 1px solid @border-color;
          border-radius: 6px;
          width: 100%;
          background: #FFFFFF;
          transition: @panel-transition;
          font-size: 14px;
          color: @light-text;
          box-shadow: @shadow-sm;

          &:focus {
            outline: none;
            border-color: @primary-color;
            box-shadow: 0 0 0 3px rgba(44, 62, 80, 0.1), @shadow-sm;
          }

          &:hover {
            border-color: @border-hover;
          }
        }
      }

      .checkbox-group {
        display: flex;
        align-items: center;
        gap: 8px;

        input[type="checkbox"] {
          width: 16px;
          height: 16px;
        }

        label {
          font-size: 14px;
          color: @light-text;
        }
      }

      .select-field {
        padding: 11px 14px;
        border: 1px solid @border-color;
        border-radius: 6px;
        background: #FFFFFF;
        width: 100%;
        transition: @panel-transition;
        font-size: 14px;
        color: @light-text;
        box-shadow: @shadow-sm;
        cursor: pointer;

        &:focus {
          outline: none;
          border-color: @primary-color;
          box-shadow: 0 0 0 3px rgba(44, 62, 80, 0.1), @shadow-sm;
        }

        &:hover {
          border-color: @border-hover;
        }
      }

    }
  }
}

/* 左侧面板切换按钮 */
.panel-toggle {
  position: absolute;
  top: 50%;
  left: @sidebar-width;
  transform: translateY(-50%) translateX(-50%);
  background: #FFFFFF;
  color: @accent-color;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  z-index: 100;
  transition: @panel-transition;
  border: 1px solid @border-color;
  box-shadow: @shadow-md;

  &:hover {
    transform: translateY(-50%) translateX(-50%) scale(1.05);
    background: @light-bg;
    border-color: @border-hover;
    box-shadow: @shadow-lg;
  }

  &.collapsed {
    left: 0;
  }

  .icon {
    font-size: 16px;
    font-weight: 500;
  }
}

/* 右侧视频显示区域 */
.video-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: @light-bg;
  position: relative;
  overflow: hidden;
  padding: 0;
  transition: @panel-transition;
  min-width: 0; /* 防止 flex 子元素溢出 */
  height: 100%;

  .video-container {
    display: flex;
    flex-direction: column;
    gap: 0;
    height: 100%;
    width: 100%;
    padding: 12px;
    overflow: hidden;
    box-sizing: border-box;
    max-width: 100%;
    max-height: 100%;

    .video-wrapper {
      display: flex;
      flex-direction: column;
      border: none;
      border-radius: 12px;
      overflow: hidden;
      position: relative;
      flex: 1;
      min-height: 0;
      background: white;
      transition: @panel-transition;
      box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08), 
                  0 2px 8px rgba(0, 0, 0, 0.05);
      margin: 0;
      max-width: 100%;
      max-height: 100%;
      box-sizing: border-box;
      
      &:hover {
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12), 
                    0 4px 12px rgba(0, 0, 0, 0.08);
      }

      .video-title {
        padding: 16px 20px;
        background: @light-bg;
        border-bottom: 1px solid @border-color;
        font-weight: 600;
        display: flex;
        justify-content: space-between;
        align-items: center;
        color: @light-text;
        font-size: 16px;
      }

      .video-content {
        flex: 1;
        display: flex;
        align-items: center;
        justify-content: center;
        background: #ffffff;
        color: @light-text;
        font-size: 16px;
        position: relative;
        overflow: hidden;
        min-height: 0;
        max-width: 100%;
        max-height: 100%;
        width: 100%;
        height: 100%;

        .image-preview, .detection-result, .video-preview {
          width: 100%;
          height: 100%;
          max-width: 100%;
          max-height: 100%;
          display: flex;
          align-items: center;
          justify-content: center;
          position: relative;
          overflow: hidden;
          box-sizing: border-box;

          .preview-image {
            max-width: 100%;
            max-height: 100%;
            width: auto;
            height: auto;
            object-fit: contain;
            display: block;
            box-sizing: border-box;
          }

          .preview-video {
            max-width: 100%;
            max-height: 100%;
            width: 100%;
            height: 100%;
            object-fit: contain;
            cursor: pointer;
          }

          .video-error-info {
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: rgba(220, 53, 69, 0.95);
            color: #FFFFFF;
            padding: 20px 24px;
            border-radius: 8px;
            max-width: 80%;
            text-align: center;
            z-index: 10;
            box-shadow: @shadow-lg;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.2);

            .error-title {
              font-size: 16px;
              font-weight: 600;
              margin-bottom: 12px;
            }

            .error-message {
              font-size: 14px;
              margin-bottom: 12px;
              line-height: 1.5;
            }

            .error-details {
              font-size: 12px;
              opacity: 0.9;
              margin-top: 12px;
              padding-top: 12px;
              border-top: 1px solid rgba(255, 255, 255, 0.2);

              div {
                margin: 4px 0;
              }
            }
          }
        }

        .detection-result {
          position: relative;

          .detection-overlay {
            position: absolute;
            top: 16px;
            right: 16px;
            background: rgba(44, 62, 80, 0.9);
            color: #FFFFFF;
            padding: 12px 18px;
            border-radius: 6px;
            font-size: 14px;
            font-weight: bold;
            backdrop-filter: blur(10px);
            box-shadow: @shadow-lg;
            border: 1px solid rgba(255, 255, 255, 0.1);
            pointer-events: none;
            z-index: 1;

            .detection-info {
              display: flex;
              flex-direction: column;
              gap: 6px;
            }
          }
        }

        .video-placeholder {
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 20px;
          color: @text-secondary;

          .icon {
            font-size: 64px;
            color: @gray-color;
            opacity: 0.5;
          }

          span {
            font-size: 16px;
            color: @text-secondary;
            font-weight: 500;
          }
        }
      }
    }

    .dual-video {
      display: flex;
      gap: 16px;
      height: 100%;
      width: 100%;
      min-width: 0;
      padding: 12px;
      overflow: hidden;
      box-sizing: border-box;
      max-width: 100%;
      max-height: 100%;

      .video-wrapper {
        flex: 1;
        min-width: 0;
        min-height: 550px;
        height: 100%;
        border-right: none;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08), 
                    0 2px 8px rgba(0, 0, 0, 0.05);
        margin: 0;

        &:hover {
          box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12), 
                      0 4px 12px rgba(0, 0, 0, 0.08);
        }
      }
    }

    .single-video {
      width: 100%;
      height: 100%;
      padding: 12px;
      display: flex;
      flex-direction: column;
      overflow: hidden;
      box-sizing: border-box;
      max-width: 100%;
      max-height: 100%;
      
      .video-wrapper {
        flex: 1;
        min-height: 0;
        overflow: hidden;
      }
    }
  }
}



/* 响应式调整 */
@media (max-width: 1200px) {
  .left-panel {
    width: 280px;
  }

  .panel-toggle {
    left: 280px;
  }
}

@media (max-width: 992px) {
  .main-content {
    flex-direction: column;
  }

  .left-panel {
    width: 100%;
    height: auto;
    border-right: none;
    border-bottom: 1px solid @border-color;
  }

  .video-area {
    height: 60vh;
  }

  .panel-toggle {
    display: none;
  }
}

@media (max-width: 768px) {
  .dual-video {
    flex-direction: column;
  }
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}
</style>
