<template>
  <BasicDrawer 
    v-bind="$attrs" 
    @register="register" 
    :title="modalTitle" 
    @ok="handleSubmit" 
    width="600"
    placement="right"
  >
    <BasicForm @register="registerForm" />
  </BasicDrawer>
</template>

<script lang="ts" setup>
import { computed, ref } from 'vue';
import { BasicDrawer, useDrawerInner } from '@/components/Drawer';
import { BasicForm, useForm } from '@/components/Form';
import { useMessage } from '@/hooks/web/useMessage';
import {
  createFrameExtractor,
  updateFrameExtractor,
  type FrameExtractor,
} from '@/api/device/algorithm_task';

defineOptions({ name: 'FrameExtractorModal' });

const { createMessage } = useMessage();
const emit = defineEmits(['success', 'register']);

const [registerForm, { setFieldsValue, validate, resetFields, updateSchema }] = useForm({
  labelWidth: 120,
  baseColProps: { span: 24 },
  schemas: [
    {
      field: 'extractor_name',
      label: '抽帧器名称',
      component: 'Input',
      required: true,
      componentProps: {
        placeholder: '请输入抽帧器名称',
      },
    },
    {
      field: 'extractor_type',
      label: '抽帧类型',
      component: 'Select',
      required: true,
      componentProps: {
        placeholder: '请选择抽帧类型',
        options: [
          { label: '按间隔', value: 'interval' },
          { label: '按时间', value: 'time' },
        ],
      },
    },
    {
      field: 'interval',
      label: '间隔',
      component: 'InputNumber',
      required: true,
      componentProps: {
        placeholder: '请输入间隔（每N帧或每N秒）',
        min: 1,
      },
    },
    {
      field: 'description',
      label: '描述',
      component: 'InputTextArea',
      componentProps: {
        placeholder: '请输入描述',
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

const modalData = ref<{ type?: string; record?: FrameExtractor }>({});

const modalTitle = computed(() => {
  if (modalData.value.type === 'view') return '查看抽帧器';
  if (modalData.value.type === 'edit') return '编辑抽帧器';
  return '新建抽帧器';
});

const [register, { setDrawerProps, closeDrawer }] = useDrawerInner(async (data) => {
  modalData.value = data || {};
  resetFields();
  
  if (modalData.value.record) {
    const record = modalData.value.record;
    await setFieldsValue({
      extractor_name: record.extractor_name,
      extractor_type: record.extractor_type,
      interval: record.interval,
      description: record.description,
      is_enabled: record.is_enabled,
    });
    
    // 查看模式禁用表单
    if (modalData.value.type === 'view') {
      updateSchema([
        { field: 'extractor_name', componentProps: { disabled: true } },
        { field: 'extractor_type', componentProps: { disabled: true } },
        { field: 'interval', componentProps: { disabled: true } },
        { field: 'description', componentProps: { disabled: true } },
        { field: 'is_enabled', componentProps: { disabled: true } },
      ]);
    }
  } else {
    // 新建模式，设置默认值
    await setFieldsValue({
      extractor_type: 'interval',
      interval: 1,
      is_enabled: true,
    });
  }
});

const handleSubmit = async () => {
  try {
    const values = await validate();
    setDrawerProps({ confirmLoading: true });
    
    if (modalData.value.type === 'edit' && modalData.value.record) {
      const response = await updateFrameExtractor(modalData.value.record.id, values);
      if (response.code === 0) {
        createMessage.success('更新成功');
        emit('success');
        closeDrawer();
      } else {
        createMessage.error(response.msg || '更新失败');
      }
    } else {
      const response = await createFrameExtractor(values);
      if (response.code === 0) {
        createMessage.success('创建成功');
        emit('success');
        closeDrawer();
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
</script>

