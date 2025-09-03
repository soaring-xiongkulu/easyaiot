<template>
  <BasicModal
    @register="register"
    :title="getTitle"
    @cancel="handleCancel"
    :width="700"
    @ok="handleOk"
    :canFullscreen="false"
  >
    <div class="product-modal">
      <Spin :spinning="state.editLoading">
        <Form
          :labelCol="{ span: 3 }"
          :model="validateInfos"
          :wrapperCol="{ span: 21 }"
          :disabled="state.isView"
        >
          <FormItem label="数据集名称" name="name" v-bind=validateInfos.name>
            <Input v-model:value="modelRef.name"/>
          </FormItem>
          <FormItem label="数据集类型" name="datasetType"
                    v-bind=validateInfos.datasetType>
            <Select
              placeholder="数据集类型"
              :options="state.datasetTypeList"
              @change="handleDatasetTypeCLickChange"
              v-model:value="modelRef.datasetType"
              allowClear
            />
          </FormItem>
          <FormItem label="数据集描述" name="description" v-bind=validateInfos.description>
            <Input v-model:value="modelRef.description"/>
          </FormItem>
          <FormItem label="数据集封面" name="coverPath" v-bind=validateInfos.coverPath>
            <Upload
              name="file"
              multiple
              @change="handleFileChange"
              :action="state.updateUrl"
              :headers="headers"
              :showUploadList="true"
              accept="*"
              :disabled="state.isView"
            >
              <a-button type="primary">
                {{ t('component.upload.choose') }}
              </a-button>
            </Upload>
          </FormItem>
        </Form>
      </Spin>
    </div>
  </BasicModal>
</template>

<script lang="ts" setup>
import {computed, reactive, ref} from 'vue';
import {BasicModal, useModalInner} from '@/components/Modal';
import {Form, FormItem, Input, Select, Spin, Upload,} from 'ant-design-vue';
import {useMessage} from '@/hooks/web/useMessage';
import {useI18n} from "@/hooks/web/useI18n";
import {useUserStoreWithOut} from "@/store/modules/user";
import {useGlobSetting} from "@/hooks/setting";
import {createDataset, updateDataset} from "@/api/device/dataset";

const {t} = useI18n()

defineOptions({name: 'DatasetModal'})

const {createMessage} = useMessage();

const userStore = useUserStoreWithOut();
const token = userStore.getAccessToken;
const headers = ref({'Authorization': `Bearer ${token}`});
const {uploadUrl} = useGlobSetting();

const state = reactive({
  updateUrl: `${uploadUrl}/dataset/image/upload-file`,
  record: null,
  isEdit: false,
  isView: false,
  fileList: [],
  loading: false,
  editLoading: false,
  datasetTypeList: [
    {value: 0, label: '图片'},
    {value: 1, label: '文本'},
  ],
});

const modelRef = reactive({
  id: null,
  name: '',
  coverPath: '',
  description: '',
  datasetType: 0,
});

const getTitle = computed(() => (state.isEdit ? '编辑数据集' : state.isView ? '查看数据集' : '新增数据集'));

function handleFileChange(info: Record<string, any>) {
  const file = info.file;
  const status = file?.status;
  const response = file?.response;
  if (status === 'done') {
    createMessage.success('上传成功');
    modelRef.coverPath = response.data;
  }
}

const [register, {closeModal}] = useModalInner((data) => {
  const {isEdit, isView, record} = data;
  state.isEdit = isEdit;
  state.isView = isView;
  if (state.isEdit || state.isView) {
    datasetEdit(record);
  }
});


const emits = defineEmits(['success']);

const rulesRef = reactive({
  name: [{required: true, message: '请输入数据集名称', trigger: ['change']}],
  description: [{required: true, message: '请输入数据集描述', trigger: ['change']}],
  datasetType: [{required: true, message: '请输入数据集类型', trigger: ['change']}],
  coverPath: [{required: true, message: '请输入封面地址', trigger: ['change']}],
});

const useForm = Form.useForm;
const {validate, resetFields, validateInfos} = useForm(modelRef, rulesRef);

function handleDatasetTypeCLickChange(value) {
  //console.log('handleCLickChange', value)
}

async function datasetEdit(record) {
  try {
    state.editLoading = true;
    Object.keys(modelRef).forEach((item) => {
      modelRef[item] = record[item];
    });
    state.editLoading = false;
    state.record = record;
  } catch (error) {
    console.error(error)
    //console.log('datasetEdit ...', error);
  }
}

function handleCancel() {
  //console.log('handleCancel');
  resetFields();
}

function handleOk() {
  validate().then(async () => {
    let api = createDataset;
    if (modelRef?.id) {
      api = updateDataset;
    }
    state.editLoading = true;
    api(modelRef)
      .then(() => {
        createMessage.success('操作成功');
        closeModal();
        resetFields();
        emits('success');
      })
      .finally(() => {
        state.editLoading = false;
      });
  }).catch((err) => {
    createMessage.error('操作失败');
    console.error(err);
  });
}
</script>
<style lang="less" scoped>
.product-modal {
  :deep(.ant-form-item-label) {
    & > label::after {
      content: '';
    }
  }
}
</style>
