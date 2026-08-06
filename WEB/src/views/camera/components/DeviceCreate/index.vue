<template>
  <div class="device-create">
    <PageHeader class="dc-header" title="添加设备" @back="handleCancel">
      <template #extra>
        <Button @click="handleCancel">取消</Button>
      </template>
    </PageHeader>

    <Tabs
      v-model:activeKey="activeTab"
      :animated="{ inkBar: true, tabPane: true }"
      :destroy-inactive-tab-pane="true"
      class="dc-tabs"
      @change="handleKindTabChange"
    >
      <TabPane key="camera" tab="IPC">
        <Tabs
          v-model:activeKey="selection.method"
          :animated="{ inkBar: true, tabPane: true }"
          class="dc-method-tabs"
          @change="handleMethodTabChange"
        >
          <TabPane key="onvif" tab="ONVIF">
            <div class="dc-pane">
              <div class="dc-body">
                <OnvifScanPanel class="panel-host" @success="handlePanelSuccess" />
              </div>
            </div>
          </TabPane>
          <TabPane key="segment_scan" tab="跨网段扫描">
            <div class="dc-pane">
              <div class="dc-body">
                <SegmentScanPanel class="panel-host" mode="camera" @success="handlePanelSuccess" />
              </div>
            </div>
          </TabPane>
          <TabPane key="manual" tab="手动填写">
            <div class="dc-pane">
              <div class="dc-body">
                <DirectRtspPanel class="panel-host" @success="handlePanelSuccess" />
              </div>
            </div>
          </TabPane>
        </Tabs>
      </TabPane>

      <TabPane key="nvr" tab="NVR">
        <Tabs
          v-model:activeKey="selection.method"
          :animated="{ inkBar: true, tabPane: true }"
          class="dc-method-tabs"
          @change="handleMethodTabChange"
        >
          <TabPane key="segment_scan" tab="跨网段扫描">
            <div class="dc-pane">
              <div class="dc-body">
                <SegmentScanPanel class="panel-host" mode="nvr" @success="handlePanelSuccess" />
              </div>
            </div>
          </TabPane>
          <TabPane key="manual" tab="手动填写">
            <div class="dc-pane">
              <div class="dc-body">
                <NvrManualPanel class="panel-host" @success="handlePanelSuccess" />
              </div>
            </div>
          </TabPane>
        </Tabs>
      </TabPane>

      <TabPane v-if="gb28181Enabled" key="gb28181" tab="国标">
        <div class="dc-pane">
          <div class="dc-body">
            <Gb28181AccessPanel class="panel-host" />
          </div>
        </div>
      </TabPane>

      <TabPane key="rtc" tab="RTC 平台">
        <div class="dc-pane">
          <div class="dc-body">
            <RtcPlatformPanel class="panel-host" @success="handlePanelSuccess" />
          </div>
        </div>
      </TabPane>
    </Tabs>
  </div>
</template>

<script lang="ts" setup>
import { reactive, ref, watch } from 'vue';
import { PageHeader, Tabs } from 'ant-design-vue';
import { Button } from '@/components/Button';
import {
  getDefaultMethodForKind,
  type CameraBrand,
  type CreateMethod,
  type DeviceKind,
} from '@/views/camera/utils/deviceCreateOptions';
import OnvifScanPanel from './panels/OnvifScanPanel.vue';
import SegmentScanPanel from './panels/SegmentScanPanel.vue';
import DirectRtspPanel from './panels/DirectRtspPanel.vue';
import NvrManualPanel from './panels/NvrManualPanel.vue';
import Gb28181AccessPanel from './panels/Gb28181AccessPanel.vue';
import RtcPlatformPanel from './panels/RtcPlatformPanel.vue';
import { isGb28181Enabled } from '@/utils/deployProfile';

const TabPane = Tabs.TabPane;

const gb28181Enabled = isGb28181Enabled();

const props = defineProps<{
  initialKind?: DeviceKind;
  initialMethod?: CreateMethod;
  initialBrand?: CameraBrand;
  /** 初始 Tab：camera | nvr | gb28181 | rtc */
  initialTab?: string;
}>();

const emit = defineEmits<{ back: []; success: [] }>();

const activeTab = ref(props.initialTab || props.initialKind || 'camera');

const kindMethodPrefs = reactive<Record<DeviceKind, CreateMethod>>({
  camera: props.initialMethod || getDefaultMethodForKind('camera'),
  nvr: getDefaultMethodForKind('nvr'),
  gb28181: 'gb_access',
});

const selection = reactive({
  kind: (props.initialKind || 'camera') as DeviceKind,
  method: kindMethodPrefs[props.initialKind || 'camera'],
});

function syncSelectionFromPrefs(kind: DeviceKind) {
  selection.kind = kind;
  selection.method = kindMethodPrefs[kind];
}

function handleKindTabChange(tab: string | number) {
  const key = String(tab);
  if (key === 'rtc' || key === 'gb28181') {
    activeTab.value = key;
    return;
  }
  syncSelectionFromPrefs(key as DeviceKind);
  activeTab.value = key;
}

function handleMethodTabChange(method: string | number) {
  selection.method = method as CreateMethod;
  kindMethodPrefs[selection.kind] = selection.method;
}

function handleCancel() {
  emit('back');
}

function handlePanelSuccess() {
  emit('success');
}

watch(
  () => props.initialTab,
  (v) => {
    if (v) activeTab.value = v;
  },
);

watch(
  () => props.initialKind,
  (v) => {
    if (v) {
      if (!gb28181Enabled && v === 'gb28181') {
        syncSelectionFromPrefs('camera');
        return;
      }
      syncSelectionFromPrefs(v);
      if (!props.initialTab) activeTab.value = v;
    }
  },
);
</script>

<style lang="less" scoped>
.device-create {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 168px);
  min-height: 420px;
  overflow: hidden;
  background: #fff;
  border-radius: 8px;

  .dc-header {
    flex-shrink: 0;
    padding: 8px 16px;
    margin: 0;
    border-bottom: 1px solid #f0f0f0;

    :deep(.ant-page-header-heading) {
      align-items: center;
    }

    :deep(.ant-page-header-heading-title) {
      font-size: 16px;
      line-height: 32px;
    }
  }

  .dc-tabs {
    flex: 1;
    min-height: 0;
    display: flex;
    flex-direction: column;

    :deep(.ant-tabs-nav) {
      flex-shrink: 0;
      margin: 0 16px;
      padding-top: 8px;
    }

    :deep(.ant-tabs-content-holder) {
      flex: 1;
      min-height: 0;
    }

    :deep(.ant-tabs-content) {
      height: 100%;
    }

    :deep(> .ant-tabs-content-holder > .ant-tabs-content > .ant-tabs-tabpane) {
      height: 100%;
    }
  }

  .dc-method-tabs {
    height: 100%;
    display: flex;
    flex-direction: column;

    :deep(.ant-tabs-nav) {
      margin: 0 0 12px;
      padding-top: 0;
    }

    :deep(.ant-tabs-content-holder) {
      flex: 1;
      min-height: 0;
    }

    :deep(.ant-tabs-content) {
      height: 100%;
    }

    :deep(.ant-tabs-tabpane) {
      height: 100%;
    }
  }

  .dc-pane {
    height: 100%;
    display: flex;
    flex-direction: column;
    padding: 0 0 12px;
  }

  .dc-body {
    flex: 1;
    min-height: 0;
    overflow: hidden;
    padding: 12px;
    border: 1px solid #f0f0f0;
    border-radius: 6px;
    background: #fff;
  }

  .panel-host {
    height: 100%;
    min-height: 0;
  }
}
</style>
