<template>
  <DeviceCreatePanelLayout>
    <template #form>
      <BasicForm @register="registerForm" />
    </template>
    <template #actions>
      <Button type="primary" :loading="submitting" @click="handleSubmit">注册设备</Button>
    </template>
  </DeviceCreatePanelLayout>
</template>

<script lang="ts" setup>
import { ref } from 'vue';
import { BasicForm, useForm } from '@/components/Form';
import { Button } from '@/components/Button';
import { useMessage } from '@/hooks/web/useMessage';
import { registerDevice } from '@/api/device/camera';
import { ensureDeviceStreamForwardTask } from '@/api/device/stream_forward';
import { resolveRegisteredDeviceId } from '@/views/camera/utils/rtspUrl';
import DeviceCreatePanelLayout from '../DeviceCreatePanelLayout.vue';
import {
  DEVICE_CREATE_COL_LINE,
  DEVICE_CREATE_FORM_GRID,
} from '../deviceCreateForm';

const emit = defineEmits<{ success: [] }>();
const props = defineProps<{ ingressNodeId?: number }>();

const { createMessage } = useMessage();
const submitting = ref(false);

const [registerForm, { validate, getFieldsValue }] = useForm({
  ...DEVICE_CREATE_FORM_GRID,
  schemas: [
    {
      field: 'name',
      label: '设备名称',
      component: 'Input',
      colProps: DEVICE_CREATE_COL_LINE,
      componentProps: { placeholder: '可选' },
    },
    {
      field: 'source',
      label: 'RTSP 地址',
      component: 'Input',
      required: true,
      colProps: DEVICE_CREATE_COL_LINE,
      componentProps: { placeholder: 'rtsp://username:password@ip:port/path' },
    },
  ],
});

async function handleSubmit() {
  try {
    await validate();
  } catch {
    return;
  }
  const values = getFieldsValue();
  const source = String(values.source || '').trim();
  if (!source) {
    createMessage.error('RTSP 取流地址不能为空');
    return;
  }
  submitting.value = true;
  try {
    const response = await registerDevice({
      name: values.name || undefined,
      source,
      stream: 0,
      cameraType: 'custom',
      ingress_node_id: props.ingressNodeId,
    });
    const deviceId = resolveRegisteredDeviceId(response);
    createMessage.success('设备注册成功');
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
    createMessage.error(err?.msg || err?.message || '设备注册失败');
  } finally {
    submitting.value = false;
  }
}
</script>
