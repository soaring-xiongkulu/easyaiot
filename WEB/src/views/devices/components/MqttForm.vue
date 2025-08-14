<template>
  <Form :model="validateInfos" :colon="false">
    <FormItem label="客户端ID" v-bind="validateInfos.clientId">
      <Input placeholder="请输入" v-model:value="modelRef.clientId"/>
    </FormItem>
    <FormItem label="用户名" v-bind="validateInfos.userName">
      <Input placeholder="请输入" v-model:value="modelRef.userName"/>
    </FormItem>
    <FormItem label="密码" v-bind="validateInfos.password">
      <Input placeholder="请输入" type="password" v-model:value="modelRef.password"/>
    </FormItem>
  </Form>
</template>
<script setup lang="ts">
import {defineExpose, defineProps, onMounted, reactive} from 'vue';
import {Form, FormItem, Input} from 'ant-design-vue';

const useForm = Form.useForm;
defineExpose({
  handleSubmit,
});

const props = defineProps({
  formData: {
    type: String,
    default: '',
  },
});

onMounted(() => {
  props.formData && fetchData();
});

function fetchData() {
  //console.log(props.formData);
  const info = JSON.parse(props.formData);
  const tempForm = Object.keys(info).map((attributeName) => {
    return {
      value: info[attributeName],
      label: attributeName,
    };
  });
  tempForm.forEach((item) => {
    //console.log('item', item);
    modelRef[item.label] = item.value;
  });
}

const modelRef = reactive({
  clientId: '',
  userName: '',
  password: '',
});
const rulesRef = reactive({
  clientId: [{required: true, message: '请输入用户端ID', trigger: 'blur'}],
  userName: [{required: true, message: '请输入用户名', trigger: 'blur'}],
});

const {resetFields, validate, validateInfos} = useForm(modelRef, rulesRef);

async function handleSubmit() {
  await validate();
  return JSON.stringify(modelRef);
}

clearForm();

function clearForm() {
  resetFields();
}
</script>
