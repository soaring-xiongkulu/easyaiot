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
        <Icon icon="ant-design:play-circle-outlined" class="title-icon" />
        AI自动标注设置
      </span>
    </template>
    
    <div class="modal-content">
      <Form
        :model="form"
        :label-col="{ span: 0 }"
        :wrapper-col="{ span: 24 }"
      >
        <!-- 选择小样本模型 -->
        <FormItem>
          <div class="form-label">选择小样本模型:</div>
          <Select
            v-model:value="form.few_shot_model_id"
            placeholder="请选择小样本模型"
            :loading="modelLoading"
            show-search
            :filter-option="filterModelOption"
            allow-clear
            class="model-select"
          >
            <SelectOption
              v-for="model in fewShotModelList"
              :key="model.id"
              :value="model.id"
            >
              {{ model.name || `模型 ${model.id}` }}
            </SelectOption>
          </Select>
          <div class="form-hint">
            请先在设置中安装YOLO11并下载或上传模型
          </div>
        </FormItem>
        
        <!-- 置信度阈值 -->
        <FormItem>
          <div class="form-label">置信度阈值:</div>
          <div class="confidence-slider-wrapper">
            <Slider
              v-model:value="form.confidence_threshold"
              :min="0.1"
              :max="0.9"
              :step="0.05"
              class="confidence-slider"
            />
            <div class="confidence-value">{{ form.confidence_threshold }}</div>
          </div>
          <div class="form-hint">
            置信度越高,检测越严格,框越少
          </div>
        </FormItem>
        
        <!-- 自动切换选项 -->
        <FormItem>
          <Checkbox v-model:checked="form.autoSwitchNext">
            保存后自动切换到下一张图片
          </Checkbox>
        </FormItem>
      </Form>
    </div>
    
    <template #footer>
      <div class="modal-footer-custom">
        <Button class="start-ai-label-btn" @click="handleStart" :loading="loading">
          <template #icon><Icon icon="ant-design:play-circle-outlined" /></template>
          开启AI标注
        </Button>
        <Button class="cancel-btn" @click="handleCancel">
          <template #icon><Icon icon="ant-design:close-outlined" /></template>
          取消
        </Button>
      </div>
    </template>
  </BasicModal>
</template>

<script lang="ts" setup>
import { ref, reactive } from 'vue';
import { BasicModal, useModal } from '@/components/Modal';
import { Icon } from '@/components/Icon';
import { Form, FormItem, Select, SelectOption, Slider, Checkbox, Button } from 'ant-design-vue';
import { useMessage } from '@/hooks/web/useMessage';
import { startAutoLabel } from '@/api/device/auto-label';

defineOptions({ name: 'AILabelModal' });

const { createMessage } = useMessage();

const emits = defineEmits(['success', 'update:form']);

const loading = ref(false);
const modelLoading = ref(false);
const fewShotModelList = ref([]);

const form = reactive({
  few_shot_model_id: undefined,
  confidence_threshold: 0.5,
  autoSwitchNext: false,
});

const [register, { openModal, closeModal }] = useModal();

// 加载小样本模型列表（暂时不调用后端，接口还没有）
async function loadFewShotModelList() {
  try {
    modelLoading.value = true;
    // TODO: 等后端接口准备好后，调用接口加载小样本模型列表
    // const response = await getFewShotModelList();
    // const res = response?.data || response;
    // if (res && res.code === 0) {
    //   fewShotModelList.value = res.data?.list || res.data || [];
    // }
    
    // 暂时使用空列表
    fewShotModelList.value = [];
  } catch (error: any) {
    console.error('加载小样本模型列表失败:', error);
    createMessage.error('加载小样本模型列表失败');
  } finally {
    modelLoading.value = false;
  }
}

// 过滤模型选项
const filterModelOption = (input: string, option: any) => {
  return option.children.toLowerCase().indexOf(input.toLowerCase()) >= 0;
};

// 开始AI标注
async function handleStart() {
  if (!form.few_shot_model_id) {
    createMessage.warning('请选择小样本模型');
    return;
  }
  
  const datasetId = (window as any).__currentDatasetId__;
  if (!datasetId) {
    createMessage.warning('请先选择数据集');
    return;
  }
  
  try {
    loading.value = true;
    const res = await startAutoLabel(datasetId, {
      few_shot_model_id: form.few_shot_model_id,
      confidence_threshold: form.confidence_threshold,
    });
    
    if (res.code === 0) {
      createMessage.success('AI自动标注任务已启动');
      closeModal();
      emits('success', {
        taskId: res.data?.task_id,
        form: { ...form }
      });
    } else {
      createMessage.error(res.msg || '启动AI自动标注失败');
    }
  } catch (error) {
    console.error('启动AI自动标注失败:', error);
    createMessage.error('启动AI自动标注失败');
  } finally {
    loading.value = false;
  }
}

// 打开模态框时加载模型列表
const openModalWithLoad = () => {
  loadFewShotModelList();
  openModal();
};

// 更新暴露的方法
defineExpose({
  openModal: openModalWithLoad,
  closeModal,
  form,
  loadFewShotModelList,
});

// 取消
function handleCancel() {
  closeModal();
}
</script>

<style lang="less" scoped>
.modal-content {
  padding: 24px;
  
  :deep(.ant-form-item) {
    margin-bottom: 24px;
    
    &:last-child {
      margin-bottom: 0;
    }
  }
}

.form-label {
  font-size: 14px;
  font-weight: 500;
  color: #333;
  margin-bottom: 8px;
  line-height: 22px;
}

.model-select {
  width: 100%;
  
  :deep(.ant-select-selector) {
    height: 32px;
    border-radius: 4px;
    border: 1px solid #d9d9d9;
    
    &:hover {
      border-color: #40a9ff;
    }
    
    .ant-select-selection-item {
      line-height: 30px;
    }
    
    .ant-select-selection-placeholder {
      line-height: 30px;
    }
  }
  
  :deep(.ant-select-focused .ant-select-selector) {
    border-color: #40a9ff;
    box-shadow: 0 0 0 2px rgba(24, 144, 255, 0.2);
  }
}

.form-hint {
  margin-top: 8px;
  font-size: 12px;
  color: #999;
  line-height: 1.5;
}

.confidence-slider-wrapper {
  position: relative;
  padding-right: 50px;
  padding-top: 8px;
  padding-bottom: 8px;
  
  .confidence-slider {
    :deep(.ant-slider) {
      margin: 0;
      
      .ant-slider-rail {
        height: 4px;
        background-color: #f0f0f0;
        border-radius: 2px;
      }
      
      .ant-slider-track {
        height: 4px;
        background-color: #1890ff;
        border-radius: 2px;
      }
      
      .ant-slider-handle {
        width: 14px;
        height: 14px;
        border: 2px solid #1890ff;
        background-color: #fff;
        margin-top: -5px;
        
        &:focus {
          border-color: #1890ff;
          box-shadow: 0 0 0 5px rgba(24, 144, 255, 0.12);
        }
        
        &:hover {
          border-color: #40a9ff;
        }
      }
    }
  }
  
  .confidence-value {
    position: absolute;
    top: 8px;
    right: 0;
    font-size: 14px;
    font-weight: 500;
    color: #333;
    line-height: 22px;
    min-width: 40px;
    text-align: right;
  }
}

:deep(.ant-checkbox-wrapper) {
  font-size: 14px;
  color: #333;
  line-height: 22px;
  
  .ant-checkbox {
    .ant-checkbox-inner {
      width: 16px;
      height: 16px;
      border-radius: 2px;
      border-color: #d9d9d9;
      
      &:after {
        width: 5.71428571px;
        height: 9.14285714px;
      }
    }
    
    &.ant-checkbox-checked .ant-checkbox-inner {
      background-color: #1890ff;
      border-color: #1890ff;
    }
  }
}

.modal-title-with-icon {
  display: flex;
  align-items: center;
  gap: 8px;
  
  .title-icon {
    font-size: 18px;
    color: #333;
  }
}

.modal-footer-custom {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 16px 24px;
  border-top: 1px solid #e8e8e8;
  
  .start-ai-label-btn {
    background: #1890ff !important;
    border-color: #1890ff !important;
    color: #fff !important;
    height: 32px;
    padding: 4px 15px;
    font-size: 14px;
    border-radius: 4px;
    display: flex;
    align-items: center;
    gap: 6px;
    
    :deep(.anticon) {
      color: #fff;
      font-size: 14px;
    }
    
    &:hover,
    &:focus {
      background: #40a9ff !important;
      border-color: #40a9ff !important;
      color: #fff !important;
    }
    
    &:active {
      background: #1890ff !important;
      border-color: #1890ff !important;
    }
  }
  
  .cancel-btn {
    background: #fff !important;
    border-color: #d9d9d9 !important;
    color: #666 !important;
    height: 32px;
    padding: 4px 15px;
    font-size: 14px;
    border-radius: 4px;
    display: flex;
    align-items: center;
    gap: 6px;
    
    :deep(.anticon) {
      color: #666;
      font-size: 14px;
    }
    
    &:hover,
    &:focus {
      background: #fff !important;
      border-color: #40a9ff !important;
      color: #40a9ff !important;
      
      :deep(.anticon) {
        color: #40a9ff;
      }
    }
  }
}
</style>