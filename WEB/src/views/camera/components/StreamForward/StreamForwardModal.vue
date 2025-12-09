<template>
  <BasicDrawer 
    v-bind="$attrs" 
    @register="register" 
    :title="modalTitle" 
    @ok="handleSubmit"
    width="800"
    placement="right"
    :showFooter="true"
    :showCancelBtn="false"
    :showOkBtn="false"
  >
    <template #footer>
      <div class="footer-buttons">
        <a-button v-if="!isViewMode" @click="handleReset" class="mr-2">重置</a-button>
        <a-button v-if="!isViewMode" type="primary" :loading="confirmLoading" @click="handleSubmit">提交</a-button>
      </div>
    </template>
    <BasicForm @register="registerForm" />
  </BasicDrawer>
</template>

<script lang="ts" setup>
import { ref, computed } from 'vue';
import { BasicDrawer, useDrawerInner } from '@/components/Drawer';
import { BasicForm, useForm } from '@/components/Form';
import { useMessage } from '@/hooks/web/useMessage';
import {
  createStreamForwardTask,
  updateStreamForwardTask,
  type StreamForwardTask,
} from '@/api/device/stream_forward';
import { getDeviceList } from '@/api/device/camera';

defineOptions({ name: 'StreamForwardModal' });

const { createMessage } = useMessage();
const emit = defineEmits(['success', 'register']);

const taskId = ref<number | null>(null);
const confirmLoading = ref(false);
const deviceOptions = ref<Array<{ label: string; value: string }>>([]);

const isViewMode = ref(false);

const modalTitle = computed(() => {
  if (isViewMode.value) return '查看推流转发任务';
  return taskId.value ? '编辑推流转发任务' : '新建推流转发任务';
});

const formValues = ref<any>({});

const [register, { setDrawerProps, closeDrawer }] = useDrawerInner(async (data) => {
  taskId.value = data?.id || null;
  formValues.value = data || {};
  isViewMode.value = data?.type === 'view';
  
  // 加载设备列表
  await loadDeviceOptions();
  
  // 设置表单值
  await resetFields();
  setFieldsValue({
    ...formValues.value,
    device_ids: formValues.value.device_ids || [],
  });
  
  setDrawerProps({ confirmLoading: false });
});

const [registerForm, { setFieldsValue, resetFields, validate }] = useForm({
  labelWidth: 120,
  schemas: [
    {
      field: 'task_name',
      label: '任务名称',
      component: 'Input',
      required: true,
      componentProps: {
        placeholder: '请输入任务名称',
        disabled: isViewMode,
      },
    },
    {
      field: 'device_ids',
      label: '关联摄像头',
      component: 'Select',
      required: true,
      componentProps: {
        mode: 'multiple',
        placeholder: '请选择摄像头',
        options: deviceOptions,
        disabled: isViewMode,
        showSearch: true,
        filterOption: (input: string, option: any) => {
          return option.label.toLowerCase().indexOf(input.toLowerCase()) >= 0;
        },
      },
    },
    {
      field: 'output_format',
      label: '输出格式',
      component: 'Select',
      required: true,
      componentProps: {
        placeholder: '请选择输出格式',
        options: [
          { label: 'RTMP', value: 'rtmp' },
          { label: 'RTSP', value: 'rtsp' },
        ],
        disabled: isViewMode,
      },
    },
    {
      field: 'output_quality',
      label: '输出质量',
      component: 'Select',
      required: true,
      componentProps: {
        placeholder: '请选择输出质量',
        options: [
          { label: '低', value: 'low' },
          { label: '中', value: 'medium' },
          { label: '高', value: 'high' },
        ],
        disabled: isViewMode,
      },
    },
    {
      field: 'output_bitrate',
      label: '输出码率',
      component: 'Input',
      componentProps: {
        placeholder: '如：512k, 1M, 2M（留空使用默认值）',
        disabled: isViewMode,
      },
    },
    {
      field: 'description',
      label: '任务描述',
      component: 'InputTextArea',
      componentProps: {
        placeholder: '请输入任务描述',
        rows: 4,
        disabled: isViewMode,
      },
    },
    {
      field: 'is_enabled',
      label: '是否启用',
      component: 'Switch',
      componentProps: {
        disabled: isViewMode,
      },
    },
  ],
});

const loadDeviceOptions = async () => {
  try {
    const response = await getDeviceList({ pageNo: 1, pageSize: 1000 });
    if (response.code === 0 && response.data) {
      deviceOptions.value = response.data.map((device: any) => ({
        label: device.name || device.id,
        value: device.id,
      }));
    }
  } catch (error) {
    console.error('加载设备列表失败', error);
  }
};

const handleReset = async () => {
  await resetFields();
  setFieldsValue({
    ...formValues.value,
    device_ids: formValues.value.device_ids || [],
  });
};

const handleSubmit = async () => {
  try {
    const values = await validate();
    setDrawerProps({ confirmLoading: true });
    
    if (taskId.value) {
      // 更新
      await updateStreamForwardTask(taskId.value, values);
      createMessage.success('更新成功');
    } else {
      // 创建
      await createStreamForwardTask(values);
      createMessage.success('创建成功');
    }
    
    closeDrawer();
    emit('success');
  } catch (error: any) {
    console.error('提交失败', error);
    createMessage.error(error?.msg || '提交失败');
  } finally {
    setDrawerProps({ confirmLoading: false });
  }
};
</script>

<style lang="less" scoped>
.footer-buttons {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}
</style>

