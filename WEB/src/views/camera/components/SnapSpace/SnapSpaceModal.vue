<template>
  <BasicModal 
    v-bind="$attrs" 
    @register="register" 
    :title="modalTitle" 
    @ok="handleSubmit"
    :width="700"
  >
    <BasicForm @register="registerForm" />
  </BasicModal>
</template>

<script lang="ts" setup>
import { ref, computed } from 'vue';
import { BasicModal, useModalInner } from '@/components/Modal';
import { BasicForm, useForm } from '@/components/Form';
import { useMessage } from '@/hooks/web/useMessage';
import { createSnapSpace, updateSnapSpace, type SnapSpace } from '@/api/device/snap';

defineOptions({ name: 'SnapSpaceModal' });

const { createMessage } = useMessage();
const emit = defineEmits(['success', 'register']);

const [registerForm, { setFieldsValue, validate, resetFields, updateSchema }] = useForm({
  labelWidth: 100,
  baseColProps: { span: 24 },
  schemas: [
    {
      field: 'space_name',
      label: '空间名称',
      component: 'Input',
      required: true,
      componentProps: {
        placeholder: '请输入空间名称',
      },
    },
    {
      field: 'save_mode',
      label: '存储模式',
      component: 'Select',
      required: true,
      componentProps: {
        options: [
          { label: '标准存储', value: 0 },
          { label: '归档存储', value: 1 },
        ],
      },
    },
    {
      field: 'save_time',
      label: '保存时间',
      component: 'InputNumber',
      required: true,
      componentProps: {
        placeholder: '0表示永久保存，>=7表示保存天数',
        min: 0,
      },
      helpMessage: '0表示永久保存，>=7表示保存天数（单位：天）',
    },
    {
      field: 'description',
      label: '描述',
      component: 'InputTextArea',
      componentProps: {
        placeholder: '请输入空间描述',
        rows: 4,
      },
    },
  ],
  showActionButtonGroup: false,
});

const modalData = ref<{ type?: string; record?: SnapSpace }>({});

const modalTitle = computed(() => {
  if (modalData.value.type === 'view') return '查看抓拍空间';
  if (modalData.value.type === 'edit') return '编辑抓拍空间';
  return '新建抓拍空间';
});

const [register, { setModalProps, closeModal }] = useModalInner(async (data) => {
  resetFields();
  setModalProps({ confirmLoading: false });
  modalData.value = data;
  
  if (data.type === 'edit' && data.record) {
    // 编辑模式：所有字段可编辑
    updateSchema([
      {
        field: 'space_name',
        componentProps: { disabled: false },
      },
      {
        field: 'save_mode',
        componentProps: { disabled: false },
      },
      {
        field: 'save_time',
        componentProps: { disabled: false },
      },
      {
        field: 'description',
        componentProps: { disabled: false },
      },
    ]);
    setFieldsValue({
      space_name: data.record.space_name,
      save_mode: data.record.save_mode,
      save_time: data.record.save_time,
      description: data.record.description,
    });
    setModalProps({ showOkBtn: true });
  } else if (data.type === 'view' && data.record) {
    // 查看模式：所有字段禁用
    updateSchema([
      {
        field: 'space_name',
        componentProps: { disabled: true },
      },
      {
        field: 'save_mode',
        componentProps: { disabled: true },
      },
      {
        field: 'save_time',
        componentProps: { disabled: true },
      },
      {
        field: 'description',
        componentProps: { disabled: true },
      },
    ]);
    setFieldsValue({
      space_name: data.record.space_name,
      save_mode: data.record.save_mode,
      save_time: data.record.save_time,
      description: data.record.description,
    });
    setModalProps({ showOkBtn: false });
  } else {
    // 新建模式：所有字段可编辑
    updateSchema([
      {
        field: 'space_name',
        componentProps: { disabled: false },
      },
      {
        field: 'save_mode',
        componentProps: { disabled: false },
      },
      {
        field: 'save_time',
        componentProps: { disabled: false },
      },
      {
        field: 'description',
        componentProps: { disabled: false },
      },
    ]);
    setModalProps({ showOkBtn: true });
  }
});

const handleSubmit = async () => {
  try {
    const values = await validate();
    setModalProps({ confirmLoading: true });
    
    if (modalData.value.type === 'edit' && modalData.value.record) {
      const response = await updateSnapSpace(modalData.value.record.id, values);
      if (response.code === 0) {
        createMessage.success('更新成功');
        closeModal();
        emit('success');
      } else {
        createMessage.error(response.msg || '更新失败');
      }
    } else {
      const response = await createSnapSpace(values);
      if (response.code === 0) {
        createMessage.success('创建成功');
        closeModal();
        emit('success');
      } else {
        createMessage.error(response.msg || '创建失败');
      }
    }
  } catch (error: any) {
    console.error('提交失败', error);
    // 如果错误已经有消息（比如axios拦截器已经显示了），就不再显示"提交失败"
    const errorMsg = error?.response?.data?.msg || error?.message || '';
    // 如果是业务错误（400等），axios拦截器已经显示了错误消息，不需要再显示
    const status = error?.response?.status;
    if (status && status >= 400 && status < 500 && errorMsg) {
      // 业务错误且已有错误消息，不重复显示
      return;
    }
    // 其他错误（网络错误等）才显示"提交失败"
    if (!errorMsg) {
      createMessage.error('提交失败');
    }
  } finally {
    setModalProps({ confirmLoading: false });
  }
};
</script>

