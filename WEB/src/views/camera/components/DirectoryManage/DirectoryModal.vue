<template>
  <BasicModal
    v-bind="$attrs"
    @register="register"
    :title="modalTitle"
    @ok="handleSubmit"
    :width="800"
  >
    <BasicForm @register="registerForm" />
  </BasicModal>
</template>

<script lang="ts" setup>
import { ref, computed } from 'vue';
import { BasicModal, useModalInner } from '@/components/Modal';
import { BasicForm, useForm } from '@/components/Form';
import { useMessage } from '@/hooks/web/useMessage';
import {
  createDirectory,
  updateDirectory,
  getDirectoryList,
  type DeviceDirectory,
} from '@/api/device/camera';

const emit = defineEmits(['success', 'register']);

const { createMessage } = useMessage();
const [registerForm, { setFieldsValue, validate, resetFields, updateSchema }] = useForm({
  labelWidth: 100,
  baseColProps: { span: 24 },
  schemas: [
    {
      field: 'name',
      label: '目录名称',
      component: 'Input',
      required: true,
      componentProps: {
        placeholder: '请输入目录名称',
      },
    },
    {
      field: 'parent_id',
      label: '父目录',
      component: 'TreeSelect',
      componentProps: {
        placeholder: '请选择父目录（不选则为根目录）',
        treeData: [],
        allowClear: true,
        treeDefaultExpandAll: true,
        fieldNames: {
          label: 'name',
          value: 'id',
          children: 'children',
        },
      },
    },
    {
      field: 'description',
      label: '目录描述',
      component: 'InputTextArea',
      componentProps: {
        placeholder: '请输入目录描述',
        rows: 4,
      },
    },
    {
      field: 'sort_order',
      label: '排序顺序',
      component: 'InputNumber',
      componentProps: {
        placeholder: '请输入排序顺序',
        min: 0,
        defaultValue: 0,
      },
    },
  ],
  showActionButtonGroup: false,
});

const [register, { setModalProps, closeModal }] = useModalInner(async (data) => {
  resetFields();
  setModalProps({ confirmLoading: false });
  
  // 加载目录树用于父目录选择
  await loadParentDirectoryOptions();
  
  if (data.type === 'edit' && data.record) {
    setFieldsValue({
      name: data.record.name,
      parent_id: data.record.parent_id,
      description: data.record.description,
      sort_order: data.record.sort_order,
    });
    currentId.value = data.record.id;
  } else {
    // 创建模式，设置默认父目录
    if (data.parent_id) {
      setFieldsValue({
        parent_id: data.parent_id,
      });
    }
    currentId.value = null;
  }
});

const currentId = ref<number | null>(null);
const parentDirectoryOptions = ref<any[]>([]);

const modalTitle = computed(() => {
  return currentId.value ? '编辑目录' : '新建目录';
});

// 加载父目录选项
const loadParentDirectoryOptions = async () => {
  try {
    const response = await getDirectoryList();
    // API返回格式: { code: 0, data: [...], msg: 'success' } 或直接返回data
    const data = response.code !== undefined ? response.data : response;
    if (data && Array.isArray(data)) {
      // 转换目录树为TreeSelect需要的格式
      const convertToTreeSelect = (directories: DeviceDirectory[], excludeId?: number): any[] => {
        return directories
          .filter((dir) => dir.id !== excludeId) // 排除当前编辑的目录
          .map((dir) => ({
            id: dir.id,
            name: dir.name,
            children: dir.children ? convertToTreeSelect(dir.children, excludeId) : [],
          }));
      };
      parentDirectoryOptions.value = convertToTreeSelect(data, currentId.value || undefined);
      
      // 更新表单中的TreeSelect选项
      updateSchema({
        field: 'parent_id',
        componentProps: {
          treeData: parentDirectoryOptions.value,
        },
      });
    }
  } catch (error) {
    console.error('加载父目录选项失败', error);
  }
};

const handleSubmit = async () => {
  try {
    const values = await validate();
    setModalProps({ confirmLoading: true });
    
    if (currentId.value) {
      // 更新目录
      const response = await updateDirectory(currentId.value, {
        name: values.name,
        parent_id: values.parent_id || null,
        description: values.description,
        sort_order: values.sort_order || 0,
      });
      // API返回格式: { code: 0, msg: '...' } 或直接返回data
      const result = response.code !== undefined ? response : { code: 0, msg: '更新成功' };
      if (result.code === 0) {
        createMessage.success('更新成功');
        closeModal();
        emit('success');
      } else {
        createMessage.error(result.msg || '更新失败');
      }
    } else {
      // 创建目录
      const response = await createDirectory({
        name: values.name,
        parent_id: values.parent_id || null,
        description: values.description,
        sort_order: values.sort_order || 0,
      });
      // API返回格式: { code: 0, msg: '...' } 或直接返回data
      const result = response.code !== undefined ? response : { code: 0, msg: '创建成功' };
      if (result.code === 0) {
        createMessage.success('创建成功');
        closeModal();
        emit('success');
      } else {
        createMessage.error(result.msg || '创建失败');
      }
    }
  } catch (error) {
    console.error('提交失败', error);
    createMessage.error('操作失败');
  } finally {
    setModalProps({ confirmLoading: false });
  }
};
</script>

<style lang="less" scoped>
</style>

