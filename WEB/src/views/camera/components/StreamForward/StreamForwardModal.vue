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
        <Button v-if="!isViewMode" @click="handleReset" class="mr-2">重置</Button>
        <Button v-if="!isViewMode" type="primary" :loading="confirmLoading" @click="handleSubmit">提交</Button>
      </div>
    </template>
    <div class="form-content">
      <a-alert
        v-if="showRuntimeBanner"
        class="runtime-version-banner mb-3"
        type="info"
        show-icon
        :message="runtimeBannerText"
      />
      <BasicForm @register="registerForm" @field-value-change="handleFieldValueChange" />
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
import { getRuntimeInfo } from '@/api/device/algorithm_task';
import { getDeviceList } from '@/api/device/camera';
import { getNodePage } from '@/api/device/node';
import { nodeHasFunction } from '@/views/node/utils/constants';
import { Button } from '@/components/Button'
defineOptions({ name: 'StreamForwardModal' });

const { createMessage } = useMessage();
const emit = defineEmits(['success', 'register']);

const schedulePolicyOptions = [
  { label: '本机部署', value: 'local' },
  { label: '自动调度节点', value: 'auto' },
  { label: '指定节点', value: 'node' },
];

const taskId = ref<number | null>(null);
const confirmLoading = ref(false);
const deviceOptions = ref<Array<{ label: string; value: string }>>([]);
const nodeOptions = ref<Array<{ label: string; value: number }>>([]);
const formValues = ref<any>({});
const runtimeInfo = ref<{ ready?: boolean; version?: string | null; binPath?: string | null } | null>(null);
const modalData = ref<{ type?: string; record?: StreamForwardTask }>({});

const showRuntimeBanner = computed(() => {
  const ex = String(formValues.value?.executor || 'cpp').toLowerCase();
  return ex === 'cpp' || ex === 'c++' || ex === 'runtime';
});

const runtimeBannerText = computed(() => {
  const info = runtimeInfo.value;
  if (info?.ready) {
    return `本机推流运行时已就绪${info.version ? `（${info.version}）` : ''}，性能优先推流将以低负载方式转发`;
  }
  return '本机推流运行时未就绪：启动「性能优先」任务时将尝试自动编译；远程节点需先在「节点管理 → 业务运行时分发」完成安装';
});

async function loadRuntimeInfo() {
  try {
    const data = await getRuntimeInfo();
    runtimeInfo.value = data || { ready: false };
  } catch {
    runtimeInfo.value = { ready: false };
  }
}

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
  runtimeInfo.value = null;
  
  // 加载设备列表与计算节点
  await Promise.all([loadDeviceOptions(), loadNodes(), loadRuntimeInfo()]);
  
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
      schedule_policy: record.schedule_policy || 'local',
      prefer_gpu: record.prefer_gpu !== false,
      target_node_id: record.target_node_id ?? undefined,
      executor: record.executor || 'cpp',
    });
    
    // 查看模式禁用表单
    if (modalData.value.type === 'view') {
      updateSchema([
        { field: 'task_name', componentProps: { disabled: true } },
        { field: 'device_ids', componentProps: { disabled: true } },
        { field: 'executor', componentProps: { disabled: true } },
        { field: 'output_format', componentProps: { disabled: true } },
        { field: 'output_quality', componentProps: { disabled: true } },
        { field: 'output_bitrate', componentProps: { disabled: true } },
        { field: 'description', componentProps: { disabled: true } },
        { field: 'is_enabled', componentProps: { disabled: true } },
        { field: 'schedule_policy', componentProps: { disabled: true } },
        { field: 'target_node_id', componentProps: { disabled: true } },
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
      schedule_policy: 'local',
      prefer_gpu: true,
      executor: 'cpp',
    });
    setDrawerProps({ showOkBtn: true });
  }
  
  setDrawerProps({ confirmLoading: false });
});

function handleFieldValueChange(field: string, value: unknown) {
  formValues.value = { ...formValues.value, [field]: value };
  if (field === 'executor' && String(value || '').toLowerCase() === 'cpp' && !runtimeInfo.value) {
    loadRuntimeInfo();
  }
}

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
      field: 'executor',
      label: '推流引擎',
      component: 'Select',
      defaultValue: 'cpp',
      componentProps: {
        placeholder: '请选择推流引擎',
        options: [
          { label: '性能优先', value: 'cpp' },
          { label: '兼容优先', value: 'python' },
        ],
      },
      helpMessage: '性能优先：原样转发，CPU 占用低，适合多路摄像头同时推流；兼容优先：可处理更多视频编码（如 HEVC），个别摄像头推流异常时可选用',
    },
    {
      field: 'schedule_policy',
      label: '调度策略',
      component: 'Select',
      defaultValue: 'local',
      componentProps: {
        placeholder: '请选择调度策略',
        options: schedulePolicyOptions,
      },
      helpMessage: '本机：在当前视频服务所在机器部署；自动/指定节点：多路摄像头默认按设备分片分散到集群节点。「性能优先」调度到节点前，请先在「节点管理 → 业务运行时分发」完成运行时安装',
    },
    {
      field: 'prefer_gpu',
      label: '优先 GPU 节点',
      component: 'Switch',
      defaultValue: true,
      componentProps: {
        checkedChildren: '是',
        unCheckedChildren: '否',
      },
      ifShow: ({ values }) => values.schedule_policy === 'auto',
      helpMessage: '自动调度时优先选择 GPU 节点；关闭则优先 CPU 计算节点',
    },
    {
      field: 'target_node_id',
      label: '目标节点',
      component: 'Select',
      componentProps: {
        placeholder: '选择在线计算节点',
        options: nodeOptions,
        showSearch: true,
        allowClear: true,
        filterOption: (input: string, option: any) => {
          return option.label.toLowerCase().indexOf(input.toLowerCase()) >= 0;
        },
      },
      ifShow: ({ values }) => values.schedule_policy === 'node',
      required: ({ values }) => values.schedule_policy === 'node',
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

const loadNodes = async () => {
  try {
    const res = await getNodePage(
      { pageNo: 1, pageSize: 200, status: 'online' },
      { errorMessageMode: 'none' },
    );
    const page = res?.data || res;
    const list = (page?.list || []).filter(
      (node: any) => nodeHasFunction(node, 'forward'),
    );
    nodeOptions.value = list.map((node: any) => ({
      label: `${node.name} (${node.host})`,
      value: node.id,
    }));
    updateSchema({
      field: 'target_node_id',
      componentProps: {
        options: nodeOptions.value,
      },
    });
  } catch (error) {
    console.error('加载节点列表失败', error);
    nodeOptions.value = [];
  }
};

const loadDeviceOptions = async () => {
  try {
    const deviceResponse = await getDeviceList({ pageNo: 1, pageSize: 1000 });
    if (deviceResponse.code === 0 && deviceResponse.data) {
      deviceOptions.value = deviceResponse.data.map((device: any) => ({
        label: device.name || device.id,
        value: device.id,
        disabled: false,
      }));
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
    const record = modalData.value.record;
    await setFieldsValue({
      task_name: record.task_name,
      device_ids: record.device_ids || [],
      output_format: record.output_format || 'rtmp',
      output_quality: record.output_quality || 'high',
      output_bitrate: record.output_bitrate,
      description: record.description,
      is_enabled: record.is_enabled !== undefined ? record.is_enabled : false,
      schedule_policy: record.schedule_policy || 'local',
      prefer_gpu: record.prefer_gpu !== false,
      target_node_id: record.target_node_id ?? undefined,
      executor: record.executor || 'cpp',
    });
  } else {
    await setFieldsValue({
      output_format: 'rtmp',
      output_quality: 'high',
      is_enabled: false,
      schedule_policy: 'local',
      prefer_gpu: true,
      executor: 'cpp',
    });
  }
};

const handleSubmit = async () => {
  try {
    const values = await validate();
    if (values.schedule_policy === 'node' && !values.target_node_id) {
      createMessage.error('请选择目标节点');
      return;
    }
    if (values.schedule_policy !== 'node') {
      values.target_node_id = null;
    }
    if (values.schedule_policy !== 'auto') {
      values.prefer_gpu = true;
    }
    confirmLoading.value = true;
    setDrawerProps({ confirmLoading: true });
    
    // 新建任务时，默认设置为未启用状态（需要通过启动按钮来启动）
    if (!taskId.value) {
      values.is_enabled = false;
    }
    
    if (taskId.value) {
      // 更新
      const response = await updateStreamForwardTask(taskId.value, values);
      const syncAction = (response as any)?.sync_action;
      const successMsg =
        syncAction === 'full_restart'
          ? '更新成功，调度策略已变更，任务已全量重启'
          : syncAction === 'rebalance'
            ? '更新成功，摄像头列表已变更，正在重平衡部署'
            : '更新成功';
      if (response && (response as any).id) {
        createMessage.success(successMsg);
        emit('success');
        closeDrawer();
      } else if (response && typeof response === 'object' && 'code' in response) {
        if ((response as any).code === 0) {
          createMessage.success(successMsg);
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

