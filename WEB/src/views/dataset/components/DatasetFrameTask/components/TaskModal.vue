<template>
  <BasicModal
    @register="register"
    :title="getTitle"
    :width="700"
    @cancel="handleCancel"
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
          <FormItem label="任务类型" name="taskType" v-bind=validateInfos.taskType>
            <Select
              placeholder="任务类型"
              :options="state.taskType"
              @change="handleCLickChange"
              v-model:value="modelRef.taskType"
              allowClear
            />
          </FormItem>
          <FormItem label="任务名称" name="taskName" v-bind=validateInfos.taskName>
            <Input v-model:value="modelRef.taskName"/>
          </FormItem>
          <FormItem v-show="modelRef.taskType == 0" label="RTMP流地址" name="rtmpUrl"
                    v-bind=validateInfos.rtmpUrl>
            <Input v-model:value="modelRef.rtmpUrl"/>
          </FormItem>
          <FormItem v-show="modelRef.taskType == 1" label="设备ID" name="deviceId"
                    v-bind=validateInfos.deviceId>
            <Input v-model:value="modelRef.deviceId"/>
          </FormItem>
          <FormItem v-show="modelRef.taskType == 1" label="通道ID" name="channelId"
                    v-bind=validateInfos.channelId>
            <Input v-model:value="modelRef.channelId"/>
          </FormItem>
        </Form>
      </Spin>
    </div>
  </BasicModal>
</template>
<script lang="ts" setup>
import {computed, onMounted, reactive} from 'vue';
import {BasicModal, useModalInner} from '@/components/Modal';
import {Form, FormItem, Input, Select, Spin,} from 'ant-design-vue';
import {useMessage} from '@/hooks/web/useMessage';
import {createDatasetFrameTask, updateDatasetFrameTask} from "@/api/device/dataset";

const {createMessage} = useMessage();

const state = reactive({
  isEdit: false,
  isView: false,
  taskType: [
    {
      label: '实时帧捕获',
      value: 0,
    },
    {
      label: 'GB28181帧捕获',
      value: 1,
    },
  ],
  loading: false,
  editLoading: false,
  defaultRule: [],
  defaultRuleParams: {
    pageSize: 30,
    page: 1,
    total: 0,
  },
  defaultQueue: [],
  defaultQueueParams: {
    pageSize: 30,
    page: 1,
    total: 0,
  },
});


const modelRef = reactive({
  id: null,
  datasetId: null,
  taskName: '',
  taskType: 0,
  channelId: '',
  deviceId: '',
  rtmpUrl: '',
});

const getTitle = computed(() => (state.isEdit ? '编辑帧捕获任务' : state.isView ? '查看帧捕获任务' : '新增帧捕获任务'));

onMounted(() => {
})

const [register, {closeModal}] = useModalInner((data) => {
  const {datasetId, isEdit, isView, record} = data;
  state.isEdit = isEdit;
  state.isView = isView;
  modelRef.datasetId = datasetId;
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
  } catch (error) {
    console.error(error)
    //console.log('modelEdit ...', error);
  }
}

const emits = defineEmits(['success']);

const rulesRef = reactive({
  taskType: [{required: true, message: '请输入任务类型', trigger: ['change']}],
  taskName: [{required: true, message: '请输入任务名称', trigger: ['change']}],
});

const useForm = Form.useForm;
const {validate, resetFields, validateInfos} = useForm(modelRef, rulesRef);

function handleCLickChange(value) {
  //console.log('handleCLickChange', value)
}

function handleCancel() {
  //console.log('handleCancel');
  resetFields();
}

function handleOk() {
  if (modelRef.taskType == 0 && modelRef.rtmpUrl == '') {
    createMessage.error("RTMP流地址不能为空")
    return;
  }
  if (modelRef.taskType == 1 && (modelRef.deviceId == '' || modelRef.channelId == '')) {
    createMessage.error("设备ID和通道ID不能为空")
    return;
  }
  validate().then(async () => {
    let api = createDatasetFrameTask;
    if (modelRef?.id) {
      api = updateDatasetFrameTask;
    }
    state.editLoading = true;
    api(modelRef)
      .then(() => {
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
