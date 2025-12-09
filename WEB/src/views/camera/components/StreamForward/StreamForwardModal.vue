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
    <div class="form-content">
      <BasicForm @register="registerForm" />
    </div>
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
import { getDeviceList, getDeviceConflicts } from '@/api/device/camera';

defineOptions({ name: 'StreamForwardModal' });

const { createMessage } = useMessage();
const emit = defineEmits(['success', 'register']);

const taskId = ref<number | null>(null);
const confirmLoading = ref(false);
const deviceOptions = ref<Array<{ label: string; value: string }>>([]);
const formValues = ref<any>({});
const modalData = ref<{ type?: string; record?: StreamForwardTask }>({});

const modalTitle = computed(() => {
  if (modalData.value.type === 'view') return '查看推流转发任务';
  if (modalData.value.type === 'edit') return '编辑推流转发任务';
  return '新建推流转发任务';
});

const isViewMode = computed(() => modalData.value.type === 'view');

const [register, { setDrawerProps, closeDrawer }] = useDrawerInner(async (data) => {
  modalData.value = data || {};
  taskId.value = null;
  confirmLoading.value = false;
  resetFields();
  
  // 加载设备列表
  await loadDeviceOptions();
  
  if (modalData.value.record) {
    const record = modalData.value.record;
    taskId.value = record.id;
    formValues.value = { ...record };
    
    await setFieldsValue({
      task_name: record.task_name,
      device_ids: record.device_ids || [],
      output_format: record.output_format || 'rtmp',
      output_quality: record.output_quality || 'high',
      output_bitrate: record.output_bitrate,
      description: record.description,
      is_enabled: record.is_enabled !== undefined ? record.is_enabled : false,
    });
    
    // 查看模式禁用表单
    if (modalData.value.type === 'view') {
      updateSchema([
        { field: 'task_name', componentProps: { disabled: true } },
        { field: 'device_ids', componentProps: { disabled: true } },
        { field: 'output_format', componentProps: { disabled: true } },
        { field: 'output_quality', componentProps: { disabled: true } },
        { field: 'output_bitrate', componentProps: { disabled: true } },
        { field: 'description', componentProps: { disabled: true } },
        { field: 'is_enabled', componentProps: { disabled: true } },
      ]);
      setDrawerProps({ showOkBtn: false });
    } else {
      setDrawerProps({ showOkBtn: true });
    }
  } else {
    // 新建模式
    formValues.value = {};
    await setFieldsValue({
      output_format: 'rtmp',
      output_quality: 'high',
      is_enabled: false,
    });
    setDrawerProps({ showOkBtn: true });
  }
  
  setDrawerProps({ confirmLoading: false });
});

const [registerForm, { setFieldsValue, resetFields, validate, updateSchema }] = useForm({
  transformDateToString: false,
  labelWidth: 150,
  baseColProps: { span: 24 },
  schemas: [
    {
      field: 'task_name',
      label: '任务名称',
      component: 'Input',
      required: true,
      componentProps: {
        placeholder: '请输入任务名称',
      },
    },
    {
      field: 'device_ids',
      label: '关联摄像头',
      component: 'Select',
      required: true,
      componentProps: {
        placeholder: '请选择摄像头（可多选）',
        options: deviceOptions,
        mode: 'multiple',
        showSearch: true,
        allowClear: true,
        filterOption: (input: string, option: any) => {
          return option.label.toLowerCase().indexOf(input.toLowerCase()) >= 0;
        },
      },
      helpMessage: '选择需要推流转发的摄像头，可多选',
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
      },
      helpMessage: '选择推流输出格式，RTMP适用于大多数流媒体平台，RTSP适用于专业监控系统',
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
      },
      helpMessage: '选择推流输出质量，质量越高占用带宽越大',
    },
    {
      field: 'output_bitrate',
      label: '输出码率',
      component: 'Input',
      componentProps: {
        placeholder: '如：512k, 1M, 2M（留空使用默认值）',
      },
      helpMessage: '自定义输出码率，例如：512k、1M、2M。留空则根据输出质量自动设置',
    },
    {
      field: 'description',
      label: '任务描述',
      component: 'InputTextArea',
      componentProps: {
        placeholder: '请输入任务描述（可选）',
        rows: 4,
        showCount: true,
        maxlength: 500,
      },
      helpMessage: '任务描述信息，用于说明此推流转发任务的用途和注意事项',
    },
    {
      field: 'is_enabled',
      label: '是否启用',
      component: 'Switch',
      componentProps: {
        checkedChildren: '是',
        unCheckedChildren: '否',
      },
      helpMessage: '创建后是否立即启用任务，启用后任务将自动开始推流转发',
    },
  ],
  showActionButtonGroup: false,
});

const loadDeviceOptions = async () => {
  try {
    // 并行加载设备列表和冲突列表
    const [deviceResponse, conflictResponse] = await Promise.all([
      getDeviceList({ pageNo: 1, pageSize: 1000 }),
      getDeviceConflicts('stream_forward')
    ]);
    
    if (deviceResponse.code === 0 && deviceResponse.data) {
      // 获取冲突的摄像头ID列表
      const conflictDeviceIds = conflictResponse.code === 0 && conflictResponse.data 
        ? new Set(conflictResponse.data) 
        : new Set();
      
      deviceOptions.value = deviceResponse.data.map((device: any) => {
        const isDisabled = conflictDeviceIds.has(device.id);
        return {
          label: `${device.name || device.id}${isDisabled ? ' (已在算法任务中使用)' : ''}`,
          value: device.id,
          disabled: isDisabled,
        };
      });
      
      // 更新表单schema，设置禁用选项
      updateSchema({
        field: 'device_ids',
        componentProps: {
          options: deviceOptions.value,
        },
      });
    }
  } catch (error) {
    console.error('加载设备列表失败', error);
  }
};

const handleReset = async () => {
  resetFields();
  if (modalData.value.record) {
    // 编辑模式，恢复到原始值
    const record = modalData.value.record;
    await setFieldsValue({
      task_name: record.task_name,
      device_ids: record.device_ids || [],
      output_format: record.output_format || 'rtmp',
      output_quality: record.output_quality || 'high',
      output_bitrate: record.output_bitrate,
      description: record.description,
      is_enabled: record.is_enabled !== undefined ? record.is_enabled : false,
    });
  } else {
    // 新建模式，重置为默认值
    await setFieldsValue({
      output_format: 'rtmp',
      output_quality: 'high',
      is_enabled: false,
    });
  }
};

const handleSubmit = async () => {
  try {
    const values = await validate();
    confirmLoading.value = true;
    setDrawerProps({ confirmLoading: true });
    
    // 新建任务时，默认设置为未启用状态（需要通过启动按钮来启动）
    if (!taskId.value) {
      values.is_enabled = false;
    }
    
    if (taskId.value) {
      // 更新
      const response = await updateStreamForwardTask(taskId.value, values);
      if (response && (response as any).id) {
        createMessage.success('更新成功');
        emit('success');
        closeDrawer();
      } else if (response && typeof response === 'object' && 'code' in response) {
        if ((response as any).code === 0) {
          createMessage.success('更新成功');
          emit('success');
          closeDrawer();
        } else {
          createMessage.error((response as any).msg || '更新失败');
        }
      } else {
        createMessage.error('更新失败');
      }
    } else {
      // 创建
      const response = await createStreamForwardTask(values);
      if (response && (response as any).id) {
        createMessage.success('创建成功');
        emit('success');
        closeDrawer();
      } else if (response && typeof response === 'object' && 'code' in response) {
        if ((response as any).code === 0) {
          createMessage.success('创建成功');
          emit('success');
          closeDrawer();
        } else {
          createMessage.error((response as any).msg || '创建失败');
        }
      } else {
        createMessage.error('创建失败');
      }
    }
  } catch (error: any) {
    console.error('提交失败', error);
    // 尝试从错误对象中提取错误消息
    let errorMsg = '提交失败';
    if (error?.response?.data?.msg) {
      errorMsg = error.response.data.msg;
    } else if (error?.data?.msg) {
      errorMsg = error.data.msg;
    } else if (error?.msg) {
      errorMsg = error.msg;
    } else if (typeof error === 'string') {
      errorMsg = error;
    } else if (error?.message) {
      errorMsg = error.message;
    }
    createMessage.error(errorMsg);
  } finally {
    confirmLoading.value = false;
    setDrawerProps({ confirmLoading: false });
  }
};
</script>

<style lang="less" scoped>
.form-content {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 0;
}

.footer-buttons {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  gap: 8px;
}

:deep(.ant-form-item) {
  margin-bottom: 24px;
}

:deep(.ant-form-item-label) {
  padding-bottom: 8px;
}

:deep(.ant-form-item-label > label) {
  font-weight: 500;
  color: rgba(0, 0, 0, 0.85);
}

:deep(.ant-input),
:deep(.ant-select-selector),
:deep(.ant-input-number) {
  border-radius: 4px;
  transition: all 0.3s;
  
  &:hover {
    border-color: #40a9ff;
  }
  
  &:focus,
  &.ant-input-focused,
  &.ant-select-focused .ant-select-selector {
    border-color: #1890ff;
    box-shadow: 0 0 0 2px rgba(24, 144, 255, 0.2);
  }
}

:deep(.ant-input-textarea) {
  .ant-input {
    resize: vertical;
  }
}

:deep(.ant-switch) {
  min-width: 44px;
}

:deep(.ant-form-item-explain) {
  margin-top: 4px;
  font-size: 12px;
  line-height: 1.5;
}

:deep(.ant-form-item-extra) {
  margin-top: 4px;
  font-size: 12px;
  color: rgba(0, 0, 0, 0.45);
  line-height: 1.5;
}
</style>

