<template>
  <BasicModal
    v-bind="$attrs"
    @register="register"
    :title="getTitle"
    :width="1400"
    @ok="handleSubmit"
    :confirmLoading="loading"
  >
    <div class="vision-inference-modal">
      <div class="modal-layout">
        <!-- 左侧：输入区域 -->
        <div class="left-section">
          <!-- 图片上传区域 -->
          <div class="upload-section">
            <div class="section-title">图片上传</div>
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
            <div class="section-title">提示词</div>
            <Textarea
              v-model:value="prompt"
              :placeholder="getPromptPlaceholder"
              :rows="6"
              :maxlength="1000"
              show-count
            />
          </div>

          <!-- 推理模式选择 -->
          <div class="mode-section">
            <div class="section-title">推理模式</div>
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
          </div>
        </div>

        <!-- 右侧：检测结果区域 -->
        <div class="right-section">
          <div class="result-wrapper">
            <div class="result-title">
              <span>检测结果</span>
            </div>
            <div class="result-content">
              <Spin :spinning="loading">
                <div v-if="result" class="llm-text-result">
                  <div class="llm-result-content" v-html="formattedResult"></div>
                </div>
                <div v-else class="result-placeholder">
                  <ExperimentOutlined class="icon" />
                  <span>检测结果将显示在这里</span>
                </div>
              </Spin>
            </div>
          </div>
        </div>
      </div>
    </div>
  </BasicModal>
</template>

<script lang="ts" setup>
import { ref, computed } from 'vue';
import { BasicModal, useModalInner } from '@/components/Modal';
import { useMessage } from '@/hooks/web/useMessage';
import { PlusOutlined, ExperimentOutlined } from '@ant-design/icons-vue';
import { Upload, Modal, FormItem, Textarea, RadioGroup, Radio, Spin } from 'ant-design-vue';
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

// 格式化结果，将markdown格式转换为HTML
const formattedResult = computed(() => {
  if (!result.value) return '';
  
  let text = result.value;
  
  // 先转义HTML特殊字符（但保留我们需要的标记）
  text = text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');
  
  // 处理分隔线（必须在其他处理之前）
  text = text.replace(/^---$/gm, '<div class="result-divider"></div>');
  
  // 处理标题（按从大到小的顺序）
  text = text.replace(/^####\s+(.+)$/gm, '<h4 class="result-h4">$1</h4>');
  text = text.replace(/^###\s+(.+)$/gm, '<h3 class="result-h3">$1</h3>');
  text = text.replace(/^##\s+(.+)$/gm, '<h2 class="result-h2">$1</h2>');
  text = text.replace(/^#\s+(.+)$/gm, '<h1 class="result-h1">$1</h1>');
  
  // 处理引用块
  text = text.replace(/^>\s+(.+)$/gm, '<div class="result-quote">$1</div>');
  
  // 处理有序列表（数字开头）
  text = text.replace(/^(\d+)\.\s+(.+)$/gm, '<div class="result-list-item"><span class="list-number">$1.</span><span class="list-content">$2</span></div>');
  
  // 处理无序列表（- 或 * 开头）
  text = text.replace(/^[-*]\s+(.+)$/gm, '<div class="result-list-item"><span class="list-bullet">•</span><span class="list-content">$1</span></div>');
  
  // 处理嵌套列表（以空格开头的列表项）
  text = text.replace(/^(\s{2,})[-*]\s+(.+)$/gm, '<div class="result-list-item nested"><span class="list-bullet">◦</span><span class="list-content">$2</span></div>');
  
  // 处理粗体（**text**）
  text = text.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
  
  // 处理行内代码（`code`）
  text = text.replace(/`([^`]+)`/g, '<code>$1</code>');
  
  // 按段落分割并处理
  const lines = text.split('\n');
  const paragraphs: string[] = [];
  let currentParagraph: string[] = [];
  
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i].trim();
    
    // 如果是空行，结束当前段落
    if (!line) {
      if (currentParagraph.length > 0) {
        const paraText = currentParagraph.join(' ');
        // 如果段落不是HTML标签开头，包装成p标签
        if (!paraText.match(/^<[h|d|q|l]/)) {
          paragraphs.push(`<p class="result-paragraph">${paraText}</p>`);
        } else {
          paragraphs.push(paraText);
        }
        currentParagraph = [];
      }
      continue;
    }
    
    // 如果是HTML标签（标题、分隔线、引用、列表），直接添加
    if (line.match(/^<[h|d|q|l]/)) {
      if (currentParagraph.length > 0) {
        const paraText = currentParagraph.join(' ');
        if (!paraText.match(/^<[h|d|q|l]/)) {
          paragraphs.push(`<p class="result-paragraph">${paraText}</p>`);
        } else {
          paragraphs.push(paraText);
        }
        currentParagraph = [];
      }
      paragraphs.push(line);
    } else {
      // 普通文本，添加到当前段落
      currentParagraph.push(line);
    }
  }
  
  // 处理最后一个段落
  if (currentParagraph.length > 0) {
    const paraText = currentParagraph.join(' ');
    if (!paraText.match(/^<[h|d|q|l]/)) {
      paragraphs.push(`<p class="result-paragraph">${paraText}</p>`);
    } else {
      paragraphs.push(paraText);
    }
  }
  
  return paragraphs.join('\n');
});

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
      // 从返回数据中提取推理结果
      // 支持多种数据格式：response.data.response 或 response.data.data.response
      const responseData = response.data?.response || 
                          response.data?.data?.response || 
                          (typeof response.data === 'string' ? response.data : '');
      result.value = responseData || '未返回推理结果';
      createMessage.success(response.msg || '推理成功！');
    } else {
      createMessage.error(response.msg || '推理失败');
      result.value = '';
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
  height: 70vh;
  min-height: 600px;

  .modal-layout {
    display: flex;
    gap: 16px;
    height: 100%;

    .left-section {
      flex: 0 0 400px;
      display: flex;
      flex-direction: column;
      gap: 20px;
      padding-right: 16px;
      border-right: 1px solid #e8e8e8;
      overflow-y: auto;

      .section-title {
        font-size: 16px;
        font-weight: 600;
        color: #333;
        margin-bottom: 12px;
        padding-bottom: 8px;
        border-bottom: 2px solid #1890ff;
      }

      .upload-section {
        .section-title {
          margin-bottom: 16px;
        }
      }

      .prompt-section {
        .section-title {
          margin-bottom: 12px;
        }
      }

      .mode-section {
        .section-title {
          margin-bottom: 12px;
        }

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
    }

    .right-section {
      flex: 1;
      display: flex;
      flex-direction: column;
      min-width: 0;

      .result-wrapper {
        display: flex;
        flex-direction: column;
        height: 100%;
        background: #ffffff;
        border: 1px solid #e8e8e8;
        border-radius: 4px;
        overflow: hidden;

        .result-title {
          padding: 16px 20px;
          background: linear-gradient(135deg, #1890ff 0%, #096dd9 100%);
          color: #ffffff;
          font-size: 16px;
          font-weight: 600;
          border-bottom: 2px solid #1890ff;
          box-shadow: 0 2px 4px rgba(24, 144, 255, 0.1);

          span {
            display: flex;
            align-items: center;
            gap: 8px;

            &::before {
              content: '';
              display: inline-block;
              width: 4px;
              height: 16px;
              background: #ffffff;
              border-radius: 2px;
            }
          }
        }

        .result-content {
          flex: 1;
          overflow-y: auto;
          padding: 0;

          .llm-text-result {
            width: 100%;
            height: 100%;
            padding: 24px;
            display: flex;
            flex-direction: column;
            background: #ffffff;
            box-sizing: border-box;

            .llm-result-content {
              flex: 1;
              font-size: 14px;
              line-height: 1.8;
              color: #333;
              word-wrap: break-word;
              overflow-y: auto;

              // 标题样式
              .result-h1 {
                font-size: 20px;
                font-weight: 700;
                color: #1890ff;
                margin: 20px 0 16px 0;
                padding-bottom: 12px;
                border-bottom: 2px solid #e8e8e8;
              }

              .result-h2 {
                font-size: 18px;
                font-weight: 600;
                color: #1890ff;
                margin: 18px 0 14px 0;
                padding-bottom: 10px;
                border-bottom: 1px solid #f0f0f0;
              }

              .result-h3 {
                font-size: 16px;
                font-weight: 600;
                color: #333;
                margin: 16px 0 12px 0;
              }

              .result-h4 {
                font-size: 15px;
                font-weight: 600;
                color: #666;
                margin: 14px 0 10px 0;
              }

              // 段落样式
              .result-paragraph {
                margin: 12px 0;
                line-height: 1.8;
                color: #333;
                text-align: justify;
              }

              // 列表样式
              .result-list-item {
                display: flex;
                margin: 8px 0;
                padding-left: 8px;
                line-height: 1.8;

                &.nested {
                  padding-left: 24px;
                  margin: 4px 0;
                }

                .list-number {
                  font-weight: 600;
                  color: #1890ff;
                  margin-right: 8px;
                  min-width: 24px;
                }

                .list-bullet {
                  color: #1890ff;
                  margin-right: 8px;
                  font-weight: bold;
                }

                .list-content {
                  flex: 1;
                  color: #333;
                }
              }

              // 分隔线样式
              .result-divider {
                height: 1px;
                background: linear-gradient(to right, transparent, #e8e8e8, transparent);
                margin: 20px 0;
              }

              // 引用样式
              .result-quote {
                margin: 12px 0;
                padding: 12px 16px;
                background: #f5f5f5;
                border-left: 4px solid #1890ff;
                border-radius: 4px;
                color: #666;
                font-style: italic;
                line-height: 1.8;
              }

              // 粗体样式
              strong {
                color: #1890ff;
                font-weight: 600;
              }

              // 代码块样式（如果有）
              code {
                background: #f5f5f5;
                padding: 2px 6px;
                border-radius: 3px;
                font-family: 'Courier New', monospace;
                font-size: 13px;
                color: #e83e8c;
              }
            }
          }

          .result-placeholder {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            height: 100%;
            color: #999;
            font-size: 14px;

            .icon {
              font-size: 48px;
              margin-bottom: 16px;
              color: #d9d9d9;
            }
          }
        }
      }
    }
  }
}
</style>
