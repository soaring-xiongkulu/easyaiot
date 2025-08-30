<template>
  <BasicModal
    v-bind="$attrs"
    :title="title"
    :width="800"
    :footer="null"
    @register="registerModal"
    @cancel="handleCancel"
  >
    <div class="jsmpeg-modal">
      <div class="player-container">
        <canvas ref="canvasRef" class="jsmpeg-canvas"></canvas>
        <div v-if="loading" class="loading-state">
          <Spin size="large" />
          <p>视频加载中...</p>
        </div>
        <div v-if="error" class="error-state">
          <p>加载失败: {{ error }}</p>
          <Button type="primary" @click="initializePlayer">重试</Button>
        </div>
      </div>
      <div class="player-controls">
        <Button @click="togglePlay" :icon="isPlaying ? 'PauseCircleOutlined' : 'PlayCircleOutlined'">
          {{ isPlaying ? '暂停' : '播放' }}
        </Button>
        <Button @click="toggleMute" :icon="isMuted ? 'AudioMutedOutlined' : 'AudioOutlined'">
          {{ isMuted ? '取消静音' : '静音' }}
        </Button>
        <span>音量: </span>
        <Slider
          :min="0"
          :max="1"
          :step="0.1"
          :value="volume"
          @change="setVolume"
          style="width: 100px; display: inline-block"
        />
        <Button @click="handleFullscreen" icon="FullscreenOutlined">
          全屏
        </Button>
      </div>
    </div>
  </BasicModal>
</template>

<script lang="ts" setup>
import { ref, onMounted, onUnmounted, watch } from 'vue';
import { BasicModal, useModalInner } from '@/components/Modal';
import { Button, Spin, Slider } from 'ant-design-vue';

defineOptions({name: 'JSMpegModal'})

// 定义组件属性
interface Props {
  streamUrl: string;
  title?: string;
}

const props = withDefaults(defineProps<Props>(), {
  title: '视频播放'
});

// 组件状态
const canvasRef = ref<HTMLCanvasElement | null>(null);
const player = ref<any>(null);
const isPlaying = ref(false);
const isMuted = ref(false);
const volume = ref(0.5);
const loading = ref(false);
const error = ref<string | null>(null);

// 注册模态框
const [registerModal, { closeModal }] = useModalInner((record) => {
  initializePlayer();
})

// 初始化播放器
const initializePlayer = () => {
  if (!canvasRef.value) return;

  // 清理现有播放器
  if (player.value) {
    player.value.destroy();
    player.value = null;
  }
  error.value = null;
  loading.value = true;

  try {
    // 创建播放器实例
    player.value = new window.JSMpeg.Player(props.streamUrl, {
      canvas: canvasRef.value,
      audio: true,
      video: true,
      autoplay: true,
      loop: false,
      preserveDrawingBuffer: false,
      pauseWhenHidden: true,
      disableGl: false,
      disableWebAssembly: false
    });

    // 设置初始音量
    if (player.value.audioOut) {
      player.value.audioOut.volume = volume.value;
    }

    // 监听事件
    player.value.onPlay = () => {
      isPlaying.value = true;
      loading.value = false;
    };

    player.value.onPause = () => {
      isPlaying.value = false;
    };

    player.value.onEnded = () => {
      isPlaying.value = false;
    };

    player.value.onError = (err: any) => {
      error.value = err.message || '未知错误';
      loading.value = false;
    };

  } catch (err: any) {
    error.value = err.message;
    loading.value = false;
  }
};

// 控制方法
const togglePlay = () => {
  if (!player.value) return;

  if (isPlaying.value) {
    player.value.pause();
  } else {
    player.value.play();
  }
};

const toggleMute = () => {
  if (!player.value || !player.value.audioOut) return;

  isMuted.value = !isMuted.value;
  player.value.audioOut.volume = isMuted.value ? 0 : volume.value;
};

const setVolume = (value: number) => {
  volume.value = Math.max(0, Math.min(1, value));

  if (player.value && player.value.audioOut) {
    player.value.audioOut.volume = volume.value;
    isMuted.value = volume.value === 0;
  }
};

const handleFullscreen = () => {
  if (!canvasRef.value) return;

  if (canvasRef.value.requestFullscreen) {
    canvasRef.value.requestFullscreen();
  }
};

const handleCancel = () => {
  if (player.value) {
    player.value.destroy();
    player.value = null;
  }
  closeModal();
};

// 监听URL变化
watch(() => props.streamUrl, (newUrl) => {
  if (newUrl) {
    initializePlayer();
  }
});

// 组件卸载时清理资源
onUnmounted(() => {
  if (player.value) {
    player.value.destroy();
  }
});
</script>

<style scoped>
.jsmpeg-modal {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.player-container {
  position: relative;
  flex: 1;
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 400px;
  background: black;
  margin-bottom: 16px;
}

.jsmpeg-canvas {
  width: 100%;
  height: auto;
  max-height: 70vh;
}

.loading-state, .error-state {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  color: white;
  background: rgba(0, 0, 0, 0.7);
}

.player-controls {
  display: flex;
  align-items: center;
  gap: 10px;
  justify-content: center;
}
</style>
