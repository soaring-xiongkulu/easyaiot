<template>
  <DeviceCreatePanelLayout>
    <template #form>
      <BasicForm @register="registerForm" />
      <Alert
        v-if="selectedPlatform?.auth_mode === 'oauth' || selectedPlatform?.auth_mode === 'webui'"
        type="info"
        show-icon
        class="rtc-oauth-tip"
      >
        <template #message>
          {{ selectedPlatform?.name }} 需先在 go2rtc WebUI 完成账号绑定。
          <a :href="go2rtcWebUrl" target="_blank" rel="noopener">打开 go2rtc 管理界面</a>
          ，绑定后将生成的源流 URL 粘贴到下方「源流 URL」字段。
        </template>
      </Alert>
      <Alert v-if="selectedPlatform?.notes" type="warning" show-icon class="rtc-notes">
        <template #message>{{ selectedPlatform.notes }}</template>
      </Alert>
    </template>
    <template #actions>
      <Button :loading="previewing" @click="handlePreview">预览 URL</Button>
      <Button type="primary" :loading="submitting" @click="handleSubmit">注册设备</Button>
    </template>
  </DeviceCreatePanelLayout>
</template>

<script lang="ts" setup>
import { computed, onMounted, ref, watch } from 'vue';
import { Alert } from 'ant-design-vue';
import { BasicForm, useForm } from '@/components/Form';
import { Button } from '@/components/Button';
import { useMessage } from '@/hooks/web/useMessage';
import {
  buildRtcStreamUrl,
  getRtcConfig,
  getRtcPlatforms,
  registerRtcLiveDevice,
  type RtcPlatform,
} from '@/api/device/camera';
import { ensureDeviceStreamForwardTask } from '@/api/device/stream_forward';
import { resolveRegisteredDeviceId } from '@/views/camera/utils/rtspUrl';
import DeviceCreatePanelLayout from '../DeviceCreatePanelLayout.vue';
import {
  DEVICE_CREATE_COL,
  DEVICE_CREATE_COL_FULL,
  DEVICE_CREATE_COL_LINE,
  DEVICE_CREATE_FORM_GRID,
} from '../deviceCreateForm';

const emit = defineEmits<{ success: [] }>();

const { createMessage } = useMessage();
const submitting = ref(false);
const previewing = ref(false);
const platforms = ref<RtcPlatform[]>([]);
const go2rtcWebUrl = ref('http://127.0.0.1:1984');
const selectedPlatformId = ref('tapo');

const selectedPlatform = computed(() =>
  platforms.value.find((p) => p.id === selectedPlatformId.value),
);

const oauthPlatforms = new Set(['ring', 'nest', 'xiaomi', 'wyze', 'roborock', 'tuya']);

function platformFieldSchemas(platform: RtcPlatform | undefined) {
  const schemas: any[] = [
    {
      field: 'platform',
      label: '摄像头平台',
      component: 'Select',
      required: true,
      colProps: DEVICE_CREATE_COL,
      defaultValue: selectedPlatformId.value,
      componentProps: {
        options: platforms.value.map((p) => ({ label: `${p.name} (${p.vendor})`, value: p.id })),
        onChange: (val: string) => {
          selectedPlatformId.value = val;
        },
      },
    },
    {
      field: 'name',
      label: '设备名称',
      component: 'Input',
      colProps: DEVICE_CREATE_COL,
      componentProps: { placeholder: '可选，默认使用平台名称' },
    },
    {
      field: 'stream',
      label: '码流',
      component: 'Select',
      colProps: DEVICE_CREATE_COL,
      defaultValue: 'main',
      componentProps: {
        options: [
          { label: '主码流 (HD)', value: 'main' },
          { label: '子码流 (SD)', value: 'sub' },
        ],
      },
      ifShow: () => !!selectedPlatform.value?.supports_substream,
    },
  ];

  if (platform && !oauthPlatforms.has(platform.id)) {
    for (const f of platform.fields) {
      schemas.push({
        field: `param_${f.name}`,
        label: f.label,
        component: f.secret ? 'InputPassword' : 'Input',
        required: f.required !== false,
        colProps: DEVICE_CREATE_COL_FULL,
        helpMessage: f.description || undefined,
        componentProps: { placeholder: f.placeholder || '' },
      });
    }
  } else {
    schemas.push({
      field: 'source',
      label: '源流 URL',
      component: 'Input',
      required: true,
      colProps: DEVICE_CREATE_COL_LINE,
      componentProps: {
        placeholder: `${platform?.schema || 'tapo'}://... 或 ring:?device_id=...`,
      },
    });
  }

  return schemas;
}

const [registerForm, { validate, getFieldsValue, resetSchema, setFieldsValue }] = useForm({
  ...DEVICE_CREATE_FORM_GRID,
  schemas: platformFieldSchemas(undefined),
});

function collectParams(values: Record<string, unknown>): Record<string, unknown> {
  const params: Record<string, unknown> = {};
  const platform = selectedPlatform.value;
  if (!platform) return params;
  for (const f of platform.fields) {
    const key = `param_${f.name}`;
    const val = values[key];
    if (val !== undefined && val !== null && String(val).trim() !== '') {
      params[f.name] = val;
    }
  }
  if (values.stream) {
    params.stream = values.stream;
  }
  return params;
}

async function loadPlatforms() {
  try {
    const [cfg, data] = await Promise.all([getRtcConfig(), getRtcPlatforms()]);
    go2rtcWebUrl.value = cfg?.go2rtc_web_url?.startsWith('/')
      ? `${window.location.origin}${cfg.go2rtc_web_url}`
      : (cfg?.go2rtc_web_url || go2rtcWebUrl.value);
    platforms.value = data?.platforms || [];
    if (platforms.value.length && !platforms.value.some((p) => p.id === selectedPlatformId.value)) {
      selectedPlatformId.value = platforms.value[0].id;
    }
    await resetSchema(platformFieldSchemas(selectedPlatform.value));
    await setFieldsValue({ platform: selectedPlatformId.value, stream: 'main' });
  } catch (error: unknown) {
    const err = error as { msg?: string; message?: string };
    createMessage.error(err?.msg || err?.message || '加载 RTC 平台列表失败，请确认 RTC 服务已启动');
  }
}

watch(selectedPlatformId, async () => {
  await resetSchema(platformFieldSchemas(selectedPlatform.value));
  await setFieldsValue({ platform: selectedPlatformId.value, stream: 'main' });
});

async function handlePreview() {
  try {
    await validate();
  } catch {
    return;
  }
  const values = getFieldsValue();
  const platform = String(values.platform || selectedPlatformId.value);
  if (oauthPlatforms.has(platform)) {
    createMessage.info('OAuth/WebUI 平台请直接使用 go2rtc WebUI 生成的源流 URL');
    return;
  }
  previewing.value = true;
  try {
    const result = await buildRtcStreamUrl({ platform, params: collectParams(values) });
    createMessage.success(`预览: ${result.source}`);
  } catch (error: unknown) {
    const err = error as { msg?: string; message?: string };
    createMessage.error(err?.msg || err?.message || '预览失败');
  } finally {
    previewing.value = false;
  }
}

async function handleSubmit() {
  try {
    await validate();
  } catch {
    return;
  }
  const values = getFieldsValue();
  const platform = String(values.platform || selectedPlatformId.value).trim();
  const payload: Record<string, unknown> = {
    name: values.name || undefined,
    enable_forward: true,
  };

  if (oauthPlatforms.has(platform)) {
    const source = String(values.source || '').trim();
    if (!source) {
      createMessage.error('请填写 go2rtc 生成的源流 URL');
      return;
    }
    payload.source = source;
    payload.platform = platform;
  } else {
    payload.platform = platform;
    payload.params = collectParams(values);
  }

  submitting.value = true;
  try {
    const response = await registerRtcLiveDevice(payload);
    const deviceId = resolveRegisteredDeviceId(response);
    createMessage.success('RTC 摄像头注册成功');
    if (deviceId) {
      try {
        await ensureDeviceStreamForwardTask(deviceId);
      } catch {
        /* 静默 */
      }
    }
    emit('success');
  } catch (error: unknown) {
    const err = error as { msg?: string; message?: string };
    createMessage.error(err?.msg || err?.message || 'RTC 摄像头注册失败');
  } finally {
    submitting.value = false;
  }
}

onMounted(() => {
  loadPlatforms();
});
</script>

<style lang="less" scoped>
.rtc-oauth-tip,
.rtc-notes {
  max-width: 1080px;
  margin-top: 12px;
}
</style>
