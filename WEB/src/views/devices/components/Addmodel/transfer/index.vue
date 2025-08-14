<template>
  <div class="transfer">
    <Form :model="validateInfos" :colon="false">
      <FormItem label="名称" v-bind="validateInfos.transportType">
        <Select v-model:value="modelRef.transportType" :options="transferList"/>
        <span>{{ transportTypeDescription.description }}</span>
      </FormItem>
    </Form>
    <component
      ref="componentRef"
      :type="modelRef.transportType"
      :is="transportTypeDescription.componentName"
    />
  </div>
</template>

<script setup lang="ts">
import {computed, defineExpose, reactive, ref} from 'vue';
import {Form, FormItem, Select} from 'ant-design-vue';
import Mqtt from './Mqtt.vue';
import Coap from './Coap.vue';
import Lwm2m from './Lwm2m/index.vue';
import Snmp from './Snmp.vue';

const useForm = Form.useForm;

defineExpose({
  getTransferFormData,
});

enum DeviceTransportType {
  DEFAULT = 'DEFAULT',
  MQTT = 'MQTT',
  COAP = 'COAP',
  LWM2M = 'LWM2M',
  SNMP = 'SNMP',
}

const transferList = reactive([
  {
    label: '默认',
    value: DeviceTransportType.DEFAULT,
    componentName: '',
    description: '支持基本MQTT、HTTP和CoAP传输',
  },
  {
    label: 'MQTT',
    value: DeviceTransportType.MQTT,
    componentName: Mqtt,
    description: '启用高级MQTT传输设置',
  },
  {
    label: 'COAP',
    value: DeviceTransportType.COAP,
    componentName: Coap,
    description: '启用高级 CoAP 传输设置',
  },
  {
    label: 'LWM2M',
    value: DeviceTransportType.LWM2M,
    componentName: Lwm2m,
    description: 'LWM2M传输类型',
  },
  {
    label: 'SNMP',
    value: DeviceTransportType.SNMP,
    componentName: Snmp,
    description: '指定 SNMP 传输配置',
  },
]);

const modelRef = reactive({
  // transportType: DeviceTransportType.DEFAULT,
  transportType: DeviceTransportType.LWM2M,
});
const transportTypeDescription = computed(() => {
  return transferList.filter((item) => item.value === modelRef.transportType)[0];
});

const rulesRef = reactive({
  type: [{required: true, message: '请选择', trigger: ['blur', 'change']}],
});
const {validateInfos} = useForm(modelRef, rulesRef);

const componentRef = ref();

async function getTransferFormData() {
  let tempData;
  if (componentRef.value.getTransferConfigFormData) {
    tempData = {
      profileData: {
        transportConfiguration: await componentRef.value.getTransferConfigFormData(),
      },
      transportType: modelRef.transportType,
    };
    return tempData;
  } else {
    const {transportType} = modelRef;
    return {
      transportType,
      profileData: {
        alarms: null,
        configuration: {type: 'DEFAULT'},
        provisionConfiguration: {type: 'DISABLED'},
        transportConfiguration: {
          type: transportType,
        },
      },
    };
  }
}
</script>

<style lang="less" scoped>
.transfer {
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
