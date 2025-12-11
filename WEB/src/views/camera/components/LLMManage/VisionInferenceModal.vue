<template>
  <BasicModal
    v-bind="$attrs"
    @register="register"
    :title="getTitle"
    :width="900"
    @ok="handleSubmit"
    :confirmLoading="loading"
  >
    <div class="vision-inference-modal">
      <!-- 图片上传区域 -->
      <div class="upload-section">
        <a-upload
          v-model:file-list="fileList"
          :before-upload="beforeUpload"
          :max-count="1"
          list-type="picture-card"
          accept="image/*"
          @preview="handlePreview"
          @remove="handleRemove"
        >
          <div v-if="fileList.length < 1">
            <PlusOutlined />
            <div style="margin-top: 8px">上传图片</div>
          </div>
        </a-upload>
        <Modal :open="previewVisible" :footer="null" @cancel="previewVisible = false">
          <img alt="preview" style="width: 100%" :src="previewImage" />
        </Modal>
      </div>

      <!-- 提示词输入区域 -->
      <div class="prompt-section">
        <FormItem label="提示词" :label-col="{ span: 4 }" :wrapper-col="{ span: 20 }">
          <Textarea
            v-model:value="prompt"
            :placeholder="getPromptPlaceholder"
            :rows="4"
            :maxlength="1000"
            show-count
          />
        </FormItem>
      </div>

      <!-- 推理模式选择 -->
      <div class="mode-section">
        <FormItem label="推理模式" :label-col="{ span: 4 }" :wrapper-col="{ span: 20 }">
          <RadioGroup v-model:value="inferenceMode" @change="handleModeChange">
            <Radio value="inference">视觉推理</Radio>
            <Radio value="understanding">视觉理解</Radio>
            <Radio value="deep-thinking">深度思考</Radio>
          </RadioGroup>
          <div class="mode-description">
            <div v-if="inferenceMode === 'inference'">
              <strong>视觉推理：</strong>分析图片中的对象、场景和可能的行为，进行逻辑推理。
            </div>
            <div v-else-if="inferenceMode === 'understanding'">
              <strong>视觉理解：</strong>深入理解图片内容，包括场景描述、对象关系、情感色彩和潜在含义。
            </div>
            <div v-else-if="inferenceMode === 'deep-thinking'">
              <strong>深度思考：</strong>多角度深度分析，包括关键信息、原因背景、影响后果和建议方案。
            </div>
          </div>
        </FormItem>
      </div>

      <!-- 结果显示区域 -->
      <div v-if="result" class="result-section">
        <Divider>推理结果</Divider>
        <div class="result-content">
          <Spin :spinning="loading">
            <div class="result-text">{{ result }}</div>
          </Spin>
        </div>
      </div>
    </div>
  </BasicModal>
</template>

<script lang="ts" setup>
import { ref, computed } from 'vue';
import { BasicModal, useModalInner } from '@/components/Modal';
import { useMessage } from '@/hooks/web/useMessage';
import { PlusOutlined } from '@ant-design/icons-vue';
import { Upload, Modal, Form, FormItem, Input, Textarea, RadioGroup, Radio, Divider, Spin } from 'ant-design-vue';
import type { UploadFile, UploadProps } from 'ant-design-vue';
import {
  visionInference,
  visionUnderstanding,
  visionDeepThinking,
} from '@/api/device/llm';

defineOptions({ name: 'VisionInferenceModal' });

const emit = defineEmits(['success', 'register']);

const { createMessage } = useMessage();
const [register, { setModalProps, closeModal }] = useModalInner(() => {
  // 初始化
  fileList.value = [];
  prompt.value = '';
  inferenceMode.value = 'inference';
  result.value = '';
  previewVisible.value = false;
  previewImage.value = '';
  loading.value = false;
});

const fileList = ref<UploadFile[]>([]);
const prompt = ref<string>('');
const inferenceMode = ref<'inference' | 'understanding' | 'deep-thinking'>('inference');
const result = ref<string>('');
const previewVisible = ref(false);
const previewImage = ref('');
const loading = ref(false);

const getTitle = computed(() => '大模型视觉推理');

const getPromptPlaceholder = computed(() => {
  if (inferenceMode.value === 'inference') {
    return '请对这张图片进行视觉推理，分析图片中的对象、场景和可能的行为。';
  } else if (inferenceMode.value === 'understanding') {
    return '请深入理解这张图片的内容，包括场景描述、对象关系、情感色彩和潜在含义。';
  } else {
    return '请对这张图片进行深度思考和分析，包括：1. 图片中的关键信息；2. 可能的原因和背景；3. 潜在的影响和后果；4. 相关的建议和解决方案。';
  }
});

const beforeUpload: UploadProps['beforeUpload'] = (file) => {
  const isImage = file.type?.startsWith('image/');
  if (!isImage) {
    createMessage.error('只能上传图片文件！');
    return false;
  }
  const isLt10M = file.size! / 1024 / 1024 < 10;
  if (!isLt10M) {
    createMessage.error('图片大小不能超过 10MB！');
    return false;
  }
  return false; // 阻止自动上传
};

const handlePreview = (file: UploadFile) => {
  if (!file.url && !file.preview) {
    file.preview = URL.createObjectURL(file.originFileObj as Blob);
  }
  previewImage.value = file.url || file.preview || '';
  previewVisible.value = true;
};

const handleRemove = () => {
  fileList.value = [];
  result.value = '';
};

const handleModeChange = () => {
  // 切换模式时更新提示词占位符
  prompt.value = '';
  result.value = '';
};

const handleSubmit = async () => {
  if (fileList.value.length === 0) {
    createMessage.error('请先上传图片！');
    return;
  }

  const file = fileList.value[0].originFileObj;
  if (!file) {
    createMessage.error('图片文件无效！');
    return;
  }

  try {
    loading.value = true;
    setModalProps({ confirmLoading: true });

    let response;
    if (inferenceMode.value === 'inference') {
      response = await visionInference(file as File, prompt.value || undefined);
    } else if (inferenceMode.value === 'understanding') {
      response = await visionUnderstanding(file as File, prompt.value || undefined);
    } else {
      response = await visionDeepThinking(file as File, prompt.value || undefined);
    }

    if (response.code === 0) {
      result.value = response.data.response || '';
      createMessage.success('推理成功！');
    } else {
      createMessage.error(response.msg || '推理失败');
    }
  } catch (error: any) {
    console.error('视觉推理失败', error);
    createMessage.error(error?.message || '推理失败，请稍后重试');
  } finally {
    loading.value = false;
    setModalProps({ confirmLoading: false });
  }
};
</script>

<style lang="less" scoped>
.vision-inference-modal {
  .upload-section {
    margin-bottom: 20px;
  }

  .prompt-section {
    margin-bottom: 20px;
  }

  .mode-section {
    margin-bottom: 20px;

    .mode-description {
      margin-top: 12px;
      padding: 12px;
      background: #f5f5f5;
      border-radius: 4px;
      font-size: 13px;
      color: #666;
      line-height: 1.6;
    }
  }

  .result-section {
    margin-top: 20px;

    .result-content {
      min-height: 100px;
      max-height: 400px;
      overflow-y: auto;
      padding: 16px;
      background: #fafafa;
      border-radius: 4px;
      border: 1px solid #e8e8e8;

      .result-text {
        white-space: pre-wrap;
        word-break: break-word;
        line-height: 1.8;
        color: #333;
      }
    }
  }
}
</style>
