<script setup lang="ts">
import { ref, watch } from 'vue';
import { Spin } from 'ant-design-vue';
import Jessibuca from '@/components/Player/module/jessibuca.vue';
import { resolveDeviceInlinePlayUrl } from '@/views/camera/utils/devicePlay';

defineOptions({ name: 'CameraInlinePreview' });

const props = defineProps<{
  deviceId?: string | null;
  deviceName?: string | null;
}>();

const loading = ref(false);
const error = ref('');
const url = ref('');

let seq = 0;

async function load(id: string, name?: string | null) {
  const mySeq = ++seq;
  loading.value = true;
  error.value = '';
  url.value = '';
  try {
    const u = await resolveDeviceInlinePlayUrl(id, {
      name: name?.trim() || undefined,
      enableAi: false,
    });
    if (mySeq !== seq) return;
    if (!u) {
      error.value = '未获取到可播放的视频流';
      return;
    }
    url.value = u;
  } catch {
    if (mySeq !== seq) return;
    error.value = '加载视频流失败';
  } finally {
    if (mySeq === seq) loading.value = false;
  }
}

watch(
  () => [props.deviceId, props.deviceName] as const,
  ([id, name]) => {
    if (id) load(id, name);
    else {
      url.value = '';
      error.value = '';
    }
  },
  { immediate: true },
);
</script>

<template>
  <div class="camera-inline-preview">
    <div v-if="loading" class="camera-inline-preview__hint">
      <Spin size="small" /> <span>正在拉流…</span>
    </div>
    <div v-else-if="error" class="camera-inline-preview__hint camera-inline-preview__hint--error">
      {{ error }}
    </div>
    <Jessibuca v-else-if="url" :playUrl="url" :hasAudio="false" class="camera-inline-preview__player" />
    <div v-else class="camera-inline-preview__hint">无预览</div>
  </div>
</template>

<style scoped lang="less">
.camera-inline-preview {
  position: relative;
  width: 100%;
  height: 176px;
  margin-top: 10px;
  border-radius: 8px;
  overflow: hidden;
  background: #0b1020;

  &__player {
    width: 100%;
    height: 100%;
  }

  &__hint {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    width: 100%;
    height: 100%;
    font-size: 13px;
    color: rgba(255, 255, 255, 0.75);

    &--error {
      color: #ff7875;
    }
  }
}
</style>
