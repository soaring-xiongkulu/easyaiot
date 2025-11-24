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
        <a-form-item label="模型列表" :required="true">
          <a-select
            v-model:value="formState.model_id"
            placeholder="模型列表"
            :options="modelOptions"
            show-search
            :filter-option="filterOption"
            allow-clear
            @change="handleModelChange"
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
        <a-form-item label="流媒体推送地址" :required="true">
          <template #extra>
            <span class="port-tip">用于视频/RTSP推理的流媒体推送地址（必填）</span>
          </template>
          <a-input
            v-model:value="formState.sorter_push_url"
            placeholder="例如: rtmp://example.com:1935/live/stream"
            style="width: 100%"
          />
        </a-form-item>
        <a-form-item label="排序器端口" :required="true">
          <template #extra>
            <span class="port-tip">排序器服务端口号（必填）</span>
          </template>
          <a-input-number
            v-model:value="formState.sorter_port"
            placeholder="请输入排序器端口"
            :min="9000"
            :max="65535"
            style="width: 100%"
          />
        </a-form-item>
        <a-form-item label="抽帧器端口" :required="true">
          <template #extra>
            <span class="port-tip">抽帧器服务端口号（必填）</span>
          </template>
          <a-input-number
            v-model:value="formState.extractor_port"
            placeholder="请输入抽帧器端口"
            :min="9100"
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

const AForm = Form;
const AFormItem = FormItem;
const ASelect = Select;
const AInput = Input;
const AInputNumber = InputNumber;

const { createMessage } = useMessage();

const modelOptions = ref<Array<{ label: string; value: number }>>([]);

const formState = reactive({
  model_id: null as number | null,
  start_port: 9999 as number,
  sorter_push_url: '' as string,
  sorter_port: 9000 as number,
  extractor_port: 9100 as number,
});


const state = reactive({
  deploying: false,
});

const deploying = computed(() => state.deploying);

// 验证表单是否有效
const isFormValid = computed(() => {
  return formState.model_id !== null 
    && formState.start_port >= 8000 
    && formState.start_port <= 65535
    && formState.sorter_push_url.trim() !== ''
    && formState.sorter_port >= 9000
    && formState.sorter_port <= 65535
    && formState.extractor_port >= 9100
    && formState.extractor_port <= 65535;
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
  formState.start_port = 9999;
  formState.sorter_push_url = '';
  formState.sorter_port = 9000;
  formState.extractor_port = 9100;
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
    const values: any = {
      model_id: formState.model_id,
      start_port: formState.start_port,
      sorter_push_url: formState.sorter_push_url.trim(),
      sorter_port: formState.sorter_port,
      extractor_port: formState.extractor_port,
    };
    
    await deployModel(values);
    createMessage.success('部署成功');
    closeModal();
    emit('success');
  } catch (error: any) {
    console.error('部署失败:', error);
    // 直接显示后端返回的错误信息
    const errorMsg = error.response?.data?.msg || error.message || '部署失败';
    createMessage.error(errorMsg);
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

