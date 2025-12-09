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
          :model="modelRef"
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
            </Select>
          </FormItem>

          <!-- 输入源 (图片/视频) -->
          <FormItem
            label="输入源"
            name="input_source"
            v-bind="validateInfos.input_source"
          >
            <Upload
              name="file"
              :action="state.uploadUrl"
              :headers="headers"
              :showUploadList="true"
              :accept="uploadAccept"
              :max-count="1"
              :disabled="state.isView"
              @change="handleFileUpload"
            >
              <a-button type="primary">点击上传</a-button>
            </Upload>
            <div v-if="modelRef.input_source" style="margin-top: 8px">
              已上传文件: {{ fileName }}
            </div>
          </FormItem>
        </Form>
      </Spin>
    </div>
  </BasicModal>
</template>

<script lang="ts" setup>
import {computed, reactive, ref} from 'vue';
import {BasicModal, useModalInner} from '@/components/Modal';
import {Form, FormItem, Input, Select, SelectOption, Spin, Upload} from 'ant-design-vue';
import ApiSelect from '@/components/Form/src/components/ApiSelect.vue';
import {useMessage} from '@/hooks/web/useMessage';
import {createInferenceTask, getModelPage, updateInferenceTask} from "@/api/device/model";
import {useUserStoreWithOut} from "@/store/modules/user";
import {useGlobSetting} from "@/hooks/setting";

// 定义类型
interface InferenceModel {
  id?: number | null;
  model_id: number | string | null; // 修改为支持字符串类型
  inference_type: 'image' | 'video';
  input_source: string;
}

const {createMessage} = useMessage();

// 获取用户token和全局设置
const userStore = useUserStoreWithOut();
const token = userStore.getAccessToken;
const headers = ref({Authorization: `Bearer ${token}`});
const {uploadUrl} = useGlobSetting();

// 定义状态管理
const state = reactive({
  editLoading: false,
  isEdit: false,
  isView: false,
  record: null as InferenceModel | null,
  uploadUrl: `${uploadUrl}/model/inference/upload_input`,
});

// 表单数据模型
const modelRef = reactive<InferenceModel>({
  model_id: 'default',
  inference_type: 'image',
  input_source: '',
});

// 计算上传文件接受类型
const uploadAccept = computed(() => {
  return modelRef.inference_type === 'image'
    ? 'image/*'
    : 'video/*';
});

// 提取文件名
const fileName = computed(() => {
  return modelRef.input_source.split('/').pop() || modelRef.input_source;
});

// 计算标题
const getTitle = computed(() =>
  state.isEdit ? '编辑推理任务' : state.isView ? '查看推理任务' : '新增推理任务'
);

// 表单验证规则
const rulesRef = reactive({
  model_id: [
    {
      required: true,
      message: '请选择模型',
      trigger: ['blur', 'change'],
      validator: () => {
        if (!modelRef.model_id) {
          return Promise.reject('请选择模型');
        }
        return Promise.resolve();
      }
    }
  ],
  inference_type: [
    {required: true, message: '请选择推理类型', trigger: ['blur', 'change']}
  ]
});

// 表单验证
const useForm = Form.useForm;
const {validate, resetFields, validateInfos} = useForm(modelRef, rulesRef);

// 模态框注册
const [register, {closeModal}] = useModalInner((data: any) => {
  const {isEdit, isView, record} = data;
  state.isEdit = isEdit;
  state.isView = isView;

  if (state.isEdit || state.isView) {
    state.editLoading = true;
    Object.assign(modelRef, record);
    state.record = record;
    state.editLoading = false;
  } else {
    resetFields();
    modelRef.inference_type = 'image';
    modelRef.model_id = null; // 重置模型选择
  }
});

// 取消操作
function handleCancel() {
  resetFields();
  closeModal();
}

// 处理文件上传事件
function handleFileUpload(info: any) {
  if (info.file.status === 'done') {
    const response = info.file.response;
    if (response && response.code === 0) {
      modelRef.input_source = response.data.url;
      createMessage.success('文件上传成功');
    } else {
      createMessage.error(response?.msg || '文件上传失败');
    }
  } else if (info.file.status === 'error') {
    createMessage.error('文件上传失败');
  }
}

// 确定操作
async function handleOk() {
  try {
    await validate();
    state.editLoading = true;

    const payload: Partial<InferenceModel> = {
      model_id: modelRef.model_id === 'default' ? null : modelRef.model_id,
      inference_type: modelRef.inference_type,
      input_source: modelRef.input_source,
    };

    // 根据是否编辑调用不同API
    const api = state.isEdit && modelRef.id
      ? updateInferenceTask
      : createInferenceTask;

    // 编辑时需要传递ID
    if (state.isEdit && modelRef.id) {
      payload.id = modelRef.id;
    }

    const res = await api(payload);
    if (res.code === 0) {
      createMessage.success(state.isEdit ? '更新成功' : '创建成功');
      closeModal();
      resetFields();
    } else {
      createMessage.error(res.msg || '操作失败');
    }
  } catch (error) {
    console.error('表单验证或操作失败:', error);
    createMessage.error('请检查表单');
  } finally {
    state.editLoading = false;
  }
}

// 获取模型列表
async function handleGetModelPage(params?: any) {
  try {
    const response = await getModelPage(params);
    const items = response.code === 0 ? response.data : [];
    // 插入默认模型选项（唯一标识为 'default'）
    items.unshift({
      id: 'default',
      name: '默认模型 (yolov8n.pt)'
    });
    return { items, total: response['total']};
  } catch (error) {
    console.error('获取模型列表异常:', error);
    createMessage.error('获取模型列表异常');
    return {
      items: [],
      total: 0
    };
  }
}
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
