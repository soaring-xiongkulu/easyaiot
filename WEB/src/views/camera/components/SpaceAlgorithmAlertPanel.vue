<template>
  <div class="space-alert-panel">
    <aside class="left-panel">
      <div class="panel-section">
        <div class="section-label">选择日期</div>
        <DatePicker
          v-model:value="selectedDate"
          value-format="YYYY-MM-DD"
          style="width: 100%"
          @change="handleDateChange"
        />
        <div v-if="dateHints.length" class="date-hints">
          <span
            v-for="d in dateHints.slice(0, 6)"
            :key="d.date"
            class="date-chip"
            :class="{ active: d.date === selectedDateStr }"
            @click="selectDate(d.date)"
          >
            {{ d.date.slice(5) }} ({{ d.count }})
          </span>
        </div>
      </div>

      <div class="panel-section alert-section">
        <div class="section-label">
          告警列表
          <span v-if="alertList.length" class="count-badge">{{ alertList.length }}</span>
          <Button
            v-if="showGalleryLink && selectedDateStr"
            type="link"
            size="small"
            class="link-action"
            @click="() => emit('view-gallery-date', selectedDateStr)"
          >
            查看当日抓拍图库
          </Button>
        </div>
        <Spin :spinning="loading">
          <div v-if="!alertList.length && !loading" class="empty-hint">
            <Empty description="该日暂无告警" :image="Empty.PRESENTED_IMAGE_SIMPLE" />
          </div>
          <div v-else class="alert-list">
            <div
              v-for="alert in alertList"
              :key="alert.id"
              class="alert-item"
              :class="{ active: selectedAlert?.id === alert.id }"
              @click="selectAlert(alert)"
            >
              <div class="alert-thumb">
                <img v-if="alert.image_url" :src="thumbUrl(alert.image_url)" alt="" />
                <span v-else-if="alert.image_status === 'pending'" class="media-pending">同步中</span>
                <PictureOutlined v-else class="no-img" />
              </div>
              <div class="alert-info">
                <div class="alert-event">
                  {{ formatAlertEvent(alert.event) }}
                  <Tag v-if="isPatrolAlert(alert)" color="purple" class="patrol-tag">巡检</Tag>
                </div>
                <div class="alert-time">{{ formatTime(alert.time) }}</div>
                <div class="alert-object">{{ alert.object || alert.device_name || '-' }}</div>
              </div>
            </div>
          </div>
        </Spin>
      </div>
    </aside>

    <main class="right-panel">
      <div v-if="selectedAlert" class="preview-section">
        <div class="preview-header">
          <div class="preview-header-main">
            <span class="preview-title">{{ formatAlertEvent(selectedAlert.event) }}</span>
            <span class="preview-time">{{ formatTime(selectedAlert.time) }}</span>
            <Tag v-if="selectedAlert.image_status === 'pending'" color="processing">图片同步中</Tag>
            <Tag v-if="selectedAlert.record_status === 'pending'" color="processing">事件片段生成中</Tag>
          </div>
          <div class="preview-actions">
            <Button
              v-if="showSnapLink && selectedAlert.time"
              @click="handleViewSnap"
            >
              <Icon icon="ant-design:picture-outlined" />
              查看算法抓拍
            </Button>
            <Button
              v-if="selectedAlert.device_id && selectedAlert.time"
              type="primary"
              size="middle"
              @click="handleViewRecord"
            >
              <Icon icon="ant-design:video-camera-outlined" />
              查看告警录像
            </Button>
          </div>
        </div>
        <div class="preview-image-wrap">
          <img
            v-if="selectedAlert.image_url"
            :src="thumbUrl(selectedAlert.image_url)"
            alt="告警图片"
            class="preview-image"
          />
          <Empty
            v-else
            :description="selectedAlert.image_status === 'pending' ? '告警已产生，图片正在从边缘节点同步' : '暂无告警图片'"
          />
        </div>
        <div class="preview-meta">
          <div class="meta-item">
            <span class="label">设备</span>
            <span>{{ selectedAlert.device_name || selectedAlert.device_id }}</span>
          </div>
          <div class="meta-item">
            <span class="label">告警对象</span>
            <span>{{ selectedAlert.object || '-' }}</span>
          </div>
          <div v-if="selectedAlert.region" class="meta-item">
            <span class="label">区域</span>
            <span>{{ selectedAlert.region }}</span>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<script lang="ts" setup>
import { computed, ref, watch } from 'vue';
import { DatePicker, Empty, Spin, Tag } from 'ant-design-vue';
import { PictureOutlined } from '@ant-design/icons-vue';
import dayjs from 'dayjs';
import { Button } from '@/components/Button';
import { Icon } from '@/components/Icon';
import { useMessage } from '@/hooks/web/useMessage';
import { queryAlarmList, queryAlertCountByDate } from '@/api/device/calculate';
import { resolveAlertImageDisplayUrl } from '@/utils/alertMinioImage';

export interface SpaceAlertItem {
  id: number;
  event?: string;
  object?: string;
  region?: string;
  time?: string;
  device_id?: string;
  device_name?: string;
  image_url?: string;
  image_status?: 'pending' | 'uploading' | 'ready' | 'failed';
  record_status?: 'not_applicable' | 'pending' | 'uploading' | 'ready' | 'failed';
  task_type?: string;
  information?: string;
}

defineOptions({ name: 'SpaceAlgorithmAlertPanel' });

const props = withDefaults(
  defineProps<{
    deviceId?: string;
    showGalleryLink?: boolean;
    showSnapLink?: boolean;
  }>(),
  {
    showGalleryLink: false,
    showSnapLink: false,
  },
);

const emit = defineEmits<{
  'view-gallery-date': [date: string];
  'view-snap': [alert: SpaceAlertItem];
  'view-record': [alert: SpaceAlertItem];
}>();

const { createMessage } = useMessage();

const selectedDate = ref<string>(dayjs().format('YYYY-MM-DD'));
const selectedDateStr = computed(() => selectedDate.value);
const alertList = ref<SpaceAlertItem[]>([]);
const selectedAlert = ref<SpaceAlertItem | null>(null);
const loading = ref(false);
const dateHints = ref<{ date: string; count: number }[]>([]);
let loadToken = 0;

function thumbUrl(url?: string) {
  return resolveAlertImageDisplayUrl(url);
}

function formatTime(time?: string, fmt = 'YYYY-MM-DD HH:mm:ss') {
  if (!time) return '-';
  return dayjs(time).format(fmt);
}

function formatAlertEvent(event?: string) {
  if (!event) return '未知告警';
  return event;
}

function isPatrolAlert(alert: SpaceAlertItem) {
  if (alert.task_type === 'patrol') return true;
  const info = alert.information;
  if (!info) return false;
  try {
    const parsed = typeof info === 'string' ? JSON.parse(info) : info;
    return parsed?.task_type === 'patrol';
  } catch {
    return false;
  }
}

function handleViewSnap() {
  const alert = selectedAlert.value;
  if (alert) emit('view-snap', alert);
}

function handleViewRecord() {
  const alert = selectedAlert.value;
  if (alert) emit('view-record', alert);
}

function selectDate(date: string) {
  if (!props.deviceId) return;
  selectedDate.value = date;
  void loadAlerts();
}

function handleDateChange() {
  if (!props.deviceId) return;
  void loadAlerts();
}

function selectAlert(alert: SpaceAlertItem) {
  selectedAlert.value = alert;
}

async function loadDateHints() {
  if (!props.deviceId) {
    dateHints.value = [];
    return;
  }
  try {
    const res = await queryAlertCountByDate({ device_id: props.deviceId });
    const list = res?.count_list || [];
    dateHints.value = list
      .filter((item: { value: string; count: number }) => item.value)
      .map((item: { value: string; count: number }) => ({
        date: String(item.value),
        count: item.count,
      }))
      .sort((a, b) => b.date.localeCompare(a.date));
    if (dateHints.value.length && !dateHints.value.some((d) => d.date === selectedDateStr.value)) {
      selectedDate.value = dateHints.value[0].date;
    }
  } catch (e) {
    console.error(e);
  }
}

async function loadAlerts() {
  if (!props.deviceId) {
    alertList.value = [];
    selectedAlert.value = null;
    return;
  }
  const token = ++loadToken;
  loading.value = true;
  selectedAlert.value = null;
  try {
    const begin = `${selectedDateStr.value} 00:00:00`;
    const end = `${selectedDateStr.value} 23:59:59`;
    const res = await queryAlarmList({
      device_id: props.deviceId,
      begin_datetime: begin,
      end_datetime: end,
      pageNo: 1,
      pageSize: 500,
    });
    if (token !== loadToken) return;
    alertList.value = res?.alert_list || [];
    if (alertList.value.length) {
      selectedAlert.value = alertList.value[0];
    }
  } catch (e) {
    if (token === loadToken) {
      console.error(e);
      createMessage.error('加载告警列表失败');
      alertList.value = [];
    }
  } finally {
    if (token === loadToken) loading.value = false;
  }
}

async function refresh() {
  await loadDateHints();
  await loadAlerts();
}

watch(
  () => props.deviceId,
  () => {
    void refresh();
  },
  { immediate: true },
);

defineExpose({ refresh });
</script>

<style lang="less" scoped>
.space-alert-panel {
  height: 100%;
  min-height: 0;
  display: flex;
  overflow: hidden;
}

.left-panel {
  width: 340px;
  flex-shrink: 0;
  background: #fff;
  border-right: 1px solid #f0f0f0;
  display: flex;
  flex-direction: column;
}

.panel-section {
  padding: 16px;
  border-bottom: 1px solid #f5f5f5;

  .section-label {
    font-size: 13px;
    font-weight: 500;
    color: #595959;
    margin-bottom: 10px;
    display: flex;
    align-items: center;
    gap: 6px;

    .count-badge {
      background: #f6ffed;
      color: #52c41a;
      font-size: 11px;
      padding: 0 6px;
      border-radius: 10px;
    }

    .link-action {
      margin-left: auto;
      padding: 0;
      height: auto;
    }
  }
}

.date-hints {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 10px;

  .date-chip {
    font-size: 12px;
    padding: 2px 8px;
    border-radius: 4px;
    background: #f5f5f5;
    cursor: pointer;

    &:hover,
    &.active {
      background: #f6ffed;
      color: #52c41a;
    }
  }
}

.alert-section {
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.alert-list {
  overflow-y: auto;
  max-height: calc(100vh - 280px);
}

.alert-item {
  display: flex;
  gap: 10px;
  padding: 10px;
  border-radius: 6px;
  cursor: pointer;
  margin-bottom: 4px;
  border: 1px solid transparent;

  &:hover {
    background: #fafafa;
  }

  &.active {
    background: #f6ffed;
    border-color: #b7eb8f;
  }

  .alert-thumb {
    width: 56px;
    height: 56px;
    flex-shrink: 0;
    border-radius: 4px;
    overflow: hidden;
    background: #f5f5f5;

    img {
      width: 100%;
      height: 100%;
      object-fit: cover;
    }

    .no-img {
      font-size: 24px;
      color: #d9d9d9;
      display: flex;
      align-items: center;
      justify-content: center;
      height: 100%;
    }

    .media-pending {
      display: flex;
      align-items: center;
      justify-content: center;
      height: 100%;
      color: #1677ff;
      font-size: 11px;
      white-space: nowrap;
    }
  }

  .alert-info {
    flex: 1;
    min-width: 0;

    .alert-event {
      font-size: 13px;
      font-weight: 500;
      color: #262626;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }

    .alert-time {
      font-size: 12px;
      color: #8c8c8c;
      margin-top: 2px;
    }

    .alert-object {
      font-size: 12px;
      color: #595959;
      margin-top: 2px;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
  }
}

.empty-hint {
  padding: 24px 0;
}

.right-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: #fff;
  min-width: 0;
  overflow: hidden;
}

.preview-section {
  flex: 1;
  padding: 20px 24px;
  overflow-y: auto;

  .preview-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    margin-bottom: 16px;

    .preview-header-main {
      display: flex;
      align-items: baseline;
      gap: 12px;
      min-width: 0;
    }

    .preview-actions {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      flex-shrink: 0;
    }

    .preview-title {
      font-size: 16px;
      font-weight: 600;
    }

    .preview-time {
      font-size: 13px;
      color: #8c8c8c;
    }
  }

  .preview-image-wrap {
    display: flex;
    justify-content: center;
    align-items: center;
    min-height: 280px;
    max-height: calc(100vh - 320px);
    background: #fafafa;
    border-radius: 8px;
    overflow: hidden;

    .preview-image {
      max-width: 100%;
      max-height: calc(100vh - 320px);
      object-fit: contain;
    }
  }

  .preview-meta {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 16px 24px;
    margin-top: 12px;
    font-size: 13px;

    .meta-item {
      .label {
        color: #8c8c8c;
        margin-right: 6px;
      }
    }
  }
}
</style>
