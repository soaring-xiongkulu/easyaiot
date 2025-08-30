<template>
  <BasicModal
    @register="register"
    :title="getTitle"
    @cancel="handleCancel"
    :width="700"
    @ok="handleOk"
    :canFullscreen="false"
  >
    <div class="product-modal">
      <Spin :spinning="state.editLoading">
        <Form
          :labelCol="{ span: 3 }"
          :model="validateInfos"
          :wrapperCol="{ span: 21 }"
        >
          <FormItem label="设备名称" name="name" v-bind=validateInfos.name>
            <Input v-model:value="modelRef.name"/>
          </FormItem>
          <FormItem label="码流索引" name="stream" v-bind=validateInfos.stream>
            <Select
              placeholder="码流索引"
              :options="state.streamList"
              @change="handleCLickChange"
              v-model:value="modelRef.stream"
              allowClear
            />
          </FormItem>
          <FormItem label="用户名" name="username" v-bind=validateInfos.userName>
            <Input v-model:value="modelRef.username"/>
          </FormItem>
          <FormItem label="密码" name="password" v-bind="validateInfos.password">
            <Input.Password v-model:value="modelRef.password" />
          </FormItem>
        </Form>
      </Spin>
    </div>
  </BasicModal>
</template>
<script lang="ts" setup>
import {computed, reactive, ref} from 'vue';
import {BasicModal, useModalInner} from '@/components/Modal';
import {Form, FormItem, Input, Select, Spin,} from 'ant-design-vue';

defineOptions({name: 'VideoRegisterModal'})

const state = reactive({
  record: null,
  editLoading: false,
  streamList: [
    {label: "主码流", value: 0},
    {label: "子码流", value: 1},
  ],
});

const modelRef = reactive({
  name: '',
  stream: 0,
  username: '',
  password: '',
});

const getTitle = computed(() => ('注册设备'));

const [register, {closeModal}] = useModalInner((data) => {
  const {record} = data;
  state.record = record;
});

const emits = defineEmits(['success']);

const checkedKeys = ref<Array<string>>([]);

function onSelect(record, selected) {
  if (selected) {
    checkedKeys.value = [...checkedKeys.value, record.ip];
  } else {
    checkedKeys.value = checkedKeys.value.filter((ip) => ip !== record.ip);
  }
}

function onSelectAll(selected, selectedRows, changeRows) {
  const changeIds = changeRows.map((item) => item.ip);
  if (selected) {
    checkedKeys.value = [...checkedKeys.value, ...changeIds];
  } else {
    checkedKeys.value = checkedKeys.value.filter((ip) => {
      return !changeIds.includes(ip);
    });
  }
}

const rulesRef = reactive({
  deviceVersion: [{required: true, message: '请输入视频设备号', trigger: ['change']}],
});

function handleCLickChange(value) {
  //console.log('handleCLickChange', value)
}

const useForm = Form.useForm;
const {validate, resetFields, validateInfos} = useForm(modelRef, rulesRef);

function handleCancel() {
  //console.log('handleCancel');
  resetFields();
}

function handleOk() {
  // alert(JSON.stringify(modelRef));
  emits('success', {...modelRef, ...state.record});
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
