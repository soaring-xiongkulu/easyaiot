<template>
  <BasicModal
    @register="register"
    @cancel="handleCancel"
    :width="900"
    @ok="handleOk"
    :canFullscreen="false"
  >
    <div class="product-modal" v-if="operateType == 'add' && !state.isTestAccess">
      <div class="product-modal">
        <Spin :spinning="state.editLoading">
          <Form
            :labelCol="{ span: 4 }"
            :model="validateInfos"
            :wrapperCol="{ span: 20 }"
          >
            <FormItem label="IP" name="ip" v-bind=validateInfos.ip>
              <Input v-model:value="modelRef.ip"/>
            </FormItem>
            <FormItem label="HTTP端口" name="httpPort" v-bind=validateInfos.httpPort>
              <Input v-model:value="modelRef.httpPort"/>
            </FormItem>
            <FormItem label="SECRET" name="secret" v-bind=validateInfos.secret>
              <Input v-model:value="modelRef.secret"/>
            </FormItem>
          </Form>
          <Button style="width: 95%;height: 38px;float: right;" type="primary" @click="test">流媒体节点测试</Button>
        </Spin>
      </div>
    </div>
    <div class="product-modal" v-else>
      <div class="product-modal">
        <Spin :spinning="state.editLoading">
          <Form
            :labelCol="{ span: 8 }"
            :model="validateInfos"
            :wrapperCol="{ span: 16 }"
          >
            <Row :gutter="0">
              <Col :span="12">
                <FormItem label="IP" name="ip" v-bind=validateInfos.ip>
                  <Input v-model:value="modelRef.ip"/>
                </FormItem>
              </Col>
              <Col :span="12">
                <FormItem label="RTMP PORT" name="rtmpPort" v-bind=validateInfos.rtmpPort>
                  <Input v-model:value="modelRef.rtmpPort"/>
                </FormItem>
              </Col>
              <Col :span="12">
                <FormItem label="HTTP端口" name="httpPort" v-bind=validateInfos.httpPort>
                  <Input v-model:value="modelRef.httpPort"/>
                </FormItem>
              </Col>
              <Col :span="12">
                <FormItem label="RTMPS PORT" name="rtmpSSlPort" v-bind=validateInfos.rtmpSSlPort>
                  <Input v-model:value="modelRef.rtmpSSlPort"/>
                </FormItem>
              </Col>
              <Col :span="12">
                <FormItem label="HOOK IP" name="hookIp" v-bind=validateInfos.hookIp>
                  <Input v-model:value="modelRef.hookIp"/>
                </FormItem>
              </Col>
              <Col :span="12">
                <FormItem label="SECRET" name="secret" v-bind=validateInfos.secret>
                  <Input v-model:value="modelRef.secret"/>
                </FormItem>
              </Col>
              <Col :span="12">
                <FormItem label="SDP IP" name="sdpIp" v-bind=validateInfos.sdpIp>
                  <Input v-model:value="modelRef.sdpIp"/>
                </FormItem>
              </Col>
              <Col :span="12">
                <FormItem label="流IP" name="streamIp" v-bind=validateInfos.streamIp>
                  <Input v-model:value="modelRef.streamIp"/>
                </FormItem>
              </Col>
              <Col :span="12">
                <FormItem label="收流端口">
                  <Row :gutter="0">
                    <Col :span="11">
                      <Input v-model:value="modelRef.rtpPortRange1"/>
                    </Col>
                    <span style="margin: 0 5px">-</span>
                    <Col :span="11">
                      <Input v-model:value="modelRef.rtpPortRange2"/>
                    </Col>
                  </Row>
                </FormItem>
              </Col>
              <Col :span="12">
                <FormItem label="HTTPS PORT" name="httpSSlPort" v-bind=validateInfos.httpSSlPort>
                  <Input v-model:value="modelRef.httpSSlPort"/>
                </FormItem>
              </Col>
              <Col :span="12">
                <FormItem label="RTSP PORT" name="rtspPort" v-bind=validateInfos.rtspPort>
                  <Input v-model:value="modelRef.rtspPort"/>
                </FormItem>
              </Col>
              <Col :span="12">
                <FormItem label="RTSPS PORT" name="rtspSSLPort" v-bind=validateInfos.rtspSSLPort>
                  <Input v-model:value="modelRef.rtspSSLPort"/>
                </FormItem>
              </Col>
            </Row>
          </Form>
        </Spin>
      </div>
    </div>
  </BasicModal>
</template>
<script lang="ts" setup>
import {reactive, ref, unref} from 'vue';
import {BasicModal, useModalInner} from '@/components/Modal';
import {Button, Col, Form, FormItem, Input, Row, Spin,} from 'ant-design-vue';
import {useMessage} from '@/hooks/web/useMessage';
import {useRoute} from "vue-router";
import {checkMediaServer, saveOrUpdateMediaServer} from "@/api/device/gb28181";

defineOptions({name: 'PullProxyModal'})

const {createMessage} = useMessage();
const route = useRoute()

const state = reactive({
  isTestAccess: false,
  editLoading: false,
  nodeTypeList: [
    {label: 'ZLMediaKit', value: 'ZLMediaKit'}
  ],
});

const modelRef = reactive({
  id: '',
  ip : '',
  httpPort: '',
  secret: '',
  type: 'zlm',
  rtmpPort : '',
  rtmpSSlPort: '',
  hookIp: '',
  sdpIp: '',
  streamIp: '',
  rtpPortRange1: '',
  rtpPortRange2: '',
  httpSSlPort: '',
  rtspPort: '',
  rtspSSLPort: '',
  autoConfig: true,
  rtpEnable: true,
  rtpPortRange: '',
  sendRtpPortRange: '',
  flvPort: 80,
  flvSSLPort: 80,
  wsFlvPort: 80,
  wsFlvSSLPort: 80,
  rtpProxyPort: 10000,
  hookAliveInterval: null,
  status: false,
  recordAssistPort: 0,
  createTime: null,
  updateTime: null,
  lastKeepaliveTime: null,
  defaultServer: false,
  recordDay: 0,
  recordPath: null,
  transcodeSuffix: null
});

const checkedKeys = ref<Array<string | number>>([]);

const operateType = ref('add');

const [register, { closeModal, setModalProps }] = useModalInner((data) => {
  console.log('data ...', data);
  operateType.value = data.type;
  setModalProps({
    title: data.type == 'add' ? '新增媒体节点' : '编辑媒体节点',
  });
  unref(operateType) == 'edit' && editMedia(data.record);
});

const editMedia = (record) => {
  for (const key in record) {
    modelRef[key] = record[key];
  }
  if(record.rtpPortRange !== '') {
    modelRef.rtpPortRange1 = record.rtpPortRange.split(',')[0];
    modelRef.rtpPortRange2 = record.rtpPortRange.split(',')[1];
  }
};

const emits = defineEmits(['success']);

function handleCLickChange(value) {
  //console.log('handleCLickChange', value)
}

const rulesRef = reactive({
  ip: [{required: true, message: '请输入IP', trigger: ['change']}],
  httpPort: [{required: true, message: '请输入HTTP端口', trigger: ['change']}],
  secret: [{required: true, message: '请输入SECRET', trigger: ['change']}],
  rtmpPort: [{required: true, message: '请输入rtmpPort', trigger: ['change']}],
  rtmpSSlPort: [{required: true, message: '请输入rtmpSSlPort', trigger: ['change']}],
  hookIp: [{required: true, message: '请输入hookIp', trigger: ['change']}],
  sdpIp: [{required: true, message: '请输入sdpIp', trigger: ['change']}],
  streamIp: [{required: true, message: '请输入streamIp', trigger: ['change']}],
  rtpPortRange1: [{required: true, message: '请输入rtpPortRange1', trigger: ['change']}],
  rtpPortRange2: [{required: true, message: '请输入rtpPortRange2', trigger: ['change']}],
  httpSSlPort: [{required: true, message: '请输入httpSSlPort', trigger: ['change']}],
  rtspPort: [{required: true, message: '请输入rtspPort', trigger: ['change']}],
  rtspSSLPort: [{required: true, message: '请输入rtspSSLPort', trigger: ['change']}],
});

const useForm = Form.useForm;
const {validate, resetFields, validateInfos} = useForm(modelRef, rulesRef);

function handleCancel() {
  state.isTestAccess = false;
  resetFields();
}

function test() {
  checkMediaServer(modelRef).then((res)=>{
    for (const key in res) {
      modelRef[key] = res[key];
    }
    state.isTestAccess = true;
  });
}

function handleOk() {
  if (operateType == 'add' && !state.isTestAccess) {
    createMessage.warn('必须先通过测试');
  }
  validate().then(async () => {
    let api = saveOrUpdateMediaServer;
    modelRef.rtpPortRange = modelRef.rtpPortRange1 + ',' +modelRef.rtpPortRange2
    modelRef.sendRtpPortRange = modelRef.rtpPortRange1 + ',' +modelRef.rtpPortRange2
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
