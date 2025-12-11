<template>
  <BasicModal
    v-bind="$attrs"
    @register="register"
    :title="getTitle"
    :width="1000"
    @ok="handleSubmit"
    :confirmLoading="loading"
  >
    <div class="video-inference-modal">
      <!-- 视频上传区域 -->
      <div class="upload-section">
        <FormItem label="视频输入" :label-col="{ span: 4 }" :wrapper-col="{ span: 20 }">
          <Tabs v-model:activeKey="inputType" @change="handleInputTypeChange">
            <TabPane key="file" tab="上传文件">
              <a-upload
                v-model:file-list="fileList"
                :before-upload="beforeUpload"
                :max-count="1"
                accept="video/*"
                @remove="handleRemove"
              >
                <a-button>
                  <template #icon>
                    <UploadOutlined />
                  </template>
                  选择视频文件
                </a-button>
              </a-upload>
              <div class="upload-tip">
                支持 MP4、AVI、MOV 等格式，文件大小不超过 100MB
              </div>
            </TabPane>
            <TabPane key="url" tab="视频URL">
              <Input
                v-model:value="videoUrl"
                placeholder="请输入视频公网URL，例如：https://example.com/video.mp4"
                :allowClear="true"
              />
              <div class="upload-tip">
                请输入可公网访问的视频URL地址
              </div>
            </TabPane>
          </Tabs>
        </FormItem>
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
            <Radio value="inference">视频推理</Radio>
            <Radio value="understanding">视频理解</Radio>
          </RadioGroup>
          <div class="mode-description">
            <div v-if="inferenceMode === 'inference'">
              <strong>视频推理：</strong>分析视频中的对象、场景和可能的行为，进行逻辑推理。
            </div>
            <div v-else-if="inferenceMode === 'understanding'">
              <strong>视频理解：</strong>深入理解视频内容，包括场景描述、对象关系、情感色彩和潜在含义。
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
            <div v-if="usage" class="usage-info">
              <div v-if="usage.prompt_tokens">提示词 tokens: {{ usage.prompt_tokens }}</div>
              <div v-if="usage.completion_tokens">完成 tokens: {{ usage.completion_tokens }}</div>
              <div v-if="usage.total_tokens">总 tokens: {{ usage.total_tokens }}</div>
            </div>
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
import { UploadOutlined } from '@ant-design/icons-vue';
import {
  Upload,
  Modal,
  Form,
  FormItem,
  Input,
  Textarea,
  RadioGroup,
  Radio,
  Divider,
  Spin,
  Tabs,
  TabPane,
  Button,
} from 'ant-design-vue';
import type { UploadFile, UploadProps } from 'ant-design-vue';
import { videoInference, videoUnderstanding } from '@/api/device/llm';

defineOptions({ name: 'VideoInferenceModal' });

const emit = defineEmits(['success', 'register']);

const { createMessage } = useMessage();
const [register, { setModalProps, closeModal }] = useModalInner(() => {
  // 初始化
  fileList.value = [];
  videoUrl.value = '';
  prompt.value = '';
  inferenceMode.value = 'inference';
  inputType.value = 'file';
  result.value = '';
  usage.value = null;
  loading.value = false;
});

const fileList = ref<UploadFile[]>([]);
const videoUrl = ref<string>('');
const prompt = ref<string>('');
const inferenceMode = ref<'inference' | 'understanding'>('inference');
const inputType = ref<'file' | 'url'>('file');
const result = ref<string>('');
const usage = ref<any>(null);
const loading = ref(false);

const getTitle = computed(() => '大模型视频推理');

const getPromptPlaceholder = computed(() => {
  if (inferenceMode.value === 'inference') {
    return '请分析这个视频中的对象、场景和可能的行为。';
  } else {
    return '请描述这个视频的内容。';
  }
});

const handleInputTypeChange = () => {
  // 切换输入类型时清空结果
  result.value = '';
  usage.value = null;
};

const beforeUpload: UploadProps['beforeUpload'] = (file) => {
  const isVideo = file.type?.startsWith('video/');
  if (!isVideo) {
    createMessage.error('只能上传视频文件！');
    return false;
  }
  const isLt100M = file.size! / 1024 / 1024 < 100;
  if (!isLt100M) {
    createMessage.error('视频大小不能超过 100MB！');
    return false;
  }
  return false; // 阻止自动上传
};

const handleRemove = () => {
  fileList.value = [];
  result.value = '';
  usage.value = null;
};

const handleModeChange = () => {
  // 切换模式时更新提示词占位符
  prompt.value = '';
  result.value = '';
  usage.value = null;
};

const handleSubmit = async () => {
  // 验证输入
  if (inputType.value === 'file' && fileList.value.length === 0) {
    createMessage.error('请先上传视频文件！');
    return;
  }
  if (inputType.value === 'url' && !videoUrl.value.trim()) {
    createMessage.error('请输入视频URL！');
    return;
  }

  try {
    loading.value = true;
    setModalProps({ confirmLoading: true });

    let response;
    const videoFile = inputType.value === 'file' && fileList.value.length > 0
      ? (fileList.value[0].originFileObj as File)
      : undefined;
    const url = inputType.value === 'url' ? videoUrl.value.trim() : undefined;

    if (inferenceMode.value === 'inference') {
      response = await videoInference(videoFile, url, prompt.value || undefined);
    } else {
      response = await videoUnderstanding(videoFile, url, prompt.value || undefined);
    }

    if (response.code === 0) {
      result.value = response.data.response || '';
      usage.value = response.data.usage || null;
      createMessage.success('推理成功！');
    } else {
      createMessage.error(response.msg || '推理失败');
    }
  } catch (error: any) {
    console.error('视频推理失败', error);
    createMessage.error(error?.message || '推理失败，请稍后重试');
  } finally {
    loading.value = false;
    setModalProps({ confirmLoading: false });
  }
};
</script>

<style lang="less" scoped>
.video-inference-modal {
  .upload-section {
    margin-bottom: 20px;

    .upload-tip {
      margin-top: 8px;
      font-size: 12px;
      color: #999;
    }
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
      max-height: 500px;
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
        margin-bottom: 12px;
      }

      .usage-info {
        margin-top: 12px;
        padding-top: 12px;
        border-top: 1px solid #e8e8e8;
        font-size: 12px;
        color: #666;

        div {
          margin-bottom: 4px;
        }
      }
    }
  }
}
</style>