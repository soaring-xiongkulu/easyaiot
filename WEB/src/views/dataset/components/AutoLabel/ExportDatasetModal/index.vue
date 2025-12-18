<template>
  <BasicModal
    @register="register"
    width="600px"
    @cancel="handleCancel"
    :canFullscreen="false"
    :showOkBtn="false"
    :showCancelBtn="false"
  >
    <template #title>
      <span class="modal-title-with-icon">
        <Icon icon="ant-design:download-outlined" class="title-icon" />
        导出数据集
      </span>
    </template>
    <div class="modal-content">
      <Form
        :model="form"
        :label-col="{ span: 8 }"
        :wrapper-col="{ span: 16 }"
      >
        <FormItem label="训练集比例: 验证集比例: 测试集比例:">
          <Space>
            <InputNumber
              v-model:value="form.train_ratio"
              :min="0"
              :max="1"
              :step="0.1"
              :precision="2"
              style="width: 100px"
            />
            <InputNumber
              v-model:value="form.val_ratio"
              :min="0"
              :max="1"
              :step="0.1"
              :precision="2"
              style="width: 100px"
            />
            <InputNumber
              v-model:value="form.test_ratio"
              :min="0"
              :max="1"
              :step="0.1"
              :precision="2"
              style="width: 100px"
            />
          </Space>
        </FormItem>
        
        <FormItem label="样本选择:">
          <RadioGroup v-model:value="form.sampleType">
            <Radio value="all">所有图片</Radio>
            <Radio value="annotated">仅已标注的图片</Radio>
            <Radio value="unannotated">仅未标注的图片</Radio>
          </RadioGroup>
        </FormItem>
        
        <FormItem label="导出数据类型:">
          <RadioGroup v-model:value="form.format">
            <Radio value="yolo">YOLO格式</Radio>
            <Radio value="resnet">ResNet格式</Radio>
            <Radio value="videonet">VideoNet格式</Radio>
            <Radio value="audionet">AudioNet格式</Radio>
          </RadioGroup>
        </FormItem>
        
        <FormItem label="类别选择:">
          <CheckboxGroup v-model:value="form.selectedClasses" style="width: 100%">
            <Row :gutter="[8, 8]">
              <Col :span="8" v-for="label in labels" :key="label.id">
                <Checkbox :value="label.name">{{ label.name }}</Checkbox>
              </Col>
            </Row>
          </CheckboxGroup>
        </FormItem>
        
        <FormItem label="导出文件前缀(可选):">
          <Input
            v-model:value="form.filePrefix"
            placeholder="输入文件前缀"
            allow-clear
          />
        </FormItem>
      </Form>
    </div>
    <template #footer>
      <div class="modal-footer-custom">
        <Button type="primary" @click="handleConfirm" :loading="loading">
          <template #icon><Icon icon="ant-design:download-outlined" /></template>
          导出
        </Button>
        <Button @click="handleCancel">取消</Button>
      </div>
    </template>
  </BasicModal>
</template>

<script lang="ts" setup>
import { ref, reactive, watch } from 'vue';
import { BasicModal, useModal } from '@/components/Modal';
import { Icon } from '@/components/Icon';
import { Form, FormItem, InputNumber, RadioGroup, Radio, CheckboxGroup, Checkbox, Row, Col, Input, Button, Space } from 'ant-design-vue';
import { useMessage } from '@/hooks/web/useMessage';
import { exportLabeledDataset } from '@/api/device/auto-label';

defineOptions({ name: 'ExportDatasetModal' });

const { createMessage } = useMessage();

const emits = defineEmits(['success']);

const loading = ref(false);
const labels = ref<any[]>([]);

const form = reactive({
  format: 'yolo',
  train_ratio: 0.7,
  val_ratio: 0.2,
  test_ratio: 0.1,
  sampleType: 'all',
  selectedClasses: [] as string[],
  filePrefix: '',
});

const [register, { openModal, closeModal }] = useModal();

// 监听标签变化
watch(() => (window as any).__currentLabels__, (newLabels: any[]) => {
  if (newLabels && Array.isArray(newLabels)) {
    labels.value = newLabels;
    // 默认选择所有类别
    if (form.selectedClasses.length === 0 && newLabels.length > 0) {
      form.selectedClasses = newLabels.map(l => l.name);
    }
  }
}, { immediate: true, deep: true });

// 打开模态框时更新标签
const openModalWithLabels = () => {
  const currentLabels = (window as any).__currentLabels__;
  if (currentLabels && Array.isArray(currentLabels)) {
    labels.value = currentLabels;
    if (form.selectedClasses.length === 0) {
      form.selectedClasses = currentLabels.map(l => l.name);
    }
  }
  openModal();
};

// 更新暴露的方法
defineExpose({
  openModal: openModalWithLabels,
  closeModal,
  form,
});

// 确认导出
const handleConfirm = async () => {
  const datasetId = (window as any).__currentDatasetId__;
  if (!datasetId) {
    createMessage.warning('请先选择数据集');
    return;
  }

  // 验证比例
  const total = form.train_ratio + form.val_ratio + form.test_ratio;
  if (Math.abs(total - 1.0) > 0.01) {
    createMessage.warning('训练集、验证集、测试集比例之和必须为1');
    return;
  }

  // 如果没有选择类别，默认选择所有类别
  if (form.selectedClasses.length === 0) {
    form.selectedClasses = labels.value.map(l => l.name);
  }

  try {
    loading.value = true;
    const res = await exportLabeledDataset(datasetId, {
      format: form.format,
      train_ratio: form.train_ratio,
      val_ratio: form.val_ratio,
      test_ratio: form.test_ratio,
      sample_type: form.sampleType,
      selected_classes: form.selectedClasses,
      file_prefix: form.filePrefix,
    });

    // 处理文件下载
    if (res instanceof Blob) {
      const url = window.URL.createObjectURL(res);
      const link = document.createElement('a');
      const prefix = form.filePrefix || `dataset_${datasetId}`;
      link.href = url;
      link.download = `${prefix}_${Date.now()}.zip`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
      createMessage.success('导出成功');
      closeModal();
      emits('success');
    } else {
      createMessage.error('导出失败');
    }
  } catch (error) {
    console.error('导出失败:', error);
    createMessage.error('导出失败');
  } finally {
    loading.value = false;
  }
};

// 取消
const handleCancel = () => {
  closeModal();
};
</script>

<style lang="less" scoped>
.modal-content {
  padding: 24px;
  
  :deep(.ant-form-item-label) {
    & > label::after {
      content: '';
    }
    
    & > label {
      font-weight: 500;
      color: #333;
    }
  }
}

.modal-title-with-icon {
  display: flex;
  align-items: center;
  gap: 8px;
  
  .title-icon {
    font-size: 18px;
  }
}

.modal-footer-custom {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 16px 24px;
  border-top: 1px solid #e8e8e8;
}
</style>
