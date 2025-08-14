<template>
  <div class="mqttConfig">
    <Form :model="validateInfos" :colon="false">
      <!--      <CommonCard title="MQTT 设备 Topic 筛选器" class="commonCard">-->
      <!--        <Row :gutter="24">-->
      <!--          <Col :span="12">-->
      <!--            <FormItem label="遥测数据 topic 筛选器" v-bind="validateInfos.deviceTelemetryTopic">-->
      <!--              <Input-->
      <!--                placeholder="请输入遥测数据 topic 筛选器"-->
      <!--                v-model:value="modelRef.deviceTelemetryTopic"-->
      <!--              />-->
      <!--            </FormItem>-->
      <!--          </Col>-->
      <!--          <Col :span="12">-->
      <!--            <FormItem label="Attributes topic filter" v-bind="validateInfos.deviceAttributesTopic">-->
      <!--              <Input-->
      <!--                placeholder="请输入Attributes topic filter"-->
      <!--                v-model:value="modelRef.deviceAttributesTopic"-->
      <!--              />-->
      <!--            </FormItem>-->
      <!--          </Col>-->
      <!--        </Row>-->
      <!--        <div class="commonCard__tip">-->
      <!--          <div>支持单<code>[+]</code>和多级<code>[#]</code>通配符。</div>-->
      <!--          <div-->
      <!--            ><code>[+]</code> is suitable for any topic filter level。例如：<b-->
      <!--              >v1/devices/+/telemetry</b-->
      <!--            >-->
      <!--            or <b>+/devices/+/attributes</b>。</div-->
      <!--          >-->
      <!--          <div-->
      <!--            ><code>[#]</code>可以替换 topic filter 本身，并且必须是 topic 的最后一个符号。例如：<b-->
      <!--              >#</b-->
      <!--            >-->
      <!--            or <b>v1/devices/me/#</b>。</div-->
      <!--          >-->
      <!--        </div>-->
      <!--      </CommonCard>-->

      <!--      <CommonCard title="MQTT 设备 Payload" class="commonCard">-->
      <!--        <FormItem label=" ">-->
      <!--          <Select-->
      <!--            v-model:value="modelRef.transportPayloadTypeConfiguration.transportPayloadType"-->
      <!--            :options="payloadList"-->
      <!--            allowClear-->
      <!--          />-->
      <!--        </FormItem>-->
      <!--        <FormItem-->
      <!--          label=" "-->
      <!--          v-if="modelRef.transportPayloadTypeConfiguration.transportPayloadType === 'PROTOBUF'"-->
      <!--        >-->
      <!--          <Checkbox-->
      <!--            v-model:checked="-->
      <!--              modelRef.transportPayloadTypeConfiguration.enableCompatibilityWithJsonPayloadFormat-->
      <!--            "-->
      <!--            >启用与其他payload格式兼容。</Checkbox-->
      <!--          >-->
      <!--          <div class="checkTip"-->
      <!--            >启用后平台将默认使用Protobuf的payload格式，如果解析失败平台将尝试使用JSON的payload格式。对于固件更新期间的向后兼容性很有用，例如固件的初始版本使用Json而新版本使用Protobuf在设备队列的固件更新过程中，需要同时支持Protobuf和JSON。兼容模式会导致一点的性能下降，因此建议在所有设备更新后禁用此模式。</div-->
      <!--          >-->
      <!--        </FormItem>-->
      <!--        <FormItem-->
      <!--          label=" "-->
      <!--          v-if="-->
      <!--            modelRef.transportPayloadTypeConfiguration.transportPayloadType === 'PROTOBUF' &&-->
      <!--            modelRef.transportPayloadTypeConfiguration.enableCompatibilityWithJsonPayloadFormat-->
      <!--          "-->
      <!--        >-->
      <!--          <Checkbox-->
      <!--            v-model:checked="-->
      <!--              modelRef.transportPayloadTypeConfiguration-->
      <!--                .useJsonPayloadFormatForDefaultDownlinkTopics-->
      <!--            "-->
      <!--            >启用与其他payload格式兼容。</Checkbox-->
      <!--          >-->
      <!--          <div class="checkTip"-->
      <!--            >启用后平台将使用Json的playload格式通过以下主题推送属性和RPC：<b>v1/devices/me/attributes/response/$request_id</b>、<b-->
      <!--              >v1/devices/me/attributes </b-->
      <!--            >、<b>v1/devices/me/rpc/request/$request_id</b>、<b>v1/devices/me/rpc/response/$request_id</b>。此设置不会影响使用新(v2)主题发送的属性和rpc订阅：<b>v2/a/res/$request_id</b>、<b>v2/a</b>、<b-->
      <!--              >v2/r /req/$request_id</b-->
      <!--            >，<b>v2/r/res/$request_id</b>。其中<b>$request_id</b>是一个整数请求标识符。</div-->
      <!--          >-->
      <!--        </FormItem>-->
      <!--        <div v-if="modelRef.transportPayloadTypeConfiguration.transportPayloadType === 'PROTOBUF'">-->
      <!--          <FormItem class="schema">-->
      <!--            <template #label>遥测数据 proto schema</template>-->
      <!--            <CodeEditor-->
      <!--              v-model:value="modelRef.transportPayloadTypeConfiguration.deviceTelemetryProtoSchema"-->
      <!--            />-->
      <!--          </FormItem>-->
      <!--          <FormItem class="schema">-->
      <!--            <template #label>Attributes proto schema</template>-->
      <!--            <CodeEditor-->
      <!--              v-model:value="modelRef.transportPayloadTypeConfiguration.deviceAttributesProtoSchema"-->
      <!--            />-->
      <!--          </FormItem>-->
      <!--          <FormItem class="schema">-->
      <!--            <template #label>RPC 请求 proto schema</template>-->
      <!--            <CodeEditor-->
      <!--              v-model:value="modelRef.transportPayloadTypeConfiguration.deviceRpcRequestProtoSchema"-->
      <!--            />-->
      <!--          </FormItem>-->
      <!--          <FormItem class="schema">-->
      <!--            <template #label>RPC 响应 proto schema</template>-->
      <!--            <CodeEditor-->
      <!--              v-model:value="-->
      <!--                modelRef.transportPayloadTypeConfiguration.deviceRpcResponseProtoSchema-->
      <!--              "-->
      <!--            />-->
      <!--          </FormItem>-->
      <!--        </div>-->
      <!--      </CommonCard>-->
      <Checkbox v-model:checked="modelRef.sendAckOnValidationException"
      >发布消息验证失败时发送PUBACK
      </Checkbox
      >
      <div class="checkTip"
      >默认情况下平台将关闭相关消息验证失败的MQTT会话，启用后平台将发布确认而不是关闭会话。
      </div
      >
    </Form>
  </div>
</template>

<script setup lang="ts">
import {defineExpose, defineProps, reactive} from 'vue';
import {
  defaultAttributesSchema,
  defaultRpcRequestSchema,
  defaultRpcResponseSchema,
  defaultTelemetrySchema,
} from './protoSchema.ts';
import {Checkbox, Form} from 'ant-design-vue';
// import { CommonCard } from '@/components/Card';

const useForm = Form.useForm;

defineExpose({
  getTransferConfigFormData,
});
const props = defineProps({
  type: {
    type: String,
  },
});

enum PayloadType {
  JSON = 'JSON',
  PROTOBUF = 'PROTOBUF',
}

const payloadList = reactive([
  {label: 'Json', value: PayloadType.JSON},
  {label: 'Protobuf', value: PayloadType.PROTOBUF},
]);

const modelRef = reactive({
  type: props.type,
  deviceTelemetryTopic: 'v1/devices/me/telemetry',
  deviceAttributesTopic: 'v1/devices/me/attributes',
  sendAckOnValidationException: false,
  transportPayloadTypeConfiguration: {
    transportPayloadType: PayloadType.JSON,
    enableCompatibilityWithJsonPayloadFormat: false,
    useJsonPayloadFormatForDefaultDownlinkTopics: false,
    deviceTelemetryProtoSchema: defaultTelemetrySchema,
    deviceAttributesProtoSchema: defaultAttributesSchema,
    deviceRpcRequestProtoSchema: defaultRpcRequestSchema,
    deviceRpcResponseProtoSchema: defaultRpcResponseSchema,
  },
});

const rulesRef = reactive({
  deviceTelemetryTopic: [
    {required: true, message: '请输入遥测数据 topic 筛选器', trigger: ['blur', 'change']},
  ],
  deviceAttributesTopic: [
    {required: true, message: '请输入Attributes topic filter', trigger: ['blur', 'change']},
  ],
});
const {validate, validateInfos} = useForm(modelRef, rulesRef);

async function getTransferConfigFormData() {
  await validate();
  return modelRef;
}
</script>

<style lang="less" scoped>
.MqttConfig {
  .commonCard {
    margin-bottom: 20px;

    .ant-form-item {
      margin-bottom: 0;
    }

    &__tip {
      margin-top: 12px;
    }
  }

  .schema {
    margin-top: 15px;
  }

  .checkTip {
    font-size: 12px;
  }
}
</style>
