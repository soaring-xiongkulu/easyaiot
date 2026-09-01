<template>
  <BasicModal
    @register="register"
    :title="getTitle"
    @cancel="handleCancel"
    :width="900"
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
          <FormItem label="告警时间" name="time" v-bind=validateInfos.time>
            <Input v-model:value="modelRef.time"/>
          </FormItem>
          <FormItem label="告警设备" name="device_name" v-bind=validateInfos.device_name>
            <Input v-model:value="modelRef.device_name"/>
          </FormItem>
          <FormItem label="告警事件" name="event" v-bind=validateInfos.event>
            <Input v-model:value="modelRef.event"/>
          </FormItem>
          <FormItem label="告警对象" name="object" v-bind=validateInfos.object>
            <Input v-model:value="modelRef.object"/>
          </FormItem>
          <FormItem label="检测区域" name="region" v-bind=validateInfos.region>
            <Input v-model:value="modelRef.region"/>
          </FormItem>
          <FormItem label="告警图片（MinIO）" name="image_url" v-bind=validateInfos.image_url>
            <Input v-model:value="modelRef.image_url"/>
          </FormItem>
          <FormItem label="告警录像" name="record_path" v-bind=validateInfos.record_path>
            <Input v-model:value="modelRef.record_path"/>
          </FormItem>
          <FormItem v-if="llmInfo" label="大模型研判" name="llm">
            <div class="llm-judge-result">
              <a-descriptions size="small" :column="2" bordered>
                <a-descriptions-item label="结论">
                  <a-tag :color="llmStatusColor">{{ llmStatusText }}</a-tag>
                </a-descriptions-item>
                <a-descriptions-item label="置信度">
                  {{ llmInfo.detail?.confidence != null ? Number(llmInfo.detail.confidence).toFixed(2) : '-' }}
                </a-descriptions-item>
                <a-descriptions-item label="判断方式" :span="2">
                  {{ llmInfo.detail?.judge_mode === 'video' ? '事件视频' : '事件图片' }}
                </a-descriptions-item>
                <a-descriptions-item label="理由" :span="2">
                  <div class="llm-judge-reason">{{ llmInfo.detail?.reason || '-' }}</div>
                </a-descriptions-item>
                <a-descriptions-item label="耗时(ms)">
                  {{ llmInfo.detail?.duration_ms ?? '-' }}
                </a-descriptions-item>
                <a-descriptions-item label="研判时间">
                  {{ formatJudgeTime(llmInfo.detail?.judged_at) }}
                </a-descriptions-item>
                <a-descriptions-item v-if="llmAttributesText" label="结构化输出" :span="2">
                  <pre class="llm-judge-attributes">{{ llmAttributesText }}</pre>
                </a-descriptions-item>
              </a-descriptions>
            </div>
          </FormItem>
        </Form>
      </Spin>
    </div>
  </BasicModal>
</template>
<script lang="ts" setup>
import {computed, reactive} from 'vue';
import {BasicModal, useModalInner} from '@/components/Modal';
import {Form, FormItem, Input, Spin,} from 'ant-design-vue';
import {useMessage} from '@/hooks/web/useMessage';

defineOptions({name: 'AlarmModal'})

const {createMessage} = useMessage();

const state = reactive({
  isEdit: false,
  isView: false,
  record: null,
  editLoading: false,
});

const modelRef = reactive({
  id: null,
  object: null,
  event: null,
  region: null,
  information: null,
  time: null,
  device_id: null,
  device_name: null,
  image_url: null,
  record_path: null,
});

const getTitle = computed(() => (state.isEdit ? '编辑告警事件' : state.isView ? '查看告警事件' : '新增告警事件'));

const [register, {closeModal}] = useModalInner((data) => {
  const {isEdit, isView, record} = data;
  state.isEdit = isEdit;
  state.isView = isView;
  if (state.isEdit || state.isView) {
    modelEdit(record);
  }
});

const emits = defineEmits(['success']);

/** information.llm 研判结论（iot-sink 异步回写：{status, detail}） */
const llmInfo = computed(() => {
  if (!modelRef.information) return null;
  let info: any = modelRef.information;
  if (typeof info === 'string') {
    try {
      info = JSON.parse(info);
    } catch (e) {
      return null;
    }
  }
  const llm = info?.llm;
  if (!llm) return null;
  let detail: any = llm.detail;
  if (typeof detail === 'string') {
    try {
      detail = JSON.parse(detail);
    } catch (e) {
      detail = null;
    }
  }
  return { status: llm.status || null, detail: detail || null };
});

const llmStatusText = computed(() => {
  switch (llmInfo.value?.status) {
    case 'confirmed':
      return '事件成立';
    case 'rejected':
      return '事件不成立';
    case 'error':
      return '研判失败';
    default:
      return '待研判';
  }
});

const llmStatusColor = computed(() => {
  switch (llmInfo.value?.status) {
    case 'confirmed':
      return 'green';
    case 'rejected':
      return 'red';
    case 'error':
      return 'orange';
    default:
      return 'default';
  }
});

const llmAttributesText = computed(() => {
  const attrs = llmInfo.value?.detail?.attributes;
  if (!attrs) return '';
  try {
    return typeof attrs === 'string' ? attrs : JSON.stringify(attrs, null, 2);
  } catch (e) {
    return String(attrs);
  }
});

function formatJudgeTime(ts: number | string | undefined | null): string {
  if (!ts) return '-';
  const num = Number(ts);
  if (!Number.isFinite(num)) return String(ts);
  const d = new Date(num > 1e12 ? num : num * 1000);
  return d.toLocaleString();
}

const rulesRef = reactive({
  deviceVersion: [{required: true, message: '请输入告警事件号', trigger: ['change']}],
});

function handleCLickChange(value) {
  //console.log('handleCLickChange', value)
}

const useForm = Form.useForm;
const {validate, resetFields, validateInfos} = useForm(modelRef, rulesRef);

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

function handleCancel() {
  //console.log('handleCancel');
  resetFields();
}

function handleOk() {
  // Alert不需要增加或删除功能，直接关闭弹框
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

.llm-judge-result {
  width: 100%;

  .llm-judge-reason {
    max-height: 120px;
    overflow-y: auto;
    white-space: pre-wrap;
    word-break: break-all;
    color: rgba(0, 0, 0, 0.75);
  }

  .llm-judge-attributes {
    max-height: 160px;
    overflow-y: auto;
    margin: 0;
    font-size: 12px;
    background: #fafafa;
    border: 1px solid #f0f0f0;
    border-radius: 4px;
    padding: 8px;
  }
}
</style>
