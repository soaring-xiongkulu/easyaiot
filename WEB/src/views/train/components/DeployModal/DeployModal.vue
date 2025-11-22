<template>
  <BasicModal
    v-bind="$attrs"
    @register="register"
    title="部署模型服务"
    width="600px"
    @ok="handleSubmit"
  >
    <BasicForm @register="registerForm"/>
  </BasicModal>
</template>

<script lang="ts" setup>
import {ref, onMounted} from 'vue';
import {BasicModal, useModalInner} from '@/components/Modal';
import {BasicForm, useForm} from '@/components/Form';
import {useMessage} from '@/hooks/web/useMessage';
import {deployModel, getModelPage} from '@/api/device/model';

const {createMessage} = useMessage();

const modelOptions = ref([]);

const loadModelOptions = async () => {
  try {
    const res = await getModelPage({pageNo: 1, pageSize: 1000});
    const models = res.data || [];
    modelOptions.value = models.map((model) => ({
      label: `${model.name} (${model.version})`,
      value: model.id,
    }));
  } catch (error) {
    console.error('获取模型列表失败:', error);
    modelOptions.value = [];
  }
};

onMounted(() => {
  loadModelOptions();
});

const [registerForm, {validate, resetFields, updateSchema}] = useForm({
  labelWidth: 100,
  schemas: [
    {
      field: 'model_id',
      label: '选择模型',
      component: 'Select',
      componentProps: {
        placeholder: '请选择要部署的模型',
        showSearch: true,
        filterOption: (input, option) => {
          return option.label.toLowerCase().indexOf(input.toLowerCase()) >= 0;
        },
        options: modelOptions,
      },
      required: true,
    },
    {
      field: 'service_name',
      label: '服务名称',
      component: 'Input',
      componentProps: {
        placeholder: '请输入服务名称（留空自动生成）',
      },
    },
    {
      field: 'start_port',
      label: '起始端口',
      component: 'InputNumber',
      componentProps: {
        placeholder: '请输入起始端口',
        min: 8000,
        max: 65535,
      },
      defaultValue: 8000,
      required: true,
    },
  ],
});

const [register, {setModalProps, closeModal}] = useModalInner(async (data) => {
  resetFields();
  setModalProps({confirmLoading: false});
  await loadModelOptions();
  updateSchema({
    field: 'model_id',
    componentProps: {
      options: modelOptions.value,
    },
  });
});

const emit = defineEmits(['success', 'register']);

const handleSubmit = async () => {
  try {
    const values = await validate();
    setModalProps({confirmLoading: true});
    
    await deployModel(values);
    createMessage.success('部署成功');
    closeModal();
    emit('success');
  } catch (error) {
    console.error('部署失败:', error);
    createMessage.error('部署失败');
  } finally {
    setModalProps({confirmLoading: false});
  }
};
</script>

