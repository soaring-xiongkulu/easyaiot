<template>
  <div class="model-workbench">
    <!-- 主内容区 -->
    <div class="main-content">
      <!-- 左侧配置面板 -->
      <div class="left-panel" :class="{ collapsed: state.leftPanelCollapsed }">
        <!-- 操作控制区域 -->
        <div class="config-section">
          <div class="section-title">
            <i class="fas fa-cogs"></i>
            <span>操作控制</span>
          </div>
          <div class="config-options">
            <div class="button-group">
              <button class="btn btn-primary" @click="initParams">
                <i class="fas fa-undo"></i>
                <span>初始化参数</span>
              </button>
              <button class="btn btn-primary" @click="saveDetectionParams">
                <i class="fas fa-save"></i>
                  <span>保存参数</span>
              </button>
            </div>
          </div>
        </div>

        <!-- 输入源选择 -->
        <div class="config-section">
          <div class="section-title">
            <i class="fas fa-signal"></i>
            <span>输入源选择</span>
          </div>
          <div class="config-options">
            <div class="input-group">
              <select class="select-field" v-model="state.activeSource">
                <option v-for="option in sourceOptions" :key="option.value" :value="option.value">
                  {{ option.label }}
                </option>
              </select>
            </div>

            <!-- 动态内容区域 -->
            <div class="source-content" v-if="state.activeSource === 'image'">
              <input type="file" class="input-field" accept="image/*">
              <button class="btn btn-primary">上传图片</button>
            </div>
            <div class="source-content" v-else-if="state.activeSource === 'video'">
              <input type="file" class="input-field" accept="video/*">
              <button class="btn btn-primary">上传视频</button>
            </div>
            <div class="source-content" v-else-if="state.activeSource === 'rtsp'">
              <input type="text" class="input-field" placeholder="输入RTSP流地址">
              <button class="btn btn-primary">连接流</button>
            </div>
            <div class="source-content" v-else-if="state.activeSource === 'camera'">
              <select class="input-field">
                <option value="">选择摄像头</option>
                <option value="camera1">摄像头 1</option>
                <option value="camera2">摄像头 2</option>
              </select>
              <button class="btn btn-primary">开启摄像头</button>
            </div>
          </div>
        </div>

        <!-- 算法列表 -->
        <div class="config-section">
          <div class="section-title">
            <i class="fas fa-microchip"></i>
            <span>算法列表</span>
          </div>
          <div class="config-options">
            <div class="algorithm-list">
              <div
                v-for="algorithm in state.algorithms"
                :key="algorithm.id"
                class="algorithm-item"
                :class="{ active: algorithm.enabled }"
                @click="toggleAlgorithm(algorithm.id)"
              >
                <input
                  type="checkbox"
                  class="algorithm-checkbox"
                  :checked="algorithm.enabled"
                  @click.stop="toggleAlgorithm(algorithm.id)"
                >
                <div class="algorithm-info">
                  <div class="algorithm-name">{{ algorithm.name }}</div>
                  <div class="algorithm-desc">{{ algorithm.description }}</div>
                </div>
                <div class="algorithm-status" :class="{ running: algorithm.running }"></div>
              </div>
            </div>
            <div class="button-group">
              <button class="btn btn-primary" @click="startAllAlgorithms">启动选中算法</button>
              <button class="btn btn-outline" @click="stopAllAlgorithms">停止所有算法</button>
            </div>
          </div>
        </div>

        <!-- 报警区域绘制 -->
        <div class="config-section">
          <div class="section-title">
            <i class="fas fa-draw-polygon"></i>
            <span>报警区域绘制</span>
          </div>
          <div class="config-options">
            <div class="button-group">
              <button class="btn btn-primary" @click="startDrawingAlertArea">绘制报警区域</button>
              <button class="btn btn-outline" @click="clearAlertArea">清除区域</button>
            </div>

            <!-- 报警区域预览 -->
            <div class="option-group">
              <div class="option-title">报警区域预览</div>
              <div class="alert-area-preview">
                <img v-if="state.alertAreaPreview" :src="state.alertAreaPreview" alt="报警区域预览">
                <div v-else class="placeholder">尚未绘制报警区域</div>
              </div>
            </div>

            <div class="option-group">
              <div class="option-title">报警置信度阈值</div>
              <div class="input-group">
                <input
                  type="range"
                  min="0"
                  max="100"
                  v-model="state.confidenceThreshold"
                  class="input-field"
                >
                <div class="input-label">{{ state.confidenceThreshold }}%</div>
              </div>
            </div>
            <div class="option-group">
              <div class="option-title">报警冷却时间</div>
              <div class="input-group">
                <input
                  type="number"
                  v-model="state.cooldownTime"
                  class="input-field"
                >
                <div class="input-label">秒</div>
              </div>
            </div>
          </div>
        </div>

        <!-- 告警通知 -->
        <div class="config-section">
          <div class="section-title">
            <i class="fas fa-bell"></i>
            <span>告警通知</span>
            <div class="checkbox-group" style="margin-left: auto;">
              <input
                type="checkbox"
                id="enable-alert-notification"
                v-model="state.enableAlertNotification"
              >
              <label for="enable-alert-notification">启用</label>
            </div>
          </div>
          <div class="config-options" v-if="state.enableAlertNotification">
            <div class="option-controls">
              <div class="checkbox-group">
                <input
                  type="checkbox"
                  id="platform-notify"
                  v-model="state.notifications.platform"
                >
                <label for="platform-notify">平台推送</label>
              </div>
              <div class="checkbox-group">
                <input
                  type="checkbox"
                  id="sms-notify"
                  v-model="state.notifications.sms"
                >
                <label for="sms-notify">短信通知</label>
              </div>
              <div class="checkbox-group">
                <input
                  type="checkbox"
                  id="email-notify"
                  v-model="state.notifications.email"
                >
                <label for="email-notify">邮件通知</label>
              </div>
              <div class="checkbox-group">
                <input
                  type="checkbox"
                  id="wechat-notify"
                  v-model="state.notifications.wechat"
                >
                <label for="wechat-notify">企业微信通知</label>
              </div>
              <div class="checkbox-group">
                <input
                  type="checkbox"
                  id="feishu-notify"
                  v-model="state.notifications.feishu"
                >
                <label for="feishu-notify">飞书通知</label>
              </div>
              <div class="checkbox-group">
                <input
                  type="checkbox"
                  id="dingtalk-notify"
                  v-model="state.notifications.dingtalk"
                >
                <label for="dingtalk-notify">钉钉通知</label>
              </div>
            </div>
          </div>
        </div>

        <!-- 告警条件 -->
        <div class="config-section">
          <div class="section-title">
            <i class="fas fa-filter"></i>
            <span>告警条件</span>
            <div class="checkbox-group" style="margin-left: auto;">
              <input
                type="checkbox"
                id="enable-alert-condition"
                v-model="state.enableAlertCondition"
              >
              <label for="enable-alert-condition">启用</label>
            </div>
          </div>
          <div class="config-options" v-if="state.enableAlertCondition">
            <div class="option-group">
              <div class="option-title">滞留时间</div>
              <div class="input-group" style="flex-direction: row; align-items: center;">
                <select class="select-field" v-model="state.stayCondition">
                  <option value="greater">大于</option>
                  <option value="equal">等于</option>
                  <option value="less">小于</option>
                </select>
                <input
                  type="number"
                  v-model="state.stayTime"
                  class="input-field"
                  style="margin: 0 5px;"
                >
                <div class="input-label">秒</div>
              </div>
            </div>
            <div class="option-group">
              <div class="option-title">目标数量</div>
              <div class="input-group" style="flex-direction: row; align-items: center;">
                <select class="select-field" v-model="state.countCondition">
                  <option value="greater">大于</option>
                  <option value="equal">等于</option>
                  <option value="less">小于</option>
                </select>
                <input
                  type="number"
                  v-model="state.targetCount"
                  class="input-field"
                  style="margin: 0 5px;"
                >
                <div class="input-label">个</div>
              </div>
            </div>
          </div>
        </div>

        <!-- 告警录像 -->
        <div class="config-section">
          <div class="section-title">
            <i class="fas fa-hdd"></i>
            <span>告警录像</span>
            <div class="checkbox-group" style="margin-left: auto;">
              <input
                type="checkbox"
                id="enable-alert-recording"
                v-model="state.enableAlertRecording"
              >
              <label for="enable-alert-recording">启用</label>
            </div>
          </div>
          <div class="config-options" v-if="state.enableAlertRecording">
            <div class="option-group">
              <div class="option-title">保存天数</div>
              <div class="input-group">
                <input
                  type="number"
                  v-model="state.saveDays"
                  class="input-field"
                >
                <div class="input-label">天（默认30天）</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 左侧面板切换按钮 -->
      <div class="panel-toggle"
           :class="{ collapsed: state.leftPanelCollapsed }"
           @click="toggleLeftPanel">
        <i :class="state.leftPanelCollapsed ? 'fas fa-chevron-right' : 'fas fa-chevron-left'"></i>
      </div>

      <!-- 右侧视频显示区域 -->
      <div class="video-area">
        <!-- 右下角控制按钮 -->
        <div class="right-controls">
          <button class="control-btn" @click="startDetection">
            <i class="fas fa-play"></i>
            <span>开始检测</span>
          </button>
          <button class="control-btn toggle-original-btn" @click="state.showOriginal = true">
            <i class="fas fa-eye"></i>
            <span>显示原始对照</span>
          </button>
          <button class="control-btn close-original-btn" @click="state.showOriginal = false">
            <i class="fas fa-eye-slash"></i>
            <span>关闭原始对照</span>
          </button>
        </div>

        <div class="video-container">
          <!-- 图片模式 -->
          <div v-if="state.activeSource === 'image'">
            <div v-if="state.showOriginal" class="dual-video">
              <div class="video-wrapper">
                <div class="video-title">
                  <span>原始输入源</span>
                </div>
                <div class="video-content">
                  <div class="video-placeholder">
                    <i class="fas fa-image fa-3x"></i>
                    <span>等待图片上传</span>
                  </div>
                </div>
              </div>
              <div class="video-wrapper">
                <div class="video-title">
                  <span>检测结果</span>
                </div>
                <div class="video-content">
                  <div class="video-placeholder">
                    <i class="fas fa-search fa-3x"></i>
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
                  <div class="video-placeholder">
                    <i class="fas fa-search fa-3x"></i>
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
                  <div class="video-placeholder">
                    <i class="fas fa-video fa-3x"></i>
                    <span>等待视频输入</span>
                  </div>
                </div>
              </div>
              <div class="video-wrapper">
                <div class="video-title">
                  <span>检测结果</span>
                </div>
                <div class="video-content">
                  <div class="video-placeholder">
                    <i class="fas fa-search fa-3x"></i>
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
                  <div class="video-placeholder">
                    <i class="fas fa-search fa-3x"></i>
                    <span>检测结果将显示在这里</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 报警区域绘制弹框 -->
      <div v-if="state.alertAreaCanvasVisible" class="alert-area-canvas-modal">
        <div class="canvas-container">
          <div class="canvas-title">报警区域绘制</div>
          <div class="canvas-wrapper">
            <canvas
              class="alert-canvas"
              width="800"
              height="400"
              @click="handleCanvasClick"
            ></canvas>
          </div>
          <div class="modal-controls">
            <button class="btn btn-primary" @click="saveAlertArea">保存报警区域</button>
            <button class="btn btn-outline" @click="clearAlertArea">清除区域</button>
            <button class="btn btn-primary" @click="takeScreenshot">拍照截图</button>
            <button class="btn btn-outline" @click="state.alertAreaCanvasVisible = false">关闭</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
// 状态管理
import {computed, reactive} from "vue";

const state = reactive({
  activeSource: 'image',
  confidenceThreshold: 70,
  cooldownTime: 5,
  stayCondition: 'greater',
  stayTime: 10,
  countCondition: 'greater',
  targetCount: 5,
  saveDays: 30,
  showOriginal: true,
  notifications: {
    platform: true,
    sms: false,
    email: true,
    wechat: false,
    feishu: false,
    dingtalk: true
  },
  algorithms: [
    { id: 1, name: 'YOLOv5', description: '实时目标检测', enabled: true, running: false },
    { id: 2, name: 'Faster R-CNN', description: '高精度目标检测', enabled: true, running: false },
    { id: 3, name: 'SSD', description: '平衡速度与精度', enabled: false, running: false },
    { id: 4, name: 'Mask R-CNN', description: '实例分割', enabled: true, running: false },
    { id: 5, name: 'RetinaNet', description: '密集目标检测', enabled: false, running: false },
    { id: 6, name: 'EfficientDet', description: '高效目标检测', enabled: true, running: false }
  ],
  detectionStatus: 'idle',
  statusText: '就绪 - 等待输入源',
  screenshotVisible: false,
  screenshotData: null,
  leftPanelCollapsed: false,
  showAdvancedSettings: false,
  alertAreaCanvasVisible: false,
  alertAreaPreview: null,
  alertAreaPoints: [],
  isDrawing: false,
  enableAlertNotification: true,
  enableAlertCondition: true,
  enableAlertRecording: true
});

const sourceOptions = [
  { value: 'image', label: '图片上传', icon: 'fas fa-image' },
  { value: 'video', label: '视频上传', icon: 'fas fa-video' },
  { value: 'rtsp', label: 'RTSP流', icon: 'fas fa-stream' },
  { value: 'camera', label: '摄像头', icon: 'fas fa-camera' }
];

const enabledAlgorithms = computed(() => {
  return state.algorithms.filter(algo => algo.enabled);
});

const runningAlgorithms = computed(() => {
  return state.algorithms.filter(algo => algo.running);
});

const selectedSource = computed(() => {
  return sourceOptions.find(option => option.value === state.activeSource);
});

const setActiveSource = (source) => {
  state.activeSource = source;
};

const toggleAlgorithm = (algorithmId) => {
  const algorithm = state.algorithms.find(a => a.id === algorithmId);
  if (algorithm) {
    algorithm.enabled = !algorithm.enabled;
  }
};

const startAllAlgorithms = () => {
  state.algorithms.forEach(algo => {
    if (algo.enabled) {
      algo.running = true;
    }
  });
  state.detectionStatus = 'running';
  state.statusText = '检测中 - 多算法并行处理';
  state.showAdvancedSettings = true;
};

const stopAllAlgorithms = () => {
  state.algorithms.forEach(algo => {
    algo.running = false;
  });
  state.detectionStatus = 'stopped';
  state.statusText = '已停止 - 等待输入源';
};

const takeScreenshot = () => {
  state.screenshotData = 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==';
  state.screenshotVisible = true;
};

const saveScreenshot = () => {
  if (state.screenshotData) {
    const link = document.createElement('a');
    link.download = 'detection_screenshot.png';
    link.href = state.screenshotData;
    link.click();
  }
};

const closeScreenshot = () => {
  state.screenshotVisible = false;
  state.screenshotData = null;
};

const saveDetectionParams = async () => {
  try {
    const params = {
      confidenceThreshold: state.confidenceThreshold,
      cooldownTime: state.cooldownTime,
      stayCondition: state.stayCondition,
      stayTime: state.stayTime,
      countCondition: state.countCondition,
      targetCount: state.targetCount,
      saveDays: state.saveDays,
      showOriginal: state.showOriginal,
      notifications: { ...state.notifications },
      enabledAlgorithms: state.algorithms
        .filter(algo => algo.enabled)
        .map(algo => algo.id),
      alertArea: state.alertAreaPoints.length > 0 ?
        state.alertAreaPoints.map(p => ({ x: p.x, y: p.y })) : null,
      enableAlertNotification: state.enableAlertNotification,
      enableAlertCondition: state.enableAlertCondition,
      enableAlertRecording: state.enableAlertRecording
    };

    // 模拟API调用
    console.log('保存检测参数:', params);
    await new Promise(resolve => setTimeout(resolve, 500));
    alert('检测参数保存成功！');
  } catch (error) {
    console.error('保存参数失败:', error);
    alert('保存参数失败，请重试');
  }
};

const loadDetectionParams = async () => {
  try {
    // 模拟API调用
    const params = await new Promise(resolve => setTimeout(() => resolve({
      confidenceThreshold: 70,
      cooldownTime: 5,
      stayCondition: 'greater',
      stayTime: 10,
      countCondition: 'greater',
      targetCount: 5,
      saveDays: 30,
      showOriginal: true,
      notifications: {
        platform: true,
        sms: false,
        email: true,
        wechat: false,
        feishu: false,
        dingtalk: true
      },
      algorithms: [1, 2, 4],
      alertArea: null,
      enableAlertNotification: true,
      enableAlertCondition: true,
      enableAlertRecording: true
    }), 300));

    // 更新状态
    state.confidenceThreshold = params.confidenceThreshold;
    state.cooldownTime = params.cooldownTime;
    state.stayCondition = params.stayCondition;
    state.stayTime = params.stayTime;
    state.countCondition = params.countCondition;
    state.targetCount = params.targetCount;
    state.saveDays = params.saveDays;
    state.showOriginal = params.showOriginal;
    state.notifications = { ...params.notifications };

    // 更新算法状态
    state.algorithms.forEach(algo => {
      algo.enabled = params.algorithms.includes(algo.id);
    });

    // 更新报警区域
    if (params.alertArea) {
      state.alertAreaPoints = params.alertArea;
      state.alertAreaPreview = 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==';
    }

    // 更新启用开关
    state.enableAlertNotification = params.enableAlertNotification;
    state.enableAlertCondition = params.enableAlertCondition;
    state.enableAlertRecording = params.enableAlertRecording;

    alert('检测参数加载成功！');
  } catch (error) {
    console.error('加载参数失败:', error);
    alert('加载参数失败，请重试');
  }
};

const initParams = () => {
  if (confirm('确定要初始化所有参数吗？当前设置将被重置。')) {
    loadDetectionParams();
  }
};

const startDetection = async () => {
  if (enabledAlgorithms.value.length === 0) {
    alert('请至少选择一个算法');
    return;
  }

  try {
    const config = {
      source: state.activeSource,
      algorithms: enabledAlgorithms.value.map(algo => algo.id),
      params: {
        confidenceThreshold: state.confidenceThreshold,
        cooldownTime: state.cooldownTime,
        stayCondition: state.stayCondition,
        stayTime: state.stayTime,
        countCondition: state.countCondition,
        targetCount: state.targetCount,
        showOriginal: state.showOriginal,
        notifications: { ...state.notifications },
        alertArea: state.alertAreaPoints.length > 0 ?
          state.alertAreaPoints.map(p => ({ x: p.x, y: p.y })) : null,
        enableAlertNotification: state.enableAlertNotification,
        enableAlertCondition: state.enableAlertCondition,
        enableAlertRecording: state.enableAlertRecording
      }
    };

    // 模拟API调用
    console.log('开始检测任务:', config);
    const result = await new Promise(resolve => setTimeout(() => resolve({
      taskId: 'detect_001',
      status: 'running'
    }), 800));

    if (result.status === 'running') {
      startAllAlgorithms();
      alert(`检测任务已启动，任务ID: ${result.taskId}`);
    }
  } catch (error) {
    console.error('启动检测失败:', error);
    alert('启动检测失败，请重试');
  }
};

const toggleLeftPanel = () => {
  state.leftPanelCollapsed = !state.leftPanelCollapsed;
};

const startDrawingAlertArea = () => {
  state.alertAreaCanvasVisible = true;
  state.alertAreaPoints = [];
  state.isDrawing = false;
};

const clearAlertArea = () => {
  state.alertAreaPoints = [];
  state.alertAreaPreview = null;
};

const saveAlertArea = () => {
  if (state.alertAreaPoints.length < 3) {
    alert('请至少绘制三个点来定义报警区域');
    return;
  }

  state.alertAreaPreview = 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==';
  state.alertAreaCanvasVisible = false;
  alert('报警区域已保存');
};

const handleCanvasClick = (event) => {
  if (!state.alertAreaCanvasVisible) return;

  const canvas = event.target;
  const rect = canvas.getBoundingClientRect();
  const x = event.clientX - rect.left;
  const y = event.clientY - rect.top;

  state.alertAreaPoints.push({ x, y });

  const ctx = canvas.getContext('2d');
  ctx.fillStyle = '#e74c3c';
  ctx.beginPath();
  ctx.arc(x, y, 5, 0, Math.PI * 2);
  ctx.fill();

  if (state.alertAreaPoints.length > 1) {
    ctx.strokeStyle = '#e74c3c';
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(
      state.alertAreaPoints[state.alertAreaPoints.length - 2].x,
      state.alertAreaPoints[state.alertAreaPoints.length - 2].y
    );
    ctx.lineTo(x, y);
    ctx.stroke();
  }

  if (state.alertAreaPoints.length > 2) {
    ctx.beginPath();
    ctx.moveTo(
      state.alertAreaPoints[0].x,
      state.alertAreaPoints[0].y
    );
    for (let i = 1; i < state.alertAreaPoints.length; i++) {
      ctx.lineTo(
        state.alertAreaPoints[i].x,
        state.alertAreaPoints[i].y
      );
    }
    ctx.closePath();
    ctx.fillStyle = 'rgba(231, 76, 60, 0.3)';
    ctx.fill();
  }
};
</script>

<style lang="less">
// 变量定义
@primary-color: #1a1a2e;
@secondary-color: #16213e;
@accent-color: #0f3460;
@success-color: #1e5128;
@warning-color: #b68a2c;
@error-color: #7d0a0a;
@light-bg: #f8f9fa;
@light-text: #333333;
@gray-color: #95a5a6;
@border-color: #d1d5db;
@sidebar-width: 320px;
@header-height: 60px;
@panel-transition: all 0.3s ease-in-out;

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}

body {
  background-color: #f5f7fa;
  color: #333;
  overflow: hidden;
}

.model-workbench {
  display: flex;
  flex-direction: column;
  height: 100vh;
  width: 100vw;
}

/* 头部样式 */
.header {
  height: @header-height;
  background: linear-gradient(to right, @primary-color, @accent-color);
  color: white;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  z-index: 100;

  .header-content {
    display: flex;
    align-items: center;
    gap: 12px;
    font-size: 20px;
    font-weight: 600;

    i {
      color: @warning-color;
      font-size: 24px;
    }
  }
}

/* 主内容区 */
.main-content {
  display: flex;
  flex: 1;
  overflow: hidden;
}

/* 左侧配置面板 */
.left-panel {
  width: @sidebar-width;
  display: flex;
  flex-direction: column;
  background: white;
  border-right: 1px solid @border-color;
  overflow-y: auto;
  transition: @panel-transition;
  box-shadow: 2px 0 10px rgba(0, 0, 0, 0.1);

  &.collapsed {
    width: 0;
    overflow: hidden;
    border-right: none;
  }

  .config-section {
    padding: 20px;
    border-bottom: 1px solid @border-color;

    .section-title {
      display: flex;
      align-items: center;
      gap: 10px;
      margin-bottom: 15px;
      font-weight: 500;
      font-size: 16px;
      color: @primary-color;
    }

    .config-options {
      display: flex;
      flex-direction: column;
      gap: 15px;

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
        gap: 10px;
        flex-wrap: wrap;

        .btn {
          padding: 8px 12px;
          border: 1px solid @border-color;
          border-radius: 4px;
          background: white;
          cursor: pointer;
          transition: all 0.2s;
          font-size: 14px;
          flex: 1;
          min-width: 120px;

          &-primary {
            background: @accent-color;
            color: white;
            border-color: @accent-color;

            &:hover {
              background: #0d2a4d;
            }
          }

          &-outline {
            background: white;
            color: @accent-color;
            border-color: @accent-color;

            &:hover {
              background: rgba(15, 52, 96, 0.1);
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
          padding: 8px 10px;
          border: 1px solid @border-color;
          border-radius: 4px;
          width: 100%;
          background: #f8f9fa;
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
      }

      .select-field {
        padding: 8px 10px;
        border: 1px solid @border-color;
        border-radius: 4px;
        background: white;
        width: 100%;
      }

      /* 算法列表样式 */
      .algorithm-list {
        display: flex;
        flex-direction: column;
        gap: 10px;
        max-height: 200px;
        overflow-y: auto;

        .algorithm-item {
          display: flex;
          align-items: center;
          padding: 10px;
          border: 1px solid @border-color;
          border-radius: 4px;
          cursor: pointer;
          transition: all 0.2s;
          background: #f8f9fa;

          &:hover {
            background: #ecf0f1;
          }

          &.active {
            border-color: @accent-color;
            background: rgba(15, 52, 96, 0.05);
          }

          .algorithm-checkbox {
            margin-right: 10px;
          }

          .algorithm-info {
            flex: 1;

            .algorithm-name {
              font-weight: 500;
              margin-bottom: 3px;
              color: @light-text;
            }

            .algorithm-desc {
              font-size: 12px;
              color: @gray-color;
            }
          }

          .algorithm-status {
            width: 10px;
            height: 10px;
            border-radius: 50%;
            background: #ddd;
            margin-left: 10px;

            &.running {
              background: @success-color;
              animation: pulse 1.5s infinite;
            }
          }
        }
      }

      /* 报警区域预览 */
      .alert-area-preview {
        margin-top: 10px;
        border: 1px solid @border-color;
        border-radius: 4px;
        padding: 10px;
        background: #f8f9fa;
        min-height: 100px;
        display: flex;
        align-items: center;
        justify-content: center;

        img {
          max-width: 100%;
          max-height: 150px;
          border-radius: 4px;
        }

        .placeholder {
          color: @gray-color;
          font-style: italic;
        }
      }
    }
  }
}

/* 左侧面板切换按钮 */
.panel-toggle {
  position: absolute;
  top: 50%;
  left: 0;
  transform: translateY(-50%);
  background: @primary-color;
  color: white;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  z-index: 100;
  transition: @panel-transition;
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.2);

  &.collapsed {
    left: 0;
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
  padding: 20px;
  transition: @panel-transition;

  .video-container {
    display: flex;
    flex-direction: column;
    gap: 15px;
    height: 100%;

    .video-wrapper {
      display: flex;
      flex-direction: column;
      border: 1px solid @border-color;
      border-radius: 8px;
      overflow: hidden;
      position: relative;
      height: 100%;
      background: #ffffff;
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);

      .video-title {
        padding: 10px 15px;
        background: #f8f9fa;
        border-bottom: 1px solid @border-color;
        font-weight: 500;
        display: flex;
        justify-content: space-between;
        align-items: center;
        color: @light-text;

        .video-controls {
          display: flex;
          gap: 5px;

          .video-control-btn {
            padding: 4px 8px;
            background: @accent-color;
            color: white;
            border: none;
            border-radius: 3px;
            cursor: pointer;
            font-size: 12px;
            transition: background 0.2s;

            &:hover {
              background: #0d2a4d;
            }
          }
        }
      }

      .video-content {
        flex: 1;
        display: flex;
        align-items: center;
        justify-content: center;
        background: #f8f9fa;
        color: @light-text;
        font-size: 16px;
        position: relative;
        overflow: hidden;

        .video-placeholder {
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 15px;
          color: @gray-color;
        }
      }
    }

    .dual-video {
      display: flex;
      gap: 15px;
      height: 100%;

      .video-wrapper {
        flex: 1;
      }
    }

    .single-video {
      width: 100%;
      height: 100%;
    }
  }
}

/* 右下角按钮容器 */
.right-controls {
  position: absolute;
  bottom: 20px;
  right: 20px;
  display: flex;
  gap: 10px;
  z-index: 10;

  .control-btn {
    padding: 8px 12px;
    background: @accent-color;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    display: flex;
    align-items: center;
    gap: 5px;
    font-size: 14px;

    &:hover {
      background: #0d2a4d;
    }

    &.toggle-original-btn {
      background: @success-color;

      &:hover {
        background: #1a5128;
      }
    }

    &.close-original-btn {
      background: @error-color;

      &:hover {
        background: #6d0a0a;
      }
    }
  }
}

/* 报警区域绘制弹框 */
.alert-area-canvas-modal {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 200;

  .canvas-container {
    background: white;
    border-radius: 8px;
    padding: 20px;
    width: 80%;
    max-width: 900px;
    max-height: 80vh;
    overflow: auto;
    position: relative;

    .canvas-title {
      font-size: 18px;
      font-weight: 500;
      margin-bottom: 15px;
      color: @primary-color;
    }

    .canvas-wrapper {
      position: relative;
      border: 1px solid @border-color;
      border-radius: 4px;
      overflow: hidden;
      margin-bottom: 15px;

      .alert-canvas {
        width: 100%;
        height: 400px;
        background: #f8f9fa;
        cursor: crosshair;
      }
    }

    .modal-controls {
      display: flex;
      gap: 10px;
      justify-content: flex-end;
    }
  }
}

@keyframes pulse {
  0% { opacity: 1; }
  50% { opacity: 0.5; }
  100% { opacity: 1; }
}

/* 响应式调整 */
@media (max-width: 1200px) {
  :root {
    --sidebar-width: 280px;
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
</style>
