<template>
  <div class="snmpConfig">
    <Form :model="validateInfos" :colon="false">
      <Row :gutter="24">
        <Col :span="12">
          <FormItem label="超时（ms）" v-bind="validateInfos.timeoutMs">
            <Input
              type="number"
              placeholder="请输入超时（ms）"
              v-model:value="modelRef.timeoutMs"
            />
          </FormItem>
        </Col>
        <Col :span="12">
          <FormItem label="重试" v-bind="validateInfos.retries">
            <Input type="number" placeholder="请输入重试" v-model:value="modelRef.retries" />
          </FormItem>
        </Col>
      </Row>
      <FormItem>
        <template #label>通信配置</template>
        <div class="warnText" v-if="modelRef.communicationConfigsSpecs.length === 0">
          请添加通信配置
        </div>
        <div
          v-for="item in modelRef.communicationConfigsSpecs.length"
          :key="item"
          class="snmpConfig__communicationConfigsSpecs"
        >
          <CommConfig
            ref="commConfigRef"
            v-model:value="modelRef.communicationConfigsSpecs[item - 1]"
            :communicationConfigsSpecs="modelRef.communicationConfigsSpecs"
            :specMap="specMap"
          />
          <MinusCircleOutlined @click="delCommunicationConfigsSpecs(item)" />
        </div>
        <Button
          @click="addCommunicationConfigsSpecs"
          v-if="modelRef.communicationConfigsSpecs.length < 4"
        >
          <PlusCircleOutlined />
          添加通信配置
        </Button>
      </FormItem>
    </Form>
  </div>
</template>

<script setup lang="ts">
  import { ref, reactive, defineExpose, defineProps } from 'vue';
  import { MinusCircleOutlined, PlusCircleOutlined } from '@ant-design/icons-vue';
  import { Form, FormItem, Row, Col, Button, Input } from 'ant-design-vue';
  import CommConfig from './CommConfig.vue';

  const useForm = Form.useForm;

  defineExpose({
    getTransferConfigFormData,
  });
  const props = defineProps({
    type: {
      type: String,
    },
  });
  enum SpecType {
    LATEST_TELEMETRY = 'LATEST_TELEMETRY',
    CLIENT_SCOPE = 'CLIENT_SCOPE',
    SERVER_SCOPE = 'SERVER_SCOPE',
    SHARED_SCOPE = 'SHARED_SCOPE',
  }
  const specMap = reactive([
    { label: 'Telemetry', value: SpecType.LATEST_TELEMETRY },
    { label: 'Client attributes', value: SpecType.CLIENT_SCOPE },
    { label: 'Shared attributes', value: SpecType.SERVER_SCOPE },
    { label: 'RPC request', value: SpecType.SHARED_SCOPE },
  ]);
  const modelRef = reactive({
    type: props.type,
    timeoutMs: '500',
    retries: '0',
    sendAckOnValidationException: false,
    communicationConfigs: [],
    communicationConfigsSpecs: [SpecType.CLIENT_SCOPE],
  });

  const rulesRef = reactive({
    timeoutMs: [{ required: true, message: '请输入超时（ms）', trigger: ['blur', 'change'] }],
    retries: [{ required: true, message: '请输入重试', trigger: ['blur', 'change'] }],
  });
  const { validate, validateInfos } = useForm(modelRef, rulesRef);

  function addCommunicationConfigsSpecs() {
    const tempComm = modelRef.communicationConfigsSpecs;
    if (tempComm.length === 0) {
      modelRef.communicationConfigsSpecs = [SpecType.LATEST_TELEMETRY];
    } else {
      const tempSpec = specMap.map((i) => i.value);
      const noneSelectSpec = tempSpec.filter((e) => !tempComm.some((e2) => e2 === e));
      modelRef.communicationConfigsSpecs.push(noneSelectSpec[0]);
    }
  }
  function delCommunicationConfigsSpecs(key) {
    modelRef.communicationConfigsSpecs.splice(key - 1, 1);
  }
  const commConfigRef = ref();
  async function getTransferConfigFormData() {
    await validate();
    modelRef.communicationConfigs = await Promise.all([
      ...commConfigRef.value.map((item) => item.getCommConfigFormData()),
    ]);
    return modelRef;
  }
</script>

<style lang="less" scoped>
  .snmpConfig {
    &__communicationConfigsSpecs {
      display: flex;
      align-items: center;
    }

    .warnText {
      color: #dd2c00;
      font-size: 18px;
      text-align: center;
    }
  }
</style>
