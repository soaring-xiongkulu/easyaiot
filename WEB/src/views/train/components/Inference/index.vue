<template>
  <div class="inference-container">
    <a-page-header
      title="模型推理"
      sub-title="选择项目并执行推理任务"
      @back="() => $router.go(-1)"
    />

    <a-card class="inference-card">
      <a-form
        :model="formState"
        :label-col="{ span: 4 }"
        :wrapper-col="{ span: 20 }"
        @finish="handleSubmit"
      >
        <!-- 项目选择 -->
        <a-form-item label="选择项目" required>
          <a-select
            v-model:value="formState.projectId"
            placeholder="请选择项目"
            @change="handleProjectChange"
          >
            <a-select-option
              v-for="project in projects"
              :key="project.id"
              :value="project.id"
            >
              {{ project.name }}
            </a-select-option>
          </a-select>
        </a-form-item>

        <!-- 模型类型选择 -->
        <a-form-item label="模型类型" required>
          <a-radio-group v-model:value="formState.modelType">
            <a-radio-button value="pretrained">预训练模型</a-radio-button>
            <a-radio-button value="custom">自定义模型</a-radio-button>
          </a-radio-group>
        </a-form-item>

        <!-- 预训练模型选择 -->
        <a-form-item
          v-if="formState.modelType === 'pretrained'"
          label="选择模型"
          required
        >
          <a-select v-model:value="formState.systemModel" placeholder="请选择预训练模型">
            <a-select-option value="yolov5">YOLOv5</a-select-option>
            <a-select-option value="resnet50">ResNet50</a-select-option>
            <a-select-option value="efficientnet">EfficientNet</a-select-option>
          </a-select>
        </a-form-item>

        <!-- 自定义模型上传 -->
        <a-form-item
          v-if="formState.modelType === 'custom'"
          label="模型文件"
          required
        >
          <a-upload
            v-model:file-list="modelFiles"
            name="model_file"
            :max-count="1"
            :before-upload="() => false"
          >
            <a-button>
              <upload-outlined />
              上传模型文件
            </a-button>
          </a-upload>
        </a-form-item>

        <!-- 推理类型选择 -->
        <a-form-item label="推理类型" required>
          <a-radio-group v-model:value="formState.inferenceType">
            <a-radio-button value="image">图片推理</a-radio-button>
            <a-radio-button value="video">视频推理</a-radio-button>
          </a-radio-group>
        </a-form-item>

        <!-- 图片推理输入 -->
        <a-form-item
          v-if="formState.inferenceType === 'image'"
          label="上传图片"
          required
        >
          <a-upload
            v-model:file-list="imageFiles"
            name="image_file"
            list-type="picture-card"
            :max-count="1"
            :before-upload="() => false"
            @preview="handlePreview"
          >
            <div v-if="imageFiles.length < 1">
              <plus-outlined />
              <div style="margin-top: 8px">上传图片</div>
            </div>
          </a-upload>
          <a-modal :visible="previewVisible" :footer="null" @cancel="previewVisible = false">
            <img alt="预览" style="width: 100%" :src="previewImage" />
          </a-modal>
        </a-form-item>

        <!-- 视频推理输入 -->
        <a-form-item
          v-if="formState.inferenceType === 'video'"
          label="上传视频"
          required
        >
          <a-upload
            v-model:file-list="videoFiles"
            name="video_file"
            :max-count="1"
            :before-upload="() => false"
          >
            <a-button>
              <upload-outlined />
              上传视频文件
            </a-button>
          </a-upload>
        </a-form-item>

        <!-- 执行按钮 -->
        <a-form-item :wrapper-col="{ offset: 4, span: 16 }">
          <a-button
            type="primary"
            html-type="submit"
            :loading="loading"
            :disabled="!formState.projectId"
          >
            执行推理
          </a-button>
        </a-form-item>
      </a-form>
    </a-card>

    <!-- 推理结果展示 -->
    <a-card v-if="result" title="推理结果" class="result-card">
      <a-tabs v-model:activeKey="activeTab">
        <a-tab-pane key="text" tab="文本结果">
          <div class="result-content">
            <pre>{{ result.text }}</pre>
          </div>
        </a-tab-pane>
        <a-tab-pane key="image" tab="可视化结果" v-if="result.image">
          <div class="result-content">
            <img :src="result.image" alt="推理结果" style="max-width: 100%" />
          </div>
        </a-tab-pane>
        <a-tab-pane key="video" tab="视频结果" v-if="result.video">
          <div class="result-content">
            <video controls :src="result.video" style="max-width: 100%"></video>
          </div>
        </a-tab-pane>
      </a-tabs>
    </a-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue';
import { UploadOutlined, PlusOutlined } from '@ant-design/icons-vue';
import { message } from 'ant-design-vue';
import { getModelPage } from '@/api/device/model';
import { runInference } from '@/api/device/model';

// 响应式状态
const projects = ref([]);
const loading = ref(false);
const result = ref(null);
const activeTab = ref('text');
const previewVisible = ref(false);
const previewImage = ref('');

// 文件列表
const modelFiles = ref([]);
const imageFiles = ref([]);
const videoFiles = ref([]);

// 表单状态
const formState = reactive({
  projectId: null,
  modelType: 'pretrained',
  systemModel: 'yolov5',
  inferenceType: 'image'
});

// 加载项目列表
const fetchProjects = async () => {
  try {
    const response = await getModelPage();
    projects.value = response.data;
    if (projects.value.length > 0) {
      formState.projectId = projects.value[0].id;
    }
  } catch (error) {
    message.error('加载项目列表失败');
    console.error(error);
  }
};

// 图片预览处理
const handlePreview = async file => {
  if (!file.url && !file.preview) {
    file.preview = await getBase64(file.originFileObj);
  }
  previewImage.value = file.url || file.preview;
  previewVisible.value = true;
};

const getBase64 = file => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.readAsDataURL(file);
    reader.onload = () => resolve(reader.result);
    reader.onerror = error => reject(error);
  });
};

// 项目变更处理
const handleProjectChange = projectId => {
  console.log('项目已变更:', projectId);
  // 可以在这里加载项目相关模型配置
};

// 表单提交
const handleSubmit = async () => {
  if (!formState.projectId) {
    message.warning('请选择项目');
    return;
  }

  const formData = new FormData();

  // 添加表单数据
  formData.append('model_type', formState.modelType);
  formData.append('inference_type', formState.inferenceType);
  formData.append('system_model', formState.systemModel);

  // 添加文件
  if (formState.modelType === 'custom' && modelFiles.value.length > 0) {
    formData.append('model_file', modelFiles.value[0].originFileObj);
  }

  if (formState.inferenceType === 'image' && imageFiles.value.length > 0) {
    formData.append('image_file', imageFiles.value[0].originFileObj);
  }

  if (formState.inferenceType === 'video' && videoFiles.value.length > 0) {
    formData.append('video_file', videoFiles.value[0].originFileObj);
  }

  loading.value = true;

  try {
    const response = await runInference(formState.projectId, formData);
    result.value = response.data;
    message.success('推理执行成功');
  } catch (error) {
    message.error('推理执行失败');
    console.error(error);
  } finally {
    loading.value = false;
  }
};

// 初始化加载项目
onMounted(() => {
  fetchProjects();
});
</script>

<style scoped>
.inference-container {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.inference-card {
  margin-top: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.result-card {
  margin-top: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.result-content {
  padding: 20px;
  background-color: #f9f9f9;
  border-radius: 4px;
  min-height: 300px;
  max-height: 600px;
  overflow: auto;
}

pre {
  white-space: pre-wrap;
  word-wrap: break-word;
}
</style>
