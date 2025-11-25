<template>
  <BasicModal v-bind="$attrs" @register="register" title="抓拍空间" @ok="handleSubmit">
    <BasicForm @register="registerForm" />
  </BasicModal>
</template>

<script lang="ts" setup>
import { ref, unref } from 'vue';
import { BasicModal, useModalInner } from '@/components/Modal';
import { BasicForm, useForm } from '@/components/Form';
import { useMessage } from '@/hooks/web/useMessage';
import { createSnapSpace, updateSnapSpace, type SnapSpace } from '@/api/device/snap';

defineOptions({ name: 'SnapSpaceModal' });

const { createMessage } = useMessage();
const emit = defineEmits(['success', 'register']);

const [registerForm, { setFieldsValue, validate, resetFields }] = useForm({
  labelWidth: 100,
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

const [register, { setModalProps, closeModal }] = useModalInner(async (data) => {
  resetFields();
  setModalProps({ confirmLoading: false });
  modalData.value = data;
  
  if (data.type === 'edit' && data.record) {
    setFieldsValue({
      space_name: data.record.space_name,
      save_mode: data.record.save_mode,
      save_time: data.record.save_time,
      description: data.record.description,
    });
  } else if (data.type === 'view' && data.record) {
    setFieldsValue({
      space_name: data.record.space_name,
      save_mode: data.record.save_mode,
      save_time: data.record.save_time,
      description: data.record.description,
    });
    setModalProps({ showOkBtn: false });
  }
});

const handleSubmit = async () => {
  try {
    const values = await validate();
    setModalProps({ confirmLoading: true });
    
    if (modalData.value.type === 'edit' && modalData.value.record) {
      await updateSnapSpace(modalData.value.record.id, values);
      createMessage.success('更新成功');
    } else {
      await createSnapSpace(values);
      createMessage.success('创建成功');
    }
    
    closeModal();
    emit('success');
  } catch (error) {
    console.error('提交失败', error);
    createMessage.error('提交失败');
  } finally {
    setModalProps({ confirmLoading: false });
  }
};
</script>

