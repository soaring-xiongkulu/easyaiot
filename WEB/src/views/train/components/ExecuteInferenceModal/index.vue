<template>
  <Form
    :labelCol="{ span: 3 }"
    :model="formModel"
    :wrapperCol="{ span: 21 }"
    ref="formRef"
  >
    <!-- 模型选择 -->
    <FormItem
      label="选择模型"
      name="model_id"
    >
      <ApiSelect
        v-model:value="formModel.model_id"
        :api="handleGetModelPage"
        result-field="items"
        label-field="name"
        value-field="id"
      />
    </FormItem>

    <!-- 推理类型 -->
    <FormItem
      label="推理类型"
      name="inference_type"
    >
      <Select
        v-model:value="formModel.inference_type"
        placeholder="请选择"
      >
        <SelectOption value="image">图片推理</SelectOption>
        <SelectOption value="video">视频推理</SelectOption>
        <SelectOption value="rtsp">实时流推理</SelectOption>
      </Select>
    </FormItem>

    <!-- 输入源 (图片/视频) -->
    <FormItem
      v-if="formModel.inference_type !== 'rtsp'"
      label="输入源"
      name="input_source"
    >
      <Upload
        v-model:file-list="formModel.input_source"
        :accept="formModel.inference_type === 'image' ? 'image/*' : 'video/*'"
        :max-count="1"
      >
        <a-button type="primary">点击上传</a-button>
      </Upload>
    </FormItem>

    <!-- RTSP地址 -->
    <FormItem
      v-if="formModel.inference_type === 'rtsp'"
      label="RTSP地址"
      name="rtsp_url"
    >
      <Input v-model:value="formModel.rtsp_url"/>
    </FormItem>

    <!-- 高级参数 -->
    <FormItem label="高级参数" name="params">
      <InputTextArea
        v-model:value="formModel.params"
        :placeholder="'JSON格式参数，如：{threshold: 0.5}'"
        :rows="4"
      />
    </FormItem>
  </Form>
</template>

<script lang="ts" setup>
import { reactive, ref } from 'vue';
import { Form, FormItem, Input, Select, SelectOption, Upload } from 'ant-design-vue';
import ApiSelect from '@/components/Form/src/components/ApiSelect.vue';
const InputTextArea = Input.TextArea;

// 使用Form.useForm进行表单验证
const useForm = Form.useForm;

// 表单数据模型
const formModel = reactive({
  model_id: undefined,
  inference_type: 'image',
  input_source: [],
  rtsp_url: '',
  params: ''
});

// 定义验证规则
const rulesRef = reactive({
  model_id: [
    { required: true, message: '请选择模型', trigger: 'blur' }
  ],
  inference_type: [
    { required: true, message: '请选择推理类型', trigger: 'change' }
  ],
  input_source: [
    {
      required: true,
      message: '请上传文件',
      trigger: 'change',
      validator: (_, value) => {
        return value && value.length > 0;
      }
    }
  ],
  rtsp_url: [
    { required: true, message: '请输入RTSP地址', trigger: 'blur' },
    {
      pattern: /^rtsp:\/\/\w+(\.\w+)+:\d+\/\w+/,
      message: '请输入有效的RTSP地址格式（如：rtsp://example.com:554/stream）',
      trigger: 'blur'
    }
  ],
  params: [
    {
      validator: (_, value) => {
        if (!value) return Promise.resolve();
        try {
          JSON.parse(value);
          return Promise.resolve();
        } catch (e) {
          return Promise.reject('请输入有效的JSON格式');
        }
      },
      trigger: 'blur'
    }
  ]
});

// 初始化表单验证
const { validate, resetFields, validateInfos } = useForm(formModel, rulesRef);

// 表单引用
const formRef = ref();

// API方法（需替换为实际实现）
const handleGetModelPage = async () => {
  // getModelPage
};

// 提交表单方法
const submitForm = async () => {
  try {
    await validate();
    console.log('表单验证通过，提交数据:', formModel);
    // 这里添加实际的提交逻辑
  } catch (errors) {
    console.error('表单验证失败:', errors);
  }
};

// 重置表单方法
const resetForm = () => {
  resetFields();
};

// 暴露方法给父组件
defineExpose({
  validate: submitForm,
  reset: resetForm
});
</script>
