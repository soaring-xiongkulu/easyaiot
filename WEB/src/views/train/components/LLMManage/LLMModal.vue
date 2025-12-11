<template>
  <BasicModal
    v-bind="$attrs"
    @register="register"
    :title="getTitle"
    :width="800"
    @ok="handleSubmit"
    @cancel="handleCancel"
  >
    <div class="llm-modal">
      <Spin :spinning="state.editLoading">
        <Form
          :labelCol="{ span: 6 }"
          :model="validateInfos"
          :wrapperCol="{ span: 18 }"
        >
          <FormItem label="模型名称" name="name" v-bind="validateInfos.name">
            <Input v-model:value="llmRef.name" placeholder="请输入模型名称，如：QWENVL3视觉模型" />
          </FormItem>

          <!-- 模型图片上传 -->
          <FormItem label="模型图片" name="icon_url" v-bind="validateInfos.icon_url">
            <Upload
              name="file"
              :action="state.imageUploadUrl"
              :headers="headers"
              :showUploadList="false"
              accept=".jpg,.jpeg,.png,.gif,.webp"
              @change="handleImageUpload"
            >
              <a-button type="primary">
                上传模型图片
              </a-button>
            </Upload>
            <div v-if="llmRef.icon_url" style="margin-top: 8px">
              <img
                :src="llmRef.icon_url"
                alt="模型图片预览"
                style="max-height: 200px; max-width: 100%; border-radius: 4px; display: block;"
              />
            </div>
          </FormItem>

          <FormItem label="服务类型" name="service_type" v-bind="validateInfos.service_type">
            <Select
              v-model:value="llmRef.service_type"
              placeholder="请选择服务类型"
              :options="state.serviceTypeOptions"
              @change="handleServiceTypeChange"
            />
          </FormItem>

          <FormItem label="供应商" name="vendor" v-bind="validateInfos.vendor">
            <Select
              v-model:value="llmRef.vendor"
              placeholder="请选择供应商"
              :options="state.vendorOptions"
            />
          </FormItem>

          <FormItem label="模型类型" name="model_type" v-bind="validateInfos.model_type">
            <Select
              v-model:value="llmRef.model_type"
              placeholder="请选择模型类型"
              :options="state.modelTypeOptions"
            />
          </FormItem>

          <FormItem label="模型标识" name="model_name" v-bind="validateInfos.model_name">
            <Input v-model:value="llmRef.model_name" placeholder="请输入模型标识，如：qwen-vl-max" />
          </FormItem>

          <FormItem label="API基础URL" name="base_url" v-bind="validateInfos.base_url" :help="state.baseUrlHelpMessage">
            <Input v-model:value="llmRef.base_url" :placeholder="state.baseUrlPlaceholder" />
          </FormItem>

          <FormItem label="API密钥" name="api_key" v-bind="validateInfos.api_key" :help="state.apiKeyHelpMessage">
            <InputPassword v-model:value="llmRef.api_key" :placeholder="state.apiKeyPlaceholder" />
          </FormItem>

          <FormItem label="API版本" name="api_version" v-bind="validateInfos.api_version">
            <Input v-model:value="llmRef.api_version" placeholder="请输入API版本（可选）" />
          </FormItem>

          <FormItem label="温度参数" name="temperature" v-bind="validateInfos.temperature">
            <InputNumber
              v-model:value="llmRef.temperature"
              :min="0"
              :max="2"
              :step="0.1"
              placeholder="0.0-2.0，控制输出的随机性"
              style="width: 100%"
            />
          </FormItem>

          <FormItem label="最大输出Token数" name="max_tokens" v-bind="validateInfos.max_tokens">
            <InputNumber
              v-model:value="llmRef.max_tokens"
              :min="1"
              :max="8000"
              placeholder="单次请求最大输出token数"
              style="width: 100%"
            />
          </FormItem>

          <FormItem label="请求超时时间（秒）" name="timeout" v-bind="validateInfos.timeout">
            <InputNumber
              v-model:value="llmRef.timeout"
              :min="10"
              :max="300"
              placeholder="API请求超时时间"
              style="width: 100%"
            />
          </FormItem>

          <FormItem label="模型描述" name="description" v-bind="validateInfos.description">
            <TextArea v-model:value="llmRef.description" placeholder="请输入模型描述（可选）" :rows="3" />
          </FormItem>
        </Form>
      </Spin>
    </div>
  </BasicModal>
</template>

<script lang="ts" setup>
import { computed, reactive, ref, watch } from 'vue';
import { BasicModal, useModalInner } from '@/components/Modal';
import { Form, FormItem, Input, InputNumber, Select, Spin, Upload } from 'ant-design-vue';
import { useMessage } from '@/hooks/web/useMessage';
import { useUserStoreWithOut } from "@/store/modules/user";
import { useGlobSetting } from "@/hooks/setting";
import { createLLM, updateLLM, getLLMDetail, type LLMModel } from '@/api/device/llm';

defineOptions({ name: 'LLMModal' });

const emit = defineEmits(['success', 'register']);

const { createMessage } = useMessage();
const TextArea = Input.TextArea;
const InputPassword = Input.Password;

const userStore = useUserStoreWithOut();
const token = userStore.getAccessToken;
const headers = ref({ 'Authorization': `Bearer ${token}` });
const { uploadUrl } = useGlobSetting();

const state = reactive({
  imageUploadUrl: `${uploadUrl}/model/llm/image_upload`,
  isEdit: false,
  editLoading: false,
  serviceTypeOptions: [
    { label: '线上服务', value: 'online' },
    { label: '本地服务', value: 'local' },
  ],
  vendorOptions: [
    { label: '阿里云', value: 'aliyun' },
    { label: 'OpenAI', value: 'openai' },
    { label: 'Anthropic', value: 'anthropic' },
    { label: '本地服务', value: 'local' },
  ],
  modelTypeOptions: [
    { label: '文本', value: 'text' },
    { label: '视觉', value: 'vision' },
    { label: '多模态', value: 'multimodal' },
  ],
  baseUrlPlaceholder: '请输入API基础URL，如：https://dashscope.aliyuncs.com/compatible-mode/ 或 http://localhost:8000/v1/',
  baseUrlHelpMessage: 'API服务的基础地址，以/结尾。本地服务示例：http://localhost:8000/v1/',
  apiKeyPlaceholder: '请输入API密钥（本地服务可选）',
  apiKeyHelpMessage: '线上服务必须提供API密钥，本地服务通常不需要',
});

const llmRef = reactive({
  id: null as number | null,
  name: '',
  icon_url: '',
  service_type: 'online',
  vendor: 'aliyun',
  model_type: 'vision',
  model_name: '',
  base_url: '',
  api_key: '',
  api_version: '',
  temperature: 0.7,
  max_tokens: 2000,
  timeout: 60,
  description: '',
  is_active: false,
  status: 'inactive',
});

const getTitle = computed(() => (state.isEdit ? '编辑大模型' : '新建大模型'));

const [register, { setModalProps, closeModal }] = useModalInner(async (data) => {
  const { isUpdate, record } = data;
  state.isEdit = !!isUpdate;

  if (state.isEdit && record?.id) {
    // 编辑模式，获取详情
    try {
      state.editLoading = true;
      // 先重置表单，清除之前的验证状态
      resetFields();
      const response = await getLLMDetail(record.id);
      // 处理不同的响应格式
      let detailData = null;
      if (response && typeof response === 'object') {
        if ('code' in response && response.code === 0 && response.data) {
          detailData = response.data;
        } else if (!('code' in response)) {
          // 响应转换器已处理，直接使用 response
          detailData = response;
        }
      }
      
      if (detailData) {
        Object.assign(llmRef, detailData);
        updateFieldsByServiceType(detailData.service_type || 'online');
      } else {
        createMessage.error('获取大模型详情失败：数据格式错误');
      }
    } catch (error) {
      console.error('获取大模型详情失败', error);
      createMessage.error('获取大模型详情失败');
    } finally {
      state.editLoading = false;
    }
  } else {
    // 创建模式，设置默认值
    resetFields();
    Object.assign(llmRef, {
      service_type: 'online',
      vendor: 'aliyun',
      model_type: 'vision',
      temperature: 0.7,
      max_tokens: 2000,
      timeout: 60,
      is_active: false,
      status: 'inactive',
      icon_url: '',
    });
    updateFieldsByServiceType('online');
  }
});

// 表单验证规则
const rulesRef = reactive({
  name: [{ required: true, message: '请输入模型名称', trigger: ['blur', 'change'] }],
  icon_url: [{ required: true, message: '请上传模型图片', trigger: 'change' }],
  service_type: [{ required: true, message: '请选择服务类型', trigger: ['blur', 'change'] }],
  vendor: [{ required: true, message: '请选择供应商', trigger: ['blur', 'change'] }],
  model_type: [{ required: true, message: '请选择模型类型', trigger: ['blur', 'change'] }],
  model_name: [{ required: true, message: '请输入模型标识', trigger: ['blur', 'change'] }],
  base_url: [{ required: true, message: '请输入API基础URL', trigger: ['blur', 'change'] }],
  api_key: [{ required: false, message: '请输入API密钥', trigger: ['blur', 'change'] }],
  temperature: [{ required: false, trigger: ['blur', 'change'] }],
  max_tokens: [{ required: false, trigger: ['blur', 'change'] }],
  timeout: [{ required: false, trigger: ['blur', 'change'] }],
});

const useForm = Form.useForm;
const { validate, resetFields, validateInfos } = useForm(llmRef, rulesRef);

// 根据服务类型更新相关字段
const updateFieldsByServiceType = (serviceType: string) => {
  const isOnline = serviceType === 'online';
  
  // 更新API密钥必填状态
  if (isOnline) {
    rulesRef.api_key[0].required = true;
    rulesRef.api_key[0].message = '请输入API密钥';
  } else {
    rulesRef.api_key[0].required = false;
    rulesRef.api_key[0].message = '本地服务可选，如需认证请填写';
  }

  // 更新提示信息
  state.apiKeyPlaceholder = isOnline ? '请输入API密钥' : '本地服务可选，如需认证请填写';
  state.apiKeyHelpMessage = isOnline 
    ? '线上服务必须提供API密钥' 
    : '本地服务通常不需要API密钥，如需认证可填写';

  state.baseUrlPlaceholder = isOnline
    ? '请输入API基础URL，如：https://dashscope.aliyuncs.com/compatible-mode/'
    : '请输入本地服务地址，如：http://localhost:8000/v1/';
  state.baseUrlHelpMessage = isOnline
    ? 'API服务的基础地址，以/结尾'
    : '本地大模型服务的API地址，以/结尾';

  // 更新供应商选项
  if (serviceType === 'local') {
    state.vendorOptions = [
      { label: '本地服务', value: 'local' },
    ];
    if (llmRef.vendor !== 'local') {
      llmRef.vendor = 'local';
    }
  } else {
    state.vendorOptions = [
      { label: '阿里云', value: 'aliyun' },
      { label: 'OpenAI', value: 'openai' },
      { label: 'Anthropic', value: 'anthropic' },
    ];
    if (llmRef.vendor === 'local') {
      llmRef.vendor = 'aliyun';
    }
  }
};

// 处理服务类型变化
const handleServiceTypeChange = (value: string) => {
  updateFieldsByServiceType(value);
};

// 监听服务类型变化
watch(() => llmRef.service_type, (newVal) => {
  updateFieldsByServiceType(newVal);
});

function handleCancel() {
  resetFields();
  closeModal();
}

// 处理模型图片上传事件
function handleImageUpload(info: any) {
  if (info.file.status === 'done') {
    const response = info.file.response;
    if (response && response.code === 0) {
      llmRef.icon_url = response.data.url;
      createMessage.success('模型图片上传成功');
    } else {
      createMessage.error(response?.msg || '图片上传失败');
    }
  } else if (info.file.status === 'error') {
    createMessage.error('图片上传失败');
  }
}

const handleSubmit = async () => {
  try {
    await validate();
    setModalProps({ confirmLoading: true });

    // 只提交必要字段
    const payload: any = {
      name: llmRef.name,
      icon_url: llmRef.icon_url,
      service_type: llmRef.service_type,
      vendor: llmRef.vendor,
      model_type: llmRef.model_type,
      model_name: llmRef.model_name,
      base_url: llmRef.base_url,
      api_key: llmRef.api_key,
      api_version: llmRef.api_version || undefined,
      temperature: llmRef.temperature,
      max_tokens: llmRef.max_tokens,
      timeout: llmRef.timeout,
      description: llmRef.description || undefined,
    };

    if (state.isEdit && llmRef.id) {
      payload.id = llmRef.id;
    } else {
      payload.is_active = false;
      payload.status = 'inactive';
    }

    let response;
    if (state.isEdit && llmRef.id) {
      response = await updateLLM(llmRef.id, payload);
    } else {
      response = await createLLM(payload as LLMModel);
    }

    // 检查响应格式：如果响应转换器已经处理过，可能只返回 data，也可能返回完整对象
    // 如果 response 有 code 字段，使用 code 判断；否则认为成功（转换器已处理）
    if (response && typeof response === 'object' && 'code' in response) {
      if (response.code === 0) {
        createMessage.success(state.isEdit ? '更新成功' : '创建成功');
        closeModal();
        resetFields();
        emit('success');
      } else {
        // 后端返回了错误码，显示后端的具体错误信息
        createMessage.error(response.msg || '操作失败');
      }
    } else {
      // 响应转换器已经处理过，直接返回了数据，说明操作成功
      createMessage.success(state.isEdit ? '更新成功' : '创建成功');
      closeModal();
      resetFields();
      emit('success');
    }
  } catch (error: any) {
    console.error('提交失败', error);
    if (error?.errorFields) {
      // 表单验证错误
      createMessage.error('表单验证失败，请检查输入');
    } else {
      // 从异常中提取后端返回的错误信息
      // 优先使用 error.response?.data?.msg（后端返回的具体错误信息，如"模型名称已存在"）
      // 如果后端返回了 msg，直接使用；否则使用 error.message 或默认提示
      const backendMsg = error?.response?.data?.msg;
      if (backendMsg) {
        // 使用后端返回的具体错误信息
        createMessage.error(backendMsg);
      } else {
        // 没有后端返回的 msg，使用异常消息或默认提示
        const errorMsg = error?.message;
        if (errorMsg && !errorMsg.includes('sys.api') && errorMsg !== '操作失败') {
          createMessage.error(errorMsg);
        } else {
          createMessage.error('操作失败');
        }
      }
    }
  } finally {
    setModalProps({ confirmLoading: false });
  }
};
</script>

<style lang="less" scoped>
.llm-modal {
  :deep(.ant-form-item-label) {
    & > label::after {
      content: '';
    }
  }
}
</style>