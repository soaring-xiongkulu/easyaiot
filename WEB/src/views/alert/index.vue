<template>
  <div class="alert-page">
    <div class="alert-tab">
      <Tabs
        :activeKey="state.activeKey"
        :animated="{ inkBar: true, tabPane: true }"
        :destroyInactiveTabPane="true"
        :tabBarGutter="60"
        @tabClick="handleTabClick"
      >
        <TabPane v-if="!edgeStandalone" key="1" tab="地图分布">
          <AlertMapView
            ref="alertMapViewRef"
            @view-image="handleCardViewImage"
            @view-video="handleCardViewVideo"
            @set-location="openDeviceLocationDrawer"
            @play="handleMapDevicePlay"
            @view="handleMapDeviceView"
            @edit="handleMapDeviceEdit"
          />
        </TabPane>
        <TabPane key="2" tab="告警事件">
          <!-- 表格模式 -->
          <BasicTable v-if="viewMode === 'table'" @register="registerTable">
            <template #toolbar>
              <AlertListToolbar
                @toggle-view="handleToggleViewMode"
                @clear-all="handleClearAllAlerts"
              />
            </template>
            <template #bodyCell="{ column, record }">
              <template v-if="column.key === 'device_id'">
                <span style="cursor: pointer" @click="handleCopy(record['device_id'])"><Icon
                  icon="tdesign:copy-filled" color="#4287FCFF"/> {{ formatDeviceId(record['device_id']) }}</span>
              </template>
              <template v-if="column.key === 'device_name'">
                <span style="cursor: pointer" @click="handleCopy(record['device_name'])"><Icon
                  icon="tdesign:copy-filled" color="#4287FCFF"/> {{ record['device_name'] }}</span>
              </template>
              <template v-if="column.key === 'task_type'">
                <a-tag :color="getTaskTypeColor(record['task_type'])">
                  {{ getTaskTypeText(record['task_type']) }}
                </a-tag>
              </template>
              <template v-if="column.dataIndex === 'action'">
                <TableAction
                  :actions="[
                    {
                      icon: 'ion:image-sharp',
                      tooltip: { title: '查看告警图片', placement: 'top' },
                      onClick: handleViewImage.bind(null, record),
                    },
                    {
                      icon: 'icon-park-outline:video',
                      tooltip: { title: '查看告警录像', placement: 'top' },
                      onClick: handleViewVideo.bind(null, record),
                    },
                  ]"
                />
              </template>
            </template>
          </BasicTable>

          <!-- 卡片模式（默认） -->
          <div v-else class="card-mode-wrapper">
            <AlertCards
              :api="queryAlarmList"
              :params="params"
              @getMethod="getMethod"
              @viewImage="handleCardViewImage"
              @viewVideo="handleCardViewVideo"
            >
              <template #header>
                <AlertListToolbar
                  @toggle-view="handleToggleViewMode"
                  @clear-all="handleClearAllAlerts"
                />
              </template>
            </AlertCards>
          </div>
        </TabPane>
        <TabPane v-if="showTicketTab" key="3" tab="告警工单">
          <AlarmTicket />
        </TabPane>
      </Tabs>
    </div>

    <ImageModal @register="registerImageModal" />
    <FaceAlertModal @register="registerFaceAlertModal" />
    <PlateAlertModal @register="registerPlateAlertModal" />
    <DialogPlayer @register="registerVideoModal" />
    <DeviceLocationDrawer @register="registerLocationDrawer" @success="handleLocationDrawerSuccess" />
  </div>
</template>
<script lang="ts" setup name="noticeSetting">
import { nextTick, reactive, ref, onMounted, onActivated, watch } from 'vue';
import { TabPane, Tabs } from 'ant-design-vue';
import { BasicTable, TableAction, useTable } from '@/components/Table';
import { useMessage } from '@/hooks/web/useMessage';
import { getBasicColumns, getFormConfig } from './Data';
import { useRouter } from 'vue-router';
import { queryAlarmList, clearAllAlerts } from '@/api/device/calculate';
import { Icon } from '@/components/Icon';
import AlertCards from '@/views/alert/components/AlertCards/index.vue';
import AlertMapView from '@/views/alert/components/AlertMapView/index.vue';
import AlertListToolbar from '@/views/alert/components/AlertListToolbar.vue';
import ImageModal from '@/views/alert/components/ImageModal/index.vue';
import FaceAlertModal from '@/views/alert/components/FaceAlertModal/index.vue';
import PlateAlertModal from '@/views/alert/components/PlateAlertModal/index.vue';
import DialogPlayer from '@/components/VideoPlayer/DialogPlayer.vue';
import { useModal } from '@/components/Modal';
import {
  mergeAlertFetchParams,
  normalizeAlertQueryParams,
  snapshotAlertFilters,
} from '@/views/alert/utils/alertQueryParams';
import DeviceLocationDrawer from '@/views/camera/components/DeviceLocationDrawer/index.vue';
import { canSetDeviceLocation } from '@/views/camera/utils/deviceLocation';
import { getDeviceInfo } from '@/api/device/camera';
import { openDeviceInDialogPlayer } from '@/views/camera/utils/devicePlay';
import { playAlertRecordInModal } from '@/utils/alertRecordPlayback';
import { hasAlertFaceMatch, hasAlertPlateMatch, isSnapAlertTask } from '@/views/alert/alertDisplay';
import { isEdgeStandaloneDeployProfile, isFlowTicketEnabled } from '@/utils/deployProfile';
import AlarmTicket from '@/views/alert/components/AlarmTicket/index.vue';

const router = useRouter();
const edgeStandalone = isEdgeStandaloneDeployProfile();
const [registerImageModal, { openModal: openImageModal }] = useModal();
const [registerFaceAlertModal, { openModal: openFaceAlertModal }] = useModal();
const [registerPlateAlertModal, { openModal: openPlateAlertModal }] = useModal();
const [registerVideoModal, { openModal: openVideoModal, closeModal: closeVideoModal, setModalProps: setVideoModalProps }] = useModal();
const [registerLocationDrawer, { openModal: openLocationModal }] = useModal();

defineOptions({ name: 'Alarm' });

const ALERT_TAB_KEYS = {
  MAP: '1',
  EVENTS: '2',
  TICKET: '3',
} as const;

const ALERT_TAB_ID_SET = new Set<string>(Object.values(ALERT_TAB_KEYS));

const viewMode = ref<'table' | 'card'>('card');

// mini / edge 单机不部署 iot-flow 工作流服务，隐藏告警工单 Tab
const showTicketTab = isFlowTicketEnabled();

const state = reactive({
  activeKey: edgeStandalone ? ALERT_TAB_KEYS.EVENTS : ALERT_TAB_KEYS.MAP,
});

const params = ref<Record<string, any>>({});
const alertMapViewRef = ref<InstanceType<typeof AlertMapView>>();

let cardListReload = () => {};

const lastTableFilterParams = ref<Record<string, any>>({});

function normalizeAlertRouteTab(tab: unknown): string {
  if (tab === 'map') return ALERT_TAB_KEYS.MAP;
  if (tab === 'events') return ALERT_TAB_KEYS.EVENTS;
  if (tab === 'ticket' && showTicketTab) return ALERT_TAB_KEYS.TICKET;
  const tabStr = String(tab);
  if (ALERT_TAB_ID_SET.has(tabStr) && (tabStr !== ALERT_TAB_KEYS.TICKET || showTicketTab)) return tabStr;
  return edgeStandalone ? ALERT_TAB_KEYS.EVENTS : ALERT_TAB_KEYS.MAP;
}

async function activateMapTab() {
  state.activeKey = ALERT_TAB_KEYS.MAP;
  await nextTick();
  const filters = lastTableFilterParams.value;
  if (Object.keys(filters).length) {
    await alertMapViewRef.value?.applyFilters?.(filters);
  } else {
    await alertMapViewRef.value?.init?.();
  }
  await alertMapViewRef.value?.resizeMap?.();
}

function handleTabClick(activeKey: string) {
  state.activeKey = activeKey;
  // 同步到 URL（query.tab）：从流程设计等子页面返回时可恢复所在的 Tab，而不是落回默认地图分布
  void router.replace({ query: { ...router.currentRoute.value.query, tab: activeKey } });
  if (activeKey === ALERT_TAB_KEYS.MAP) {
    void activateMapTab();
  }
}

// 人脸/车牌轨迹入口跳转：URL 携带 trajectory_person / trajectory_plate 时，
// 无论当前在哪个 tab 都强制切到地图分布（轨迹加载由 AlertMapPanel 自身的 route.query watch 完成）
watch(
  () => [
    router.currentRoute.value.query.trajectory_person,
    router.currentRoute.value.query.trajectory_plate,
  ],
  ([person, plate]) => {
    if (!person && !plate) return;
    if (state.activeKey !== ALERT_TAB_KEYS.MAP) {
      state.activeKey = ALERT_TAB_KEYS.MAP;
      void activateMapTab();
    }
  },
);

const refreshData = () => {
  const route = router.currentRoute.value;
  const rawTab = route.query.tab ?? (route.query.view === 'map' ? ALERT_TAB_KEYS.MAP : undefined);
  const tab = rawTab
    ? normalizeAlertRouteTab(rawTab)
    : (edgeStandalone ? ALERT_TAB_KEYS.EVENTS : ALERT_TAB_KEYS.MAP);
  if (tab === ALERT_TAB_KEYS.MAP) {
    void activateMapTab();
    return;
  }
  state.activeKey = tab;
  if (tab === ALERT_TAB_KEYS.TICKET) {
    // 告警工单 Tab：子 Tab 由 AlarmTicket 自行恢复，无需加载事件列表
    return;
  }
  if (route.query.task_name) {
    params.value = { task_name: route.query.task_name };
    setTimeout(() => {
      const form = getForm();
      if (form) {
        form.setFieldsValue({ task_name: route.query.task_name });
      }
      reload();
      cardListReload();
    }, 100);
  } else {
    reload();
    cardListReload();
  }
};

onMounted(() => {
  refreshData();
});

onActivated(() => {
  refreshData();
});

function getMethod(m: any) {
  cardListReload = m;
}

function handleToggleViewMode() {
  viewMode.value = viewMode.value === 'card' ? 'table' : 'card';
  if (viewMode.value === 'table') {
    reload();
  } else {
    cardListReload();
  }
}

function handleCardViewImage(record) {
  handleViewImage(record);
}

function handleCardViewVideo(record) {
  handleViewVideo(record);
}

function openDeviceLocationDrawer(record: { id?: string; name?: string; device_kind?: string }) {
  if (!canSetDeviceLocation(record)) return;
  openLocationModal(true, { deviceId: record.id, record });
}

function handleLocationDrawerSuccess() {
  alertMapViewRef.value?.refresh?.();
}

async function handleMapDevicePlay(record: { id?: string }) {
  if (!record?.id) return;
  try {
    const info = await getDeviceInfo(record.id);
    openDeviceInDialogPlayer(openVideoModal, info);
  } catch {
    createMessage.error('加载设备信息失败');
  }
}

function handleMapDeviceView(record: { id?: string }) {
  if (!record?.id) return;
  router.push({ path: '/camera', query: { tab: '3', highlight: record.id } });
}

function handleMapDeviceEdit(record: { id?: string }) {
  if (!record?.id) return;
  router.push({ path: '/camera', query: { tab: '3', edit: record.id } });
}

const { createMessage, createConfirm } = useMessage();
const [
  registerTable,
  {
    reload,
    getForm,
  },
] = useTable({
  canResize: true,
  showIndexColumn: false,
  title: '告警事件列表',
  api: queryAlarmList,
  columns: getBasicColumns(),
  useSearchForm: true,
  showTableSetting: false,
  formConfig: getFormConfig(),
  fetchSetting: {
    listField: 'alert_list',
    totalField: 'total',
    pageField: 'pageNo',
    sizeField: 'pageSize',
  },
  beforeFetch: (p) => {
    const route = router.currentRoute.value;
    const merged = mergeAlertFetchParams(
      p as Record<string, unknown>,
      lastTableFilterParams.value,
    );
    const normalized = normalizeAlertQueryParams(
      merged,
      route.query.task_name as string | undefined,
    );
    lastTableFilterParams.value = snapshotAlertFilters(normalized);
    return normalized;
  },
  rowKey: 'id',
});

const handleViewImage = (record: Record<string, any>) => {
  const minioUrl = record['image_url'];
  if (minioUrl == null || String(minioUrl).trim() === '') {
    createMessage.warn('告警图片不存在');
    return;
  }
  // 关联人脸的告警走人脸专属弹框（全景图 + 人脸头像 + 姓名/行为/地点/事件），
  // 关联车牌的告警走车牌专属弹框（全景图 + 车牌号/车主/置信度 + 轨迹入口），
  // 其余告警保持原有图片弹框
  if (hasAlertFaceMatch(record)) {
    openFaceAlertModal(true, { record });
    return;
  }
  if (hasAlertPlateMatch(record)) {
    openPlateAlertModal(true, { record });
    return;
  }
  openImageModal(true, {
    image_url: minioUrl,
    information: record.information,
    event: record.event,
  });
};

let lastVideoErrorTime = 0;
let lastVideoErrorMsg = '';

const handleViewVideo = async (record) => {
  if (isSnapAlertTask(record)) {
    createMessage.warn('抓拍任务无告警录像');
    return;
  }
  if (!record['device_id'] || !record['time']) {
    createMessage.warn('缺少必要信息：设备ID或告警时间');
    return;
  }

  try {
    const ok = await playAlertRecordInModal(
      { openModal: openVideoModal, closeModal: closeVideoModal, setModalProps: setVideoModalProps },
      {
        id: record['id'],
        device_id: record['device_id'],
        time: record['time'],
        record_path: record['record_path'],
      },
    );
    if (ok) {
      lastVideoErrorTime = 0;
      lastVideoErrorMsg = '';
    } else {
      showVideoErrorOnce('暂未找到该时间段的录像文件，请稍后再试');
    }
  } catch (error: any) {
    console.error('查询录像失败:', error);
    const errorData = error?.response?.data || error?.data;
    const errorMsg = errorData?.message || error?.message || '查询录像失败，请稍后重试';
    showVideoErrorOnce(errorMsg);
  }
};

function showVideoErrorOnce(message: string) {
  const now = Date.now();
  if (now - lastVideoErrorTime < 3000 && lastVideoErrorMsg === message) {
    return;
  }
  lastVideoErrorTime = now;
  lastVideoErrorMsg = message;
  createMessage.warn(message);
}

function formatDeviceId(deviceId: string | null | undefined): string {
  if (!deviceId) return '-';
  if (deviceId.length <= 8) return deviceId;
  return deviceId.substring(0, 8) + '...';
}

function getTaskTypeText(taskType: string | null | undefined): string {
  if (!taskType) return '实时';
  if (taskType === 'snap' || taskType === 'snapshot') {
    return '抓拍';
  } else if (taskType === 'realtime') {
    return '实时';
  }
  return taskType;
}

function getTaskTypeColor(taskType: string | null | undefined): string {
  if (!taskType) return 'blue';
  if (taskType === 'snap' || taskType === 'snapshot') {
    return 'green';
  } else if (taskType === 'realtime') {
    return 'blue';
  }
  return 'default';
}

async function handleCopy(record: object) {
  if (navigator.clipboard) {
    await navigator.clipboard.writeText(record);
  } else {
    const textarea = document.createElement('textarea');
    textarea.value = record;
    document.body.appendChild(textarea);
    textarea.select();
    document.execCommand('copy');
    document.body.removeChild(textarea);
  }
  createMessage.success('复制成功');
}

const handleClearAllAlerts = () => {
  createConfirm({
    title: '清空告警',
    iconType: 'warning',
    content: '确定要清空所有告警记录吗？此操作不可恢复！',
    async onOk() {
      try {
        await clearAllAlerts();
        createMessage.success('清空告警成功');
        reload();
        cardListReload();
        alertMapViewRef.value?.refresh?.();
      } catch (error: any) {
        const errorMsg =
          error?.response?.data?.msg ||
          error?.response?.data?.message ||
          error?.message ||
          '清空告警失败，请稍后重试';
        createMessage.error(errorMsg);
      }
    },
  });
};
</script>

<style scoped lang="less">
.alert-page {
  min-height: 0;
  background: #ffffff;
}

.alert-tab {
  padding: 0;

  :deep(.ant-tabs-nav) {
    padding: 5px 0 0 25px;
  }

  :deep(.ant-tabs) {
    background-color: #ffffff;
  }
}

.card-mode-wrapper {
  min-height: 0;
}
</style>
