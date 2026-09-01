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
        <Alert
          v-if="state.isPreset"
          type="warning"
          show-icon
          banner
          style="margin-bottom: 16px"
          message="当前使用占位密钥"
          description="端点与参数已按厂商最佳实践配置好，当前为占位密钥（sk-placeholder-*）。填入真实 API 密钥后即可启用。"
        />
        <Form
          :labelCol="{ span: 6 }"
          :model="validateInfos"
          :wrapperCol="{ span: 18 }"
        >
          <FormItem label="模型名称" name="name" v-bind="validateInfos.name">
            <Input v-model:value="llmRef.name" placeholder="请输入模型名称，如：QWENVL3视觉模型" />
          </FormItem>

          <FormItem label="服务类型" name="service_type" v-bind="validateInfos.service_type">
            <Select
              v-model:value="llmRef.service_type"
              placeholder="请选择服务类型"
              :options="state.serviceTypeOptions"
              @change="handleServiceTypeChange"
            />
          </FormItem>

          <FormItem label="接入模板" name="vendor" v-bind="validateInfos.vendor" :help="state.templateHelpMessage">
            <Select
              v-model:value="llmRef.vendor"
              placeholder="请选择接入模板（OpenAI 兼容）"
              :options="state.vendorOptions"
              :loading="state.templatesLoading"
              @change="handleTemplateChange"
            />
            <div v-if="state.templateDocUrl" style="margin-top: 4px; font-size: 12px; color: #666">
              还没有密钥？
              <a :href="state.templateDocUrl" target="_blank" rel="noopener">去厂商控制台获取 →</a>
            </div>
          </FormItem>

          <FormItem label="模型标识" name="model_name" v-bind="validateInfos.model_name">
            <AutoComplete
              v-model:value="llmRef.model_name"
              :options="state.modelNameOptions"
              placeholder="请输入模型标识，如：qwen-vl-max"
              :filter-option="false"
            />
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
import { computed, onMounted, reactive, ref, watch } from 'vue';
import { BasicModal, useModalInner } from '@/components/Modal';
import { AutoComplete, Alert, Form, FormItem, Input, InputNumber, Select, Spin } from 'ant-design-vue';
import { useMessage } from '@/hooks/web/useMessage';
import { useUserStoreWithOut } from "@/store/modules/user";
import { useGlobSetting } from "@/hooks/setting";
import { createLLM, updateLLM, getLLMDetail, getLLMTemplates, type LLMModel, type LLMTemplate } from '@/api/device/llm';
import { Button } from '@/components/Button'
defineOptions({ name: 'LLMModal' });

const emit = defineEmits(['success', 'register']);

const { createMessage } = useMessage();
const TextArea = Input.TextArea;
const InputPassword = Input.Password;

const userStore = useUserStoreWithOut();

const state = reactive({
  isEdit: false,
  editLoading: false,
  templatesLoading: false,
  isPreset: false, // 预置模板数据（占位密钥 sk-placeholder-*）
  templateDocUrl: '', // 当前模板的取密钥文档链接
  // 模板兜底清单（后端 /templates 不可用时降级使用；以后端返回为准）
  templates: [
    { key: 'dashscope', label: '阿里云百炼', base_url: 'https://dashscope.aliyuncs.com/compatible-mode/v1', doc_url: 'https://bailian.console.aliyun.com/', builtin_models: ['qwen3.8-max', 'qwen3.8-max-preview', 'qwen3.7-max', 'qwen3.7-plus', 'qwen3.7-flash', 'qwen3.6-max-preview', 'qwen3.6-plus', 'qwen3.6-flash', 'qwen3.5-plus', 'qwen3.5-flash', 'qwen3.5-omni-plus', 'qwen3.5-omni-flash', 'qwen3-vl-plus', 'qwen3-vl-flash', 'qwen-vl-max'] },
    { key: 'deepseek', label: 'DeepSeek', base_url: 'https://api.deepseek.com/v1', doc_url: 'https://platform.deepseek.com/', builtin_models: ['deepseek-v4-flash', 'deepseek-v4-pro', 'deepseek-v4-flash-vision-exp'] },
    { key: 'zhipu', label: '智谱 GLM', base_url: 'https://open.bigmodel.cn/api/paas/v4', doc_url: 'https://open.bigmodel.cn/', builtin_models: ['glm-5.3', 'glm-5.3-flash', 'glm-5.2', 'glm-5.1', 'glm-5-turbo', 'glm-5', 'glm-4.7', 'glm-4.7-flashx', 'glm-4.7-flash', 'glm-4.6', 'glm-4.5', 'glm-4.5-air', 'glm-4.5-airx', 'glm-4.5-flash', 'glm-4-plus', 'glm-4-long', 'glm-4-air', 'glm-4-airx', 'glm-4-flashx-250414', 'glm-4-flash-250414', 'glm-4-flash', 'glm-5v-turbo', 'glm-4.6v', 'glm-4.6v-flash', 'glm-4.5v', 'glm-4.1v-thinking-flashx', 'glm-4.1v-thinking-flash', 'glm-4v-plus', 'glm-4v-flash', 'glm-ocr'] },
    { key: 'openai', label: 'OpenAI', base_url: 'https://api.openai.com/v1', doc_url: 'https://platform.openai.com/', builtin_models: ['gpt-5.6-sol', 'gpt-5.6', 'gpt-5.6-sol-pro', 'gpt-5.6-terra', 'gpt-5.6-luna', 'gpt-5.5', 'gpt-5.4-mini', 'gpt-4.1-mini'] },
    { key: 'kimi', label: 'Kimi（月之暗面）', base_url: 'https://api.moonshot.cn/v1', doc_url: 'https://platform.moonshot.cn/', builtin_models: ['kimi-k2.6', 'kimi-k2.7-code'] },
    { key: 'claude', label: 'Claude（Anthropic）', base_url: '', doc_url: 'https://console.anthropic.com/', builtin_models: ['claude-opus-4-7', 'claude-opus-4-6', 'claude-opus-4-5', 'claude-sonnet-4-6', 'claude-sonnet-4-5', 'claude-haiku-4-5'] },
    { key: 'anthropic', label: 'Anthropic 兼容', base_url: '', doc_url: 'https://console.anthropic.com/', builtin_models: [] },
    { key: 'custom', label: '自定义 OpenAI 兼容', base_url: '', builtin_models: [] },
  ] as LLMTemplate[],
  vendorOptions: [] as { label: string; value: string }[],
  modelNameOptions: [] as { value: string }[],
  templateHelpMessage: '选择模板后自动填充 API 端点；所有厂商统一走 OpenAI 兼容协议',
  serviceTypeOptions: [
    { label: '线上服务', value: 'online' },
    { label: '本地服务', value: 'local' },
  ],
  baseUrlPlaceholder: '请输入API基础URL，如：https://dashscope.aliyuncs.com/compatible-mode/v1 或 http://localhost:8000/v1',
  baseUrlHelpMessage: 'OpenAI 兼容 API 基础地址（/v1 根地址，无需拼到 /chat/completions）',
  apiKeyPlaceholder: '请输入API密钥（本地服务可选）',
  apiKeyHelpMessage: '线上服务必须提供API密钥，本地服务通常不需要',
});

const getTemplateByKey = (key: string): LLMTemplate | undefined =>
  state.templates.find((t) => t.key === key);

const loadTemplates = async () => {
  state.templatesLoading = true;
  try {
    const response: any = await getLLMTemplates();
    const list = response?.data?.templates ?? (Array.isArray(response) ? response : null);
    if (Array.isArray(list) && list.length) {
      state.templates = list;
    }
  } catch (error) {
    console.warn('加载模板列表失败，使用内置模板', error);
  } finally {
    state.vendorOptions = state.templates.map((t) => ({ label: t.label, value: t.key }));
    state.templatesLoading = false;
  }
};

onMounted(loadTemplates);

// 选择模板：自动填充端点与常用模型建议
const handleTemplateChange = (key: string) => {
  const template = getTemplateByKey(key);
  state.templateDocUrl = template?.doc_url ?? '';
  state.modelNameOptions = (template?.builtin_models ?? []).map((m) => ({ value: m }));
  if (template?.base_url) {
    llmRef.base_url = template.base_url;
  }
  // 若模型标识为空且模板只有唯一常用模型，直接预填
  if (!llmRef.model_name && state.modelNameOptions.length === 1) {
    llmRef.model_name = state.modelNameOptions[0].value;
  }
};

const llmRef = reactive({
  id: null as number | null,
  name: '',
  icon_url: '',
  service_type: 'online',
  vendor: 'dashscope',
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
      let detailData: LLMModel | null = null;
      if (response && typeof response === 'object') {
        if ('code' in response && response.code === 0 && response.data) {
          detailData = response.data;
        } else if (!('code' in response)) {
          // 响应转换器已处理，直接使用 response
          detailData = response as unknown as LLMModel;
        }
      }
      
      if (detailData) {
        Object.assign(llmRef, detailData);
        // vendor 存储的是模板 key（存量数据由后端解析为 template 字段）
        llmRef.vendor = detailData.template || detailData.vendor || 'custom';
        state.isPreset = !!detailData.is_preset;
        syncModelNameOptions();
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
      vendor: 'dashscope',
      temperature: 0.7,
      max_tokens: 2000,
      timeout: 60,
      is_active: false,
      status: 'inactive',
      icon_url: '',
      model_name: '',
      base_url: '',
      api_key: '',
      description: '',
    });
    syncModelNameOptions();
    updateFieldsByServiceType('online');
    state.isPreset = false;
    state.templateDocUrl = '';
  }
});

// 表单验证规则
const rulesRef = reactive({
  name: [{ required: true, message: '请输入模型名称', trigger: ['blur', 'change'] }],
  service_type: [{ required: true, message: '请选择服务类型', trigger: ['blur', 'change'] }],
  vendor: [{ required: true, message: '请选择接入模板', trigger: ['blur', 'change'] }],
  model_name: [{ required: true, message: '请输入模型标识', trigger: ['blur', 'change'] }],
  base_url: [{ required: true, message: '请输入API基础URL', trigger: ['blur', 'change'] }],
  api_key: [{ required: false, message: '请输入API密钥', trigger: ['blur', 'change'] }],
  temperature: [{ required: false, trigger: ['blur', 'change'] }],
  max_tokens: [{ required: false, trigger: ['blur', 'change'] }],
  timeout: [{ required: false, trigger: ['blur', 'change'] }],
});

const useForm = Form.useForm;
const { validate, resetFields, validateInfos } = useForm(llmRef, rulesRef);

// 根据服务类型更新相关字段（模板选项不再随服务类型切换）
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
  state.apiKeyPlaceholder = state.isPreset
    ? '请输入真实 API 密钥（当前为占位密钥 sk-placeholder-*）'
    : isOnline
      ? '请输入API密钥'
      : '本地服务可选，如需认证请填写';
  state.apiKeyHelpMessage = isOnline
    ? '线上服务必须提供API密钥'
    : '本地大模型服务（vLLM / Ollama 等）通常无需密钥，如需认证可填写';

  state.baseUrlPlaceholder = isOnline
    ? '请输入API基础URL，如：https://dashscope.aliyuncs.com/compatible-mode/v1'
    : '请输入本地服务地址，如：http://localhost:8000/v1';
  state.baseUrlHelpMessage = isOnline
    ? 'OpenAI 兼容 API 基础地址（/v1 根地址）'
    : '本地大模型服务的 OpenAI 兼容 API 地址（/v1 根地址）';
};

// 按当前模板同步模型标识建议列表
const syncModelNameOptions = () => {
  const template = getTemplateByKey(llmRef.vendor);
  state.modelNameOptions = (template?.builtin_models ?? []).map((m) => ({ value: m }));
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

const handleSubmit = async () => {
  try {
    await validate();
    setModalProps({ confirmLoading: true });

    // 只提交必要字段（model_type 已废弃，后端保留默认值）
    const payload: any = {
      name: llmRef.name,
      icon_url: llmRef.icon_url,
      service_type: llmRef.service_type,
      vendor: llmRef.vendor,
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
