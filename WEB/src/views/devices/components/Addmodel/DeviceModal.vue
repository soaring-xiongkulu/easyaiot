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
          <FormItem label="设备SN" name="deviceSn" v-bind=validateInfos.deviceSn>
            <Input v-model:value="modelRef.deviceSn" />
          </FormItem>
          <FormItem label="应用场景" name="appId" v-bind=validateInfos.appId>
            <Input v-model:value="modelRef.appId" />
          </FormItem>
          <FormItem label="设备名称" name="deviceName" v-bind=validateInfos.deviceName>
            <Input v-model:value="modelRef.deviceName" />
          </FormItem>
          <FormItem label="所属产品" name="productIdentification" v-bind=validateInfos.productIdentification>
            <Select
              placeholder="所属产品"
              :options="state.productList"
              @change="handleCLickChange"
              v-model:value="modelRef.productIdentification"
              allowClear
            />
          </FormItem>
          <FormItem label="设备描述" name="deviceDescription" v-bind=validateInfos.deviceDescription>
            <Input v-model:value="modelRef.deviceDescription" />
          </FormItem>
          <FormItem label="备注" name="remark" v-bind=validateInfos.remark>
            <Textarea
              placeholder="请输入备注"
              v-model:value="modelRef.remark"
              :maxlength="200"
              :rows="3"
              showCount
            />
          </FormItem>
        </Form>
      </Spin>
    </div>
  </BasicModal>
</template>
<script lang="ts" setup>
import {computed, onMounted, reactive} from 'vue';
import {BasicModal, useModalInner} from '@/components/Modal';
import {Form, FormItem, Input, Select, Spin, Textarea,} from 'ant-design-vue';
import {useMessage} from '@/hooks/web/useMessage';
import {getDeviceProfiles} from "@/api/device/product";
import {saveDevices, updateDevices} from "@/api/device/devices";

const { createMessage } = useMessage();

const state = reactive({
  productList: [],
  record: null,
  productType: true,
  fileList: [],
  loading: false,
  editLoading: false,
  defaultRule: [],
  defaultRuleParams: {
    pageSize: 30,
    page: 1,
    total: 0,
  },
  productTemplateList : [],
  defaultQueue: [],
  defaultQueueParams: {
    pageSize: 30,
    page: 1,
    total: 0,
  },
});

const modelRef = reactive({
  id :'',
  deviceSn: '',
  appId: '',
  deviceName: '',
  productIdentification: '',
  deviceDescription: '',
  remark: '',
});

const getTitle = computed(() => (state.productType ? '新增产品' : '编辑产品'));

onMounted(() => {
  initProductList();
})

async function initProductList(){
  const record = await getDeviceProfiles({page: 1, pageSize: 100});
  state.productList = state.productList.concat(
    record.data.map((item) => {
      item.value = item.productIdentification;
      item.label = item.productName;
      return item;
    }),
  );
}

const [register, { closeModal }] = useModalInner((data) => {
  const { type, record } = data;
  state.productType = type;

  !type && productEdit(record);
});

const emits = defineEmits(['success']);

const rulesRef = reactive({
  deviceSn: [{ required: true, message: '请输入设备SN', trigger: ['change'] }],
  appId: [{ required: true, message: '请输入应用场景', trigger: ['change'] }],
  deviceName: [{ required: true, message: '请输入设备名称', trigger: ['change'] }],
  productIdentification: [{ required: true, message: '请选择所属产品', trigger: ['change'] }],
});

const useForm = Form.useForm;
const { validate, resetFields, validateInfos } = useForm(modelRef, rulesRef);

function handleCLickChange(value) {
  //console.log('handleCLickChange', value)
}

async function productEdit(record) {
  try {
    state.editLoading = true;
    Object.keys(modelRef).forEach((item) => {
      modelRef[item] = record[item];
    });
    state.editLoading = false;
    state.record = record;
  }catch (error) {
    console.error(error)
    //console.log('productEdit ...', error);
  }
}

function handleCancel() {
  //console.log('handleCancel');
  resetFields();
}

function handleOk() {
  //alert(modelRef?.id);
  validate().then(async () => {
    let api = saveDevices;
    if (modelRef?.id) {
      api = updateDevices;
    }
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
