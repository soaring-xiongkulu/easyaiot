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
        <Button v-if="!taskStatus?.is_running" :loading="saving" @click="handleSave"
          >保存配置</Button
        >
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
        message="摄像头人脸采集"
        description="默认将清晰、未匹配的人脸送入待入库工作台，审核确认后再进入正式库；已存在、低质量或抓帧失败的样本会分类统计。"
        class="tip-alert"
      />

      <div v-if="taskStatus?.is_running" class="status-panel running">
        <a-badge status="processing" text="摄像头自动录入运行中" />
        <div class="status-grid">
          <div class="status-item">
            <span class="label">已录入</span>
            <span class="value">{{ taskStatus.enrolled_count ?? 0 }}</span>
          </div>
          <div class="status-item">
            <span class="label">待审核</span>
            <span class="value">{{ taskStatus.candidate_count ?? 0 }}</span>
          </div>
          <div class="status-item">
            <span class="label">重复</span>
            <span class="value">{{ taskStatus.duplicate_count ?? 0 }}</span>
          </div>
          <div class="status-item">
            <span class="label">质量拒绝</span>
            <span class="value">{{ taskStatus.rejected_count ?? 0 }}</span>
          </div>
          <div class="status-item">
            <span class="label">抓帧失败</span>
            <span class="value">{{ taskStatus.capture_failed_count ?? 0 }}</span>
          </div>
          <div class="status-item">
            <span class="label">已跳过</span>
            <span class="value">{{ taskStatus.skipped_count ?? 0 }}</span>
          </div>
          <div class="status-item">
            <span class="label">到期时间</span>
            <span class="value">{{ formatTime(taskStatus.expires_at) }}</span>
          </div>
          <div class="status-item">
            <span class="label">单轮预计</span>
            <span class="value">{{ taskStatus.effective_cycle_sec ?? "-" }} 秒</span>
          </div>
        </div>
      </div>

      <BasicForm @register="registerForm" />
    </div>
  </BasicDrawer>
</template>

<script lang="ts" setup>
import { onUnmounted, ref } from "vue";
import { BasicDrawer, useDrawerInner } from "@/components/Drawer";
import { BasicForm, useForm } from "@/components/Form";
import { useMessage } from "@/hooks/web/useMessage";
import { getDeviceList } from "@/api/device/camera";
import { Button } from "@/components/Button";
import {
  getFaceAutoEnrollTask,
  isAutoEnrollConfigError,
  parseFaceApiError,
  saveFaceAutoEnrollConfig,
  startFaceAutoEnroll,
  stopFaceAutoEnroll,
  type FaceAutoEnrollTask,
  type FaceLibrary,
} from "@/api/device/face_library";

defineOptions({ name: "FaceAutoEnrollDrawer" });

const emit = defineEmits(["success", "register"]);
const { createMessage } = useMessage();

const library = ref<FaceLibrary | null>(null);
const taskStatus = ref<FaceAutoEnrollTask | null>(null);
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
  if (!val) return "-";
  try {
    return new Date(val).toLocaleString();
  } catch {
    return val;
  }
}

const numberFieldStyle = { width: "160px" };

const [registerForm, { setFieldsValue, validate, updateSchema, resetFields }] = useForm({
  labelWidth: 96,
  baseColProps: { span: 24 },
  schemas: [
    {
      field: "device_ids",
      label: "绑定摄像头",
      component: "Select",
      required: true,
      itemProps: { class: "form-item-device-ids" },
      componentProps: {
        placeholder: "请选择摄像头",
        mode: "multiple",
        showSearch: true,
        allowClear: true,
        maxTagCount: 2,
        maxTagPlaceholder: (omitted: unknown[]) => `+${omitted.length}`,
        options: deviceOptions,
        style: { width: "100%", maxWidth: "400px" },
        filterOption: (input: string, option: any) =>
          (option?.label ?? "").toLowerCase().includes(input.toLowerCase()),
      },
    },
    {
      field: "enroll_mode",
      label: "入库方式",
      component: "Select",
      required: true,
      defaultValue: "pending",
      componentProps: {
        options: [
          { label: "待审核（推荐）", value: "pending" },
          { label: "直接进入正式库", value: "direct" },
        ],
        style: { width: "240px" },
      },
      helpMessage: "仅受控单人正脸点位建议使用直接入库",
    },
    {
      field: "duration_minutes",
      label: "开启时长",
      component: "InputNumber",
      required: true,
      defaultValue: 60,
      colProps: { span: 12 },
      componentProps: {
        min: 1,
        max: 1440,
        precision: 0,
        addonAfter: "分钟",
        style: numberFieldStyle,
        placeholder: "如 60",
      },
      helpMessage: "到期后自动停止",
    },
    {
      field: "capture_interval_sec",
      label: "抓帧间隔",
      component: "InputNumber",
      required: true,
      defaultValue: 5,
      colProps: { span: 12 },
      componentProps: {
        min: 2,
        max: 300,
        precision: 0,
        addonAfter: "秒",
        style: numberFieldStyle,
        placeholder: "如 5",
      },
      helpMessage: "两次抓帧之间的间隔",
    },
    {
      field: "person_name_prefix",
      label: "命名前缀",
      component: "Input",
      defaultValue: "摄像头自动录入",
      componentProps: {
        placeholder: "如：摄像头自动录入",
        maxlength: 50,
        style: { maxWidth: "360px" },
      },
      helpMessage: "新人脸命名为「前缀-001」，可在人脸管理中修改",
    },
  ],
});

async function loadDevices() {
  const response = await getDeviceList({ pageNo: 1, pageSize: 1000 });
  deviceOptions.value = (response.data || []).map((item: any) => ({
    label: item.name || item.id,
    value: item.id,
  }));
  updateSchema([
    {
      field: "device_ids",
      componentProps: {
        options: deviceOptions.value,
        mode: "multiple",
        maxTagCount: 2,
        maxTagPlaceholder: (omitted: unknown[]) => `+${omitted.length}`,
        style: { width: "100%", maxWidth: "400px" },
      },
    },
  ]);
}

async function loadTaskConfig() {
  if (!library.value?.id) return;
  const res = await getFaceAutoEnrollTask(library.value.id);
  taskStatus.value = res.data || null;
  await resetFields();
  if (res.data) {
    await setFieldsValue({
      device_ids: res.data.device_ids || [],
      duration_minutes: res.data.duration_minutes ?? 60,
      capture_interval_sec: res.data.capture_interval_sec ?? 5,
      person_name_prefix: res.data.person_name_prefix || "摄像头自动录入",
      enroll_mode: res.data.enroll_mode || "pending",
    });
  }
}

const [register, { setDrawerProps, closeDrawer }] = useDrawerInner(async (data) => {
  library.value = data?.library || null;
  setDrawerProps({ title: `摄像头自动录入 · ${library.value?.name || ""}` });
  await loadDevices();
  await loadTaskConfig();
  const formDisabled = !!taskStatus.value?.is_running;
  updateSchema([
    {
      field: "device_ids",
      componentProps: {
        disabled: formDisabled,
        options: deviceOptions.value,
        mode: "multiple",
        maxTagCount: 2,
        maxTagPlaceholder: (omitted: unknown[]) => `+${omitted.length}`,
        style: { width: "100%", maxWidth: "400px" },
      },
    },
    {
      field: "enroll_mode",
      componentProps: {
        disabled: formDisabled,
        options: [
          { label: "待审核（推荐）", value: "pending" },
          { label: "直接进入正式库", value: "direct" },
        ],
        style: { width: "240px" },
      },
    },
    {
      field: "duration_minutes",
      componentProps: {
        disabled: formDisabled,
        min: 1,
        max: 1440,
        precision: 0,
        addonAfter: "分钟",
        style: numberFieldStyle,
      },
    },
    {
      field: "capture_interval_sec",
      componentProps: {
        disabled: formDisabled,
        min: 2,
        max: 300,
        precision: 0,
        addonAfter: "秒",
        style: numberFieldStyle,
      },
    },
    {
      field: "person_name_prefix",
      componentProps: { disabled: formDisabled, maxlength: 50, style: { maxWidth: "360px" } },
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
    await saveFaceAutoEnrollConfig(library.value.id, values);
    createMessage.success("配置已保存");
    await loadTaskConfig();
    emit("success");
  } catch (e: any) {
    createMessage.error(e?.message || "保存失败");
  } finally {
    saving.value = false;
  }
}

async function handleStart() {
  if (!library.value?.id) return;
  try {
    const values = await validate();
    starting.value = true;
    await saveFaceAutoEnrollConfig(library.value.id, values);
    await startFaceAutoEnroll(library.value.id);
    createMessage.success("摄像头自动录入已开启");
    await loadTaskConfig();
    startStatusTimer();
    emit("success");
  } catch (e: unknown) {
    if (isAutoEnrollConfigError(e)) {
      createMessage.warning("请至少绑定一个摄像头后再开启");
    } else {
      createMessage.error(parseFaceApiError(e, "开启摄像头自动录入失败"));
    }
  } finally {
    starting.value = false;
  }
}

async function handleStop() {
  if (!library.value?.id) return;
  try {
    stopping.value = true;
    await stopFaceAutoEnroll(library.value.id);
    createMessage.success("摄像头自动录入已关闭");
    clearStatusTimer();
    await loadTaskConfig();
    emit("success");
  } catch (e: unknown) {
    createMessage.error(parseFaceApiError(e, "关闭摄像头自动录入失败"));
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

  :deep(.ant-form-item-label > label) {
    white-space: nowrap;
  }

  :deep(.ant-form-item-extra),
  :deep(.ant-form-item-explain) {
    max-width: 100%;
    white-space: normal;
    word-break: break-word;
    line-height: 1.5;
  }

  :deep(.ant-input-number-group-wrapper) {
    width: auto !important;
    max-width: 100%;
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
