<template>
  <DeviceCreatePanelLayout>
    <template #form>
      <BasicForm @register="registerForm">
        <template #rtsp_template_slot="{ model, field }">
          <a-input
            v-model:value="model[field]"
            placeholder="rtsp://{username}:{password}@{ip}:{port}/cam/realmonitor?channel={channel}&subtype={subtype}"
            allow-clear
          />
          <div style="margin-top: 6px; color: #909399; font-size: 12px; line-height: 1.6;">
            <div>完整格式：rtsp://{username}:{password}@{ip}:{port}/{channel}/{subtype}</div>
            <div>参数说明：username用户名  password密码  ip设备IP  port端口  channel通道号  subtype码流(0主/1子)</div>
          </div>
        </template>
      </BasicForm>
    </template>
    <template #actions>
      <Button type="primary" :loading="submitting" @click="handleSubmit">登记并挂载通道</Button>
    </template>
  </DeviceCreatePanelLayout>
</template>

<script lang="ts" setup>
import { ref } from 'vue';
import { BasicForm, useForm } from '@/components/Form';
import { Button } from '@/components/Button';
import { useMessage } from '@/hooks/web/useMessage';
import { registerNvrWithChannels } from '@/api/device/camera';
import {
  formatNvrRegisterHint,
  nvrRegisterRegisteredCount,
} from '@/views/camera/utils/nvrRegisterMessage';
import DeviceCreatePanelLayout from '../DeviceCreatePanelLayout.vue';
import {
  DEVICE_CREATE_FORM_GRID,
  DEVICE_CREATE_NUMBER_PROPS,
} from '../deviceCreateForm';
import { CAMERA_BRAND_OPTIONS, isCustomBrand } from '@/views/camera/utils/deviceCreateOptions';

const emit = defineEmits<{ success: [] }>();
const props = defineProps<{ ingressNodeId?: number }>();

const { createMessage } = useMessage();
const submitting = ref(false);

const [registerForm, { validate, getFieldsValue }] = useForm({
  ...DEVICE_CREATE_FORM_GRID,
  schemas: [
    {
      field: 'ip',
      label: 'NVR IP',
      component: 'Input',
      required: true,
      componentProps: { placeholder: '192.168.1.64' },
    },
    {
      field: 'port',
      label: 'Web 端口',
      component: 'InputNumber',
      defaultValue: 80,
      componentProps: { min: 1, max: 65535, ...DEVICE_CREATE_NUMBER_PROPS },
    },
    {
      field: 'vendor',
      label: '品牌',
      component: 'Select',
      componentProps: {
        allowClear: true,
        placeholder: '自动识别',
        options: CAMERA_BRAND_OPTIONS,
        showSearch: true,
        filterOption: (input: string, option: { label?: string }) =>
          (option?.label ?? '').toLowerCase().includes(input.toLowerCase()),
      },
    },
    {
      field: 'rtsp_template',
      label: 'RTSP 地址模板',
      component: 'Input',
      required: true,
      slot: 'rtsp_template_slot',
      ifValues: (values: Record<string, any>) => isCustomBrand(values.vendor),
    },
    {
      field: 'channel_count',
      label: '通道数量',
      component: 'InputNumber',
      defaultValue: 1,
      required: true,
      componentProps: { min: 1, max: 1024, ...DEVICE_CREATE_NUMBER_PROPS },
      helpMessage: '自定义品牌时需手动指定通道总数',
      ifValues: (values: Record<string, any>) => isCustomBrand(values.vendor),
    },
    {
      field: 'username',
      label: '用户名',
      component: 'Input',
      required: true,
      defaultValue: 'admin',
      componentProps: { placeholder: 'admin', allowClear: true },
    },
    {
      field: 'password',
      label: '密码',
      component: 'InputPassword',
      required: true,
      componentProps: { allowClear: true },
    },
    {
      field: 'name',
      label: '设备名称',
      component: 'Input',
      componentProps: { placeholder: '可选', allowClear: true },
    },
  ],
});

function buildChannelsForCustom(
  channelCount: number,
) {
  const channels: Array<{
    channel_id: number;
    name: string;
  }> = [];
  for (let i = 1; i <= channelCount; i++) {
    channels.push({
      channel_id: i,
      name: `通道${i}`,
    });
  }
  return channels;
}

async function handleSubmit() {
  try {
    await validate();
  } catch {
    return;
  }
  const values = getFieldsValue();
  const ip = String(values.ip || '').trim();
  if (!ip) {
    createMessage.warning('请填写 NVR IP');
    return;
  }

  const vendor = values.vendor;
  const isCustom = isCustomBrand(vendor);

  submitting.value = true;
  try {
    const port = values.port ?? 80;
    const rtspTemplate = String(values.rtsp_template || '').trim();
    const channelCount = values.channel_count ?? 1;
    const username = String(values.username || '').trim();
    const password = values.password || '';

    const requestData = {
      ip,
      port,
      username,
      password,
      vendor: isCustom ? 'custom' : vendor,
      name: values.name || undefined,
      scheme: port === 443 || port === 8443 ? 'https' : 'http',
      timeout: 15,
      ingress_node_id: props.ingressNodeId,
    } as Parameters<typeof registerNvrWithChannels>[0];

    if (isCustom) {
      if (!rtspTemplate) {
        createMessage.warning('请填写 RTSP 地址模板');
        return;
      }
      requestData.rtsp_template = rtspTemplate;
      requestData.channel_count = channelCount;
      const channels = buildChannelsForCustom(channelCount);
      requestData.channels = channels;
    }

    const res = await registerNvrWithChannels(requestData);
    const n = nvrRegisterRegisteredCount(res);
    if (n > 0) {
      createMessage.success(`NVR 已登记，已挂载 ${n} 路通道`);
      emit('success');
    } else {
      createMessage.warning(`NVR 登记失败：${formatNvrRegisterHint(res)}`);
    }
  } catch (e: unknown) {
    const err = e as { msg?: string; message?: string };
    createMessage.error(err?.msg || err?.message || 'NVR 登记失败');
  } finally {
    submitting.value = false;
  }
}
</script>
