<script lang="ts" setup>
import { computed, ref } from 'vue';
import {
  CheckCircleFilled,
  CloseCircleFilled,
  CloseOutlined,
  DownOutlined,
  UpOutlined,
} from '@ant-design/icons-vue';
import { Button } from '@/components/Button';
import { copyText } from '@/utils/copyTextToClipboard';
import type { StorageStackCheckResult } from '@/api/device/node';
import { NODE_TERM } from '../../utils/constants';
import { formatDeployLog, stepStatusLabel } from '../../utils/deployLog';

defineOptions({ name: 'StorageStackCheckResult' });

const props = defineProps<{ result: StorageStackCheckResult }>();
const emit = defineEmits<{ close: [] }>();
const detailExpanded = ref(false);

type OverallTone = 'success' | 'warning' | 'info' | 'error';

const overall = computed(() => {
  const r = props.result;
  if (!r.success) {
    return { tone: 'error' as OverallTone, badge: '检测失败', title: r.message || '无法完成远程检测' };
  }
  if (r.deployed) {
    return { tone: 'success' as OverallTone, badge: '已就绪', title: r.message || 'NFS 服务端与挂载均已就绪' };
  }
  if (r.cephHealthy || r.nfsHealthy || r.osdRunning || r.mountReady) {
    return { tone: 'warning' as OverallTone, badge: '部分就绪', title: r.message || `${NODE_TERM.storageService}未完整就绪` };
  }
  return { tone: 'info' as OverallTone, badge: '未部署', title: r.message || `可进行 ${NODE_TERM.storageService} ${NODE_TERM.deploy}` };
});

const badgeClass = computed(() => {
  const tone = overall.value.tone;
  if (tone === 'success') return 'node-meta-badge--readiness-ready';
  if (tone === 'warning') return 'node-meta-badge--readiness-pending';
  if (tone === 'info') return 'node-meta-badge--status-pending';
  return 'node-meta-badge--status-offline';
});

const serviceCards = computed(() => {
  const r = props.result;
  const nfsHealthy = !!(r.nfsHealthy ?? r.cephHealthy);
  const portOk = !!(r.nfsPortOk ?? r.osdRunning);
  return [
    { key: 'server', label: 'NFS 服务端', ok: nfsHealthy },
    { key: 'port', label: '2049 端口', ok: portOk },
    { key: 'export', label: 'Export / 子目录', ok: !!r.poolExists },
    { key: 'mount', label: '客户端挂载', ok: !!r.mountReady },
  ];
});

const logText = computed(() => formatDeployLog(props.result.steps || []));

function handleCopyLog() {
  if (!logText.value.trim()) return;
  copyText(logText.value, '检测日志已复制');
}
</script>

<template>
  <div class="media-check" :class="`media-check--${overall.tone}`">
    <div class="media-check__hero">
      <div class="media-check__hero-main">
        <span class="node-meta-badge" :class="badgeClass">{{ overall.badge }}</span>
        <p class="media-check__title">{{ overall.title }}</p>
      </div>
      <button type="button" class="media-check__close" aria-label="关闭检测结果" @click="emit('close')">
        <CloseOutlined />
      </button>
    </div>

    <div class="media-check__section">
      <div class="media-check__section-title">NFS 组件</div>
      <div class="media-check__grid media-check__grid--services">
        <div
          v-for="item in serviceCards"
          :key="item.key"
          class="media-check-card"
          :class="item.ok ? 'is-ok' : 'is-fail'"
        >
          <div class="media-check-card__head">
            <CheckCircleFilled v-if="item.ok" class="media-check-card__icon" />
            <CloseCircleFilled v-else class="media-check-card__icon" />
            <div class="media-check-card__meta">
              <span class="media-check-card__name">{{ item.label }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div v-if="logText.trim()" class="media-check__log">
      <div class="media-check__log-header">
        <button type="button" class="media-check__log-toggle" @click="detailExpanded = !detailExpanded">
          <span>检测明细</span>
          <UpOutlined v-if="detailExpanded" />
          <DownOutlined v-else />
        </button>
        <Button size="small" @click="handleCopyLog">复制日志</Button>
      </div>
      <pre v-show="detailExpanded" class="media-check__log-body">{{ logText }}</pre>
    </div>
  </div>
</template>

<style lang="less" scoped>
@import '../../utils/theme.less';
@import '../../utils/node-badge.less';
@import '../../utils/setup-panel.less';

.media-check {
  .setup-section-card();
  margin-top: 12px;
  padding: 16px 20px;
  border-left-width: 3px;
  border-left-style: solid;

  &--success { border-left-color: #d9f7be; }
  &--warning { border-left-color: #ffe7ba; }
  &--info { border-left-color: #adc6ff; }
  &--error { border-left-color: #ffccc7; }
}

.media-check__hero {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 14px;
  padding-bottom: 14px;
  border-bottom: 1px solid @node-border-light;
}

.media-check__title {
  margin: 10px 0 0;
  font-size: @node-font-body;
  line-height: 1.65;
  color: @node-text-body;
}

.media-check__close {
  flex-shrink: 0;
  width: 28px;
  height: 28px;
  border: none;
  border-radius: 6px;
  background: transparent;
  color: @node-text-muted;
  cursor: pointer;
}

.media-check__section-title {
  margin-bottom: 10px;
  font-size: @node-font-caption;
  font-weight: 500;
  color: @node-text-muted;
}

.media-check__grid--services {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: 8px;
}

.media-check-card {
  padding: 10px 12px;
  border-radius: @node-radius;
  border: 1px solid @node-border-light;
  background: #fff;
}

.media-check-card__head {
  display: flex;
  align-items: center;
  gap: 8px;
}

.media-check-card__icon {
  font-size: 16px;
  .is-ok & { color: #52c41a; }
  .is-fail & { color: #ff4d4f; }
}

.media-check__log {
  margin-top: 14px;
  padding-top: 14px;
  border-top: 1px dashed @node-border-light;
}

.media-check__log-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.media-check__log-toggle {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 0;
  border: none;
  background: none;
  cursor: pointer;
}

.media-check__log-body {
  margin: 10px 0 0;
  padding: 12px 14px;
  max-height: 280px;
  overflow: auto;
  border: 1px solid #d9d9d9;
  background: #f5f5f5;
  font-family: Consolas, Monaco, monospace;
  font-size: 13px;
  white-space: pre-wrap;
}
</style>
