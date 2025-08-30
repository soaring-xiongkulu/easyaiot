<template>
  <BasicModal
    @register="register"
    :title="getTitle"
    @cancel="handleCancel"
    :width="700"
    @ok="handleOk"
    :canFullscreen="false"
  >
    <div class="inference-modal">
      <Spin :spinning="state.editLoading">
        <Form
          :labelCol="{ span: 3 }"
          :model="validateInfos"
          :wrapperCol="{ span: 21 }"
          :disabled="state.isView"
        >
          <!-- 模型选择 -->
          <FormItem
            label="选择模型"
            name="model_id"
            v-bind="validateInfos.model_id"
          >
            <ApiSelect
              v-model:value="modelRef.model_id"
              :api="handleGetModelPage"
              result-field="items"
              label-field="name"
              value-field="id"
              :disabled="state.isView"
            >
            </ApiSelect>
          </FormItem>

          <!-- 推理类型 -->
          <FormItem
            label="推理类型"
            name="inference_type"
            v-bind="validateInfos.inference_type"
          >
            <Select
              v-model:value="modelRef.inference_type"
              placeholder="请选择"
              :disabled="state.isView"
            >
              <SelectOption value="image">图片推理</SelectOption>
              <SelectOption value="video">视频推理</SelectOption>
              <SelectOption value="rtsp">实时流推理</SelectOption>
            </Select>
          </FormItem>

          <!-- 输入源 (图片/视频) -->
          <FormItem
            v-if="modelRef.inference_type !== 'rtsp'"
            label="输入源"
            name="input_source"
            v-bind="validateInfos.input_source"
          >
            <Upload
              name="file"
              :action="state.uploadUrl"
              :headers="headers"
              :showUploadList="true"
              :accept="modelRef.inference_type === 'image' ? 'image/*' : 'video/*'"
              :max-count="1"
              :disabled="state.isView"
              @change="handleFileUpload"
            >
              <a-button type="primary">点击上传</a-button>
            </Upload>
            <div v-if="modelRef.input_source" style="margin-top: 8px">
              已上传文件: {{ modelRef.input_source }}
            </div>
          </FormItem>

          <!-- RTSP地址 -->
          <FormItem
            v-if="modelRef.inference_type === 'rtsp'"
            label="RTSP地址"
            name="rtsp_url"
            v-bind="validateInfos.rtsp_url"
          >
            <Input
              v-model:value="modelRef.rtsp_url"
              :disabled="state.isView"
            />
          </FormItem>
        </Form>
      </Spin>
    </div>
  </BasicModal>
</template>

<script lang="ts" setup>
import { computed, reactive, ref } from 'vue';
import { BasicModal, useModalInner } from '@/components/Modal';
import { Form, FormItem, Input, Select, SelectOption, Spin, Upload } from 'ant-design-vue';
import ApiSelect from '@/components/Form/src/components/ApiSelect.vue';
import { useMessage } from '@/hooks/web/useMessage';
import { getModelPage } from "@/api/device/model";
import { createInferenceTask, updateInferenceTask } from "@/api/device/inference";
import { useUserStoreWithOut } from "@/store/modules/user";
import { useGlobSetting } from "@/hooks/setting";

const { createMessage } = useMessage();

// 获取用户token和全局设置
const userStore = useUserStoreWithOut();
const token = userStore.getAccessToken;
const headers = ref({ 'Authorization': `Bearer ${token}` });
const { uploadUrl } = useGlobSetting();

// 定义状态管理
const state = reactive({
  editLoading: false,
  isEdit: false,
  isView: false,
  record: null,
  uploadUrl: `${uploadUrl}/inference/upload`, // 推理任务上传接口
});

// 表单数据模型
const modelRef = reactive({
  id: null,
  model_id: null,
  inference_type: 'image',
  input_source: '',
  rtsp_url: '',
});

// 计算标题
const getTitle = computed(() =>
  state.isEdit ? '编辑推理任务' : state.isView ? '查看推理任务' : '新增推理任务'
);

// 表单验证规则
const rulesRef = reactive({
  model_id: [
    { required: true, message: '请选择模型', trigger: ['blur', 'change'] }
  ],
  inference_type: [
    { required: true, message: '请选择推理类型', trigger: ['blur', 'change'] }
  ],
  input_source: [
    {
      required: true,
      message: '请上传文件',
      trigger: 'change',
      validator: (_, value) => {
        if (modelRef.inference_type !== 'rtsp' && !value) {
          return Promise.reject('请上传文件');
        }
        return Promise.resolve();
      }
    }
  ],
  rtsp_url: [
    {
      required: true,
      message: '请输入RTSP地址',
      trigger: 'blur',
      validator: (_, value) => {
        if (modelRef.inference_type === 'rtsp' && !value) {
          return Promise.reject('请输入RTSP地址');
        }
        if (modelRef.inference_type === 'rtsp' && !/^rtsp:\/\/\w+(\.\w+)+:\d+\/\w+/.test(value)) {
          return Promise.reject('请输入有效的RTSP地址格式（如：rtsp://example.com:554/stream）');
        }
        return Promise.resolve();
      }
    }
  ]
});

// 表单验证
const useForm = Form.useForm;
const { validate, resetFields, validateInfos } = useForm(modelRef, rulesRef);

// 模态框注册
const [register, { closeModal }] = useModalInner((data) => {
  const { isEdit, isView, record } = data;
  state.isEdit = isEdit;
  state.isView = isView;

  if (state.isEdit || state.isView) {
    state.editLoading = true;
    Object.keys(modelRef).forEach(key => {
      modelRef[key] = record[key] ?? '';
    });
    state.record = record;
    state.editLoading = false;
  } else {
    resetFields();
    modelRef.inference_type = 'image';
  }
});

const emits = defineEmits(['success']);

// 取消操作
function handleCancel() {
  resetFields();
  closeModal();
}

// 处理文件上传事件
function handleFileUpload(info) {
  if (info.file.status === 'done') {
    const response = info.file.response;
    if (response && response.code === 0) {
      modelRef.input_source = response.data.path; // 存储文件路径
      createMessage.success('文件上传成功');
    } else {
      createMessage.error(response?.msg || '文件上传失败');
    }
  } else if (info.file.status === 'error') {
    createMessage.error('文件上传失败');
  }
}

// 确定操作
function handleOk() {
  validate().then(async () => {
    try {
      state.editLoading = true;
      const api = modelRef.id ? updateInferenceTask : createInferenceTask;
      const payload = {
        id: modelRef.id,
        model_id: modelRef.model_id,
        inference_type: modelRef.inference_type,
        input_source: modelRef.input_source,
        rtsp_url: modelRef.rtsp_url
      };

      const res = await api(payload);
      if (res.code === 0) {
        createMessage.success('操作成功');
        closeModal();
        resetFields();
        emits('success');
      } else {
        createMessage.error(res.msg || '操作失败');
      }
    } catch (error) {
      console.error(error);
      createMessage.error('操作失败');
    } finally {
      state.editLoading = false;
    }
  }).catch(err => {
    createMessage.error('请检查表单');
    console.error('表单验证失败:', err);
  });
}

const handleGetModelPage = async (params?: any) => {
  try {
    const response = await getModelPage(params);
    if (response.code === 0) {
      return {
        items: response.data,
        total: response.total
      };
    } else {
      console.error('获取模型列表失败:', response.msg);
      createMessage.error('获取模型列表失败');
      return {
        items: [],
        total: 0
      };
    }
  } catch (error) {
    console.error('获取模型列表异常:', error);
    createMessage.error('获取模型列表异常');
    return {
      items: [],
      total: 0
    };
  }
};
</script>

<style lang="less" scoped>
.inference-modal {
  :deep(.ant-form-item-label) {
    & > label::after {
      content: '';
    }
  }
}
</style>
