<template xmlns="">
  <BasicModal
    @register="register"
    :title="getTitle"
    @cancel="handleCancel"
    :width="1200"
    @ok="handleOk"
    :canFullscreen="false"
  >
    <div class="product-modal">
      <Spin :spinning="state.editLoading">
        <div class="container" style="width:1200px; height: 653px; margin-top: 5px">
          <easyPlayer ref="recordVideoPlayer" :videoUrl="state.currentUrl"
                      :height="false"></easyPlayer>
        </div>
      </Spin>
    </div>
  </BasicModal>
</template>
<script lang="ts" setup>
import {computed, reactive} from 'vue';
import {BasicModal, useModalInner} from '@/components/Modal';
import {Form, Spin,} from 'ant-design-vue';
import {useMessage} from '@/hooks/web/useMessage';
import easyPlayer from "@/components/VideoPlayer/EasyPlayer.vue";

defineOptions({name: 'RtmpPlayModal'})

// 定义坐标点类型
interface Point {
  x: number
  y: number
}

const {createMessage} = useMessage();

const state = reactive({
  isEdit: false,
  isView: false,
  type: null,
  record: null,
  editLoading: false,
  aiModelList: [],
  video: 'http://lndxyj.iqilu.com/public/upload/2019/10/14/8c001ea0c09cdc59a57829dabc8010fa.mp4',
  videoUrl: '',
  activePlayer: "jessibuca",
  presetPos: '',
  deviceIdentification: '',
  // 如何你只是用一种播放器，直接注释掉不用的部分即可
  player: {
    jessibuca: ["ws_flv", "flv"],
    webRTC: ["rtc", "rtcs"],
  },
  hasAudio: false,
  currentUrl: null,
});

const modelRef = reactive({
  id: null,
  ai_region: null,
});

const getTitle = computed(() => (state.isEdit ? '编辑视频流' : state.isView ? '查看视频流' : '新增视频流'));

const [register, {closeModal}] = useModalInner((data) => {
  const {record} = data;
  state.currentUrl = record['http_stream'];
});

const emits = defineEmits(['success']);

const rulesRef = reactive({
  deviceVersion: [{required: true, message: '请输入视频流', trigger: ['change']}],
});

const useForm = Form.useForm;
const {validate, resetFields, validateInfos} = useForm(modelRef, rulesRef);

function handleCancel() {
  state.currentUrl = null;
  resetFields();
}

function handleOk() {
  state.currentUrl = null;
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

  .container {
    position: relative;
    width: fit-content;
  }

  canvas {
    position: absolute;
    top: 0;
    left: 0;
    pointer-events: auto;
  }
}
</style>
