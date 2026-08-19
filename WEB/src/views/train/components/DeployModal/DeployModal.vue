<template>
  <BasicModal
    v-bind="$attrs"
    @register="register"
    title="模型部署"
    @cancel="handleCancel"
    :width="650"
    @ok="handleSubmit"
    :canFullscreen="false"
    :confirmLoading="deploying"
    :okButtonProps="{ disabled: !isFormValid }"
  >
    <div class="deploy-confirm-modal">
      <a-form :model="formState" :label-col="{ span: 5 }" :wrapper-col="{ span: 19 }" class="deploy-form">
        <a-form-item label="模型列表" :required="true" class="form-item-input">
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
        <a-form-item label="部署目标" class="form-item-input">
          <a-select
            v-model:value="formState.deploy_target"
            :options="deployTargetOptions"
            @change="handleDeployTargetChange"
          />
        </a-form-item>
        <a-form-item
          v-if="formState.deploy_target === 'auto'"
          label="优先 GPU"
          class="form-item-input"
        >
          <a-switch v-model:checked="formState.prefer_gpu" checked-children="是" un-checked-children="否" />
          <span class="port-tip" style="margin-left: 8px">自动调度时优先选择 GPU 节点</span>
        </a-form-item>
        <a-form-item
          v-if="formState.deploy_target === 'node'"
          label="目标节点"
          :required="true"
          class="form-item-input"
        >
          <a-select
            v-model:value="formState.target_node_id"
            placeholder="选择在线计算节点"
            :options="nodeOptions"
            show-search
            :filter-option="filterOption"
            allow-clear
          />
        </a-form-item>
        <a-form-item label="端口" :required="true" class="form-item-input">
          <template #extra>
            <span class="port-tip">端口占用时自动寻找未占用端口</span>
          </template>
          <a-input-number
            v-model:value="formState.start_port"
            placeholder="请输入端口"
            :min="8000"
            :max="65535"
          />
        </a-form-item>
      </a-form>
    </div>
  </BasicModal>
</template>

<script lang="ts" setup>
import { computed, reactive, ref, watch, onMounted } from 'vue';
import { BasicModal, useModalInner } from '@/components/Modal';
import { Form, FormItem, Select, InputNumber, Switch } from 'ant-design-vue';
import { useMessage } from '@/hooks/web/useMessage';
import { deployModel, getModelPage } from '@/api/device/model';
import { getNodePage } from '@/api/device/node';
import { nodeHasAnyFunction } from '@/views/node/utils/constants';

const AForm = Form;
const AFormItem = FormItem;
const ASelect = Select;
const AInputNumber = InputNumber;
const ASwitch = Switch;

const { createMessage } = useMessage();

const modelOptions = ref<Array<{ label: string; value: number }>>([]);
const nodeOptions = ref<Array<{ label: string; value: number }>>([]);

const deployTargetOptions = [
  { label: '本机部署', value: 'local' },
  { label: '自动调度节点', value: 'auto' },
  { label: '指定节点', value: 'node' },
];

const formState = reactive({
  model_id: null as number | null,
  start_port: 9999 as number,
  deploy_target: 'local' as string,
  prefer_gpu: true,
  target_node_id: null as number | null,
});


const state = reactive({
  deploying: false,
});

const deploying = computed(() => state.deploying);

// 验证表单是否有效
const isFormValid = computed(() => {
  const base = formState.model_id !== null
    && formState.start_port >= 8000
    && formState.start_port <= 65535;
  if (formState.deploy_target === 'node') {
    return base && formState.target_node_id !== null;
  }
  return base;
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

const loadNodeOptions = async () => {
  try {
    const res = await getNodePage({ pageNo: 1, pageSize: 200, status: 'online' });
    const page = res?.data || res;
    const list = (page?.list || []).filter(
      (node: any) => nodeHasAnyFunction(node, ['infer', 'llm']),
    );
    nodeOptions.value = list.map((node: any) => ({
      label: `${node.name} (${node.host})`,
      value: node.id,
    }));
  } catch (error) {
    console.error('获取节点列表失败:', error);
    nodeOptions.value = [];
  }
};

onMounted(() => {
  loadModelOptions();
  loadNodeOptions();
});

const [register, { closeModal, setModalProps }] = useModalInner(async () => {
  formState.model_id = null;
  formState.start_port = 9999;
  formState.deploy_target = 'local';
  formState.prefer_gpu = true;
  formState.target_node_id = null;
  state.deploying = false;
  setModalProps({ confirmLoading: false });
  await Promise.all([loadModelOptions(), loadNodeOptions()]);
});

function handleDeployTargetChange() {
  if (formState.deploy_target !== 'node') {
    formState.target_node_id = null;
  }
}

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
    const values: Record<string, unknown> = {
      model_id: formState.model_id,
      start_port: formState.start_port,
      auto_schedule: formState.deploy_target === 'auto',
    };
    if (formState.deploy_target === 'auto') {
      values.prefer_gpu = formState.prefer_gpu;
    }
    if (formState.deploy_target === 'node' && formState.target_node_id) {
      values.target_node_id = formState.target_node_id;
    }

    const response = await deployModel(values);
    // 检查响应中是否有警告标记
    if (response && (response as any).warning) {
      // 显示警告信息（模型下载失败但服务记录已创建）
      const warningMsg = (response as any).msg || '模型文件下载失败，请检查模型文件路径和MinIO配置';
      createMessage.warning(warningMsg);
      closeModal();
      emit('success');
    } else {
      const msg = (response as any)?.msg;
      createMessage.success(msg || '部署成功');
      closeModal();
      emit('success');
    }
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

  .deploy-form {
    max-width: 100%;
    margin: 0 auto;

    :deep(.ant-form-item-label) {
      text-align: center;
    }

    .form-item-input {
      :deep(.ant-select),
      :deep(.ant-input-number) {
        width: 100%;
      }
    }
  }
}
</style>

