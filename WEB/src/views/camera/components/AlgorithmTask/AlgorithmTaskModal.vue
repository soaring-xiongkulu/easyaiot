<template>
  <BasicDrawer 
    v-bind="$attrs" 
    @register="register" 
    :title="modalTitle" 
    @ok="handleSubmit" 
    width="800"
    placement="right"
  >
    <a-tabs v-model:activeKey="activeTab">
      <a-tab-pane key="basic" tab="基础配置">
        <BasicForm @register="registerForm" />
      </a-tab-pane>
      <a-tab-pane key="services" tab="算法服务" :disabled="!taskId">
        <AlgorithmServiceList
          v-if="taskId"
          :task-id="taskId"
          @refresh="handleServicesRefresh"
        />
        <a-empty v-else description="请先保存基础配置，然后才能配置算法服务" />
      </a-tab-pane>
    </a-tabs>
  </BasicDrawer>
</template>

<script lang="ts" setup>
import { ref, computed } from 'vue';
import { BasicDrawer, useDrawerInner } from '@/components/Drawer';
import { BasicForm, useForm } from '@/components/Form';
import { useMessage } from '@/hooks/web/useMessage';
import {
  createAlgorithmTask,
  updateAlgorithmTask,
  type AlgorithmTask,
} from '@/api/device/algorithm_task';
import { getDeviceList } from '@/api/device/camera';
import { getSnapSpaceList } from '@/api/device/snap';
import AlgorithmServiceList from './AlgorithmServiceList.vue';

defineOptions({ name: 'AlgorithmTaskModal' });

const { createMessage } = useMessage();
const emit = defineEmits(['success', 'register']);

const activeTab = ref('basic');
const taskId = ref<number | null>(null);
const formValues = ref<any>({});

const deviceOptions = ref<Array<{ label: string; value: string }>>([]);
const spaceOptions = ref<Array<{ label: string; value: number }>>([]);

// 加载设备列表
const loadDevices = async () => {
  try {
    const response = await getDeviceList({ pageNo: 1, pageSize: 1000 });
    deviceOptions.value = (response.data || []).map((item) => ({
      label: item.name || item.id,
      value: item.id,
    }));
  } catch (error) {
    console.error('加载设备列表失败', error);
  }
};

// 加载抓拍空间列表
const loadSpaces = async () => {
  try {
    const response = await getSnapSpaceList({ pageNo: 1, pageSize: 1000 });
    spaceOptions.value = (response.data || []).map((item) => ({
      label: item.space_name,
      value: item.id,
    }));
  } catch (error) {
    console.error('加载抓拍空间列表失败', error);
  }
};

const [registerForm, { setFieldsValue, validate, resetFields, updateSchema }] = useForm({
  labelWidth: 120,
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
      field: 'task_type',
      label: '任务类型',
      component: 'Select',
      required: true,
      componentProps: {
        placeholder: '请选择任务类型',
        options: [
          { label: '实时算法任务', value: 'realtime' },
          { label: '抓拍算法任务', value: 'snap' },
        ],
      },
    },
    {
      field: 'device_ids',
      label: '关联摄像头',
      component: 'Select',
      required: false,
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
    },
    {
      field: 'space_id',
      label: '抓拍空间',
      component: 'Select',
      required: true,
      componentProps: {
        placeholder: '请选择抓拍空间',
        options: spaceOptions,
      },
      ifShow: ({ values }) => values.task_type === 'snap',
    },
    {
      field: 'cron_expression',
      label: 'Cron表达式',
      component: 'Input',
      required: true,
      componentProps: {
        placeholder: '例如: 0 */5 * * * * (每5分钟)',
      },
      helpMessage: '标准Cron表达式，例如: 0 */5 * * * * 表示每5分钟执行一次',
      ifShow: ({ values }) => values.task_type === 'snap',
    },
    {
      field: 'frame_skip',
      label: '抽帧间隔',
      component: 'InputNumber',
      componentProps: {
        placeholder: '每N帧抓一次',
        min: 1,
      },
      helpMessage: '抽帧模式下，每N帧抓一次（默认1）',
      ifShow: ({ values }) => values.task_type === 'snap',
    },
    {
      field: 'description',
      label: '任务描述',
      component: 'InputTextArea',
      componentProps: {
        placeholder: '请输入任务描述',
        rows: 4,
      },
    },
    {
      field: 'is_enabled',
      label: '是否启用',
      component: 'Switch',
      componentProps: {
        checkedChildren: '是',
        unCheckedChildren: '否',
      },
    },
  ],
  showActionButtonGroup: false,
});

const modalData = ref<{ type?: string; record?: AlgorithmTask }>({});

const modalTitle = computed(() => {
  if (modalData.value.type === 'view') return '查看算法任务';
  if (modalData.value.type === 'edit') return '编辑算法任务';
  return '新建算法任务';
});

const [register, { setDrawerProps, closeDrawer }] = useDrawerInner(async (data) => {
  modalData.value = data || {};
  taskId.value = null;
  resetFields();
  
  // 加载选项数据
  await Promise.all([loadDevices(), loadSpaces()]);
  
  if (modalData.value.record) {
    const record = modalData.value.record;
    taskId.value = record.id;
    await setFieldsValue({
      task_name: record.task_name,
      task_type: record.task_type || 'realtime',
      device_ids: record.device_ids || [],
      space_id: record.space_id,
      cron_expression: record.cron_expression,
      frame_skip: record.frame_skip || 1,
      description: record.description,
      is_enabled: record.is_enabled,
    });
    
    // 查看模式禁用表单
    if (modalData.value.type === 'view') {
      updateSchema([
        { field: 'task_name', componentProps: { disabled: true } },
        { field: 'task_type', componentProps: { disabled: true } },
        { field: 'device_ids', componentProps: { disabled: true } },
        { field: 'space_id', componentProps: { disabled: true } },
        { field: 'cron_expression', componentProps: { disabled: true } },
        { field: 'frame_skip', componentProps: { disabled: true } },
        { field: 'description', componentProps: { disabled: true } },
        { field: 'is_enabled', componentProps: { disabled: true } },
      ]);
    }
  } else {
    // 新建模式，设置默认值
    await setFieldsValue({
      task_type: 'realtime',
      is_enabled: false,
      frame_skip: 1,
    });
  }
});

const handleSubmit = async () => {
  try {
    const values = await validate();
    setDrawerProps({ confirmLoading: true });
    
    if (modalData.value.type === 'edit' && modalData.value.record) {
      const response = await updateAlgorithmTask(modalData.value.record.id, values);
      if (response.code === 0) {
        createMessage.success('更新成功');
        taskId.value = modalData.value.record.id;
        emit('success');
        closeDrawer();
      } else {
        createMessage.error(response.msg || '更新失败');
      }
    } else {
      const response = await createAlgorithmTask(values);
      if (response.code === 0 && response.data) {
        taskId.value = response.data.id;
        createMessage.success('创建成功');
        // 创建成功后切换到算法服务配置标签页
        activeTab.value = 'services';
        emit('success');
      } else {
        createMessage.error(response.msg || '创建失败');
      }
    }
  } catch (error) {
    console.error('提交失败', error);
    createMessage.error('提交失败');
  } finally {
    setDrawerProps({ confirmLoading: false });
  }
};

const handleServicesRefresh = () => {
  emit('success');
};
</script>

