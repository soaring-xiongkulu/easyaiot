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
import { listFrameExtractors } from '@/api/device/algorithm_task';
import { listSorters } from '@/api/device/algorithm_task';
import AlgorithmServiceList from './AlgorithmServiceList.vue';

defineOptions({ name: 'AlgorithmTaskModal' });

const { createMessage } = useMessage();
const emit = defineEmits(['success', 'register']);

const activeTab = ref('basic');
const taskId = ref<number | null>(null);
const formValues = ref<any>({});

const deviceOptions = ref<Array<{ label: string; value: string }>>([]);
const extractorOptions = ref<Array<{ label: string; value: number }>>([]);
const sorterOptions = ref<Array<{ label: string; value: number }>>([]);

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

// 加载抽帧器列表
const loadExtractors = async () => {
  try {
    const response = await listFrameExtractors({ pageNo: 1, pageSize: 1000 });
    extractorOptions.value = (response.data || []).map((item) => ({
      label: item.extractor_name,
      value: item.id,
    }));
  } catch (error) {
    console.error('加载抽帧器列表失败', error);
  }
};

// 加载排序器列表
const loadSorters = async () => {
  try {
    const response = await listSorters({ pageNo: 1, pageSize: 1000 });
    sorterOptions.value = (response.data || []).map((item) => ({
      label: item.sorter_name,
      value: item.id,
    }));
  } catch (error) {
    console.error('加载排序器列表失败', error);
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
      field: 'extractor_id',
      label: '抽帧器',
      component: 'Select',
      componentProps: {
        placeholder: '请选择抽帧器（可选）',
        options: extractorOptions,
        allowClear: true,
      },
    },
    {
      field: 'sorter_id',
      label: '排序器',
      component: 'Select',
      componentProps: {
        placeholder: '请选择排序器（可选）',
        options: sorterOptions,
        allowClear: true,
      },
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
  await Promise.all([loadDevices(), loadExtractors(), loadSorters()]);
  
  if (modalData.value.record) {
    const record = modalData.value.record;
    taskId.value = record.id;
    await setFieldsValue({
      task_name: record.task_name,
      device_ids: record.device_ids || [],
      extractor_id: record.extractor_id,
      sorter_id: record.sorter_id,
      description: record.description,
      is_enabled: record.is_enabled,
    });
    
    // 查看模式禁用表单
    if (modalData.value.type === 'view') {
      updateSchema([
        { field: 'task_name', componentProps: { disabled: true } },
        { field: 'extractor_id', componentProps: { disabled: true } },
        { field: 'device_ids', componentProps: { disabled: true } },
        { field: 'sorter_id', componentProps: { disabled: true } },
        { field: 'description', componentProps: { disabled: true } },
        { field: 'is_enabled', componentProps: { disabled: true } },
      ]);
    }
  } else {
    // 新建模式，设置默认值
    await setFieldsValue({
      is_enabled: true,
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

