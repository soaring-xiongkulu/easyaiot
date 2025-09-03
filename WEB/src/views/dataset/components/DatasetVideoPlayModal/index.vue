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
        <video v-show="state.playUrl != null" :src="state.playUrl" id="myVideo" ref="videoRef"
               controls autoplay style="width: 100%; height: 100%"
               class="shiping1 video-js vjs-big-play-centered" preload="auto">
          <source src="" type="video/mp4">
        </video>
      </Spin>
    </div>
  </BasicModal>
</template>

<script lang="ts" setup>
import {computed, reactive, ref} from 'vue';
import {BasicModal, useModalInner} from '@/components/Modal';
import {Form, Spin,} from 'ant-design-vue';
import {useMessage} from '@/hooks/web/useMessage';
import {createDatasetVideo, updateDatasetVideo} from "@/api/device/dataset";
import {useUserStoreWithOut} from "@/store/modules/user";
import {useGlobSetting} from "@/hooks/setting";
import {useI18n} from "@/hooks/web/useI18n";

const {t} = useI18n()

defineOptions({name: 'DatasetVideoPlayModal'})

const {createMessage} = useMessage();

const userStore = useUserStoreWithOut();
const token = userStore.getAccessToken;
const headers = ref({'Authorization': `Bearer ${token}`});
const {uploadUrl} = useGlobSetting();

const state = reactive({
  updateUrl: `${uploadUrl}/dataset/image/upload-file`,
  record: null,
  isView: false,
  fileList: [],
  loading: false,
  editLoading: false,
  playUrl: null,
});

const modelRef = reactive({
  id: null,
  videoPath: '',
  coverPath: '',
  description: '',
  datasetId: null,
});

const getTitle = computed(() => '上传视频');

const [register, {closeModal}] = useModalInner((data) => {
  const {playUrl} = data;
  state.playUrl = playUrl;
});

const emits = defineEmits(['success']);

const rulesRef = reactive({
  videoPath: [{required: true, message: '请输入视频地址', trigger: ['change']}],
  coverPath: [{required: true, message: '请输入封面地址', trigger: ['change']}],
  description: [{required: true, message: '请输入描述', trigger: ['change']}],
});

const useForm = Form.useForm;
const {validate, resetFields, validateInfos} = useForm(modelRef, rulesRef);

function handleCancel() {
  //console.log('handleCancel');
  state.playUrl = null;
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
