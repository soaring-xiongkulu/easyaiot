<template>
  <BasicModal
    @register="register"
    title="导出模型"
    @cancel="handleCancel"
    :width="700"
    @ok="handleConfirm"
    :canFullscreen="false"
    :confirmLoading="exporting"
    :okButtonProps="{ disabled: !isFormValid }"
  >
    <div class="export-confirm-modal">
      <a-form :model="formState" :label-col="{ span: 6 }" :wrapper-col="{ span: 18 }">
        <a-form-item label="PT模型" :required="true">
          <a-select
            v-model:value="formState.modelId"
            placeholder="请选择要导出的PT模型"
            :options="modelOptions"
            show-search
            :filter-option="filterOption"
            allow-clear
            @change="handleModelChange"
          />
        </a-form-item>
        <a-form-item label="导出格式" :required="true">
          <a-select
            v-model:value="formState.format"
            placeholder="请选择导出格式"
            :options="formatOptions"
            allow-clear
            @change="handleFormatChange"
          />
        </a-form-item>
      </a-form>
    </div>
  </BasicModal>
</template>

<script lang="ts" setup>
import { computed, reactive, watch } from 'vue';
import { BasicModal, useModalInner } from '@/components/Modal';
import { Form, FormItem, Select } from 'ant-design-vue';

const AForm = Form;
const AFormItem = FormItem;
const ASelect = Select;

const props = defineProps({
  modelOptions: {
    type: Array as () => Array<{ label: string; value: number }>,
    default: () => [],
  },
});

const emit = defineEmits(['confirm']);

const formatOptions = [
  { label: 'ONNX', value: 'onnx' },
  { label: 'OpenVINO', value: 'openvino' },
];

const formState = reactive({
  modelId: null as number | null,
  format: null as 'onnx' | 'openvino' | null,
});

const state = reactive({
  exporting: false,
});

const exporting = computed(() => state.exporting);

// 验证表单是否有效
const isFormValid = computed(() => {
  return formState.modelId !== null && formState.format !== null;
});

const [register, { closeModal, setModalProps }] = useModalInner((data) => {
  // 重置表单
  formState.modelId = null;
  formState.format = null;
  state.exporting = false;
  setModalProps({ confirmLoading: false });
});

// 监听导出状态，更新弹框按钮的 loading 状态
watch(() => state.exporting, (loading) => {
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

// 格式选择变化
const handleFormatChange = () => {
  // 可以在这里添加逻辑
};

function handleCancel() {
  if (!state.exporting) {
    closeModal();
  }
}

function handleConfirm() {
  if (state.exporting) {
    return; // 如果正在导出，不允许重复点击
  }

  // 验证表单
  if (!isFormValid.value) {
    return; // 表单验证失败，不执行导出
  }

  state.exporting = true;
  emit('confirm', {
    modelId: formState.modelId,
    format: formState.format,
  });
}
</script>

<style lang="less" scoped>
.export-confirm-modal {
  padding: 8px 0;

  :deep(.ant-descriptions-item-label) {
    font-weight: 500;
    width: 120px;
  }
}
</style>

