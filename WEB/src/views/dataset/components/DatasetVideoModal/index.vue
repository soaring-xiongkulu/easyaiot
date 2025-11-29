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
        >
          <FormItem label="视频名称" name="name" v-bind=validateInfos.name>
            <Input v-model:value="modelRef.name"/>
          </FormItem>
          <FormItem label="视频地址" name="videoPath" v-bind=validateInfos.videoPath>
            <Upload
              name="file"
              multiple
              @change="handleVideoPathFileChange"
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
          <FormItem label="封面地址" name="coverPath" v-bind=validateInfos.coverPath>
            <Upload
              name="file"
              multiple
              @change="handleCoverPathFileChange"
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
          <FormItem label="描述" name="description" v-bind=validateInfos.description>
            <Input v-model:value="modelRef.description"/>
          </FormItem>
        </Form>
      </Spin>
    </div>
  </BasicModal>
</template>

<script lang="ts" setup>
import {computed, reactive, ref} from 'vue';
import {BasicModal, useModalInner} from '@/components/Modal';
import {Form, FormItem, Input, Spin, Upload,} from 'ant-design-vue';
import {useMessage} from '@/hooks/web/useMessage';
import {createDatasetVideo, updateDatasetVideo} from "@/api/device/dataset";
import {useUserStoreWithOut} from "@/store/modules/user";
import {useGlobSetting} from "@/hooks/setting";
import {useI18n} from "@/hooks/web/useI18n";

const {t} = useI18n()

defineOptions({name: 'DatasetVideoModal'})

const {createMessage} = useMessage();

const userStore = useUserStoreWithOut();
const token = userStore.getAccessToken;
const headers = ref({'Authorization': `Bearer ${token}`});
const {uploadUrl} = useGlobSetting();

const state = reactive({
  updateUrl: `${uploadUrl}/dataset/image/upload-file`,
  record: null,
  isView: false,
  isEdit: false,
  fileList: [],
  loading: false,
  editLoading: false,
});

const modelRef = reactive({
  id: null,
  name: '',
  videoPath: '',
  coverPath: '',
  description: '',
  datasetId: null,
});

const getTitle = computed(() => '上传视频');

const [register, {closeModal}] = useModalInner((data) => {
  const {datasetId, isEdit, isView, record} = data;
  modelRef.datasetId = datasetId;
  state.isEdit = isEdit;
  state.isView = isView;
  if (state.isEdit || state.isView) {
    modelEdit(record);
  }
});

async function modelEdit(record) {
  try {
    state.editLoading = true;
    Object.keys(modelRef).forEach((item) => {
      modelRef[item] = record[item];
    });
    state.editLoading = false;
    state.record = record;
  } catch (error) {
    console.error(error)
    //console.log('modelEdit ...', error);
  }
}

const emits = defineEmits(['success']);

function handleVideoPathFileChange(info: Record<string, any>) {
  const file = info.file;
  const status = file?.status;
  const response = file?.response;
  if (status === 'done') {
    if (response && (response.code === 0 || response.code === 200)) {
      // 兼容不同的响应格式
      const path = response.data?.url || response.data || response.url || '';
      if (path) {
        modelRef.videoPath = path;
        createMessage.success('视频上传成功');
      } else {
        createMessage.error('上传成功但未获取到文件路径');
        console.error('上传响应:', response);
      }
    } else {
      createMessage.error(response?.msg || '视频上传失败');
      console.error('上传失败:', response);
    }
  } else if (status === 'error') {
    createMessage.error('视频上传失败');
    console.error('上传错误:', file?.error);
  }
}

function handleCoverPathFileChange(info: Record<string, any>) {
  const file = info.file;
  const status = file?.status;
  const response = file?.response;
  if (status === 'done') {
    if (response && (response.code === 0 || response.code === 200)) {
      // 兼容不同的响应格式
      const path = response.data?.url || response.data || response.url || '';
      if (path) {
        modelRef.coverPath = path;
        createMessage.success('封面上传成功');
      } else {
        createMessage.error('上传成功但未获取到文件路径');
        console.error('上传响应:', response);
      }
    } else {
      createMessage.error(response?.msg || '封面上传失败');
      console.error('上传失败:', response);
    }
  } else if (status === 'error') {
    createMessage.error('封面上传失败');
    console.error('上传错误:', file?.error);
  }
}

const rulesRef = reactive({
  name: [{required: true, message: '请输入视频名称', trigger: ['change']}],
  videoPath: [{required: true, message: '请上传视频地址', trigger: ['change']}],
  coverPath: [{required: true, message: '请上传封面地址', trigger: ['change']}],
  description: [{required: true, message: '请输入描述', trigger: ['change']}],
});

const useForm = Form.useForm;
const {validate, resetFields, validateInfos} = useForm(modelRef, rulesRef);

function handleCancel() {
  //console.log('handleCancel');
  resetFields();
}

function handleOk() {
  validate().then(async () => {
    let api = createDatasetVideo;
    if (modelRef?.id) {
      api = updateDatasetVideo;
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
