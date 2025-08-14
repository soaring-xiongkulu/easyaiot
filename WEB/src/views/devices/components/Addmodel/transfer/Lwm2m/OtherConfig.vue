<template>
  <div class="coAPConfig">
    <Form :model="validateInfos" :colon="false">
<!--      <CommonCard title="固件升级" class="commonCard">-->
<!--        <FormItem label="固件升级策略">-->
<!--          <Select-->
<!--            v-model:value="modelRef.coapDeviceTypeConfiguration.coapDeviceType"-->
<!--            :options="coapList"-->
<!--          />-->
<!--        </FormItem>-->
<!--      </CommonCard>-->

<!--      <CommonCard title="软件更新" class="commonCard">-->
<!--        <FormItem label="软件更新策略">-->
<!--          <Select-->
<!--            v-model:value="-->
<!--              modelRef.coapDeviceTypeConfiguration.transportPayloadModeConfiguration-->
<!--                .transportPayloadMode-->
<!--            "-->
<!--            :options="payloadList"-->
<!--          />-->
<!--        </FormItem>-->
<!--      </CommonCard>-->
<!--      <CommonCard title="节能模式" class="commonCard">-->
<!--        <FormItem label=" ">-->
<!--          <Select v-model:value="modelRef.clientSettings.powerMode" :options="powerList" />-->
<!--        </FormItem>-->
<!--      </CommonCard>-->
    </Form>
  </div>
</template>

<script setup lang="ts">
  import { ref, reactive, defineExpose, defineProps } from 'vue';
  import { Form, FormItem, Select } from 'ant-design-vue';
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

  enum PayloadMode {
    JSON = 'Json',
    PROTOBUF = 'Protobuf',
  }

  const payloadList = reactive([
    { label: PayloadMode.JSON, value: PayloadMode.JSON },
    { label: PayloadMode.PROTOBUF, value: PayloadMode.PROTOBUF },
  ]);
  enum CoapMode {
    DEFAULT = 'DEFAULT',
    EFENTO = 'EFENTO',
  }

  const coapList = reactive([
    { label: '默认', value: CoapMode.DEFAULT },
    { label: 'Efento NB-IoT', value: CoapMode.EFENTO },
  ]);

  enum PowerMode {
    PSM = 'PSM',
    DRX = 'DRX',
    E_DRX = 'E_DRX',
  }
  const powerList = reactive([
    { label: '节能模式(PSM)', value: PowerMode.PSM },
    { label: '非连续接收(DRX)', value: PowerMode.DRX },
    { label: '连续接收(eDRX)', value: PowerMode.E_DRX },
  ]);

  const modelRef = reactive({
    type: props.type,
    clientSettings: {
      powerMode: PowerMode.DRX,
    },
    coapDeviceTypeConfiguration: {
      coapDeviceType: CoapMode.DEFAULT,
      transportPayloadModeConfiguration: {
        transportPayloadMode: PayloadMode.JSON,
      },
    },
  });
  const { validateInfos } = useForm(modelRef);
  const protoSchemaRef = ref();
  async function getTransferConfigFormData() {
    const tempTransportPayloadModeConfiguration =
      modelRef.coapDeviceTypeConfiguration.transportPayloadModeConfiguration;
    if (tempTransportPayloadModeConfiguration.transportPayloadMode === PayloadMode.PROTOBUF) {
      const tempResult = await protoSchemaRef.value.getProtoSchemaFormData();
      modelRef.coapDeviceTypeConfiguration.transportPayloadModeConfiguration = Object.assign(
        tempTransportPayloadModeConfiguration,
        tempResult,
      );
    }
    return modelRef;
  }
</script>

<style lang="less" scoped>
  .coAPConfig {
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
