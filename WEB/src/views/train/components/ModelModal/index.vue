<template>
  <BasicDrawer
    v-bind="$attrs"
    @register="register"
    :title="getTitle"
    width="1400"
    placement="right"
    :showFooter="true"
    :showCancelBtn="false"
    :showOkBtn="false"
    destroy-on-close
  >
    <template #footer>
      <div class="footer-buttons">
        <Button @click="handleCancel">{{ state.isView ? '关闭' : '取消' }}</Button>
        <Button v-if="!state.isView" type="primary" :loading="state.editLoading" @click="handleOk">
          保存
        </Button>
      </div>
    </template>

    <Spin :spinning="state.editLoading">
      <div class="model-drawer-content">
        <BasicForm @register="registerForm" />

        <Divider orientation="left">模型资源</Divider>
        <Form
          :label-col="{ style: { width: '150px' } }"
          :wrapper-col="{ span: 21 }"
          :disabled="state.isView"
          class="resource-form"
        >
          <FormItem label="模型图片" required>
            <Upload
              name="file"
              :action="state.imageUploadUrl"
              :headers="headers"
              :show-upload-list="false"
              accept=".jpg,.jpeg,.png"
              :disabled="state.isView"
              @change="handleImageUpload"
            >
              <Button type="primary" :disabled="state.isView">
                {{ state.isView ? '已上传' : '上传模型图片' }}
              </Button>
            </Upload>
            <div v-if="modelRef.imageUrl" class="preview-wrap">
              <img :src="resolveModelImageDisplayUrl(modelRef.imageUrl)" alt="模型图片" class="preview-image" />
            </div>
          </FormItem>

          <FormItem label="模型文件">
            <Upload
              name="file"
              :action="state.modelUploadUrl"
              :headers="headers"
              :show-upload-list="false"
              accept=".pt,.pth,.h5,.onnx,.rknn"
              :disabled="state.isView"
              @change="handleFileUpload"
            >
              <Button type="primary" :disabled="state.isView">
                {{ state.isView ? '已上传' : '上传模型文件' }}
              </Button>
            </Upload>
            <div v-if="modelRef.filePath" class="form-extra" :title="fileName">
              已上传：{{ fileName }}
            </div>
            <div class="form-hint">支持 .pt / .onnx / .rknn；继续训练需使用 .pt 权重，RK3588 硬件任务使用 .rknn</div>
          </FormItem>

          <FormItem label="检测类别">
            <div class="class-tags-panel">
              <div v-if="state.classNames.length > 0" class="class-tag-list">
                <Tag v-for="name in state.classNames" :key="name" color="blue">{{ name }}</Tag>
              </div>
              <div v-if="state.classNames.length > 0" class="form-hint">
                共 {{ state.classNames.length }} 个检测类别
              </div>
              <span v-else-if="state.modelFormat !== 'rknn'" class="form-hint">
                上传 .pt / .onnx 权重后将自动识别检测类别
              </span>
              <Input.TextArea
                v-if="state.modelFormat === 'rknn'"
                v-model:value="state.rknnClassNamesText"
                :rows="3"
                :disabled="state.isView"
                placeholder="RKNN 为编译后模型，无法自动读取类别；请每行填写一个类别，不填则使用运行时默认类别"
                @blur="syncRknnClassNames"
              />
            </div>
          </FormItem>
        </Form>
      </div>
    </Spin>
  </BasicDrawer>
</template>

<script lang="ts" setup>
import { computed, reactive, ref } from 'vue';
import { BasicDrawer, useDrawerInner } from '@/components/Drawer';
import { BasicForm, useForm } from '@/components/Form';
import { Form, FormItem, Input, Spin, Upload, Divider, Tag } from 'ant-design-vue';
import { useMessage } from '@/hooks/web/useMessage';
import { useUserStoreWithOut } from '@/store/modules/user';
import { useGlobSetting } from '@/hooks/setting';
import { createModel, updateModel, getModelClasses, parseModelClassPayload } from '@/api/device/model';
import { normalizeModelVersion } from '../../utils/modelVersionUtils';
import { resolveModelImageDisplayUrl } from '@/utils/alertMinioImage';
import { Button } from '@/components/Button';

defineOptions({ name: 'ModelDrawer' });

const { createMessage } = useMessage();

const userStore = useUserStoreWithOut();
const token = userStore.getAccessToken;
const headers = ref({ 'X-Authorization': `Bearer ${token}` });
const { uploadUrl } = useGlobSetting();

const state = reactive({
  modelUploadUrl: `${uploadUrl}/model/upload`,
  imageUploadUrl: `${uploadUrl}/model/image_upload`,
  isEdit: false,
  isView: false,
  editLoading: false,
  modelFormat: '',
  classNames: [] as string[],
  rknnClassNamesText: '',
});

const modelRef = reactive({
  id: null as number | null,
  filePath: '',
  imageUrl: '',
});

const getTitle = computed(() => (state.isEdit ? '编辑模型' : state.isView ? '查看模型' : '新增模型'));

const fileName = computed(() => {
  const path = modelRef.filePath || '';
  if (!path) return '';
  return path.split('/').pop()?.split('?')[0] || path;
});

const emits = defineEmits(['success', 'register']);

const [registerForm, { setFieldsValue, validate, resetFields, setProps }] = useForm({
  labelWidth: 150,
  baseColProps: { span: 24 },
  showActionButtonGroup: false,
  schemas: [
    {
      field: 'name',
      label: '模型名称',
      component: 'Input',
      required: true,
      componentProps: { placeholder: '请输入模型名称' },
    },
    {
      field: 'version',
      label: '模型版本',
      component: 'Input',
      required: true,
      defaultValue: '1.0.0',
      componentProps: { placeholder: '例如：1.0.0' },
    },
    {
      field: 'description',
      label: '模型描述',
      component: 'InputTextArea',
      componentProps: { placeholder: '请输入模型描述', rows: 4 },
    },
    {
      field: 'status',
      label: '状态',
      component: 'Select',
      required: true,
      componentProps: {
        placeholder: '请选择状态',
        options: [
          { value: 0, label: '未部署' },
          { value: 1, label: '已部署' },
          { value: 3, label: '已下线' },
        ],
      },
    },
  ],
});

const [register, { closeDrawer }] = useDrawerInner((data) => {
  const { isEdit, isView, record } = data || {};
  state.isEdit = !!isEdit;
  state.isView = !!isView;

  setProps({ disabled: state.isView });

  if (state.isEdit || state.isView) {
    modelEdit(record);
  } else {
    resetFormState();
  }
});

function resetFormState() {
  resetFields();
  modelRef.id = null;
  modelRef.filePath = '';
  modelRef.imageUrl = '';
  state.modelFormat = '';
  state.classNames = [];
  state.rknnClassNamesText = '';
}

function parseClassNamesText(value: string): string[] {
  return String(value || '')
    .split(/[\n,，]+/)
    .map((name) => name.trim())
    .filter(Boolean);
}

function applyClassNames(classNames: string[]) {
  state.classNames = Array.isArray(classNames) ? [...classNames] : [];
  state.rknnClassNamesText = state.classNames.join('\n');
}

function syncRknnClassNames() {
  applyClassNames(parseClassNamesText(state.rknnClassNamesText));
}

function detectModelFormat(record: any): string {
  const path = String(
    record?.filePath ?? record?.model_path ?? record?.onnx_model_path ?? record?.rknn_model_path ?? '',
  ).toLowerCase();
  if (path.includes('.rknn')) return 'rknn';
  if (path.includes('.onnx')) return 'onnx';
  if (path) return 'pt';
  return '';
}

async function loadClassNamesForRecord(record: any) {
  const fromRecord = parseModelClassPayload(record);
  if (fromRecord.classNames.length > 0) {
    applyClassNames(fromRecord.classNames);
    return;
  }
  // RKNN 是编译产物，接口无法反解类别，避免无意义的后端 404 探测
  if (state.modelFormat === 'rknn' || !record?.id) return;
  try {
    const resp = await getModelClasses(record.id);
    applyClassNames(parseModelClassPayload(resp).classNames);
  } catch (error) {
    console.warn('加载检测类别失败', error);
  }
}

async function modelEdit(record: any) {
  try {
    state.editLoading = true;
    modelRef.id = record.id ?? null;
    modelRef.filePath = record.filePath ?? record.model_path ?? record.rknn_model_path ?? '';
    modelRef.imageUrl = record.imageUrl ?? record.image_url ?? '';
    state.modelFormat = detectModelFormat(record);
    const s = record.status;
    await setFieldsValue({
      name: record.name ?? '',
      version: normalizeModelVersion(record.version),
      description: record.description ?? '',
      status: s === '' || s === undefined || s === null ? 0 : Number(s),
    });
    await loadClassNamesForRecord(record);
  } catch (error) {
    console.error(error);
    createMessage.error('加载模型信息失败');
  } finally {
    state.editLoading = false;
  }
}

function handleCancel() {
  resetFormState();
  closeDrawer();
}

function handleFileUpload(info: any) {
  if (info.file.status === 'done') {
    const response = info.file.response;
    if (response && response.code === 0) {
      modelRef.filePath = response.data.url;
      state.modelFormat = response.data.model_format || 'pt';
      applyClassNames(parseModelClassPayload(response.data).classNames);
      createMessage.success('模型文件上传成功');
    } else {
      createMessage.error(response?.msg || '文件上传失败');
    }
  } else if (info.file.status === 'error') {
    const response = info.file.response;
    createMessage.error(response?.msg || info.file.error?.message || '文件上传失败');
  }
}

function handleImageUpload(info: any) {
  if (info.file.status === 'done') {
    const response = info.file.response;
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

async function handleOk() {
  try {
    const values = await validate();
    if (!modelRef.imageUrl) {
      createMessage.warning('请上传模型图片');
      return;
    }
    state.editLoading = true;
    const api = modelRef.id ? updateModel : createModel;
    const classNames = state.modelFormat === 'rknn'
      ? parseClassNamesText(state.rknnClassNamesText)
      : state.classNames;
    const payload = {
      id: modelRef.id,
      name: values.name,
      version: normalizeModelVersion(values.version),
      description: values.description,
      status: values.status,
      filePath: modelRef.filePath,
      imageUrl: modelRef.imageUrl,
      classNames,
      selectedClassNames: classNames,
    };

    await api(payload);
    createMessage.success('操作成功');
    closeDrawer();
    resetFormState();
    emits('success');
  } catch (error) {
    console.error(error);
  } finally {
    state.editLoading = false;
  }
}
</script>

<style lang="less" scoped>
.model-drawer-content {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.resource-form {
  :deep(.ant-form-item) {
    margin-bottom: 16px;
  }
}

.preview-wrap {
  margin-top: 8px;
}

.preview-image {
  max-height: 120px;
  max-width: 100%;
  border-radius: 4px;
  border: 1px solid #f0f0f0;
  display: block;
}

.form-extra {
  margin-top: 8px;
  color: rgba(0, 0, 0, 0.65);
  font-size: 13px;
  word-break: break-all;
}

.class-tags-panel {
  width: 100%;
}

.class-tag-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  max-height: 160px;
  overflow-y: auto;
  padding: 10px 12px;
  border: 1px solid #f0f0f0;
  border-radius: 6px;
  background: #fafafa;

  :deep(.ant-tag) {
    margin: 0;
  }
}

.form-hint {
  margin-top: 4px;
  color: rgba(0, 0, 0, 0.45);
  font-size: 13px;
  line-height: 1.5;
}

.footer-buttons {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  gap: 8px;
}
</style>
