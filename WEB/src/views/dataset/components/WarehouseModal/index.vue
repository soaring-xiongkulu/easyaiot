<!-- WarehouseModal.vue -->
<template>
  <BasicModal
    @register="register"
    :title="getTitle"
    @cancel="handleCancel"
    :width="700"
    @ok="handleOk"
    :canFullscreen="false"
  >
    <div class="warehouse-modal">
      <Spin :spinning="state.editLoading">
        <Form
          :labelCol="{ span: 4 }"
          :model="validateInfos"
          :wrapperCol="{ span: 20 }"
          :disabled="state.isView"
        >
          <FormItem label="数据仓名称" name="name" v-bind="validateInfos.name">
            <Input v-model:value="modelRef.name" placeholder="请输入数据仓名称"/>
          </FormItem>
          <FormItem label="封面图片" name="coverPath" v-bind="validateInfos.coverPath">
            <Upload
              name="file"
              @change="handleFileChange"
              :action="state.updateUrl"
              :headers="headers"
              :showUploadList="true"
              accept="image/*"
              :disabled="state.isView"
            >
              <a-button type="primary">
                {{ t('component.upload.choose') }}
              </a-button>
              <div v-if="modelRef.coverPath" class="mt-2">
                <img :src="modelRef.coverPath" alt="封面图" class="cover-preview"/>
              </div>
            </Upload>
          </FormItem>
          <FormItem label="数据仓描述" name="description" v-bind="validateInfos.description">
            <TextArea v-model:value="modelRef.description" placeholder="请输入数据仓描述"
                      :rows="4"/>
          </FormItem>

          <!-- 数据集关联管理 -->
          <FormItem label="关联数据集" v-if="state.isEdit || state.isView">
            <DatasetSelector
              v-model:value="modelRef.datasets"
              :disabled="state.isView"
              @change="handleDatasetChange"
            />
          </FormItem>
        </Form>
      </Spin>
    </div>
  </BasicModal>
</template>

<script lang="ts" setup>
import {computed, reactive, ref} from 'vue';
import {BasicModal, useModalInner} from '@/components/Modal';
import {Form, FormItem, Input, message as antMessage, Spin, Upload} from 'ant-design-vue';
import {useMessage} from '@/hooks/web/useMessage';
import {useI18n} from "@/hooks/web/useI18n";
import {useUserStoreWithOut} from "@/store/modules/user";
import {useGlobSetting} from "@/hooks/setting";
import {createWarehouse, getWarehouse, updateWarehouse} from "@/api/device/dataset";

const {t} = useI18n();
const {createMessage} = useMessage();
const TextArea = Input.TextArea;

defineOptions({name: 'WarehouseModal'});

const userStore = useUserStoreWithOut();
const token = userStore.getAccessToken;
const headers = ref({'Authorization': `Bearer ${token}`});
const {uploadUrl} = useGlobSetting();

const state = reactive({
  updateUrl: `${uploadUrl}/packages/upload-package`,
  isEdit: false,
  isView: false,
  editLoading: false,
});

const modelRef = reactive({
  id: null,
  name: '',
  coverPath: '',
  description: '',
  datasets: [] as any[], // 关联的数据集
});

const getTitle = computed(() =>
  state.isEdit ? '编辑数据仓' : state.isView ? '数据仓详情' : '新增数据仓'
);

function handleFileChange(info) {
  if (info.file.status === 'done') {
    modelRef.coverPath = info.file.response.data;
    createMessage.success('上传成功');
  } else if (info.file.status === 'error') {
    createMessage.error('上传失败');
  }
}

const [register, {closeModal}] = useModalInner(async (data) => {
  const {isEdit, isView, record} = data;
  state.isEdit = isEdit;
  state.isView = isView;

  if (state.isEdit || state.isView) {
    state.editLoading = true;
    try {
      // 获取数据仓详情（包含关联数据集）
      const res = await getWarehouse({id: record.id});
      Object.assign(modelRef, res.data);
      state.editLoading = false;
    } catch (error) {
      createMessage.error('获取数据失败');
      state.editLoading = false;
    }
  } else {
    // 重置表单
    resetFields();
  }
});

const emits = defineEmits(['success']);

const rulesRef = reactive({
  name: [{required: true, message: '请输入数据仓名称', trigger: ['blur', 'change']}],
  description: [{required: true, message: '请输入数据仓描述', trigger: ['blur', 'change']}],
});

const useForm = Form.useForm;
const {validate, resetFields, validateInfos} = useForm(modelRef, rulesRef);

function handleDatasetChange(selectedDatasets) {
  modelRef.datasets = selectedDatasets;
}

async function handleOk() {
  try {
    await validate();
    const api = modelRef.id ? updateWarehouse : createWarehouse;
    state.editLoading = true;

    // 准备数据，包含关联数据集ID
    const payload = {
      ...modelRef,
      datasetIds: modelRef.datasets.map(ds => ds.id)
    };

    await api(payload);
    createMessage.success('操作成功');
    closeModal();
    resetFields();
    emits('success');
  } catch (error) {
    console.error(error);
    antMessage.error('操作失败');
  } finally {
    state.editLoading = false;
  }
}

function handleCancel() {
  resetFields();
  closeModal();
}
</script>

<style lang="less" scoped>
.warehouse-modal {
  :deep(.ant-form-item-label) {
    text-align: left;
  }

  .cover-preview {
    max-width: 200px;
    max-height: 150px;
    border: 1px solid #eee;
    border-radius: 4px;
    padding: 4px;
  }
}
</style>
