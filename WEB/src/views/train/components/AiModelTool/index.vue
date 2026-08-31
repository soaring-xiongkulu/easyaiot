<template>
  <div class="model-workbench">
    <!-- 主内容区 -->
    <div class="main-content">
      <!-- 左侧配置面板 -->
      <div class="left-panel" :class="{ collapsed: state.leftPanelCollapsed }">
        <div class="left-panel-body">
          <!-- 分析类型 -->
          <div class="config-section">
            <div class="section-title">
              <ExperimentOutlined class="icon" />
              <span>分析类型</span>
            </div>
            <div class="config-options">
              <div class="input-group">
                <select class="select-field" v-model="state.analysisType" @change="handleAnalysisTypeChange">
                  <option v-for="option in analysisTypeOptions" :key="option.value" :value="option.value">
                    {{ option.label }}
                  </option>
                </select>
              </div>
            </div>
          </div>

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
                  <template v-if="isPoseMode">
                    <option value="yolo26n-pose">Yolo26n-Pose（姿态）</option>
                    <option v-for="model in poseCustomModels" :key="model.id" :value="model.id">
                      {{ model.name }} ({{ formatVersion(model.version) }})
                    </option>
                  </template>
                  <template v-else>
                    <option value="yolov8">Yolov8模型</option>
                    <option value="yolov11">Yolov11模型</option>
                    <option value="yolov26">Yolov26模型</option>
                    <option v-for="model in state.models" :key="model.id" :value="model.id">
                      {{ model.name }} ({{ formatVersion(model.version) }})
                    </option>
                  </template>
                </select>
              </div>
            </div>
          </div>

          <!-- 检测类别 -->
          <div class="config-section" v-if="isCustomModelSelected && !isPoseMode">
            <div class="section-title">
              <AppstoreOutlined class="icon" />
              <span>检测类别</span>
              <BasicHelp class="section-help" placement="top" text="目标检测模型可识别的类别；未选择时默认检测全部类别" />
            </div>
            <div class="config-options">
              <div v-if="state.classesLoading" class="class-tags-status">正在加载检测类别...</div>
              <div v-else-if="state.availableClassNames.length === 0" class="class-tags-status class-tags-status--warn">
                未能读取检测类别
              </div>
              <ApiSelect
                v-else
                v-model:value="state.selectedClassNames"
                mode="multiple"
                allow-clear
                placeholder="默认检测全部类别"
                :max-tag-count="4"
                class="class-select"
                :options="classNameOptions"
                :immediate="false"
              />
            </div>
          </div>

          <!-- 模型服务 + 大模型 -->
          <div class="config-section" v-if="state.activeSource === 'image' && !isPoseMode">
            <div class="config-row config-row--2">
              <div class="config-col">
                <div class="section-title">
                  <SettingOutlined class="icon" />
                  <span>模型服务</span>
                  <ReloadOutlined class="icon refresh-icon" @click="loadDeployServices" :class="{ spinning: state.deployServicesLoading }" title="刷新服务列表" />
                </div>
                <div class="config-options">
                  <ApiSelect
                    v-model:value="state.selectedDeployServiceId"
                    allow-clear
                    placeholder="请选择模型服务"
                    class="class-select"
                    :options="deployServiceOptions"
                    :immediate="false"
                    :loading="state.deployServicesLoading"
                    @change="handleDeployServiceChange"
                  />
                </div>
              </div>
              <div class="config-col">
                <div class="section-title">
                  <SettingOutlined class="icon" />
                  <span>大模型</span>
                  <ReloadOutlined class="icon refresh-icon" @click="loadLLMs" :class="{ spinning: state.llmsLoading }" title="刷新当前启用大模型" />
                </div>
                <div class="config-options">
                  <ApiSelect
                    v-model:value="state.selectedLLMId"
                    allow-clear
                    placeholder="使用当前启用大模型"
                    class="class-select"
                    :options="llmOptions"
                    :immediate="false"
                    :loading="state.llmsLoading"
                    @change="handleLLMChange"
                  />
                </div>
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

          <!-- 检测置信度 -->
          <div class="config-section">
            <div class="section-title">
              <ExperimentOutlined class="icon" />
              <span>{{ isPoseMode ? '姿态置信度' : '检测置信度' }}</span>
            </div>
            <div class="config-options">
              <InputNumber
                v-model:value="state.detectConf"
                class="detect-conf-input"
                :min="0.1"
                :max="0.95"
                :step="0.05"
              />
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

              <div class="source-content" v-if="state.activeSource === 'image'">
                <div class="file-upload-wrapper">
                  <input type="file" class="file-input" accept="image/*" @change="handleImageUpload" ref="imageInput" id="image-upload-input">
                  <label for="image-upload-input" class="file-upload-label">
                    <PictureOutlined class="icon" />
                    <span>{{ state.uploadedImageFile ? state.uploadedImageFile.name : '选择图片文件' }}</span>
                  </label>
                </div>
              </div>
              <div class="source-content" v-else-if="state.activeSource === 'video'">
                <div class="file-upload-wrapper">
                  <input type="file" class="file-input" accept="video/*" @change="handleVideoUpload" ref="videoInput" id="video-upload-input">
                  <label for="video-upload-input" class="file-upload-label">
                    <VideoCameraOutlined class="icon" />
                    <span>{{ state.uploadedVideoFile ? state.uploadedVideoFile.name : '选择视频文件' }}</span>
                  </label>
                </div>
              </div>
              <div class="source-content" v-else-if="state.activeSource === 'camera'">
                <div class="camera-select-combo">
                  <select class="select-field camera-select-field" v-model="state.selectedCameraId" @change="handleCameraChange">
                    <option value="">请选择在线摄像头</option>
                    <option v-for="cam in cameraOptions" :key="cam.id" :value="cam.id">
                      {{ cam.name || cam.id }}{{ getCameraOnlineLabel(cam) }}
                    </option>
                  </select>
                  <button type="button" class="camera-refresh-btn" :disabled="state.camerasLoading" title="刷新摄像头列表" @click="refreshCameras">
                    <SyncOutlined :spin="state.camerasLoading" />
                  </button>
                </div>
                <div v-if="state.camerasLoading" class="class-tags-status">正在加载摄像头...</div>
                <div v-else-if="cameraOptions.length === 0" class="class-tags-status class-tags-status--warn">暂无可用摄像头</div>
              </div>
            </div>
          </div>
        </div>

        <!-- 控制操作 -->
        <div class="config-section config-section--footer">
          <div class="section-title">
            <ControlOutlined class="icon" />
            <span>控制操作</span>
          </div>
          <div class="config-options">
            <div class="button-group">
              <button
                v-if="state.activeSource !== 'camera' || !state.cameraStreamActive"
                class="btn btn-primary"
                @click="startDetection"
                :disabled="getStartButtonDisabled()"
              >
                <PlayCircleOutlined class="icon" />
                <span v-if="state.inferenceLoading">推理中...</span>
                <span v-else-if="state.activeSource === 'camera'">开始实时推理</span>
                <span v-else-if="isPoseMode">开始姿态分析</span>
                <span v-else>开始检测</span>
              </button>
              <button v-if="state.activeSource === 'camera' && state.cameraStreamActive" class="btn btn-white" @click="stopCameraInference()">
                <CloseOutlined class="icon" />
                <span>停止推理</span>
              </button>
              <button class="btn btn-white" @click="state.showOriginal = !state.showOriginal">
                <EyeOutlined v-if="!state.showOriginal" class="icon" />
                <CloseOutlined v-else class="icon" />
                <span>{{ state.showOriginal ? '关闭对照' : '显示对照' }}</span>
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
                  <span>{{ resultPanelTitle }}</span>
                </div>
                <div class="video-content video-content-scrollable">
                  <div v-if="state.llmTextResult" class="llm-text-result">
                    <div class="llm-result-content" v-html="formatLLMResult(state.llmTextResult)"></div>
                  </div>
                  <div v-else-if="state.selectedLLMId && state.activeSource === 'image'" class="llm-text-result">
                    <div class="llm-result-placeholder">
                      <ExperimentOutlined class="icon" />
                      <p>已选择大模型，请上传图片并点击"开始检测"进行推理</p>
                    </div>
                  </div>
                  <div v-else-if="state.detectionResult" class="detection-result">
                    <img :src="state.detectionResult" alt="检测结果" class="preview-image" @error="handleImageError">
                    <div class="detection-overlay">
                      <div class="detection-info">
                        <div class="detection-count">{{ resultCountLabel }}</div>
                        <div v-if="!isPoseMode" class="confidence">平均置信度: {{ state.averageConfidence }}%</div>
                      </div>
                    </div>
                  </div>
                  <div v-else class="video-placeholder">
                    <ExperimentOutlined class="icon" />
                    <span>{{ isPoseMode ? '姿态结果将显示在这里' : '检测结果将显示在这里' }}</span>
                  </div>
                </div>
              </div>
            </div>
            <div v-else class="single-video">
              <div class="video-wrapper">
                <div class="video-title">
                  <span>{{ resultPanelTitle }}</span>
                </div>
                <div class="video-content video-content-scrollable">
                  <div v-if="state.llmTextResult" class="llm-text-result">
                    <div class="llm-result-content" v-html="formatLLMResult(state.llmTextResult)"></div>
                  </div>
                  <div v-else-if="state.selectedLLMId && state.activeSource === 'image'" class="llm-text-result">
                    <div class="llm-result-placeholder">
                      <ExperimentOutlined class="icon" />
                      <p>已选择大模型，请上传图片并点击"开始检测"进行推理</p>
                    </div>
                  </div>
                  <div v-else-if="state.detectionResult" class="detection-result">
                    <img :src="state.detectionResult" alt="检测结果" class="preview-image" @error="handleImageError">
                    <div class="detection-overlay">
                      <div class="detection-info">
                        <div class="detection-count">{{ resultCountLabel }}</div>
                        <div v-if="!isPoseMode" class="confidence">平均置信度: {{ state.averageConfidence }}%</div>
                      </div>
                    </div>
                  </div>
                  <div v-else class="video-placeholder">
                    <ExperimentOutlined class="icon" />
                    <span>{{ isPoseMode ? '姿态结果将显示在这里' : '检测结果将显示在这里' }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- 在线摄像头实时推理 -->
          <div v-else-if="state.activeSource === 'camera'">
            <div v-if="state.showOriginal" class="dual-video">
              <div class="video-wrapper">
                <div class="video-title">
                  <span>原始画面</span>
                </div>
                <div class="video-content stream-player-content">
                  <Jessibuca
                    v-if="state.cameraPreviewUrl"
                    :key="'camera-preview-' + state.selectedCameraId"
                    :playUrl="state.cameraPreviewUrl"
                    :hasAudio="false"
                  />
                  <div v-else class="video-placeholder">
                    <VideoCameraOutlined class="icon" />
                    <span>{{ state.selectedCameraId ? '正在加载预览...' : '请选择摄像头' }}</span>
                  </div>
                </div>
              </div>
              <div class="video-wrapper">
                <div class="video-title">
                  <span>推理结果</span>
                  <span v-if="state.cameraStreamActive" class="stream-live-badge">LIVE</span>
                </div>
                <div class="video-content stream-player-content">
                  <Jessibuca
                    v-if="state.cameraResultUrl"
                    :key="'camera-result-' + state.selectedCameraId + '-' + state.selectedModelId"
                    :playUrl="state.cameraResultUrl"
                    :hasAudio="false"
                  />
                  <div v-else-if="state.inferenceLoading" class="video-placeholder">
                    <SearchOutlined class="icon" />
                    <span>正在启动实时推理...</span>
                  </div>
                  <div v-else class="video-placeholder">
                    <SearchOutlined class="icon" />
                    <span>{{ isPoseMode ? '点击「开始实时推理」查看姿态结果' : '点击「开始实时推理」查看检测结果' }}</span>
                  </div>
                </div>
              </div>
            </div>
            <div v-else class="single-video">
              <div class="video-wrapper">
                <div class="video-title">
                  <span>推理结果</span>
                  <span v-if="state.cameraStreamActive" class="stream-live-badge">LIVE</span>
                </div>
                <div class="video-content stream-player-content">
                  <Jessibuca
                    v-if="state.cameraResultUrl"
                    :key="'camera-result-single-' + state.selectedCameraId + '-' + state.selectedModelId"
                    :playUrl="state.cameraResultUrl"
                    :hasAudio="false"
                  />
                  <div v-else-if="state.inferenceLoading" class="video-placeholder">
                    <SearchOutlined class="icon" />
                    <span>正在启动实时推理...</span>
                  </div>
                  <div v-else class="video-placeholder">
                    <SearchOutlined class="icon" />
                    <span>{{ isPoseMode ? '点击「开始实时推理」查看姿态结果' : '点击「开始实时推理」查看检测结果' }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- 视频模式 -->
          <div v-else-if="state.activeSource === 'video'">
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
                  <span>{{ resultPanelTitle }}</span>
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
                    <span>{{ isPoseMode ? '姿态结果将显示在这里' : '检测结果将显示在这里' }}</span>
                  </div>
                </div>
              </div>
            </div>
            <div v-else class="single-video">
              <div class="video-wrapper">
                <div class="video-title">
                  <span>{{ resultPanelTitle }}</span>
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
                    <span>{{ isPoseMode ? '姿态结果将显示在这里' : '检测结果将显示在这里' }}</span>
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
import { computed, reactive, ref, onMounted, onUnmounted, nextTick, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import { getModelPage, runInference, runClusterInference, uploadInputFile, getInferenceTaskDetail, getInferenceTasks, getDeployServicePage, getModelClasses, parseModelClassPayload, stopRtspInference, posePredict, posePredictVideo, poseVideoProgress, poseOutputVideo, poseRtspStart, poseRtspStop } from "@/api/device/model";
import { getLLMList, visionInference, type LLMModel } from "@/api/device/llm";
import { getDeviceList, startStreamForwarding, getStreamStatus, type DeviceInfo } from '@/api/device/camera';
import { ensureDeviceStreamForwardTask } from '@/api/device/stream_forward';
import { rewriteStreamHostToPageHost, convertRtmpToHttp, resolveMonitorPlayUrl, probeStreamPlayable } from '@/views/camera/utils/devicePlay';
import { isGb28181Device } from '@/views/camera/utils/deviceLabel';
import { isNvrListRow } from '@/views/camera/utils/deviceLabel';
import Jessibuca from '@/components/Player/module/jessibuca.vue';
import { useMessage } from '@/hooks/web/useMessage';
import { ApiSelect } from '@/components/Form';
import { BasicHelp } from '@/components/Basic';
import { InputNumber, Tooltip } from 'ant-design-vue';
import {
  SettingOutlined,
  AppstoreOutlined,
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
  SyncOutlined,
  HistoryOutlined,
  QuestionCircleOutlined
} from '@ant-design/icons-vue';
import { formatModelVersionDisplay } from '../../utils/modelVersionUtils';

const { createMessage } = useMessage();
const formatVersion = formatModelVersionDisplay;

// 接收父组件传递的初始大模型ID
const props = defineProps<{
  initialLLMId?: number | null;
  tabActive?: boolean;
}>();

// 类型定义

interface Model {
  id: number;
  name: string;
  version: string;
  status: number;
  class_names?: string[];
  classNames?: string[];
  selected_class_names?: string[];
  selectedClassNames?: string[];
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
  detectConf: number;
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
  llmTextResult: string | null; // 大模型文本推理结果
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
  llms: LLMModel[]; // 大模型列表
  selectedLLMId: number | null; // 选中的大模型ID
  llmsLoading: boolean; // 大模型加载状态
  availableClassNames: string[];
  selectedClassNames: string[];
  classesLoading: boolean;
  cameras: DeviceInfo[];
  camerasLoading: boolean;
  selectedCameraId: string;
  cameraPreviewUrl: string | null;
  cameraResultUrl: string | null;
  cameraStreamActive: boolean;
  cameraInferenceRecordId: number | null;
  cameraInferenceDeviceId: string;
  analysisType: 'detect' | 'pose';
  posePollTimer: number | null;
  poseJobId: string | null;
}

// 状态管理
const state = reactive<AppState>({
  activeSource: 'image',
  detectConf: 0.5,
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
  llmTextResult: null,
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
  deployServicesLoading: false,
  llms: [],
  selectedLLMId: null,
  llmsLoading: false,
  availableClassNames: [],
  selectedClassNames: [],
  classesLoading: false,
  cameras: [],
  camerasLoading: false,
  selectedCameraId: '',
  cameraPreviewUrl: null,
  cameraResultUrl: null,
  cameraStreamActive: false,
  cameraInferenceRecordId: null,
  cameraInferenceDeviceId: '',
  analysisType: 'detect',
  posePollTimer: null,
  poseJobId: null,
});

// 轮询超时时间（30分钟）
// 视频推理在生产环境可能耗时较长，5分钟容易提前超时
const POLLING_TIMEOUT = 30 * 60 * 1000;
// 轮询间隔（2秒），降低接口压力
const POLLING_INTERVAL = 2000;

const sourceOptions = [
  { value: 'image', label: '图片上传' },
  { value: 'video', label: '视频上传' },
  { value: 'camera', label: '在线摄像头' },
];

const analysisTypeOptions = [
  { value: 'detect', label: '目标检测' },
  { value: 'pose', label: '姿态分析' },
];

const POSE_BUILTIN_MODELS = ['yolo26n-pose'];

const imageInput = ref<HTMLInputElement | null>(null);
const videoInput = ref<HTMLInputElement | null>(null);
const inputVideoRef = ref<HTMLVideoElement | null>(null);
const resultVideoRef = ref<HTMLVideoElement | null>(null);

const selectedSource = computed(() => {
  return sourceOptions.find(option => option.value === state.activeSource);
});

const isCustomModelSelected = computed(() => {
  const modelId = state.selectedModelId;
  if (isPoseMode.value) {
    return modelId !== null && modelId !== '' && !POSE_BUILTIN_MODELS.includes(String(modelId));
  }
  return modelId !== null && modelId !== '' && !['yolov8', 'yolov11', 'yolov26'].includes(String(modelId));
});

const isPoseMode = computed(() => state.analysisType === 'pose');

const poseCustomModels = computed(() =>
  state.models.filter((m) => {
    const name = (m.name || '').toLowerCase();
    return name.includes('pose');
  }),
);

const resultCountLabel = computed(() => {
  if (isPoseMode.value) {
    return `检测到 ${state.detectionCount} 个人体`;
  }
  return `检测到 ${state.detectionCount} 个目标`;
});

const resultPanelTitle = computed(() => (isPoseMode.value ? '姿态结果' : '检测结果'));

const classNameOptions = computed(() =>
  state.availableClassNames.map((name) => ({ label: name, value: name })),
);

const deployServiceOptions = computed(() =>
  state.deployServices.map((service) => ({
    label: `${service.model_name}服务（${formatVersion(service.model_version)}）`,
    value: service.id,
  })),
);

const llmOptions = computed(() =>
  state.llms.map((llm) => ({
    // 单模型管控：列表仅含平台当前启用的唯一大模型
    label: llm.name,
    value: llm.id,
  })),
);

const getCameraRtspUrl = (device: DeviceInfo): string | null => {
  const url = (device.rtsp_direct || device.source || '').trim();
  return url.startsWith('rtsp://') ? url : null;
};

/** 推理下拉可选设备：含直连 RTSP、GB28181、NVR 通道等（后端可通过 device_id 取流） */
const isSelectableInferenceCamera = (device: DeviceInfo): boolean => {
  const id = (device.id || '').trim();
  if (!id) return false;
  return !isNvrListRow(device);
};

const cameraOptions = computed(() =>
  state.cameras
    .filter(isSelectableInferenceCamera)
    .slice()
    .sort((a, b) => String(a.name || a.id).localeCompare(String(b.name || b.id), 'zh-CN')),
);

const resolveHistoryCameraId = (inputSource: string): string | null => {
  const source = (inputSource || '').trim();
  if (!source) return null;
  if (source.startsWith('device:')) {
    return source.slice('device:'.length).trim() || null;
  }
  return null;
};

const matchHistoryCamera = (inputSource: string): DeviceInfo | undefined => {
  const deviceId = resolveHistoryCameraId(inputSource);
  if (deviceId) {
    return state.cameras.find((cam) => cam.id === deviceId);
  }
  return state.cameras.find((cam) => getCameraRtspUrl(cam) === inputSource);
};

const selectedCamera = computed(() =>
  state.cameras.find((cam) => cam.id === state.selectedCameraId) || null,
);

const selectedCameraRtsp = computed(() =>
  selectedCamera.value ? getCameraRtspUrl(selectedCamera.value) : null,
);

const maskRtspUrl = (url: string): string =>
  url.replace(/\/\/([^:@/]+):([^@/]+)@/, '//$1:***@');

const getCameraOnlineLabel = (device: DeviceInfo): string => {
  if (device.connection_status === 'online' || device.channel_online === true) {
    return '（在线）';
  }
  if (device.connection_status === 'offline' || device.channel_online === false) {
    return '（离线）';
  }
  return '';
};

const toStreamPlayUrl = (url: string): string => {
  if (!url) return '';
  let playUrl = url;
  if (url.startsWith('rtmp://')) {
    playUrl = convertRtmpToHttp(url) || url;
  }
  return rewriteStreamHostToPageHost(playUrl);
};

const loadClassesForModel = async (model?: Model | null) => {
  if (!model?.id) {
    state.availableClassNames = [];
    state.selectedClassNames = [];
    state.classesLoading = false;
    return;
  }

  state.classesLoading = true;
  try {
    let { classNames, selectedClassNames } = parseModelClassPayload(model);
    if (classNames.length === 0) {
      const resp = await getModelClasses(model.id);
      const parsed = parseModelClassPayload(resp);
      classNames = parsed.classNames;
      selectedClassNames = parsed.selectedClassNames;
      model.classNames = classNames;
      model.selectedClassNames = selectedClassNames;
    }
    state.availableClassNames = classNames;
    state.selectedClassNames = selectedClassNames.length > 0 ? selectedClassNames : [...classNames];
  } catch (error) {
    console.warn('加载模型标签失败', error);
    state.availableClassNames = [];
    state.selectedClassNames = [];
  } finally {
    state.classesLoading = false;
  }
};

watch(
  () => state.selectedModelId,
  async (modelId) => {
    if (!modelId || ['yolov8', 'yolov11', 'yolov26'].includes(String(modelId))) {
      state.availableClassNames = [];
      state.selectedClassNames = [];
      state.classesLoading = false;
      return;
    }
    const model = state.models.find((item) => String(item.id) === String(modelId));
    await loadClassesForModel(model);
  },
  { immediate: true },
);

watch(
  () => props.tabActive,
  (active) => {
    if (!active && state.cameraStreamActive) {
      void stopCameraInference(false);
      return;
    }
    if (active && state.activeSource === 'camera') {
      refreshCameras();
    }
  },
);

const setActiveSource = (source: string) => {
  state.activeSource = source;
};

// 格式化大模型推理结果，将markdown格式转换为HTML
const formatLLMResult = (text: string | null): string => {
  if (!text) return '';
  
  let formatted = text
    // 先转义HTML特殊字符（但保留我们需要的标记）
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');
  
  // 处理分隔线（必须在其他处理之前）
  formatted = formatted.replace(/^---$/gm, '<div class="result-divider"></div>');
  
  // 处理标题（按从大到小的顺序）
  formatted = formatted.replace(/^####\s+(.+)$/gm, '<h4 class="result-h4">$1</h4>');
  formatted = formatted.replace(/^###\s+(.+)$/gm, '<h3 class="result-h3">$1</h3>');
  formatted = formatted.replace(/^##\s+(.+)$/gm, '<h2 class="result-h2">$1</h2>');
  formatted = formatted.replace(/^#\s+(.+)$/gm, '<h1 class="result-h1">$1</h1>');
  
  // 处理引用块
  formatted = formatted.replace(/^>\s+(.+)$/gm, '<div class="result-quote">$1</div>');
  
  // 处理有序列表（数字开头）
  formatted = formatted.replace(/^(\d+)\.\s+(.+)$/gm, '<div class="result-list-item"><span class="list-number">$1.</span><span class="list-content">$2</span></div>');
  
  // 处理无序列表（- 或 * 开头）
  formatted = formatted.replace(/^[-*]\s+(.+)$/gm, '<div class="result-list-item"><span class="list-bullet">•</span><span class="list-content">$1</span></div>');
  
  // 处理嵌套列表（以空格开头的列表项）
  formatted = formatted.replace(/^(\s{2,})[-*]\s+(.+)$/gm, '<div class="result-list-item nested"><span class="list-bullet">◦</span><span class="list-content">$2</span></div>');
  
  // 处理粗体（**text**）
  formatted = formatted.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
  
  // 处理行内代码（`code`）
  formatted = formatted.replace(/`([^`]+)`/g, '<code>$1</code>');
  
  // 按段落分割并处理
  const lines = formatted.split('\n');
  const paragraphs: string[] = [];
  let currentParagraph: string[] = [];
  
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i].trim();
    
    // 如果是空行，结束当前段落
    if (!line) {
      if (currentParagraph.length > 0) {
        const paraText = currentParagraph.join(' ');
        // 如果段落不是HTML标签开头，包装成p标签
        if (!paraText.match(/^<[h|d|q|l]/)) {
          paragraphs.push(`<p class="result-paragraph">${paraText}</p>`);
        } else {
          paragraphs.push(paraText);
        }
        currentParagraph = [];
      }
      continue;
    }
    
    // 如果是HTML标签（标题、分隔线、引用、列表），直接添加
    if (line.match(/^<[h|d|q|l]/)) {
      if (currentParagraph.length > 0) {
        const paraText = currentParagraph.join(' ');
        if (!paraText.match(/^<[h|d|q|l]/)) {
          paragraphs.push(`<p class="result-paragraph">${paraText}</p>`);
        } else {
          paragraphs.push(paraText);
        }
        currentParagraph = [];
      }
      paragraphs.push(line);
    } else {
      // 普通文本，添加到当前段落
      currentParagraph.push(line);
    }
  }
  
  // 处理最后一个段落
  if (currentParagraph.length > 0) {
    const paraText = currentParagraph.join(' ');
    if (!paraText.match(/^<[h|d|q|l]/)) {
      paragraphs.push(`<p class="result-paragraph">${paraText}</p>`);
    } else {
      paragraphs.push(paraText);
    }
  }
  
  return paragraphs.join('\n');
};

const loadDetectionParams = async () => {
  try {
    // 模拟API调用
    const params = await new Promise<any>(resolve => setTimeout(() => resolve({
      detectConf: 0.5,
      cooldownTime: 5,
      showOriginal: true
    }), 300));

    // 更新状态
    state.detectConf = params.detectConf ?? 0.5;
    state.cooldownTime = params.cooldownTime;
    state.showOriginal = params.showOriginal;
  } catch (error) {
    console.error('加载参数失败:', error);
    alert('加载参数失败，请重试');
  }
};

// 判断开始检测按钮是否应该被禁用
const getStartButtonDisabled = (): boolean => {
  // 如果正在推理中，禁用按钮
  if (state.inferenceLoading) {
    return true;
  }
  
  // 图片推理：需要有大模型、模型服务或模型选择，以及图片文件
  if (state.activeSource === 'image') {
    const hasModel = state.selectedLLMId || state.selectedDeployServiceId || state.selectedModelId;
    const hasImage = state.uploadedImageFile || state.historyInputSource;
    return !hasModel || !hasImage;
  }
  
  // 视频推理：需要有模型选择，以及视频文件
  if (state.activeSource === 'video') {
    const hasModel = state.selectedModelId;
    const hasVideo = state.uploadedVideoFile || state.historyInputSource;
    return !hasModel || !hasVideo;
  }

  // 在线摄像头：需要有模型和摄像头，且未在推流中
  if (state.activeSource === 'camera') {
    if (state.cameraStreamActive) return true;
    const hasModel = state.selectedModelId;
    const hasCamera = !!state.selectedCameraId;
    return !hasModel || !hasCamera;
  }
  
  // 默认禁用
  return true;
};

// 统一提取真实可上传文件，兼容 File、Blob 以及 antd UploadFile(originFileObj)
const resolveUploadBlob = (fileLike: any): Blob | null => {
  if (!fileLike) return null;
  if (fileLike instanceof Blob) return fileLike;
  if (fileLike.originFileObj instanceof Blob) return fileLike.originFileObj;
  return null;
};

const handleAnalysisTypeChange = async () => {
  state.detectionResult = null;
  state.detectionCount = 0;
  state.averageConfidence = 0;
  state.llmTextResult = null;
  stopPosePolling();
  if (isPoseMode.value) {
    if (!POSE_BUILTIN_MODELS.includes(String(state.selectedModelId || ''))) {
      state.selectedModelId = 'yolo26n-pose';
    }
    state.selectedLLMId = null;
    state.selectedDeployServiceId = null;
  } else if (POSE_BUILTIN_MODELS.includes(String(state.selectedModelId || ''))) {
    state.selectedModelId = 'yolov26';
  }
};

const resolvePoseModelParams = (): { modelId: number; modelFilePath?: string } => {
  const selected = String(state.selectedModelId || '');
  if (selected === 'yolo26n-pose') {
    return { modelId: 0, modelFilePath: 'yolo26n-pose.pt' };
  }
  const parsed = typeof state.selectedModelId === 'number'
    ? state.selectedModelId
    : parseInt(String(state.selectedModelId), 10);
  return { modelId: Number.isNaN(parsed) ? 0 : parsed };
};

const stopPosePolling = () => {
  if (state.posePollTimer) {
    clearInterval(state.posePollTimer);
    state.posePollTimer = null;
  }
  state.poseJobId = null;
};

const startPosePolling = (jobId: string) => {
  stopPosePolling();
  state.poseJobId = jobId;
  state.pollingStartTime = Date.now();

  state.posePollTimer = window.setInterval(async () => {
    if (state.pollingStartTime && Date.now() - state.pollingStartTime > POLLING_TIMEOUT) {
      stopPosePolling();
      state.inferenceLoading = false;
      state.detectionStatus = 'failed';
      state.statusText = '姿态分析超时';
      createMessage.error('视频姿态分析超时');
      return;
    }

    try {
      const resp = await poseVideoProgress(jobId);
      const responseData = resp.data || resp;
      if (responseData.code !== 0) {
        throw new Error(responseData.msg || '查询进度失败');
      }
      const progress = responseData.data || {};
      if (progress.status === 'error') {
        stopPosePolling();
        state.inferenceLoading = false;
        state.detectionStatus = 'failed';
        state.statusText = '姿态分析失败';
        createMessage.error(progress.error || responseData.msg || '视频姿态分析失败');
        return;
      }
      if (progress.status === 'done') {
        stopPosePolling();
        const stats = progress.stats || {};
        state.detectionCount = stats.totalPersons || 0;
        if (stats.result_url) {
          state.detectionResult = getMediaUrl(stats.result_url);
        } else if (stats.output) {
          const blobResp = await poseOutputVideo(stats.output);
          const blob = blobResp.data instanceof Blob ? blobResp.data : blobResp;
          state.detectionResult = URL.createObjectURL(blob);
        }
        state.inferenceLoading = false;
        state.detectionStatus = 'completed';
        state.statusText = '姿态分析完成';
        createMessage.success('视频姿态分析完成');
      }
    } catch (error: any) {
      console.error('姿态视频轮询失败:', error);
    }
  }, POLLING_INTERVAL);
};

const startPoseAnalysis = async () => {
  if (!state.selectedModelId) {
    createMessage.warning('请先选择姿态模型');
    return;
  }

  if (state.activeSource === 'image' && !state.uploadedImageFile) {
    createMessage.warning('请先上传图片');
    return;
  }
  if (state.activeSource === 'video' && !state.uploadedVideoFile) {
    createMessage.warning('请先上传视频');
    return;
  }
  if (state.activeSource === 'camera') {
    if (!state.selectedCameraId) {
      createMessage.warning('请选择有效的在线摄像头');
      return;
    }
  }

  state.inferenceLoading = true;
  state.detectionStatus = 'running';
  state.statusText = '姿态分析中...';
  state.detectionResult = null;
  state.detectionCount = 0;

  const { modelId, modelFilePath } = resolvePoseModelParams();

  try {
    if (state.activeSource === 'image') {
      const formData = new FormData();
      const blob = resolveUploadBlob(state.uploadedImageFile);
      if (!blob) throw new Error('图片文件无效');
      formData.append('file', blob);
      formData.append('conf', String(state.detectConf));
      if (modelFilePath) formData.append('model_file_path', modelFilePath);

      const resp = await posePredict(modelId, formData);
      const responseData = resp.data || resp;
      if (responseData.code !== 0) throw new Error(responseData.msg || '姿态分析失败');
      const data = responseData.data || {};
      state.detectionCount = data.count || 0;
      if (data.imageBase64) {
        state.detectionResult = `data:image/jpeg;base64,${data.imageBase64}`;
      }
      state.detectionStatus = 'completed';
      state.statusText = '姿态分析完成';
      createMessage.success('姿态分析完成');
      return;
    }

    if (state.activeSource === 'video') {
      const formData = new FormData();
      const blob = resolveUploadBlob(state.uploadedVideoFile);
      if (!blob) throw new Error('视频文件无效');
      formData.append('file', blob);
      formData.append('conf', String(state.detectConf));
      if (modelFilePath) formData.append('model_file_path', modelFilePath);

      const resp = await posePredictVideo(modelId, formData);
      const responseData = resp.data || resp;
      if (responseData.code !== 0) throw new Error(responseData.msg || '视频姿态任务启动失败');
      const jobId = responseData.data?.jobId;
      if (!jobId) throw new Error('未获取到任务 ID');
      startPosePolling(jobId);
      createMessage.success('视频姿态分析任务已提交，处理中...');
      return;
    }

    if (state.activeSource === 'camera') {
      const device = selectedCamera.value;
      if (device) {
        await ensureCameraStreamReady(device);
      }
      const formData = new FormData();
      const parameters: Record<string, any> = {
        conf: state.detectConf,
        conf_thres: state.detectConf,
        stream_extract_interval: 5,
      };
      if (device?.rtmp_stream) parameters.rtmp_stream = device.rtmp_stream;
      if (device?.http_stream) parameters.http_stream = device.http_stream;
      const rtsp = device ? getCameraRtspUrl(device) : null;
      if (rtsp) parameters.rtsp_direct = rtsp;
      formData.append('device_id', state.selectedCameraId);
      if (selectedCameraRtsp.value) formData.append('input_source', selectedCameraRtsp.value);
      formData.append('parameters', JSON.stringify(parameters));
      if (modelFilePath) formData.append('model_file_path', modelFilePath);

      const resp = await poseRtspStart(modelId, formData);
      const responseData = resp.data || resp;
      if (responseData.code !== 0) throw new Error(responseData.msg || '姿态推流启动失败');
      const result = responseData.data?.result || responseData.data || {};
      const streamUrl = result.stream_url;
      if (!streamUrl) throw new Error('未获取到姿态推流地址');
      state.cameraResultUrl = toStreamPlayUrl(streamUrl);
      state.cameraInferenceRecordId = result.record_id ?? responseData.data?.record_id ?? null;
      state.cameraInferenceDeviceId = state.selectedCameraId;
      state.cameraStreamActive = true;
      state.detectionStatus = 'running';
      state.statusText = '实时姿态分析中';
      createMessage.success('实时姿态分析已启动');
      return;
    }
  } catch (error: any) {
    console.error('姿态分析失败:', error);
    state.detectionStatus = 'failed';
    state.statusText = '姿态分析失败';
    createMessage.error(error?.message || '姿态分析失败');
  } finally {
    if (state.activeSource !== 'video' && state.activeSource !== 'camera') {
      state.inferenceLoading = false;
    } else if (state.activeSource === 'camera' && !state.cameraStreamActive) {
      state.inferenceLoading = false;
    }
  }
};

const startDetection = async () => {
  if (isPoseMode.value) {
    await startPoseAnalysis();
    return;
  }
  // 检查是否有可用的模型（大模型、模型服务或模型选择）
  const hasModel = state.selectedLLMId || state.selectedDeployServiceId || state.selectedModelId;
  if (!hasModel) {
    createMessage.warning('请先选择模型、模型服务或大模型');
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

  if (state.activeSource === 'camera') {
    if (!state.selectedCameraId) {
      createMessage.warning('请选择有效的在线摄像头');
      return;
    }
    if (!state.selectedModelId) {
      createMessage.warning('请先选择模型');
      return;
    }
  }

  state.inferenceLoading = true;
  state.detectionStatus = 'running';
  state.statusText = '推理中...';

  try {
    const formData = new FormData();
    
    // 设置推理类型（在线摄像头走后端 rtsp 推理）
    formData.append(
      'inference_type',
      state.activeSource === 'camera' ? 'rtsp' : state.activeSource,
    );
    
    // 设置推理参数
    const parameters: Record<string, any> = {
      conf_thres: state.detectConf,
      iou_thres: 0.45,
      use_stream_algorithm_defaults: false,
      stream_imgsz: 640,
      // 与 VIDEO OVERLAY_EXTRACT_INTERVAL 一致：每 5 帧检测一次，推流不阻塞
      stream_extract_interval: 5,
    };
    if (
      isCustomModelSelected.value &&
      state.availableClassNames.length > 0 &&
      state.selectedClassNames.length > 0 &&
      state.selectedClassNames.length < state.availableClassNames.length
    ) {
      parameters.selected_classes = [...state.selectedClassNames];
    }

    // 如果是默认模型，添加模型文件路径参数
    if (state.selectedModelId === 'yolov8') {
      formData.append('model_file_path', 'yolov8n.pt');
    } else if (state.selectedModelId === 'yolov11') {
      formData.append('model_file_path', 'yolo11n.pt');
    } else if (state.selectedModelId === 'yolov26') {
      formData.append('model_file_path', 'yolo26n.pt');
    }
    // 注意：用户上传的模型不需要传递 model_file_path，后端会根据 model_id 从 MinIO 下载

    // 视频推理场景：先上传文件，run接口只传input_source，避免大文件直传导致超时
    let uploadedVideoInputSource: string | null = null;
    if (state.activeSource === 'video' && state.uploadedVideoFile) {
      const uploadVideoBlob = resolveUploadBlob(state.uploadedVideoFile);
      if (!uploadVideoBlob) {
        throw new Error('视频文件无效，请重新选择后重试');
      }
      const uploadFormData = new FormData();
      uploadFormData.append('file', uploadVideoBlob);
      const uploadResp = await uploadInputFile(uploadFormData);
      // 兼容三种响应格式：
      // 1) defHttp已解包：{ url, fileName }
      // 2) 标准包装：{ code, msg, data: { url, fileName } }
      // 3) axios原始响应：{ data: { code, msg, data: { url } } }
      const rawUpload = uploadResp?.data || uploadResp;
      const uploadCode = rawUpload?.code;
      const uploadMsg = rawUpload?.msg || rawUpload?.data?.msg;
      const uploadPayload = rawUpload?.data?.url
        ? rawUpload.data
        : (rawUpload?.data?.data || rawUpload);
      const uploadUrl = uploadPayload?.url;

      if ((typeof uploadCode !== 'undefined' && uploadCode !== 0) || !uploadUrl) {
        console.error('视频文件上传响应异常:', uploadResp);
        throw new Error(uploadMsg || '视频文件上传失败');
      }
      uploadedVideoInputSource = uploadUrl;
    }

    // 根据输入源类型添加文件或URL
    if (state.activeSource === 'image' && state.uploadedImageFile) {
      const uploadImageBlob = resolveUploadBlob(state.uploadedImageFile);
      if (!uploadImageBlob) {
        throw new Error('图片文件无效，请重新选择后重试');
      }
      formData.append('file', uploadImageBlob);
    } else if (state.activeSource === 'image' && state.historyInputSource) {
      // 从历史记录还原的图片，使用 input_source URL
      formData.append('input_source', state.historyInputSource);
    } else if (state.activeSource === 'video' && state.uploadedVideoFile) {
      // 视频走上传接口后，这里只传URL，避免run接口请求过大
      formData.append('input_source', uploadedVideoInputSource || '');
    } else if (state.activeSource === 'video' && state.historyInputSource) {
      // 从历史记录还原的视频，使用 input_source URL
      formData.append('input_source', state.historyInputSource);
    } else if (state.activeSource === 'camera' && state.selectedCameraId) {
      const device = selectedCamera.value;
      if (device) {
        await ensureCameraStreamReady(device);
        if (device.rtmp_stream) {
          parameters.rtmp_stream = device.rtmp_stream;
        }
        if (device.http_stream) {
          parameters.http_stream = device.http_stream;
        }
        const rtsp = getCameraRtspUrl(device);
        if (rtsp) {
          parameters.rtsp_direct = rtsp;
        }
      }
      formData.append('device_id', state.selectedCameraId);
      if (selectedCameraRtsp.value) {
        formData.append('input_source', selectedCameraRtsp.value);
      }
    }

    formData.append('parameters', JSON.stringify(parameters));

    // 判断使用哪个接口：优先级 大模型 > 模型服务 > 模型选择
    let response;
    let useLLM = false;
    let useClusterService = false;
    
    // 优先级1：大模型（仅在图片推理时）
    if (state.selectedLLMId && state.activeSource === 'image' && (state.uploadedImageFile || state.historyInputSource)) {
      const selectedLLM = state.llms.find(llm => llm.id === state.selectedLLMId);
      if (selectedLLM) {
        useLLM = true;
        // 单模型管控：列表仅含平台当前启用的唯一大模型，无需前端再激活
        // 使用大模型视觉推理接口
        // 如果有上传的文件，使用文件；否则使用历史记录的 input_source
        if (state.uploadedImageFile) {
          response = await visionInference(state.uploadedImageFile, '请对这张图片进行视觉推理，分析图片中的对象、场景和可能的行为。');
        } else {
          // 如果只有历史记录的 input_source，需要先下载图片
          createMessage.warning('使用历史记录时，请重新上传图片文件');
          state.inferenceLoading = false;
          state.detectionStatus = 'failed';
          state.statusText = '推理失败';
          return;
        }
      } else {
        createMessage.warning('选中的大模型无效，将使用其他方式');
        useLLM = false;
      }
    }
    
    // 优先级2：模型服务（仅在图片推理时，且未选择大模型）
    if (!useLLM && state.selectedDeployServiceId && state.activeSource === 'image') {
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
    
    // 优先级3：模型选择（如果未选择大模型和模型服务）
    if (!useLLM && !useClusterService) {
      // 调用推理接口
      // 重要：用户上传的模型应该传递实际的 model_id（数字），而不是转换为 0
      // 只有默认模型（yolov8/yolov11/yolov26）才传递 0
      let modelId: number;
      if (state.selectedModelId === 'yolov8' || state.selectedModelId === 'yolov11' || state.selectedModelId === 'yolov26') {
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
    
    // 处理大模型响应
    if (useLLM) {
      // 记录原始响应，用于调试
      console.log('大模型推理响应:', response);
      
      // 检查响应格式：可能是 { code: 0, data: { response: "..." }, msg: "..." } 或直接是 { response: "..." }
      let llmResult = '';
      let success = false;
      let errorMsg = '';
      
      // 情况1：标准响应格式 { code: 0, data: { response: "..." }, msg: "..." }
      if (response && typeof response === 'object' && 'code' in response) {
        if (response.code === 0) {
          success = true;
          // 从 data.response 中提取结果
          if (response.data && typeof response.data === 'object') {
            llmResult = response.data.response || '';
          } else if (typeof response.data === 'string') {
            llmResult = response.data;
          }
          errorMsg = response.msg || '大模型推理执行成功';
        } else {
          success = false;
          errorMsg = response.msg || '大模型推理失败';
        }
      } 
      // 情况2：响应转换器已处理，直接是 data 对象 { response: "...", mode: "inference", ... }
      else if (response && typeof response === 'object' && 'response' in response) {
        success = true;
        llmResult = response.response || '';
        errorMsg = '大模型推理执行成功';
      }
      // 情况3：响应转换器已处理，但结构不同（嵌套的 data）
      else if (response && typeof response === 'object' && 'data' in response) {
        const data = response.data;
        if (data && typeof data === 'object' && 'response' in data) {
          success = true;
          llmResult = data.response || '';
          errorMsg = '大模型推理执行成功';
        } else if (typeof data === 'string') {
          success = true;
          llmResult = data;
          errorMsg = '大模型推理执行成功';
        } else {
          success = false;
          errorMsg = '无法解析大模型响应格式';
          console.error('大模型响应 data 格式无法识别:', data);
        }
      }
      // 情况4：直接是字符串
      else if (typeof response === 'string') {
        success = true;
        llmResult = response;
        errorMsg = '大模型推理执行成功';
      }
      // 情况5：无法识别格式
      else {
        success = false;
        errorMsg = '无法识别大模型响应格式';
        console.error('大模型响应格式无法识别，原始响应:', response);
        console.error('响应类型:', typeof response);
        console.error('响应键:', response && typeof response === 'object' ? Object.keys(response) : 'N/A');
      }
      
      if (success) {
        // 大模型返回的是文本结果
        state.llmTextResult = llmResult || '推理完成，但未返回结果';
        state.detectionResult = null; // 大模型不返回图片，清空图片结果
        state.detectionCount = 0;
        state.averageConfidence = 0;
        state.detectionStatus = 'completed';
        state.statusText = '推理完成';
        createMessage.success(errorMsg);
        console.log('大模型推理结果已设置:', llmResult.substring(0, 100) + '...');
        return;
      } else {
        console.error('大模型推理失败:', errorMsg);
        throw new Error(errorMsg);
      }
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
      } else if (state.activeSource === 'camera') {
        const streamUrl = result?.stream_url || responseData.data?.result?.stream_url;
        const recordId = responseData.data?.record_id || result?.record_id;
        if (streamUrl) {
          state.cameraResultUrl = toStreamPlayUrl(streamUrl);
          state.cameraInferenceRecordId = recordId ?? null;
          state.cameraInferenceDeviceId = state.selectedCameraId;
          state.cameraStreamActive = true;
          state.detectionStatus = 'running';
          state.statusText = '实时推理中';
          createMessage.success('实时推理已启动');
          return;
        } else {
          throw new Error('未获取到推理推流地址');
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
    
    // 检查是否是模型不存在的错误
    let errorMessage = '推理执行失败，请重试';
    
    // 检查 HTTP 状态码
    if (error.response?.status === 400) {
      errorMessage = '模型不存在';
    }
    // 检查响应数据中的 code 和 msg
    else if (error.response?.data) {
      const responseData = error.response.data;
      if (responseData.code === 400 || (responseData.msg && (responseData.msg.includes('不存在') || responseData.msg.includes('模型')))) {
        errorMessage = '模型不存在';
      } else if (responseData.msg) {
        errorMessage = responseData.msg;
      }
    }
    // 检查错误消息中是否包含"不存在"或"模型"关键词
    else if (error.message && (error.message.includes('不存在') || (error.message.includes('模型') && error.message.includes('400')))) {
      errorMessage = '模型不存在';
    }
    // 使用默认错误消息
    else if (error.message) {
      errorMessage = error.message;
    }
    
    createMessage.error(errorMessage);
  } finally {
    // 视频推理提交后会进入轮询阶段，此时不要在finally里提前关闭loading
    if (state.currentInferenceRecordId === null && state.activeSource !== 'camera') {
      state.inferenceLoading = false;
    } else if (state.activeSource === 'camera') {
      state.inferenceLoading = false;
    }
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
    const response = await getModelPage({ pageNo: 1, pageSize: 1000 });
    if (response.code === 0) {
      state.models = response.data || [];
      if (state.models.length > 0 && !state.selectedModelId) {
        state.selectedModelId = state.models[0].id;
      }
      if (isCustomModelSelected.value) {
        const model = state.models.find((item) => String(item.id) === String(state.selectedModelId));
        await loadClassesForModel(model);
      }
    }
  } catch (error: any) {
    console.error('加载模型列表失败:', error);
    createMessage.error('加载模型列表失败');
  } finally {
    state.loading = false;
  }
};

// 加载大模型列表（仅加载已激活的大模型，用于模型推理）
const loadLLMs = async () => {
  state.llmsLoading = true;
  try {
    // 在模型推理时，只获取已激活的大模型
    const response = await getLLMList({ page: 1, pageSize: 100, is_active: 'true' });
    if (response && typeof response === 'object') {
      if ('code' in response && response.code === 0 && response.data) {
        // 标准格式：包含 code 和 data
        state.llms = response.data.list || [];
      } else if ('list' in response && Array.isArray(response.list)) {
        // 转换器已解包的格式：直接包含 list
        state.llms = response.list;
      } else {
        state.llms = [];
      }
    } else {
      state.llms = [];
    }
  } catch (error: any) {
    console.error('加载大模型列表失败:', error);
    createMessage.error('加载大模型列表失败');
  } finally {
    state.llmsLoading = false;
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

// 处理大模型选择变化
const handleLLMChange = () => {
  // 如果选择了大模型，清空模型选择和模型服务选择，并设置默认demo数据
  if (state.selectedLLMId) {
    state.selectedModelId = null;
    state.selectedDeployServiceId = null;
    // 立即清空检测结果，让界面切换到大模型样式
    state.detectionResult = null;
    state.detectionCount = 0;
    state.averageConfidence = 0;
  } else {
    // 如果取消选择大模型，也清空相关结果
    state.llmTextResult = null;
  }
  stopPollingInferenceResult();
};

// 处理部署服务选择变化
const handleDeployServiceChange = () => {
  // 如果选择了模型服务，清空大模型选择和模型选择
  if (state.selectedDeployServiceId) {
    state.selectedLLMId = null; // 恢复大模型下拉框为默认：请选择大模型
    state.selectedModelId = null;
  }
  state.detectionResult = null;
  state.llmTextResult = null; // 清空大模型文本结果，恢复初始样式
  state.detectionCount = 0;
  state.averageConfidence = 0;
  stopPollingInferenceResult();
};

const handleModelChange = async () => {
  if (state.selectedModelId) {
    state.selectedLLMId = null;
    state.selectedDeployServiceId = null;
  }
  state.detectionResult = null;
  state.llmTextResult = null;
  state.detectionCount = 0;
  state.averageConfidence = 0;
  stopPollingInferenceResult();

  if (state.activeSource === 'camera' && state.cameraStreamActive && state.selectedCameraId) {
    const cameraId = state.selectedCameraId;
    await stopCameraInference(false);
    await new Promise((resolve) => setTimeout(resolve, 600));
    if (state.selectedModelId) {
      await startDetection();
    } else {
      state.selectedCameraId = cameraId;
    }
  }
};

// 切换输入源时清理
const handleSourceChange = async () => {
  stopPollingInferenceResult();
  cleanupVideoUrl();
  state.historyInputSource = null; // 清除历史记录的 input_source
  state.detectionResult = null;
  state.llmTextResult = null;

  if (state.activeSource === 'camera') {
    state.showOriginal = true;
    state.selectedLLMId = null;
    state.selectedDeployServiceId = null;
    refreshCameras();
    return;
  }

  await stopCameraInference(false);
  state.selectedCameraId = '';
  state.cameraPreviewUrl = null;
  state.cameraResultUrl = null;
  state.cameraStreamActive = false;
  state.cameraInferenceRecordId = null;
  state.cameraInferenceDeviceId = '';

  // 如果切换到图片推理，加载大模型列表和部署服务列表；否则清空选择
  if (state.activeSource === 'image') {
    loadLLMs();
    loadDeployServices();
  } else {
    // 非图片推理时，清空大模型和模型服务选择（因为大模型和模型服务只支持图片推理）
    state.selectedLLMId = null;
    state.selectedDeployServiceId = null;
  }
};

const loadCameras = async () => {
  state.camerasLoading = true;
  try {
    const response = await getDeviceList({ pageNo: 1, pageSize: 1000 });
    const list = Array.isArray(response)
      ? response
      : (response?.data || response?.list || []);
    state.cameras = Array.isArray(list) ? list : [];
  } catch (error: any) {
    console.error('加载摄像头列表失败:', error);
    createMessage.error('加载摄像头列表失败');
  } finally {
    state.camerasLoading = false;
  }
};

const refreshCameras = async () => {
  await loadCameras();
  await reloadSelectedCameraPreview();
};

const STREAM_READY_PROBE_MS = 2000;
const STREAM_READY_MAX_WAIT_MS = 30000;

const collectCameraStreamProbeUrls = (device: DeviceInfo): string[] => {
  const urls: string[] = [];
  const seen = new Set<string>();
  const add = (url?: string | null) => {
    const trimmed = (url || '').trim();
    if (!trimmed || seen.has(trimmed)) return;
    seen.add(trimmed);
    urls.push(trimmed);
  };

  add(device.http_stream);
  if (device.rtmp_stream) {
    add(convertRtmpToHttp(device.rtmp_stream));
    add(device.rtmp_stream);
  }
  add(`http://127.0.0.1:8080/live/${device.id}.flv`);
  return urls;
};

const waitForCameraStreamReady = async (device: DeviceInfo): Promise<boolean> => {
  const candidates = collectCameraStreamProbeUrls(device);
  if (candidates.length === 0) {
    return false;
  }

  const deadline = Date.now() + STREAM_READY_MAX_WAIT_MS;
  while (Date.now() < deadline) {
    for (const url of candidates) {
      if (await probeStreamPlayable(url, STREAM_READY_PROBE_MS)) {
        return true;
      }
    }
    await new Promise((resolve) => setTimeout(resolve, 1500));
  }
  return false;
};

const ensureCameraStreamReady = async (device: DeviceInfo): Promise<void> => {
  const isGb28181 = isGb28181Device(device.source, device.device_kind);

  if (!isGb28181) {
    try {
      await ensureDeviceStreamForwardTask(device.id);
    } catch (error) {
      console.warn('确保推流转发任务失败，回退旧版推流接口:', error);
      try {
        await startStreamForwarding(device.id, true);
      } catch (fallbackError) {
        console.warn('启动摄像头推流失败，将继续尝试推理:', fallbackError);
      }
    }

    await new Promise((resolve) => setTimeout(resolve, 2000));

    const ready = await waitForCameraStreamReady(device);
    if (!ready) {
      console.warn('摄像头 SRS 流尚未探测就绪，推理将依赖后端重试拉流');
    }
    return;
  }

  // 国标设备走 WVP 点播，由后端 resolve_gb28181_source 解析拉流地址
  console.info('国标摄像头推理将由后端解析 WVP 点播地址');
};

const resolveCameraPreviewUrl = async (device: DeviceInfo): Promise<string | null> => {
  let url = await resolveMonitorPlayUrl(device, 'video');
  if (url) {
    return toStreamPlayUrl(url);
  }

  await ensureCameraStreamReady(device);

  try {
    const statusResp = await getStreamStatus(device.id);
    const statusData = statusResp?.data ?? statusResp;
    const httpStream = statusData?.http_stream || device.http_stream;
    if (httpStream) {
      return toStreamPlayUrl(httpStream);
    }
    const rtmpStream = statusData?.rtmp_url || statusData?.rtmp_stream || device.rtmp_stream;
    if (rtmpStream) {
      return toStreamPlayUrl(rtmpStream);
    }
  } catch (error) {
    console.warn('获取摄像头预览流失败:', error);
  }

  if (device.http_stream || device.rtmp_stream) {
    return toStreamPlayUrl(device.http_stream || device.rtmp_stream || '');
  }

  return null;
};

const reloadSelectedCameraPreview = async () => {
  if (state.activeSource !== 'camera' || !state.selectedCameraId) return;

  state.cameraPreviewUrl = null;

  const device = selectedCamera.value;
  if (!device) return;

  try {
    const previewUrl = await resolveCameraPreviewUrl(device);
    state.cameraPreviewUrl = previewUrl;
    if (!previewUrl) {
      createMessage.warning('无法获取摄像头预览流，请确认设备在线且已开启推流');
    }
  } catch (error: any) {
    console.error('加载摄像头预览失败:', error);
    createMessage.error('加载摄像头预览失败');
  }
};

const handleCameraChange = async () => {
  if (state.cameraStreamActive || state.cameraInferenceRecordId) {
    await stopCameraInference(false);
  }
  if (!state.selectedCameraId) {
    state.cameraPreviewUrl = null;
    return;
  }
  await reloadSelectedCameraPreview();
};

const stopCameraInference = async (showMsg = true) => {
  if (!state.cameraStreamActive && !state.cameraInferenceRecordId) {
    return;
  }
  try {
    if (isPoseMode.value) {
      await poseRtspStop({ stop_all: true });
    } else {
      await stopRtspInference({ stop_all: true });
    }
  } catch (error) {
    console.warn('停止实时推理失败:', error);
  }
  state.cameraStreamActive = false;
  state.cameraResultUrl = null;
  state.cameraInferenceRecordId = null;
  state.cameraInferenceDeviceId = '';
  state.inferenceLoading = false;
  if (state.detectionStatus === 'running' && state.activeSource === 'camera') {
    state.detectionStatus = 'idle';
    state.statusText = '就绪 - 等待输入源';
  }
  if (showMsg && state.activeSource === 'camera') {
    createMessage.info('已停止实时推理');
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
      createMessage.warning('推理任务处理时间较长，已停止自动轮询，请到历史记录查看最新状态');
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
    'FAILED': '失败',
    'STREAMING': '推流中',
    'RUNNING': '运行中',
  };
  const typeMap: Record<string, string> = {
    image: '图片',
    video: '视频',
    rtsp: '摄像头',
  };
  const typeLabel = typeMap[record.inference_type || ''] || '';
  const status = statusMap[record.status] || record.status;
  return `${dateStr}${typeLabel ? ` - ${typeLabel}` : ''} - ${status}`;
};

// 处理历史记录选择
const handleHistoryRecordChange = async () => {
  if (!state.selectedHistoryRecordId) {
    // 清空选择时，清理状态
    state.detectionResult = null;
    state.llmTextResult = null;
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
    state.llmTextResult = null;
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
    } else if (inferenceType === 'rtsp') {
      state.activeSource = 'camera';
      await loadCameras();
      const matchedCamera = matchHistoryCamera(inputSource);
      if (matchedCamera) {
        state.selectedCameraId = matchedCamera.id;
        await handleCameraChange();
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
      if (inferenceType === 'rtsp') {
        state.cameraResultUrl = toStreamPlayUrl(taskData.stream_output_url);
        state.cameraStreamActive = ['STREAMING', 'RUNNING'].includes(taskData.status);
      } else {
        state.detectionResult = taskData.stream_output_url;
      }
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
  
  // 如果是图片推理，加载大模型列表和部署服务列表
  if (state.activeSource === 'image') {
    loadLLMs();
    loadDeployServices();
  }
  
  // 如果父组件传递了初始大模型ID，设置选中
  if (props.initialLLMId) {
    // 等待大模型列表加载完成后再设置
    loadLLMs().then(() => {
      const llm = state.llms.find(l => l.id === props.initialLLMId);
      if (llm) {
        state.selectedLLMId = props.initialLLMId;
      }
    });
  }
});

// 组件卸载时清理
onUnmounted(() => {
  stopPollingInferenceResult();
  stopPosePolling();
  stopCameraInference(false);
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
  height: 100%;
  min-height: 480px;
  max-height: 100%;
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

  .left-panel-body {
    flex: 1;
    min-height: 0;
    overflow-x: hidden;
    overflow-y: auto;
    padding-bottom: 4px;

    &::-webkit-scrollbar {
      width: 5px;
    }

    &::-webkit-scrollbar-thumb {
      background: fade(@border-color, 80%);
      border-radius: 4px;
    }
  }

  .config-row {
    display: flex;
    gap: 10px;

    &--2 {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 10px;
    }
  }

  .config-col {
    min-width: 0;
    display: flex;
    flex-direction: column;
    gap: 8px;

    .section-title {
      margin-bottom: 0;
    }
  }

  .config-section {
    padding: 10px 16px 12px;
    border-bottom: 1px solid fade(@border-color, 65%);
    background: transparent;
    margin: 0;
    border-radius: 0;
    transition: @panel-transition;
    flex-shrink: 0;
    overflow: visible;
    display: flex;
    flex-direction: column;

    &--footer {
      flex-shrink: 0;
      border-bottom: none;
      border-top: 1px solid @border-color;
      padding: 12px 16px 14px;
      background: #fff;
      box-shadow: 0 -4px 12px rgba(0, 0, 0, 0.04);
      z-index: 1;
    }

      .section-title {
      display: flex;
      align-items: center;
      gap: 8px;
      margin-bottom: 8px;
      font-weight: 600;
      font-size: 14px;
      line-height: 1.3;
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

      .section-help {
        margin-left: 4px;
        color: @text-secondary;
        font-size: 14px;
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
      gap: 8px;
      overflow: visible;
      flex: none;
      min-height: auto;

      .detect-conf-input {
        width: 100%;

        :deep(.ant-input-number) {
          width: 100%;
          border-radius: 6px;
        }

        :deep(.ant-input-number-input) {
          height: 36px;
        }
      }

      .class-select {
        width: 100%;

        :deep(.ant-select-selector) {
          min-height: 38px !important;
          border-radius: 6px !important;
          border-color: @border-color !important;
          box-shadow: @shadow-sm;
          padding-top: 2px;
          padding-bottom: 2px;
        }

        :deep(.ant-select:hover .ant-select-selector) {
          border-color: @border-hover !important;
        }

        :deep(.ant-select-focused .ant-select-selector) {
          border-color: @primary-color !important;
          box-shadow: 0 0 0 3px rgba(44, 62, 80, 0.1), @shadow-sm !important;
        }
      }

      .model-select-tip {
        font-size: 12px;
        color: @text-muted;
        line-height: 1.4;
      }

      .class-tags-status {
        font-size: 13px;
        color: @text-secondary;
        line-height: 1.5;

        &--warn {
          color: @warning-color;
        }
      }

      .class-select {
        width: 100%;
      }

      .class-tags-hint {
        font-size: 12px;
        color: @text-muted;
        line-height: 1.4;
      }

      .camera-select-combo {
        display: flex;
        align-items: stretch;
        width: 100%;
        border: 1px solid @border-color;
        border-radius: 6px;
        background: #fff;
        box-shadow: @shadow-sm;
        overflow: hidden;
        transition: @panel-transition;

        &:hover {
          border-color: @border-hover;
        }

        &:focus-within {
          border-color: @primary-color;
          box-shadow: 0 0 0 3px rgba(44, 62, 80, 0.1), @shadow-sm;
        }

        .camera-select-field {
          flex: 1;
          min-width: 0;
          border: none;
          border-radius: 0;
          box-shadow: none;
          background: transparent;

          &:focus {
            outline: none;
            box-shadow: none;
          }

          &:hover {
            border-color: transparent;
          }
        }

        .camera-refresh-btn {
          flex-shrink: 0;
          display: flex;
          align-items: center;
          justify-content: center;
          width: 40px;
          border: none;
          border-left: 1px solid @border-color;
          background: transparent;
          color: @text-secondary;
          cursor: pointer;
          transition: @panel-transition;
          padding: 0;
          font-size: 14px;

          &:hover:not(:disabled) {
            color: @primary-color;
          }

          &:disabled {
            cursor: not-allowed;
            opacity: 0.65;
          }
        }
      }

      .camera-rtsp-hint {
        font-size: 12px;
        color: @text-muted;
        line-height: 1.4;
        word-break: break-all;
      }

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

        .stream-live-badge {
          font-size: 12px;
          font-weight: 700;
          color: @error-color;
          letter-spacing: 0.5px;
        }
      }

      .video-content {
        flex: 1;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        background: #ffffff;
        color: @light-text;
        font-size: 16px;
        position: relative;
        overflow-y: auto;
        overflow-x: hidden;
        min-height: 0;
        max-width: 100%;
        width: 100%;

        // 可滚动的视频内容区域（用于大模型推理结果）
        &.video-content-scrollable {
          align-items: flex-start;
          overflow-y: auto;
          overflow-x: hidden;
        }

        &.stream-player-content {
          align-items: stretch;
          justify-content: stretch;
          padding: 0;
          background: #000;
          min-height: 280px;

          :deep(.jessibuca-container),
          :deep(.container-shell),
          :deep(#container) {
            width: 100% !important;
            height: 100% !important;
            min-height: 280px;
          }
        }

        .image-preview {
          width: 100%;
          height: 100%;
          max-width: 100%;
          max-height: 100%;
          display: flex;
          align-items: flex-start;
          justify-content: center;
          position: relative;
          overflow: hidden;
          box-sizing: border-box;
          flex-shrink: 0;

          .preview-image {
            max-width: 100%;
            max-height: 100%;
            width: auto;
            height: auto;
            object-fit: contain;
            display: block;
            box-sizing: border-box;
            flex-shrink: 0;
          }
        }

        .detection-result, .video-preview {
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
          flex-shrink: 0;

          .preview-image {
            max-width: 100%;
            max-height: 100%;
            width: auto;
            height: auto;
            object-fit: contain;
            display: block;
            box-sizing: border-box;
            flex-shrink: 0;
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

        .llm-text-result {
          width: 100%;
          flex: 1;
          min-height: 0;
          padding: 24px;
          display: flex;
          flex-direction: column;
          background: #FFFFFF;
          overflow: hidden;
          box-sizing: border-box;
          align-self: stretch;

          .llm-result-placeholder {
            flex: 1;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            padding: 40px 20px;
            color: #999;
            font-size: 14px;
            text-align: center;

            .icon {
              font-size: 64px;
              margin-bottom: 16px;
              color: @primary-color;
              opacity: 0.5;
            }

            p {
              margin: 0;
              line-height: 1.6;
              color: #666;
            }
          }

          .llm-result-content {
            flex: 1;
            min-height: 0;
            font-size: 14px;
            line-height: 1.8;
            color: #333;
            word-wrap: break-word;
            overflow-y: auto;
            padding: 12px;
            background: #ffffff;

            // 标题样式
            :deep(.result-h1) {
              font-size: 20px;
              font-weight: 700;
              color: @primary-color;
              margin: 20px 0 16px 0;
              padding-bottom: 12px;
              border-bottom: 2px solid @border-color;
            }

            :deep(.result-h2) {
              font-size: 18px;
              font-weight: 600;
              color: @primary-color;
              margin: 18px 0 14px 0;
              padding-bottom: 10px;
              border-bottom: 1px solid #f0f0f0;
            }

            :deep(.result-h3) {
              font-size: 16px;
              font-weight: 600;
              color: #333;
              margin: 16px 0 12px 0;
            }

            :deep(.result-h4) {
              font-size: 15px;
              font-weight: 600;
              color: #666;
              margin: 14px 0 10px 0;
            }

            // 段落样式
            :deep(.result-paragraph) {
              margin: 12px 0;
              line-height: 1.8;
              color: #333;
              text-align: justify;
            }

            // 列表样式
            :deep(.result-list-item) {
              display: flex;
              margin: 8px 0;
              padding-left: 8px;
              line-height: 1.8;

              &.nested {
                padding-left: 24px;
                margin: 4px 0;
              }

              .list-number {
                font-weight: 600;
                color: @primary-color;
                margin-right: 8px;
                min-width: 24px;
              }

              .list-bullet {
                color: @primary-color;
                margin-right: 8px;
                font-weight: bold;
              }

              .list-content {
                flex: 1;
                color: #333;
              }
            }

            // 分隔线样式
            :deep(.result-divider) {
              height: 1px;
              background: linear-gradient(to right, transparent, @border-color, transparent);
              margin: 20px 0;
            }

            // 引用样式
            :deep(.result-quote) {
              margin: 12px 0;
              padding: 12px 16px;
              background: #f5f5f5;
              border-left: 4px solid @primary-color;
              border-radius: 4px;
              color: #666;
              font-style: italic;
              line-height: 1.8;
            }

            // 粗体样式
            :deep(strong) {
              color: @primary-color;
              font-weight: 600;
            }

            // 代码样式
            :deep(code) {
              background: #f5f5f5;
              padding: 2px 6px;
              border-radius: 3px;
              font-family: 'Courier New', monospace;
              font-size: 13px;
              color: #e83e8c;
            }
            border-radius: 6px;
            border: 1px solid @border-color;
          }
        }

        .video-placeholder {
          flex: 1;
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          gap: 20px;
          color: @text-secondary;
          width: 100%;
          min-height: 0;

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
      height: 700px;
      width: 100%;
      min-width: 0;
      padding: 12px;
      overflow: hidden;
      box-sizing: border-box;
      max-width: 100%;
      max-height: 100%;
      align-items: stretch;

      .video-wrapper {
        flex: 1;
        min-width: 0;
        min-height: 0;
        height: 100%;
        border-right: none;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08), 
                    0 2px 8px rgba(0, 0, 0, 0.05);
        margin: 0;
        display: flex;
        flex-direction: column;
        overflow: hidden;

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
    max-width: 100%;
    min-width: 0;
    max-height: 42vh;
    border-right: none;
    border-bottom: 1px solid @border-color;

    .left-panel-body {
      max-height: calc(42vh - 72px);
    }
  }

  .video-area {
    flex: 1;
    min-height: 0;
    height: auto;
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
