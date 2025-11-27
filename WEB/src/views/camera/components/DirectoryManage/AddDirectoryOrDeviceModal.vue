<template>
  <BasicModal
    v-bind="$attrs"
    @register="register"
    title="添加目录/摄像头"
    @ok="handleSubmit"
    :width="650"
  >
    <BasicForm @register="registerForm" />
  </BasicModal>
</template>

<script lang="ts" setup>
import { ref, computed, watch } from 'vue';
import { BasicModal, useModalInner } from '@/components/Modal';
import { BasicForm, useForm } from '@/components/Form';
import { useMessage } from '@/hooks/web/useMessage';
import {
  createDirectory,
  getDirectoryList,
  getDeviceList,
  moveDeviceToDirectory,
  type DeviceDirectory,
  type DeviceInfo,
} from '@/api/device/camera';

const emit = defineEmits(['success', 'register']);

const { createMessage } = useMessage();
const [registerForm, { setFieldsValue, validate, resetFields, updateSchema }] = useForm({
  labelWidth: 100,
  baseColProps: { span: 24 },
  schemas: [
    {
      field: 'addType',
      label: '添加类型',
      component: 'RadioGroup',
      required: true,
      defaultValue: 'directory',
      componentProps: {
        options: [
          { label: '添加目录', value: 'directory' },
          { label: '添加摄像头', value: 'device' },
        ],
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
      field: 'name',
      label: '目录名称',
      component: 'Input',
      required: true,
      componentProps: {
        placeholder: '请输入目录名称',
      },
      ifShow: ({ values }) => values.addType === 'directory',
    },
    {
      field: 'description',
      label: '目录描述',
      component: 'InputTextArea',
      componentProps: {
        placeholder: '请输入目录描述',
        rows: 4,
      },
      ifShow: ({ values }) => values.addType === 'directory',
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
      ifShow: ({ values }) => values.addType === 'directory',
    },
    {
      field: 'device_ids',
      label: '选择摄像头',
      component: 'Select',
      required: true,
      componentProps: {
        mode: 'multiple',
        placeholder: '请选择摄像头（支持多选，可重复添加）',
        options: [],
        showSearch: true,
        filterOption: (input: string, option: any) => {
          return option.label.toLowerCase().includes(input.toLowerCase());
        },
      },
      ifShow: ({ values }) => values.addType === 'device',
    },
  ],
  showActionButtonGroup: false,
});

const [register, { setModalProps, closeModal }] = useModalInner(async (data) => {
  resetFields();
  setModalProps({ confirmLoading: false });
  
  // 加载目录树用于父目录选择
  await loadParentDirectoryOptions();
  
  // 加载摄像头列表
  await loadDeviceOptions();
  
  // 如果传入了默认类型和父目录ID，设置默认值
  if (data) {
    if (data.defaultType) {
      await setFieldsValue({ addType: data.defaultType });
    }
    if (data.defaultParentId) {
      await setFieldsValue({ parent_id: data.defaultParentId });
    }
  }
});

const parentDirectoryOptions = ref<any[]>([]);
const deviceOptions = ref<any[]>([]);

// 加载父目录选项
const loadParentDirectoryOptions = async () => {
  try {
    const response = await getDirectoryList();
    const data = response.code !== undefined ? response.data : response;
    if (data && Array.isArray(data)) {
      const convertToTreeSelect = (directories: DeviceDirectory[]): any[] => {
        return directories.map((dir) => ({
          id: dir.id,
          name: dir.name,
          children: dir.children ? convertToTreeSelect(dir.children) : [],
        }));
      };
      parentDirectoryOptions.value = convertToTreeSelect(data);
      
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

// 加载摄像头选项
const loadDeviceOptions = async () => {
  try {
    const response = await getDeviceList({
      pageNo: 1,
      pageSize: 1000, // 获取所有设备
    });
    const data = response.code !== undefined ? response.data : response;
    if (data && Array.isArray(data)) {
      deviceOptions.value = data.map((device: DeviceInfo) => ({
        label: `${device.name || device.id} (${device.model || '-'})`,
        value: device.id,
      }));
      
      updateSchema({
        field: 'device_ids',
        componentProps: {
          options: deviceOptions.value,
        },
      });
    }
  } catch (error) {
    console.error('加载摄像头列表失败', error);
    createMessage.error('加载摄像头列表失败');
  }
};

const handleSubmit = async () => {
  try {
    const values = await validate();
    setModalProps({ confirmLoading: true });
    
    if (values.addType === 'directory') {
      // 创建目录
      const response = await createDirectory({
        name: values.name,
        parent_id: values.parent_id || null,
        description: values.description,
        sort_order: values.sort_order || 0,
      });
      const result = response.code !== undefined ? response : { code: 0, msg: '创建成功' };
      if (result.code === 0) {
        createMessage.success('目录创建成功');
        closeModal();
        emit('success');
      } else {
        createMessage.error(result.msg || '创建失败');
      }
    } else {
      // 添加摄像头到目录
      if (!values.device_ids || values.device_ids.length === 0) {
        createMessage.error('请至少选择一个摄像头');
        setModalProps({ confirmLoading: false });
        return;
      }
      
      if (!values.parent_id) {
        createMessage.error('添加摄像头时必须选择目录');
        setModalProps({ confirmLoading: false });
        return;
      }
      
      // 批量移动摄像头到目录
      const promises = values.device_ids.map((deviceId: string) =>
        moveDeviceToDirectory(deviceId, values.parent_id)
      );
      
      try {
        await Promise.all(promises);
        createMessage.success(`成功添加 ${values.device_ids.length} 个摄像头到目录`);
        closeModal();
        emit('success');
      } catch (error) {
        console.error('添加摄像头失败', error);
        createMessage.error('部分摄像头添加失败，请重试');
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

