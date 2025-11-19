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
          <FormItem label="包版本号" name="version" v-bind=validateInfos.version>
            <Input v-model:value="modelRef.version"/>
          </FormItem>
          <FormItem label="包名称" name="name" v-bind=validateInfos.name>
            <Input v-model:value="modelRef.name"/>
          </FormItem>
          <FormItem label="包类型" name="type" v-bind=validateInfos.type>
            <Select
              placeholder="包类型"
              :options="state.typeList"
              @change="handleTypeCLickChange"
              v-model:value="modelRef.type"
              allowClear
            />
          </FormItem>
          <FormItem label="包位置" name="url" v-bind=validateInfos.url>
            <Upload
              name="file"
              multiple
              @change="handleFileChange"
              :action="state.updateUrl"
              :headers="headers"
              :showUploadList="true"
              accept="*"
              :disabled="state.isView"
            >
              <a-button type="primary">
                {{ t('component.upload.choose') }}
              </a-button>
            </Upload>
          </FormItem>
          <FormItem label="关键版本" name="type" v-bind=validateInfos.keyVersionFlag>
            <Select
              placeholder="关键版本"
              :options="state.keyVersionFlagList"
              @change="handleKeyVersionFlagCLickChange"
              v-model:value="modelRef.keyVersionFlag"
              allowClear
            />
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
import {computed, reactive, ref} from 'vue';
import {BasicModal, useModalInner} from '@/components/Modal';
import {Form, FormItem, Input, Select, Spin, Textarea, Upload,} from 'ant-design-vue';
import {useMessage} from '@/hooks/web/useMessage';
import {getDeviceProfiles} from "@/api/device/product";
import {addOtaApp, fetchPkgList, updateOtaApp} from "@/api/device/ota";
import {useI18n} from "@/hooks/web/useI18n";
import {useUserStoreWithOut} from "@/store/modules/user";
import {useGlobSetting} from "@/hooks/setting";

const {t} = useI18n()

defineOptions({name: 'OtaVersionModal'})

const {createMessage} = useMessage();

const userStore = useUserStoreWithOut();
const token = userStore.getAccessToken;
const headers = ref({'Authorization': `Bearer ${token}`});
const {uploadUrl} = useGlobSetting();

const state = reactive({
  updateUrl: `${uploadUrl}/packages/upload-package`,
  fileId: '',
  typeList: [
    {label: "软件包", value: '0'},
    {label: "固件包", value: '1'},
  ],
  keyVersionFlagList: [
    {label: "否", value: 0},
    {label: "是", value: 1},
  ],
  appPackageList: [],
  osPackageList: [],
  productList: [],
  upgradeModeList: [
    {label: "非强制升级", value: 0},
    {label: "强制升级", value: 1},
  ],
  record: null,
  isEdit: false,
  isView: false,
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
  upgradeMode: 0,
  remark: '',
  productIdentification: '',
  version: '',
  name: '',
  type: '0',
  keyVersionFlag: 0,
  url: '',
});

const getTitle = computed(() => (state.isEdit ? '编辑OTA升级包' : state.isView ? '查看OTA升级包' : '新增OTA升级包'));

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

function handleFileChange(info: Record<string, any>) {
  const file = info.file;
  const status = file?.status;
  const response = file?.response;
  if (status === 'done') {
    createMessage.success('上传成功');
    modelRef.url = response.data;
  }
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

function handleTypeCLickChange(value) {
  //console.log('handleCLickChange', value)
}

function handleKeyVersionFlagCLickChange(value) {
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
  validate().then(async () => {
    let api = addOtaApp;
    if (modelRef?.id) {
      api = updateOtaApp;
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
