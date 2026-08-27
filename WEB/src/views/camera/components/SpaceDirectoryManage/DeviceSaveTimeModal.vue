<template>
  <BasicModal
    v-bind="$attrs"
    @register="register"
    title="空间存储策略"
    :width="520"
    @ok="handleSubmit"
  >
    <BasicForm @register="registerForm" />
    <div v-if="saveTimeCustom" class="save-time-field">
      <div class="save-time-field__label">保存时间</div>
      <SaveTimeInput v-model:value="saveTime" />
    </div>
  </BasicModal>
</template>

<script lang="ts" setup>
import { ref } from 'vue';
import { BasicModal, useModalInner } from '@/components/Modal';
import { BasicForm, useForm } from '@/components/Form';
import { useMessage } from '@/hooks/web/useMessage';
import { updateSnapSpace } from '@/api/device/snap';
import {
  getDeviceRecordingPolicy,
  updateDeviceRecordingPolicy,
  updateRecordSpace,
} from '@/api/device/record';
import SaveTimeInput from './SaveTimeInput.vue';
import {
  DEFAULT_SAVE_TIME,
  formatSaveTimeLabel,
  isValidSaveTime,
  type SpaceKind,
} from '@/views/camera/utils/spaceSaveTime';

const emit = defineEmits(['success', 'register']);

const { createMessage } = useMessage();
const spaceId = ref<number | null>(null);
const deviceId = ref('');
const spaceKind = ref<SpaceKind>('snap');
const directorySaveTime = ref(DEFAULT_SAVE_TIME);
const groupSaveTime = ref<number | null>(null);
const hasGroupPolicy = ref(false);
const inheritedSaveTime = ref(DEFAULT_SAVE_TIME);
const initialSaveMode = ref(0);
const saveTimeCustom = ref(false);
const saveTime = ref(DEFAULT_SAVE_TIME);

const [registerForm, { setFieldsValue, validate, resetFields, updateSchema }] = useForm({
  labelWidth: 110,
  baseColProps: { span: 24 },
  schemas: [
    {
      field: 'device_name',
      label: '设备名称',
      component: 'Input',
      componentProps: { disabled: true },
    },
    {
      field: 'save_mode',
      label: '存储模式',
      component: 'Select',
      componentProps: {
        options: [
          { label: '标准存储', value: 0 },
          { label: '归档存储', value: 1 },
        ],
      },
      helpMessage: '标准存储适合频繁访问，归档存储成本更低',
    },
    {
      field: 'save_time_custom',
      label: '自定义策略',
      component: 'Switch',
      defaultValue: false,
      componentProps: {
        checkedChildren: '自定义',
        unCheckedChildren: '跟随分组',
      },
      helpMessage: '',
    },
    {
      field: 'recording_mode',
      label: '录像方式',
      component: 'Select',
      defaultValue: 'continuous',
      ifShow: () => spaceKind.value === 'record',
      componentProps: {
        options: [
          { label: '连续录像', value: 'continuous' },
          { label: '仅事件录像', value: 'event_only' },
          { label: '关闭录像', value: 'off' },
        ],
      },
      helpMessage: '物理存储位置继承摄像头接入节点：中心共享或边缘本地；此处只控制该设备是否连续录像。',
    },
    {
      field: 'playback_route_mode',
      label: '边缘回放路由',
      component: 'Select',
      defaultValue: 'auto',
      ifShow: () => spaceKind.value === 'record',
      componentProps: {
        options: [
          { label: '自动选择', value: 'auto' },
          { label: '优先直连边缘', value: 'direct' },
          { label: '始终由主节点代理', value: 'proxy' },
        ],
      },
      helpMessage: '建议保持自动；专网/NAT 场景可强制主节点代理，客户端不会接触边缘服务器路径。',
    },
    {
      field: 'event_pre_seconds',
      label: '事件前录像',
      component: 'InputNumber',
      defaultValue: 10,
      ifShow: () => spaceKind.value === 'record',
      componentProps: { min: 0, max: 300, addonAfter: '秒' },
    },
    {
      field: 'event_post_seconds',
      label: '事件后录像',
      component: 'InputNumber',
      defaultValue: 20,
      ifShow: () => spaceKind.value === 'record',
      componentProps: { min: 0, max: 300, addonAfter: '秒' },
    },
    {
      field: 'event_image_sync',
      label: '同步事件图片',
      component: 'Switch',
      defaultValue: true,
      ifShow: () => spaceKind.value === 'record',
    },
    {
      field: 'event_clip_sync',
      label: '同步事件片段',
      component: 'Switch',
      defaultValue: true,
      ifShow: () => spaceKind.value === 'record',
    },
  ],
  showActionButtonGroup: false,
});

const [register, { setModalProps, closeModal }] = useModalInner(async (data) => {
  resetFields();
  spaceId.value = data?.spaceId ?? null;
  deviceId.value = data?.deviceId ?? '';
  spaceKind.value = data?.spaceKind ?? 'snap';
  directorySaveTime.value = data?.directorySaveTime ?? DEFAULT_SAVE_TIME;
  groupSaveTime.value = data?.groupSaveTime ?? null;
  hasGroupPolicy.value = !!data?.groupType;
  initialSaveMode.value = data?.saveMode ?? 0;
  inheritedSaveTime.value = hasGroupPolicy.value
    ? (groupSaveTime.value ?? data?.directorySaveTime ?? DEFAULT_SAVE_TIME)
    : directorySaveTime.value;
  const custom = !!data?.saveTimeCustom;
  saveTimeCustom.value = custom;
  saveTime.value = custom ? (data?.saveTime ?? DEFAULT_SAVE_TIME) : inheritedSaveTime.value;
  await setFieldsValue({
    device_name: data?.deviceName ?? '',
    save_mode: data?.saveMode ?? 0,
    save_time_custom: custom,
  });
  if (spaceKind.value === 'record' && deviceId.value) {
    try {
      const response = await getDeviceRecordingPolicy(deviceId.value) as any;
      const policy = response?.data || response;
      await setFieldsValue({
        recording_mode: policy?.recording_mode || 'continuous',
        playback_route_mode: policy?.playback_route_mode || 'auto',
        event_pre_seconds: policy?.event_pre_seconds ?? 10,
        event_post_seconds: policy?.event_post_seconds ?? 20,
        event_image_sync: policy?.event_image_sync !== false,
        event_clip_sync: policy?.event_clip_sync !== false,
      });
      const storage = policy?.effective_storage;
      if (storage?.mode) {
        updateSchema({
          field: 'recording_mode',
          helpMessage: `当前物理存储：${storage.mode === 'edge_local' ? '边缘本地存储' : '中心共享存储'}；配置状态：${storage.state || 'unknown'}。录像方式变更不会搬迁或删除历史录像。`,
        });
      }
    } catch (e) {
      console.warn('加载设备录像策略失败', e);
      createMessage.warning('未能读取设备录像策略，将使用默认值');
    }
  }
  const followLabel = hasGroupPolicy.value ? '跟随分组' : '跟随目录';
  updateSchema({
    field: 'save_time_custom',
    componentProps: {
      checkedChildren: '自定义',
      unCheckedChildren: followLabel,
      onChange: (checked: boolean) => {
        saveTimeCustom.value = checked;
      },
    },
    helpMessage: `关闭时${followLabel}（${formatSaveTimeLabel(inheritedSaveTime.value)}）`,
  });
});

async function handleSubmit() {
  if (spaceId.value == null) return;
  const values = await validate();
  const custom = !!values.save_time_custom;
  saveTimeCustom.value = custom;
  if (custom && !isValidSaveTime(saveTime.value)) {
    createMessage.warning('自定义保存时间须为永久，或不少于 1 小时');
    return;
  }
  setModalProps({ confirmLoading: true });
  try {
    const payload = {
      save_mode: Number(values.save_mode ?? initialSaveMode.value),
      ...(custom
        ? { save_time: saveTime.value, save_time_custom: true }
        : { save_time_custom: false }),
    };
    const api = spaceKind.value === 'snap' ? updateSnapSpace : updateRecordSpace;
    const res = await api(spaceId.value, payload);
    if (res?.code !== undefined && res.code !== 0) {
      createMessage.error(res.msg || '保存失败');
      return;
    }
    if (spaceKind.value === 'record' && deviceId.value) {
      const retentionHours = custom ? saveTime.value : inheritedSaveTime.value;
      const policyRes = await updateDeviceRecordingPolicy(deviceId.value, {
        recording_mode: values.recording_mode,
        retention_hours: retentionHours,
        playback_route_mode: values.playback_route_mode,
        event_pre_seconds: Number(values.event_pre_seconds ?? 10),
        event_post_seconds: Number(values.event_post_seconds ?? 20),
        event_image_sync: values.event_image_sync !== false,
        event_clip_sync: values.event_clip_sync !== false,
      }) as any;
      if (policyRes?.code !== undefined && policyRes.code !== 0) {
        createMessage.error(policyRes.msg || '录像策略保存失败');
        return;
      }
    }
    createMessage.success('空间存储策略已更新');
    closeModal();
    emit('success');
  } catch (e) {
    console.error(e);
    createMessage.error('保存空间存储策略失败');
  } finally {
    setModalProps({ confirmLoading: false });
  }
}
</script>

<style lang="less" scoped>
.save-time-field {
  margin-top: 8px;
  padding-left: 110px;

  &__label {
    margin-bottom: 8px;
    font-size: 14px;
    color: rgba(0, 0, 0, 0.88);
  }
}
</style>
