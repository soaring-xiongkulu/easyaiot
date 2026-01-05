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
          :disabled="state.isView"
        >
          <FormItem label="设备版本号" name="deviceVersion" v-bind=validateInfos.deviceVersion>
            <Input v-model:value="modelRef.deviceVersion"/>
          </FormItem>
          <FormItem label="所属产品" name="appPkgId" v-bind=validateInfos.appPkgId>
            <Select
              placeholder="所属产品"
              :options="state.productList"
              @change="handleProductCLickChange"
              v-model:value="modelRef.productIdentification"
              allowClear
            />
          </FormItem>
          <FormItem label="软件包" name="appPkgId" v-bind=validateInfos.appPkgId>
            <Select
              placeholder="软件包"
              :options="state.appPackageList"
              @change="handleAppCLickChange"
              v-model:value="modelRef.appPkgId"
              allowClear
            />
          </FormItem>
          <FormItem label="固件包" name="osPkgId" v-bind=validateInfos.osPkgId>
            <Select
              placeholder="固件包"
              :options="state.osPackageList"
              @change="handleOsCLickChange"
              v-model:value="modelRef.osPkgId"
              allowClear
            />
          </FormItem>
          <FormItem label="升级方式" name="upgradeMode" v-bind=validateInfos.upgradeMode>
            <Select
              placeholder="升级方式"
              :options="state.upgradeModeList"
              @change="handleMethodCLickChange"
              v-model:value="modelRef.upgradeMode"
              allowClear
            />
          </FormItem>
          <FormItem label="升级描述" name="remark" v-bind=validateInfos.remark>
            <Textarea
              placeholder="请输入升级描述"
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
import {computed, reactive} from 'vue';
import {BasicModal, useModalInner} from '@/components/Modal';
import {Form, FormItem, Input, Select, Spin, Textarea,} from 'ant-design-vue';
import {useMessage} from '@/hooks/web/useMessage';
import {getDeviceProfiles} from "@/api/device/product";
import {addVersion, fetchPkgList, updateVersion} from "@/api/device/ota";

defineOptions({name: 'VideoModal'})

const {createMessage} = useMessage();

const state = reactive({
  isEdit: false,
  isView: false,
  appPackageList: [],
  osPackageList: [],
  productList: [],
  upgradeModeList: [
    {label: "非强制升级", value: 0},
    {label: "强制升级", value: 1},
  ],
  record: null,
  fileList: [],
  loading: false,
  editLoading: false,
  defaultRule: [],
  defaultRuleParams: {
    pageSize: 30,
    page: 1,
    total: 0,
  },
  productTemplateList: [],
  defaultQueue: [],
  defaultQueueParams: {
    pageSize: 30,
    page: 1,
    total: 0,
  },
});

const modelRef = reactive({
  id: '',
  deviceVersion: '',
  osPkgId: '',
  appPkgId: '',
  upgradeMode: 0,
  remark: '',
  productIdentification: '',
});

const getTitle = computed(() => (state.isEdit ? '编辑设备版本' : state.isView ? '查看设备版本' : '新增设备版本'));

async function initAppList() {
  state.appPackageList = [];
  const record = await fetchPkgList({type: 0, pageNo: 1, pageSize: 100});
  state.appPackageList = state.appPackageList.concat(
    record.data.map((item) => {
      item.value = item.id;
      item.label = item.name;
      return item;
    }),
  );
}

async function initOsList() {
  state.osPackageList = [];
  const record = await fetchPkgList({type: 1, pageNo: 1, pageSize: 100});
  state.osPackageList = state.osPackageList.concat(
    record.data.map((item) => {
      item.value = item.id;
      item.label = item.name;
      return item;
    }),
  );
}

async function initProductList() {
  state.productList = [];
  const record = await getDeviceProfiles({page: 1, pageSize: 100});
  state.productList = state.productList.concat(
    record.data.map((item) => {
      item.value = item.productIdentification;
      item.label = item.productName;
      return item;
    }),
  );
}

const [register, {closeModal}] = useModalInner((data) => {
  const {isEdit, isView, record} = data;
  state.isEdit = isEdit;
  state.isView = isView;
  if (state.isEdit || state.isView) {
    productEdit(record);
  }
  initAppList();
  initOsList();
  initProductList();
});

const emits = defineEmits(['success']);

const rulesRef = reactive({
  deviceVersion: [{required: true, message: '请输入设备版本号', trigger: ['change']}],
});

const useForm = Form.useForm;
const {validate, resetFields, validateInfos} = useForm(modelRef, rulesRef);

function handleAppCLickChange(value) {
  //console.log('handleCLickChange', value)
}

function handleOsCLickChange(value) {
  //console.log('handleCLickChange', value)
}

function handleProductCLickChange(value) {
  //console.log('handleCLickChange', value)
}

function handleMethodCLickChange(value) {
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

function handleOk() {//alert(modelRef?.id);
  validate().then(async () => {
    let api = addVersion;
    if (modelRef?.id) {
      api = updateVersion;
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
