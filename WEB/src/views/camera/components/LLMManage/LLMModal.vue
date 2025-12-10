<template>
  <BasicModal
    v-bind="$attrs"
    @register="register"
    :title="getTitle"
    :width="800"
    @ok="handleSubmit"
  >
    <BasicForm @register="registerForm" />
  </BasicModal>
</template>

<script lang="ts" setup>
import { ref, computed, watch } from 'vue';
import { BasicModal, useModalInner } from '@/components/Modal';
import { BasicForm, useForm } from '@/components/Form';
import { useMessage } from '@/hooks/web/useMessage';
import { createLLM, updateLLM, getLLMDetail, type LLMModel } from '@/api/device/llm';

defineOptions({ name: 'LLMModal' });

const emit = defineEmits(['success', 'register']);

const { createMessage } = useMessage();
const isUpdate = ref(false);
const rowId = ref<number>();
const serviceType = ref<string>('online');

const [register, { setModalProps, closeModal }] = useModalInner(async (data) => {
  isUpdate.value = !!data?.isUpdate;
  rowId.value = data?.record?.id;

  if (isUpdate.value && rowId.value) {
    // 编辑模式，获取详情
    try {
      const response = await getLLMDetail(rowId.value);
      if (response.code === 0) {
        serviceType.value = response.data.service_type || 'online';
        await setFieldsValue(response.data);
      }
    } catch (error) {
      console.error('获取大模型详情失败', error);
    }
  } else {
    // 创建模式，设置默认值
    serviceType.value = 'online';
    await resetFields();
    await setFieldsValue({
      service_type: 'online',
      vendor: 'aliyun',
      model_type: 'vision',
      temperature: 0.7,
      max_tokens: 2000,
      timeout: 60,
      is_active: false,
      status: 'inactive',
    });
  }
});

const getTitle = computed(() => (isUpdate.value ? '编辑大模型' : '新建大模型'));

const [registerForm, { setFieldsValue, resetFields, validate, updateSchema }] = useForm({
  labelWidth: 120,
  baseColProps: { span: 24 },
  schemas: [
    {
      field: 'name',
      label: '模型名称',
      component: 'Input',
      required: true,
      componentProps: {
        placeholder: '请输入模型名称，如：QWENVL3视觉模型',
      },
    },
    {
      field: 'service_type',
      label: '服务类型',
      component: 'Select',
      required: true,
      componentProps: {
        placeholder: '请选择服务类型',
        options: [
          { label: '线上服务', value: 'online' },
          { label: '本地服务', value: 'local' },
        ],
        onChange: (value: string) => {
          serviceType.value = value;
          updateApiKeyField(value);
          // 如果切换到本地服务，自动设置vendor为local
          if (value === 'local') {
            setFieldsValue({ vendor: 'local' });
          } else if (value === 'online') {
            // 如果切换到线上服务，设置默认vendor
            setFieldsValue({ vendor: 'aliyun' });
          }
        },
      },
      defaultValue: 'online',
    },
    {
      field: 'vendor',
      label: '供应商',
      component: 'Select',
      required: true,
      componentProps: {
        placeholder: '请选择供应商',
        options: [
          { label: '阿里云', value: 'aliyun' },
          { label: 'OpenAI', value: 'openai' },
          { label: 'Anthropic', value: 'anthropic' },
          { label: '本地服务', value: 'local' },
        ],
      },
    },
    {
      field: 'model_type',
      label: '模型类型',
      component: 'Select',
      required: true,
      componentProps: {
        placeholder: '请选择模型类型',
        options: [
          { label: '文本', value: 'text' },
          { label: '视觉', value: 'vision' },
          { label: '多模态', value: 'multimodal' },
        ],
      },
    },
    {
      field: 'model_name',
      label: '模型标识',
      component: 'Input',
      required: true,
      componentProps: {
        placeholder: '请输入模型标识，如：qwen-vl-max',
      },
      helpMessage: '模型在API中的标识名称',
    },
    {
      field: 'base_url',
      label: 'API基础URL',
      component: 'Input',
      required: true,
      componentProps: {
        placeholder: '请输入API基础URL，如：https://dashscope.aliyuncs.com/compatible-mode/ 或 http://localhost:8000/v1/',
      },
      helpMessage: 'API服务的基础地址，以/结尾。本地服务示例：http://localhost:8000/v1/',
    },
    {
      field: 'api_key',
      label: 'API密钥',
      component: 'InputPassword',
      required: true, // 将在updateApiKeyField中动态更新
      componentProps: {
        placeholder: '请输入API密钥（本地服务可选）',
      },
      helpMessage: '线上服务必须提供API密钥，本地服务通常不需要',
      ifShow: true,
    },
    {
      field: 'api_version',
      label: 'API版本',
      component: 'Input',
      componentProps: {
        placeholder: '请输入API版本（可选）',
      },
    },
    {
      field: 'temperature',
      label: '温度参数',
      component: 'InputNumber',
      componentProps: {
        min: 0,
        max: 2,
        step: 0.1,
        placeholder: '0.0-2.0，控制输出的随机性',
      },
      defaultValue: 0.7,
    },
    {
      field: 'max_tokens',
      label: '最大输出Token数',
      component: 'InputNumber',
      componentProps: {
        min: 1,
        max: 8000,
        placeholder: '单次请求最大输出token数',
      },
      defaultValue: 2000,
    },
    {
      field: 'timeout',
      label: '请求超时时间（秒）',
      component: 'InputNumber',
      componentProps: {
        min: 10,
        max: 300,
        placeholder: 'API请求超时时间',
      },
      defaultValue: 60,
    },
    {
      field: 'description',
      label: '模型描述',
      component: 'InputTextArea',
      componentProps: {
        placeholder: '请输入模型描述（可选）',
        rows: 3,
      },
    },
    {
      field: 'icon_url',
      label: '图标URL',
      component: 'Input',
      componentProps: {
        placeholder: '请输入图标URL（可选）',
      },
    },
  ],
  showActionButtonGroup: false,
});

// 更新API密钥字段的必填状态和提示信息
const updateApiKeyField = (serviceTypeValue: string) => {
  const isOnline = serviceTypeValue === 'online';
  updateSchema({
    field: 'api_key',
    required: isOnline,
    componentProps: {
      placeholder: isOnline ? '请输入API密钥' : '本地服务可选，如需认证请填写',
    },
    helpMessage: isOnline 
      ? '线上服务必须提供API密钥' 
      : '本地服务通常不需要API密钥，如需认证可填写',
  });
  
  // 更新base_url的提示信息
  updateSchema({
    field: 'base_url',
    componentProps: {
      placeholder: isOnline
        ? '请输入API基础URL，如：https://dashscope.aliyuncs.com/compatible-mode/'
        : '请输入本地服务地址，如：http://localhost:8000/v1/',
    },
    helpMessage: isOnline
      ? 'API服务的基础地址，以/结尾'
      : '本地大模型服务的API地址，以/结尾',
  });
  
  // 更新vendor选项
  if (serviceTypeValue === 'local') {
    updateSchema({
      field: 'vendor',
      componentProps: {
        options: [
          { label: '本地服务', value: 'local' },
        ],
      },
    });
  } else {
    updateSchema({
      field: 'vendor',
      componentProps: {
        options: [
          { label: '阿里云', value: 'aliyun' },
          { label: 'OpenAI', value: 'openai' },
          { label: 'Anthropic', value: 'anthropic' },
        ],
      },
    });
  }
};

// 监听服务类型变化
watch(serviceType, (newVal) => {
  updateApiKeyField(newVal);
});

const handleSubmit = async () => {
  try {
    const values = await validate();
    setModalProps({ confirmLoading: true });

    let response;
    if (isUpdate.value && rowId.value) {
      response = await updateLLM(rowId.value, values);
    } else {
      response = await createLLM(values as LLMModel);
    }

    if (response.code === 0) {
      createMessage.success(isUpdate.value ? '更新成功' : '创建成功');
      closeModal();
      emit('success');
    } else {
      createMessage.error(response.msg || '操作失败');
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
