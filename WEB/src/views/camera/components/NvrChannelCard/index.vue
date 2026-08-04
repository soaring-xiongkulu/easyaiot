<template>
  <div
    class="nvr-channel-card"
    :class="online === false ? 'offline' : 'online'"
  >
    <div class="status">{{ statusText }}</div>
    <div class="title" :title="displayName">{{ displayName }}</div>
    <div class="card-body">
      <div class="channel-info">
        <div class="props">
          <div class="prop-row channel-ip-row">
            <div class="prop prop-ip">
              <div class="label">IP</div>
              <div class="value">{{ item.ip || '—' }}</div>
            </div>
            <div class="prop prop-channel">
              <div class="label">通道号</div>
              <div class="value">CH{{ item.nvr_channel ?? '-' }}</div>
            </div>
          </div>
          <div class="prop prop-rtsp">
            <div class="label">RTSP</div>
            <div class="rtsp-value-row" :title="rtspUrl || undefined">
              <span class="value rtsp-text">{{ rtspUrl || '—' }}</span>
              <Icon
                v-if="rtspUrl"
                icon="tdesign:copy-filled"
                :size="14"
                color="#4287FCFF"
                class="copy-icon"
                @click.stop="handleCopyRtsp"
              />
            </div>
          </div>
        </div>
        <div class="btns" @click.stop>
          <div
            v-if="hasPlayableStream(item)"
            class="btn"
            :title="playButtonTitle"
            @click="emit('play', item)"
          >
            <Icon icon="octicon:play-16" :size="15" color="#3B82F6" />
          </div>
          <div class="btn" title="详情" @click="emit('view', item)">
            <Icon icon="ant-design:eye-filled" :size="15" color="#3B82F6" />
          </div>
          <div class="btn" title="编辑" @click="emit('edit', item)">
            <Icon icon="ant-design:edit-filled" :size="15" color="#3B82F6" />
          </div>
          <div class="btn" title="设置坐标" @click="emit('setLocation', item)">
            <Icon icon="ant-design:environment-outlined" :size="15" color="#3B82F6" />
          </div>
          <Popconfirm
            title="是否确认删除？"
            ok-text="是"
            cancel-text="否"
            @confirm="emit('delete', item)"
          >
            <div class="btn" title="删除" @click.stop>
              <Icon icon="material-symbols:delete-outline-rounded" :size="15" color="#DC2626" />
            </div>
          </Popconfirm>
        </div>
      </div>
      <div class="channel-img">
        <img :src="deviceImage" alt="" class="img" @click="emit('view', item)" />
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { computed } from 'vue';
import { Popconfirm } from 'ant-design-vue';
import { Icon } from '@/components/Icon';
import type { DeviceInfo } from '@/api/device/camera';
import { formatCameraDeviceLabel } from '@/views/camera/utils/deviceLabel';
import { hasPlayableStream } from '@/views/camera/utils/devicePlay';
import { copyText } from '@/utils/copyTextToClipboard';
import { useMessage } from '@/hooks/web/useMessage';
import HAIKANG_IMAGE from '@/assets/images/video/haikang.png';
import DAHUA_IMAGE from '@/assets/images/video/dahua.png';
import OTHER_IMAGE from '@/assets/images/video/other.png';

const props = defineProps<{
  item: DeviceInfo & {
    online_text?: string;
    online?: boolean | null;
    rtsp_url?: string;
    rtsp_direct?: string;
  };
  playButtonTitle?: string;
}>();

const { createMessage } = useMessage();

const emit = defineEmits<{
  view: [device: DeviceInfo];
  edit: [device: DeviceInfo];
  setLocation: [device: DeviceInfo];
  play: [device: DeviceInfo];
  delete: [device: DeviceInfo];
}>();

const playButtonTitle = computed(() => props.playButtonTitle ?? '播放视频流');

const online = computed(() => props.item.online ?? props.item.channel_online);

const statusText = computed(() => {
  if (props.item.online_text) return props.item.online_text;
  if (online.value === true) return '在线';
  if (online.value === false) return '离线';
  return '—';
});

const displayName = computed(() => formatCameraDeviceLabel(props.item));

const rtspUrl = computed(
  () => (props.item.source || props.item.rtsp_url || props.item.rtsp_direct || '').trim(),
);

function handleCopyRtsp() {
  if (!rtspUrl.value) return;
  copyText(rtspUrl.value, '已复制 RTSP');
  createMessage.success('复制成功');
}

const deviceImage = computed(() => {
  const m = (props.item.manufacturer || '').toLowerCase();
  if (m.includes('海康') || m.includes('hik')) return HAIKANG_IMAGE;
  if (m.includes('大华') || m.includes('dahua')) return DAHUA_IMAGE;
  return OTHER_IMAGE;
});
</script>

<style lang="less" scoped>
.nvr-channel-card {
  overflow: hidden;
  box-shadow: 0 0 4px #00000026;
  border-radius: 8px;
  padding: 16px 0;
  position: relative;
  background-color: #fff;
  background-repeat: no-repeat;
  background-position: center center;
  background-size: 104% 104%;
  transition: all 0.5s;
  min-height: 208px;
  height: 100%;

  &.online {
    background-image: url('@/assets/images/product/blue-bg.719b437a.png');

    .status {
      background: #d9dffd;
      color: #266cfbff;
    }
  }

  &.offline {
    background-image: url('@/assets/images/product/red-bg.101af5ac.png');

    .status {
      background: #fad7d9;
      color: #d43030;
    }
  }

  .status {
    min-width: 90px;
    height: 25px;
    border-radius: 6px 0 0 6px;
    font-size: 12px;
    font-weight: 500;
    line-height: 25px;
    text-align: center;
    position: absolute;
    right: 0;
    top: 16px;
    padding: 0 8px;
    white-space: nowrap;
    z-index: 1;
  }

  .title {
    font-size: 15px;
    font-weight: 600;
    color: #050708;
    line-height: 20px;
    height: 20px;
    margin: 0 16px 8px;
    padding-right: 88px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .card-body {
    position: relative;
    padding-left: 16px;
    min-height: 140px;
  }

  .channel-info {
    flex-direction: column;
    max-width: calc(100% - 132px);

    .props {
      margin-top: 4px;

      .prop-row {
        display: flex;
        align-items: flex-start;
        gap: 12px;
        margin-bottom: 8px;
      }

      .prop {
        margin-bottom: 0;

        .label {
          font-size: 12px;
          font-weight: 400;
          color: #666;
          line-height: 14px;
        }

        .value {
          font-size: 14px;
          font-weight: 600;
          color: #050708;
          line-height: 14px;
          white-space: nowrap;
          margin-top: 6px;
        }
      }

      .prop-ip {
        flex: 1;
        min-width: 0;

        .value {
          overflow: visible;
          text-overflow: clip;
        }
      }

      .prop-channel {
        flex: 0 0 auto;

        .value {
          text-align: right;
        }
      }

      .prop-rtsp {
        margin-bottom: 8px;
        min-width: 0;
        max-width: 100%;

        .rtsp-value-row {
          display: flex;
          align-items: center;
          gap: 4px;
          margin-top: 6px;
          min-width: 0;
          padding-right: 4px;
        }

        .rtsp-text {
          flex: 1;
          min-width: 0;
          font-size: 12px;
          font-weight: 500;
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
        }

        .copy-icon {
          flex-shrink: 0;
          cursor: pointer;
        }
      }
    }

    .btns {
      display: flex;
      position: absolute;
      left: 16px;
      bottom: 16px;
      margin-top: 20px;
      width: 200px;
      height: 28px;
      border-radius: 45px;
      justify-content: space-around;
      padding: 0 10px;
      align-items: center;
      border: 2px solid #266cfbff;
      z-index: 2;

      .btn {
        width: 28px;
        text-align: center;
        position: relative;
        cursor: pointer;

        &:before {
          content: '';
          display: block;
          position: absolute;
          width: 1px;
          height: 7px;
          background-color: #e2e2e2;
          left: 0;
          top: 9px;
        }

        &:first-child:before {
          display: none;
        }

        :deep(.anticon) {
          display: flex;
          align-items: center;
          justify-content: center;
          color: #87ceeb;
          transition: color 0.3s;
        }

        &:hover :deep(.anticon) {
          color: #5ba3f5;
        }
      }
    }
  }

  .channel-img {
    position: absolute;
    right: 6px;
    top: 0;

    img {
      cursor: pointer;
      width: 120px;
    }
  }
}
</style>
