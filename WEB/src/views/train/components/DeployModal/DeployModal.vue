<template>
  <BasicModal
    v-bind="$attrs"
    @register="register"
    title="模型部署"
    @cancel="handleCancel"
    :width="700"
    @ok="handleSubmit"
    :canFullscreen="false"
    :confirmLoading="deploying"
    :okButtonProps="{ disabled: !isFormValid }"
  >
    <div class="deploy-confirm-modal">
      <a-form :model="formState" :label-col="{ span: 5 }" :wrapper-col="{ span: 19 }">
        <a-form-item label="请选择要部署的模型" :required="true">
          <a-select
            v-model:value="formState.model_id"
            placeholder="请选择要部署的模型"
            :options="modelOptions"
            show-search
            :filter-option="filterOption"
            allow-clear
            @change="handleModelChange"
          />
        </a-form-item>
        <a-form-item label="服务名称" :required="true">
          <a-input
            v-model:value="formState.service_name"
            placeholder="服务名称（自动生成）"
            readonly
            disabled
          />
        </a-form-item>
        <a-form-item label="端口" :required="true">
          <template #extra>
            <span class="port-tip">端口占用时自动寻找未占用端口</span>
          </template>
          <a-input-number
            v-model:value="formState.start_port"
            placeholder="请输入端口"
            :min="8000"
            :max="65535"
            style="width: 100%"
          />
        </a-form-item>
      </a-form>
    </div>
  </BasicModal>
</template>

<script lang="ts" setup>
import { computed, reactive, ref, watch, onMounted } from 'vue';
import { BasicModal, useModalInner } from '@/components/Modal';
import { Form, FormItem, Select, Input, InputNumber } from 'ant-design-vue';
import { useMessage } from '@/hooks/web/useMessage';
import { deployModel, getModelPage } from '@/api/device/model';
import { buildUUID } from '@/utils/uuid';

const AForm = Form;
const AFormItem = FormItem;
const ASelect = Select;
const AInput = Input;
const AInputNumber = InputNumber;

const { createMessage } = useMessage();

const modelOptions = ref<Array<{ label: string; value: number }>>([]);

const formState = reactive({
  model_id: null as number | null,
  service_name: '' as string,
  start_port: 8000 as number,
});

const state = reactive({
  deploying: false,
});

const deploying = computed(() => state.deploying);

// 验证表单是否有效
const isFormValid = computed(() => {
  return formState.model_id !== null && formState.service_name && formState.start_port >= 8000 && formState.start_port <= 65535;
});

const loadModelOptions = async () => {
  try {
    const res = await getModelPage({ pageNo: 1, pageSize: 1000 });
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

const [register, { closeModal, setModalProps }] = useModalInner(async (data) => {
  // 重置表单
  formState.model_id = null;
  formState.service_name = buildUUID(); // 自动生成UUID
  formState.start_port = 8000;
  state.deploying = false;
  setModalProps({ confirmLoading: false });
  await loadModelOptions();
});

// 监听部署状态，更新弹框按钮的 loading 状态
watch(() => state.deploying, (loading) => {
  setModalProps({ confirmLoading: loading });
});

// 过滤选项
const filterOption = (input: string, option: any) => {
  return option?.label?.toLowerCase().indexOf(input.toLowerCase()) >= 0;
};

// 模型选择变化
const handleModelChange = () => {
  // 可以在这里添加逻辑
};

function handleCancel() {
  if (!state.deploying) {
    closeModal();
  }
}

const emit = defineEmits(['success', 'register']);

const handleSubmit = async () => {
  if (state.deploying) {
    return; // 如果正在部署，不允许重复点击
  }

  // 验证表单
  if (!isFormValid.value) {
    createMessage.warning('请填写必填字段');
    return; // 表单验证失败，不执行部署
  }

  try {
    state.deploying = true;
    const values = {
      model_id: formState.model_id,
      service_name: formState.service_name, // 必填，已自动生成
      start_port: formState.start_port,
    };
    
    await deployModel(values);
    createMessage.success('部署成功');
    closeModal();
    emit('success');
  } catch (error: any) {
    console.error('部署失败:', error);
    createMessage.error(error.message || '部署失败');
  } finally {
    state.deploying = false;
  }
};
</script>

<style lang="less" scoped>
.deploy-confirm-modal {
  padding: 8px 0;

  :deep(.ant-descriptions-item-label) {
    font-weight: 500;
    width: 120px;
  }

  .port-tip {
    color: #999;
    font-size: 12px;
  }
}
</style>

