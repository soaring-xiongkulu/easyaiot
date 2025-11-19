<template>
  <Form :model="validateInfos" :colon="false">
    <FormItem label="">
      <Row :gutter="24">
        <Col :span="12">
          <FormItem label="安全配置模式" v-bind="validateInfos.securityMode">
            <Select v-model:value="modelRef.securityMode" :options="securityModeList" />
          </FormItem>
        </Col>
        <Col :span="12">
          <FormItem label="服务器ID" v-bind="validateInfos.shortServerId">
            <div class="flex">
              <Input
                placeholder="请输入服务器ID"
                type="number"
                v-model:value="modelRef.shortServerId"
              />
              <Tooltip>
                <template #title>服务器ID用作关联服务器对象实例的链接</template>
                <question-circle-outlined />
              </Tooltip>
            </div>
          </FormItem>
        </Col>
      </Row>
      <Row :gutter="24">
        <Col :span="12">
          <FormItem label="主机" v-bind="validateInfos.host">
            <Input placeholder="请输入主机" v-model:value="modelRef.host" />
          </FormItem>
        </Col>
        <Col :span="12">
          <FormItem label="端口" v-bind="validateInfos.port">
            <Input placeholder="请输入端口" v-model:value="modelRef.port" />
          </FormItem>
        </Col>
      </Row>
      <Row :gutter="24">
        <Col :span="12">
          <FormItem label="停留时间" v-bind="validateInfos.clientHoldOffTime">
            <div class="flex">
              <Input
                placeholder="请输入停留时间"
                type="number"
                v-model:value="modelRef.clientHoldOffTime"
              />
              <Tooltip>
                <template #title>客户端仅与Bootstrap-Server共用停留时间</template>
                <question-circle-outlined />
              </Tooltip>
            </div>
          </FormItem>
        </Col>
        <Col :span="12">
          <FormItem label="账户超时" v-bind="validateInfos.bootstrapServerAccountTimeout">
            <div class="flex">
              <Input
                placeholder="请输入账户超时"
                type="number"
                v-model:value="modelRef.bootstrapServerAccountTimeout"
              />
              <Tooltip>
                <template #title>Bootstrap-Server帐户资源的超时值。</template>
                <question-circle-outlined />
              </Tooltip>
            </div>
          </FormItem>
        </Col>
      </Row>
      <FormItem
        label="服务器公钥"
        v-show="modelRef.securityMode === 'RPK' || modelRef.securityMode === 'X509'"
        v-bind="validateInfos.serverPublicKey"
      >
        <div class="flex">
          <Input placeholder="请输入服务器公钥" v-model:value="modelRef.serverPublicKey" />
          <Tooltip>
            <template #title>X509公钥必须是X509v3格式而且支持EC算法</template>
            <question-circle-outlined />
          </Tooltip>
        </div>
      </FormItem>
      <Row :gutter="24">
        <Col :span="12">
          <FormItem label="客户端注册生命周期" v-bind="validateInfos.lifetime">
            <Input
              placeholder="请输入客户端注册生命周期"
              type="number"
              v-model:value="modelRef.lifetime"
            />
          </FormItem>
        </Col>
        <Col :span="12">
          <FormItem label="最小期限" v-bind="validateInfos.defaultMinPeriod">
            <div class="flex">
              <Input
                placeholder="请输入最小期限"
                type="number"
                v-model:value="modelRef.defaultMinPeriod"
              />
              <Tooltip>
                <template #title>LWM2M客户端在观察中不包含此参数时使用的默认值。</template>
                <question-circle-outlined />
              </Tooltip>
            </div>
          </FormItem>
        </Col>
      </Row>
      <FormItem label="绑定" v-bind="validateInfos.binding">
        <div class="flex">
          <Select v-model:value="modelRef.binding" :options="bindingList" />
          <Tooltip>
            <template #title>
              这是LwM2M服务器对象的\"绑定\"资源列表 -/1/x/7。<br />
              表示LwM2M客户端中支持的绑定模式。<br />
              此值应与设备对象(/3/0/16)中的\"支持的绑定和模式\"资源。<br />
              虽然支持多个传输但在整个传输会话期间只能使用一个传输绑定。<br />
              例如：当UDP和SMS都受支持，LwM2M客户端和LwM2M服务器可以选择在整个传输会话期间通过UDP或SMS进行通信。
            </template>
            <question-circle-outlined />
          </Tooltip>
        </div>
      </FormItem>
      <FormItem label="">
        <Checkbox v-model:checked="modelRef.notifIfDisabled"> 禁用或离线时通知存储 </Checkbox>
      </FormItem>
    </FormItem>
  </Form>
</template>

<script setup lang="ts">
  import { Form, FormItem, Row, Col, Input, Select, Checkbox, Tooltip } from 'ant-design-vue';
  import { reactive, defineProps } from 'vue';
  import { QuestionCircleOutlined } from '@ant-design/icons-vue';

  const useForm = Form.useForm;

  enum Lwm2mSecurityType {
    PSK = 'PSK',
    RPK = 'RPK',
    X509 = 'X509',
    NO_SEC = 'NO_SEC',
  }
  const securityModeList = reactive([
    { label: 'Pre-Shared Key', value: Lwm2mSecurityType.PSK },
    { label: 'Raw Public Key', value: Lwm2mSecurityType.RPK },
    { label: 'X.509 Certificate', value: Lwm2mSecurityType.X509 },
    { label: 'No Security', value: Lwm2mSecurityType.NO_SEC },
  ]);

  const props = defineProps({
    defaultShortServerId: {
      type: String,
      default: '123',
    },
  });

  enum BindingType {
    U = 'U',
    M = 'M',
    H = 'H',
    T = 'T',
    S = 'S',
    N = 'N',
    UQ = 'UQ',
    UQS = 'UQS',
    TQ = 'TQ',
    TQS = 'TQS',
    SQ = 'SQ',
  }
  const bindingList = reactive([
    { label: 'U: 客户端通过UDP绑定。', value: BindingType.U },
    { label: 'M: 客户端通过MQTT绑定。', value: BindingType.M },
    { label: 'H: 客户端通过HTTP绑定。', value: BindingType.H },
    { label: 'T: 客户端通过TCP绑定。', value: BindingType.T },
    { label: 'S: 客户端通过SMS绑定。', value: BindingType.S },
    { label: 'N: 客户端通过非IP绑定将响应发送到请求（支持LWM2M1.1）。', value: BindingType.N },
    { label: 'UQ: 通过UDP队列模式连接（不支持LWM2M 1.1）。', value: BindingType.UQ },
    { label: 'UQS: 通过UDP和SMS活动连接（不支持LWM2M 1.1）。', value: BindingType.UQS },
    { label: 'TQ: 通过TCP队列模式连接（不支持LWM2M 1.1）。', value: BindingType.TQ },
    { label: 'TQS: 通过TCP和SMS活动连接（不支持LWM2M 1.1）。', value: BindingType.TQS },
    { label: 'SQ: 通过队列模式的SMS连接（不支持LWM2M 1.1）。', value: BindingType.SQ },
  ]);
  const modelRef = reactive({
    securityMode: Lwm2mSecurityType.NO_SEC,
    shortServerId: props.defaultShortServerId,
    host: '0.0.0.0',
    port: '5686',
    clientHoldOffTime: '1',
    bootstrapServerAccountTimeout: '0',
    serverPublicKey: '',
    lifetime: '300',
    defaultMinPeriod: '1',
    binding: BindingType.U,
    notifIfDisabled: true,
  });
  const rulesRef = reactive({
    shortServerId: [{ required: true, message: '请输入服务器ID', trigger: ['blur', 'change'] }],
    host: [{ required: true, message: '请输入主机', trigger: ['blur', 'change'] }],
    port: [{ required: true, message: '请输入端口', trigger: ['blur', 'change'] }],
    clientHoldOffTime: [{ required: true, message: '请输入停留时间', trigger: ['blur', 'change'] }],
    bootstrapServerAccountTimeout: [
      { required: true, message: '请输入账户超时', trigger: ['blur', 'change'] },
    ],
    serverPublicKey: [{ required: true, message: '请输入服务器公钥', trigger: ['blur', 'change'] }],
    lifetime: [
      { required: true, message: '请输入客户端注册生命周期', trigger: ['blur', 'change'] },
    ],
    defaultMinPeriod: [{ required: true, message: '请输入最小期限', trigger: ['blur', 'change'] }],
  });
  const { validateInfos } = useForm(modelRef, rulesRef);
</script>

<style lang="less" scoped>
  .delIcon {
    margin-top: 5px;
  }

  .flex {
    display: flex;
    align-items: center;

    .ant-input {
      margin-right: 5px;
    }
  }

  .ant-form-item {
    margin-bottom: 10px;
  }
</style>
