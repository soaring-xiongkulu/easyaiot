<template>
  <BasicModal
    @register="register"
    :title="getTitle"
    @cancel="handleCancel"
    :width="700"
    @ok="handleOk"
    :canFullscreen="false"
  >
    <div class="model-modal">
      <Spin :spinning="state.editLoading">
        <Form
          :labelCol="{ span: 4 }"
          :model="validateInfos"
          :wrapperCol="{ span: 20 }"
          :disabled="state.isView"
        >
          <FormItem label="模型名称" name="name" v-bind="validateInfos.name">
            <Input v-model:value="modelRef.name" placeholder="请输入模型名称" />
          </FormItem>
          <FormItem label="模型版本" name="version" v-bind="validateInfos.version">
            <Input
              v-model:value="modelRef.version"
              placeholder="请输入模型版本（例如：1.0.0）"
            />
          </FormItem>
          <FormItem label="模型描述" name="description" v-bind="validateInfos.description">
            <TextArea v-model:value="modelRef.description" placeholder="请输入模型描述" :rows="4" />
          </FormItem>
          <FormItem label="状态" name="status" v-bind="validateInfos.status">
            <Select
              v-model:value="modelRef.status"
              placeholder="请选择状态"
              :options="state.statusOptions"
              :disabled="state.isView"
            />
          </FormItem>

          <!-- 模型图片上传 -->
          <FormItem label="模型图片" name="imageUrl" v-bind="validateInfos.imageUrl">
            <Upload
              name="file"
              :action="state.imageUploadUrl"
              :headers="headers"
              :showUploadList="false"
              accept=".jpg,.jpeg,.png"
              :disabled="state.isView"
              @change="handleImageUpload"
            >
              <a-button type="primary" :disabled="state.isView">
                {{ state.isView ? '已上传' : '上传模型图片' }}
              </a-button>
            </Upload>
            <div v-if="modelRef.imageUrl" style="margin-top: 8px">
              <img
                :src="modelRef.imageUrl"
                alt="模型图片预览"
                style="max-height: 200px; max-width: 100%;"
              />
            </div>
          </FormItem>

          <!-- 模型文件上传 -->
          <FormItem label="模型文件" name="filePath">
            <Upload
              name="file"
              :action="state.modelUploadUrl"
              :headers="headers"
              :showUploadList="true"
              accept=".pt,.pth,.h5,.onnx"
              :disabled="state.isView"
              @change="handleFileUpload"
            >
              <a-button type="primary" :disabled="state.isView">
                {{ state.isView ? '已上传' : '上传模型文件' }}
              </a-button>
            </Upload>
            <div v-if="modelRef.filePath" style="margin-top: 8px">
              已上传文件: {{ modelRef.filePath }}
            </div>
          </FormItem>
        </Form>
      </Spin>
    </div>
  </BasicModal>
</template>

<script lang="ts" setup>
import { computed, reactive, ref } from 'vue';
import { BasicModal, useModalInner } from '@/components/Modal';
import { Form, FormItem, Input, Select, Spin, Upload } from 'ant-design-vue';
import { useMessage } from '@/hooks/web/useMessage';
import { useUserStoreWithOut } from "@/store/modules/user";
import { useGlobSetting } from "@/hooks/setting";
import { createModel, updateModel } from "@/api/device/model";

const { createMessage } = useMessage();
const TextArea = Input.TextArea;

const userStore = useUserStoreWithOut();
const token = userStore.getAccessToken;
const headers = ref({ 'Authorization': `Bearer ${token}` });
const { uploadUrl } = useGlobSetting();

const state = reactive({
  modelUploadUrl: `${uploadUrl}/model/upload`, // 模型文件上传接口
  imageUploadUrl: `${uploadUrl}/model/image_upload`, // 模型图片上传接口
  isEdit: false,
  isView: false,
  editLoading: false,
  statusOptions: [
    { value: 0, label: '未部署' },
    { value: 1, label: '已部署' },
    { value: 2, label: '训练中' },
    { value: 3, label: '已下线' },
  ],
});

const modelRef = reactive({
  id: null,
  name: '',
  version: '',
  description: '',
  status: 0,
  filePath: '', // 存储Minio返回的objectKey
  imageUrl: '', // 存储模型图片URL
});

const getTitle = computed(() => (state.isEdit ? '编辑模型' : state.isView ? '查看模型' : '新增模型'));

const [register, { closeModal }] = useModalInner((data) => {
  const { isEdit, isView, record } = data;
  state.isEdit = isEdit;
  state.isView = isView;

  if (state.isEdit || state.isView) {
    modelEdit(record);
  } else {
    resetFields();
  }
});

const emits = defineEmits(['success']);

// 表单验证规则
const rulesRef = reactive({
  name: [{ required: true, message: '请输入模型名称', trigger: ['blur', 'change'] }],
  version: [{ required: true, message: '请输入模型版本', trigger: ['blur', 'change'] }],
  status: [{ required: true, message: '请选择状态', trigger: ['blur', 'change'] }],
  imageUrl: [{ required: true, message: '请上传模型图片', trigger: 'change' }]
});

const useForm = Form.useForm;
const { validate, resetFields, validateInfos } = useForm(modelRef, rulesRef);

async function modelEdit(record) {
  try {
    state.editLoading = true;
    Object.assign(modelRef, record);
    state.editLoading = false;
  } catch (error) {
    console.error(error);
    createMessage.error('加载模型信息失败');
  }
}

function handleCancel() {
  resetFields();
  closeModal();
}

// 处理模型文件上传事件
function handleFileUpload(info) {
  if (info.file.status === 'done') {
    const response = info.file.response;
    if (response && response.code === 200) {
      modelRef.filePath = response.data.objectKey; // 存储Minio返回的objectKey
      createMessage.success('模型文件上传成功');
    } else {
      createMessage.error(response?.msg || '文件上传失败');
    }
  } else if (info.file.status === 'error') {
    createMessage.error('文件上传失败');
  }
}

// 处理模型图片上传事件
function handleImageUpload(info) {
  if (info.file.status === 'done') {
    const response = info.file.response;
    console.log('response', JSON.stringify(response));
    if (response && response.code === 0) {
      modelRef.imageUrl = response.data.url;
      createMessage.success('模型图片上传成功');
    } else {
      createMessage.error(response?.msg || '图片上传失败');
    }
  } else if (info.file.status === 'error') {
    createMessage.error('图片上传失败');
  }
}

function handleOk() {
  validate().then(async () => {
    state.editLoading = true;
    const api = modelRef.id ? updateModel : createModel;

    try {
      // 只提交必要字段
      const payload = {
        id: modelRef.id,
        name: modelRef.name,
        version: modelRef.version,
        description: modelRef.description,
        status: modelRef.status,
        filePath: modelRef.filePath, // 包含Minio objectKey
        imageUrl: modelRef.imageUrl  // 包含图片URL
      };

      await api(payload);
      createMessage.success('操作成功');
      closeModal();
      resetFields();
      emits('success');
    } catch (error) {
      console.error(error);
      createMessage.error('操作失败');
    } finally {
      state.editLoading = false;
    }
  }).catch((err) => {
    console.error(err);
    createMessage.error('表单验证失败，请检查输入');
  });
}
</script>

<style lang="less" scoped>
.model-modal {
  :deep(.ant-form-item-label) {
    & > label::after {
      content: '';
    }
  }
}
</style>
