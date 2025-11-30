<template>
  <a-modal
    v-model:open="open"
    :title="serviceData ? '编辑算法服务' : '添加算法服务'"
    width="600"
    @ok="handleSubmit"
    @cancel="handleCancel"
  >
    <a-form
      ref="formRef"
      :model="formData"
      :rules="rules"
      :label-col="{ span: 6 }"
      :wrapper-col="{ span: 18 }"
    >
      <a-form-item label="服务名称" name="service_name">
        <a-input v-model:value="formData.service_name" placeholder="请输入服务名称" />
      </a-form-item>
      <a-form-item label="服务URL" name="service_url">
        <a-input v-model:value="formData.service_url" placeholder="请输入服务URL" />
      </a-form-item>
      <a-form-item label="服务类型" name="service_type">
        <a-input v-model:value="formData.service_type" placeholder="例如: FIRE, CROWD, SMOKE" />
      </a-form-item>
      <a-form-item label="模型ID" name="model_id">
        <a-input-number v-model:value="formData.model_id" placeholder="请输入模型ID" style="width: 100%" />
      </a-form-item>
      <a-form-item label="阈值" name="threshold">
        <a-input-number
          v-model:value="formData.threshold"
          placeholder="请输入阈值"
          :min="0"
          :max="1"
          :step="0.01"
          style="width: 100%"
        />
      </a-form-item>
      <a-form-item label="请求方法" name="request_method">
        <a-select v-model:value="formData.request_method" placeholder="请选择请求方法">
          <a-select-option value="GET">GET</a-select-option>
          <a-select-option value="POST">POST</a-select-option>
        </a-select>
      </a-form-item>
      <a-form-item label="超时时间" name="timeout">
        <a-input-number
          v-model:value="formData.timeout"
          placeholder="请输入超时时间（秒）"
          :min="1"
          style="width: 100%"
        />
      </a-form-item>
      <a-form-item label="排序顺序" name="sort_order">
        <a-input-number
          v-model:value="formData.sort_order"
          placeholder="请输入排序顺序"
          :min="0"
          style="width: 100%"
        />
      </a-form-item>
      <a-form-item label="是否启用" name="is_enabled">
        <a-switch v-model:checked="formData.is_enabled" />
      </a-form-item>
    </a-form>
  </a-modal>
</template>

<script lang="ts" setup>
import { ref, watch } from 'vue';
import { useMessage } from '@/hooks/web/useMessage';
import {
  createTaskService,
  updateTaskService,
  type AlgorithmModelService,
} from '@/api/device/algorithm_task';

defineOptions({ name: 'AlgorithmServiceModal' });

const props = defineProps<{
  taskId: number;
  serviceData?: AlgorithmModelService | null;
}>();

const emit = defineEmits(['update:open', 'success']);

const { createMessage } = useMessage();

const open = ref(false);
const formRef = ref();

const formData = ref({
  service_name: '',
  service_url: '',
  service_type: '',
  model_id: undefined as number | undefined,
  threshold: undefined as number | undefined,
  request_method: 'POST',
  timeout: 30,
  sort_order: 0,
  is_enabled: true,
});

const rules = {
  service_name: [{ required: true, message: '请输入服务名称', trigger: 'blur' }],
  service_url: [{ required: true, message: '请输入服务URL', trigger: 'blur' }],
  request_method: [{ required: true, message: '请选择请求方法', trigger: 'change' }],
  timeout: [{ required: true, message: '请输入超时时间', trigger: 'blur' }],
};

watch(
  () => props.serviceData,
  (val) => {
    if (val) {
      formData.value = {
        service_name: val.service_name || '',
        service_url: val.service_url || '',
        service_type: val.service_type || '',
        model_id: val.model_id,
        threshold: val.threshold,
        request_method: val.request_method || 'POST',
        timeout: val.timeout || 30,
        sort_order: val.sort_order || 0,
        is_enabled: val.is_enabled !== undefined ? val.is_enabled : true,
      };
    } else {
      formData.value = {
        service_name: '',
        service_url: '',
        service_type: '',
        model_id: undefined,
        threshold: undefined,
        request_method: 'POST',
        timeout: 30,
        sort_order: 0,
        is_enabled: true,
      };
    }
  },
  { immediate: true }
);

watch(open, (val) => {
  emit('update:open', val);
});

const handleSubmit = async () => {
  try {
    await formRef.value.validate();
    
    // 将布尔值转换为整数：true -> 1, false -> 0
    const submitData = {
      ...formData.value,
      is_enabled: formData.value.is_enabled === true || formData.value.is_enabled === 'true' ? 1 : 0,
    };
    
    if (props.serviceData) {
      // 更新
      const response = await updateTaskService(props.serviceData.id, submitData);
      if (response.code === 0) {
        createMessage.success('更新成功');
        emit('success');
        open.value = false;
      } else {
        createMessage.error(response.msg || '更新失败');
      }
    } else {
      // 创建
      const response = await createTaskService(props.taskId, submitData);
      if (response.code === 0) {
        createMessage.success('创建成功');
        emit('success');
        open.value = false;
      } else {
        createMessage.error(response.msg || '创建失败');
      }
    }
  } catch (error) {
    console.error('提交失败', error);
  }
};

const handleCancel = () => {
  open.value = false;
};
</script>

