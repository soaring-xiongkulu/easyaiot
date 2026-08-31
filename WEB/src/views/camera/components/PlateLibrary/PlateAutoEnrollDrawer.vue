<template>
  <BasicDrawer
    v-bind="$attrs"
    @register="register"
    width="900"
    placement="right"
    :showFooter="true"
    :showCancelBtn="false"
    :showOkBtn="false"
  >
    <template #footer>
      <div class="footer-buttons">
        <Button @click="closeDrawer">关闭</Button>
        <Button v-if="!taskStatus?.is_running" :loading="saving" @click="handleSave">保存配置</Button>
        <Button
          v-if="!taskStatus?.is_running"
          type="primary"
          :loading="starting"
          @click="handleStart"
        >
          开启摄像头自动录入
        </Button>
        <Button v-else danger type="primary" :loading="stopping" @click="handleStop">
          关闭摄像头自动录入
        </Button>
      </div>
    </template>

    <div v-if="library" class="auto-enroll-drawer">
      <a-alert
        type="info"
        show-icon
        :closable="false"
        message="摄像头自动录入"
        description="绑定摄像头后，系统为车辆生成 VID 并记录轨迹。新车辆默认进入待入库工作台，不会直接修改正式车牌库。"
        class="tip-alert"
      />

      <div v-if="taskStatus?.is_running" class="status-panel running">
        <a-badge status="processing" text="摄像头自动录入运行中" />
        <div class="status-grid">
          <div class="status-item">
            <span class="label">新 VID</span>
            <span class="value">{{ taskStatus.candidate_count ?? 0 }}</span>
          </div>
          <div class="status-item">
            <span class="label">重复轨迹</span>
            <span class="value">{{ taskStatus.duplicate_count ?? 0 }}</span>
          </div>
          <div class="status-item">
            <span class="label">质量拒绝</span>
            <span class="value">{{ taskStatus.rejected_count ?? 0 }}</span>
          </div>
          <div class="status-item">
            <span class="label">到期时间</span>
            <span class="value">{{ formatTime(taskStatus.expires_at) }}</span>
          </div>
        </div>
      </div>

      <BasicForm @register="registerForm" />
    </div>
  </BasicDrawer>
</template>

<script lang="ts" setup>
import { onUnmounted, ref } from 'vue';
import { BasicDrawer, useDrawerInner } from '@/components/Drawer';
import { BasicForm, useForm } from '@/components/Form';
import { useMessage } from '@/hooks/web/useMessage';
import { getDeviceList } from '@/api/device/camera';
import { Button } from '@/components/Button'
import {
getPlateAutoEnrollTask,
  isAutoEnrollConfigError,
  parsePlateApiError,
  savePlateAutoEnrollConfig,
  startPlateAutoEnroll,
  stopPlateAutoEnroll,
  type PlateAutoEnrollTask,
  type PlateLibrary,
} from '@/api/device/plate_library';

defineOptions({ name: 'PlateAutoEnrollDrawer' });

const emit = defineEmits(['success', 'register']);
const { createMessage } = useMessage();

const library = ref<PlateLibrary | null>(null);
const taskStatus = ref<PlateAutoEnrollTask | null>(null);
const saving = ref(false);
const starting = ref(false);
const stopping = ref(false);
const deviceOptions = ref<Array<{ label: string; value: string }>>([]);
let statusTimer: ReturnType<typeof setInterval> | null = null;

function clearStatusTimer() {
  if (statusTimer) {
    clearInterval(statusTimer);
    statusTimer = null;
  }
}

function startStatusTimer() {
  clearStatusTimer();
  statusTimer = setInterval(() => {
    if (taskStatus.value?.is_running) {
      loadTaskConfig();
    } else {
      clearStatusTimer();
    }
  }, 5000);
}

onUnmounted(clearStatusTimer);

function formatTime(val?: string) {
  if (!val) return '-';
  try {
    return new Date(val).toLocaleString();
  } catch {
    return val;
  }
}

const numberFieldStyle = { width: '160px' };

const [registerForm, { setFieldsValue, validate, updateSchema, resetFields }] = useForm({
  labelWidth: 96,
  baseColProps: { span: 24 },
  schemas: [
    {
      field: 'device_ids',
      label: '绑定摄像头',
      component: 'Select',
      required: true,
      itemProps: { class: 'form-item-device-ids' },
      componentProps: {
        placeholder: '请选择摄像头',
        mode: 'multiple',
        showSearch: true,
        allowClear: true,
        maxTagCount: 2,
        maxTagPlaceholder: (omitted: unknown[]) => `+${omitted.length}`,
        options: deviceOptions,
        style: { width: '100%', maxWidth: '400px' },
        filterOption: (input: string, option: any) =>
          (option?.label ?? '').toLowerCase().includes(input.toLowerCase()),
      },
    },
    {
      field: 'duration_minutes',
      label: '开启时长',
      component: 'InputNumber',
      required: true,
      defaultValue: 60,
      colProps: { span: 12 },
      componentProps: {
        min: 1,
        max: 1440,
        precision: 0,
        addonAfter: '分钟',
        style: numberFieldStyle,
        placeholder: '如 60',
      },
      helpMessage: '到期后自动停止',
    },
    {
      field: 'capture_interval_sec',
      label: '抓帧间隔',
      component: 'InputNumber',
      required: true,
      defaultValue: 5,
      colProps: { span: 12 },
      componentProps: {
        min: 2,
        max: 300,
        precision: 0,
        addonAfter: '秒',
        style: numberFieldStyle,
        placeholder: '如 5',
      },
      helpMessage: '两次抓帧之间的间隔',
    },
  ],
  showActionButtonGroup: false,
});

async function loadDevices() {
  const response = await getDeviceList({ pageNo: 1, pageSize: 1000 });
  const list = response?.list || response?.data?.list || response?.data || [];
  deviceOptions.value = (Array.isArray(list) ? list : []).map((item: any) => ({
    label: item.name || item.id,
    value: item.id,
  }));
  updateSchema([
    {
      field: 'device_ids',
      componentProps: {
        options: deviceOptions.value,
        mode: 'multiple',
        maxTagCount: 2,
        maxTagPlaceholder: (omitted: unknown[]) => `+${omitted.length}`,
        style: { width: '100%', maxWidth: '400px' },
      },
    },
  ]);
}

async function loadTaskConfig() {
  if (!library.value?.id) return;
  const res = await getPlateAutoEnrollTask(library.value.id);
  taskStatus.value = res?.data || null;
  await resetFields();
  if (res?.data) {
    await setFieldsValue({
      device_ids: res.data.device_ids || [],
      duration_minutes: res.data.duration_minutes ?? 60,
      capture_interval_sec: res.data.capture_interval_sec ?? 5,
    });
  }
}

const [register, { setDrawerProps, closeDrawer }] = useDrawerInner(async (data) => {
  library.value = data?.library || data?.record || null;
  setDrawerProps({ title: `摄像头自动录入 · ${library.value?.name || ''}` });
  await loadDevices();
  await loadTaskConfig();
  const formDisabled = !!taskStatus.value?.is_running;
  updateSchema([
    {
      field: 'device_ids',
      componentProps: {
        disabled: formDisabled,
        options: deviceOptions.value,
        mode: 'multiple',
        maxTagCount: 2,
        maxTagPlaceholder: (omitted: unknown[]) => `+${omitted.length}`,
        style: { width: '100%', maxWidth: '400px' },
      },
    },
    {
      field: 'duration_minutes',
      componentProps: {
        disabled: formDisabled,
        min: 1,
        max: 1440,
        precision: 0,
        addonAfter: '分钟',
        style: numberFieldStyle,
      },
    },
    {
      field: 'capture_interval_sec',
      componentProps: {
        disabled: formDisabled,
        min: 2,
        max: 300,
        precision: 0,
        addonAfter: '秒',
        style: numberFieldStyle,
      },
    },
  ]);
  if (taskStatus.value?.is_running) {
    startStatusTimer();
  } else {
    clearStatusTimer();
  }
});

async function handleSave() {
  if (!library.value?.id) return;
  try {
    const values = await validate();
    saving.value = true;
    await savePlateAutoEnrollConfig(library.value.id, { ...values, enroll_mode: 'pending' });
    createMessage.success('配置已保存');
    await loadTaskConfig();
    emit('success');
  } catch (e: unknown) {
    createMessage.error(parsePlateApiError(e, '保存失败'));
  } finally {
    saving.value = false;
  }
}

async function handleStart() {
  if (!library.value?.id) return;
  try {
    const values = await validate();
    starting.value = true;
    await savePlateAutoEnrollConfig(library.value.id, { ...values, enroll_mode: 'pending' });
    await startPlateAutoEnroll(library.value.id);
    createMessage.success('摄像头自动录入已开启');
    await loadTaskConfig();
    startStatusTimer();
    emit('success');
  } catch (e: unknown) {
    if (isAutoEnrollConfigError(e)) {
      createMessage.warning('请至少绑定一个摄像头后再开启');
    } else {
      createMessage.error(parsePlateApiError(e, '开启摄像头自动录入失败'));
    }
  } finally {
    starting.value = false;
  }
}

async function handleStop() {
  if (!library.value?.id) return;
  try {
    stopping.value = true;
    await stopPlateAutoEnroll(library.value.id);
    createMessage.success('摄像头自动录入已关闭');
    clearStatusTimer();
    await loadTaskConfig();
    emit('success');
  } catch (e: unknown) {
    createMessage.error(parsePlateApiError(e, '关闭摄像头自动录入失败'));
  } finally {
    stopping.value = false;
  }
}
</script>

<style lang="less" scoped>
.auto-enroll-drawer {
  padding-right: 4px;

  :deep(.ant-form-item) {
    margin-bottom: 18px;
  }

  :deep(.form-item-device-ids) {
    margin-bottom: 12px;

    .ant-form-item-control-input-content {
      max-width: 400px;
    }

    .ant-select-multiple .ant-select-selector {
      min-height: 32px;
      padding-top: 2px;
      padding-bottom: 2px;
    }

    .ant-form-item-extra:empty {
      display: none;
      margin: 0;
      min-height: 0;
    }
  }

  .tip-alert {
    margin-bottom: 16px;
  }

  .status-panel {
    margin-bottom: 16px;
    padding: 12px 16px;
    border-radius: 8px;
    border: 1px solid #e8e8e8;
    background: #fafafa;

    &.running {
      border-color: #91caff;
      background: #e6f4ff;
    }

    .status-grid {
      display: flex;
      gap: 24px;
      margin-top: 12px;

      .status-item {
        display: flex;
        flex-direction: column;
        gap: 4px;

        .label {
          font-size: 12px;
          color: rgba(0, 0, 0, 0.45);
        }

        .value {
          font-size: 16px;
          font-weight: 600;
        }
      }
    }
  }
}

.footer-buttons {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}
</style>
