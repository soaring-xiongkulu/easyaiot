<template>
  <Form :model="validateInfos" :colon="false">
    <FormItem label="设备配置" v-bind="validateInfos.credentialsType">
      <Select
        placeholder="凭据类型"
        v-model:value="modelRef.credentialsType"
        :options="credentialsList"
        @change="handleCLickChange"
        allowClear
      />
    </FormItem>
    <FormItem
      label="访问令牌"
      v-show="modelRef.credentialsType === 'ACCESS_TOKEN'"
      v-bind="validateInfos.credentialsId"
    >
      <Input placeholder="请输入" v-model:value="modelRef.credentialsId"/>
    </FormItem>
    <FormItem
      label="PEM证书格式"
      v-show="modelRef.credentialsType === 'X509_CERTIFICATE'"
      v-bind="validateInfos.credentialsValue"
    >
      <Textarea placeholder="请输入" v-model:value="modelRef.credentialsValue"/>
    </FormItem>
    <mqtt-form
      v-if="modelRef.credentialsType === 'MQTT_BASIC'"
      ref="mqttFormRef"
      :formData="modelRef.credentialsValue"
    />
  </Form>
</template>
<script setup lang="ts">
import {defineExpose, reactive, ref} from 'vue';
import {Form, FormItem, Input, Select, Textarea} from 'ant-design-vue';
import {getDeviceCredentials} from '@/api/device/devices';
import MqttForm from './MqttForm.vue';

const useForm = Form.useForm;

defineExpose({
  fetchData,
  handleValidate,
});

const credentialsList = ref([
  {label: 'Access token', value: 'ACCESS_TOKEN'},
  {label: 'X.509', value: 'X509_CERTIFICATE'},
  {label: 'MQTT Basic', value: 'MQTT_BASIC'},
]);
const mqttFormRef = ref();

const modelRef = reactive({
  credentialsType: 'ACCESS_TOKEN',
  credentialsId: '',
  credentialsValue: '',
});
const checkCredentialsId = async (_rule, value: string) => {
  if (!value && modelRef.credentialsType === 'ACCESS_TOKEN') {
    return Promise.reject('请输入访问令牌');
  } else {
    return Promise.resolve();
  }
};
const checkCredentialsValue = async (_rule, value: string) => {
  if (!value && modelRef.credentialsType === 'X509_CERTIFICATE') {
    return Promise.reject('请输入PEM证书格式');
  } else {
    return Promise.resolve();
  }
};
const rulesRef = reactive({
  credentialsType: [{required: true, message: '请选择凭据类型', trigger: ['blur', 'change']}],
  credentialsId: [{required: true, validator: checkCredentialsId, trigger: ['blur', 'change']}],
  credentialsValue: [
    {required: true, validator: checkCredentialsValue, trigger: ['blur', 'change']},
  ],
});

const {resetFields, validate, validateInfos} = useForm(modelRef, rulesRef);

async function fetchData(id) {
  resetFields();
  const credentialsResult = await getDeviceCredentials(id);
  const tempForm = Object.keys(credentialsResult).map((attributeName) => {
    return {
      value: credentialsResult[attributeName],
      label: attributeName,
    };
  });
  tempForm.forEach((item) => {
    modelRef[item.label] = item.value;
  });
  // getDeviceProfileInfo(id);
  //console.log(getDeviceProfileInfo);
}

// 切换清空数据
function handleCLickChange() {
  modelRef.credentialsId = '';
  modelRef.credentialsValue = '';
}

async function handleValidate() {
  if (modelRef.credentialsType === 'MQTT_BASIC') {
    modelRef.credentialsValue = await mqttFormRef.value.handleSubmit();
  } else {
    await validate();
  }
  return modelRef;
}
</script>
