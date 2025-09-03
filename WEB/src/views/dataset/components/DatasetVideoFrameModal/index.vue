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
          :labelCol="{ span: 4 }"
          :model="validateInfos"
          :wrapperCol="{ span: 18 }"
        >
          <FormItem label="抽帧间隔(秒)" name="frameInterval" v-bind=validateInfos.frameInterval>
            <Slider v-model:value="modelRef.videoFrameInterval"
                    :tipFormatter="(value)=>{return `${value}秒`}" :min="0.5" :max="10"
                    :step="0.5"/>
            <Tag color="blue">{{ modelRef.videoFrameInterval }}秒</Tag>
          </FormItem>
          <FormItem label="图像质量" name="quality" v-bind=validateInfos.quality>
            <Slider v-model:value="modelRef.videoQuality" :min="20" :max="100"
                    :step="20"/>
            <Tag color="blue">
              {{ modelRef.videoQuality <= 60 ? '低质量' : modelRef.videoQuality == 80 ? '中质量' : '高质量' }}
            </Tag>
          </FormItem>
        </Form>
      </Spin>
    </div>
  </BasicModal>
</template>

<script lang="ts" setup>
import {computed, reactive, ref} from 'vue';
import {BasicModal, useModalInner} from '@/components/Modal';
import {Form, FormItem, Slider, Spin, Tag} from 'ant-design-vue';
import {useMessage} from '@/hooks/web/useMessage';
import {useUserStoreWithOut} from "@/store/modules/user";
import {useGlobSetting} from "@/hooks/setting";
import {useI18n} from "@/hooks/web/useI18n";

const {t} = useI18n()

defineOptions({name: 'DatasetVideoFrameModal'})

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
  videoPath: '',
});

const modelRef = reactive({
  videoPath: '',
  videoFrameInterval: 1,
  videoQuality: 80,
});

const getTitle = computed(() => '抽帧设置');

const [register, {closeModal}] = useModalInner((data) => {
  const {videoPath} = data;
  state.videoPath = videoPath;
});

const emits = defineEmits(['success']);

const rulesRef = reactive({
  frameInterval: [{required: true, message: '请输入抽帧间隔(秒)', trigger: ['change']}],
  quality: [{required: true, message: '请输入图像质量', trigger: ['change']}],
});

const useForm = Form.useForm;
const {validate, resetFields, validateInfos} = useForm(modelRef, rulesRef);

function handleCancel() {
  resetFields();
}

function handleOk() {
  modelRef.videoPath = state.videoPath
  emits('success', modelRef);
  closeModal();
  resetFields();
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
