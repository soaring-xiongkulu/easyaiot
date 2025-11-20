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
          <FormItem label="告警图片" name="image_path" v-bind=validateInfos.image_path>
            <Input v-model:value="modelRef.image_path"/>
          </FormItem>
          <FormItem label="告警录像" name="record_path" v-bind=validateInfos.record_path>
            <Input v-model:value="modelRef.record_path"/>
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
  image_path: null,
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
</style>
