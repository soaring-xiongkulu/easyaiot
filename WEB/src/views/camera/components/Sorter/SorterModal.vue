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
  createSorter,
  updateSorter,
  type Sorter,
} from '@/api/device/algorithm_task';

defineOptions({ name: 'SorterModal' });

const { createMessage } = useMessage();
const emit = defineEmits(['success', 'register']);

const [registerForm, { setFieldsValue, validate, resetFields, updateSchema }] = useForm({
  labelWidth: 120,
  baseColProps: { span: 24 },
  schemas: [
    {
      field: 'sorter_name',
      label: '排序器名称',
      component: 'Input',
      required: true,
      componentProps: {
        placeholder: '请输入排序器名称',
      },
    },
    {
      field: 'sorter_type',
      label: '排序类型',
      component: 'Select',
      required: true,
      componentProps: {
        placeholder: '请选择排序类型',
        options: [
          { label: '置信度', value: 'confidence' },
          { label: '时间', value: 'time' },
          { label: '分数', value: 'score' },
        ],
      },
    },
    {
      field: 'sort_order',
      label: '排序顺序',
      component: 'Select',
      required: true,
      componentProps: {
        placeholder: '请选择排序顺序',
        options: [
          { label: '升序', value: 'asc' },
          { label: '降序', value: 'desc' },
        ],
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

const modalData = ref<{ type?: string; record?: Sorter }>({});

const modalTitle = computed(() => {
  if (modalData.value.type === 'view') return '查看排序器';
  if (modalData.value.type === 'edit') return '编辑排序器';
  return '新建排序器';
});

const [register, { setDrawerProps, closeDrawer }] = useDrawerInner(async (data) => {
  modalData.value = data || {};
  resetFields();
  
  if (modalData.value.record) {
    const record = modalData.value.record;
    await setFieldsValue({
      sorter_name: record.sorter_name,
      sorter_type: record.sorter_type,
      sort_order: record.sort_order,
      description: record.description,
      is_enabled: record.is_enabled,
    });
    
    // 查看模式禁用表单
    if (modalData.value.type === 'view') {
      updateSchema([
        { field: 'sorter_name', componentProps: { disabled: true } },
        { field: 'sorter_type', componentProps: { disabled: true } },
        { field: 'sort_order', componentProps: { disabled: true } },
        { field: 'description', componentProps: { disabled: true } },
        { field: 'is_enabled', componentProps: { disabled: true } },
      ]);
    }
  } else {
    // 新建模式，设置默认值
    await setFieldsValue({
      sorter_type: 'confidence',
      sort_order: 'desc',
      is_enabled: true,
    });
  }
});

const handleSubmit = async () => {
  try {
    const values = await validate();
    setDrawerProps({ confirmLoading: true });
    
    if (modalData.value.type === 'edit' && modalData.value.record) {
      const response = await updateSorter(modalData.value.record.id, values);
      if (response.code === 0) {
        createMessage.success('更新成功');
        emit('success');
        closeDrawer();
      } else {
        createMessage.error(response.msg || '更新失败');
      }
    } else {
      const response = await createSorter(values);
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

