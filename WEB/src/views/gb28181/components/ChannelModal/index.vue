<template>
  <BasicModal
    @register="register"
    title="编辑通道"
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
          <FormItem label="产品模板" name="templateIdentification"
                    v-bind=validateInfos.templateIdentification>
            <Select
              placeholder="产品模板"
              :options="state.productTemplateList"
              @change="handleCLickChange"
              v-model:value="modelRef.templateIdentification"
              allowClear
            />
          </FormItem>
          <FormItem label="应用场景" name="appId" v-bind=validateInfos.appId>
            <Input v-model:value="modelRef.appId"/>
          </FormItem>
          <FormItem label="产品名称" name="productName" v-bind=validateInfos.productName>
            <Input v-model:value="modelRef.productName"/>
          </FormItem>
          <FormItem label="产品类型" name="productType" v-bind=validateInfos.productType>
            <Select
              placeholder="产品类型"
              :options="productTypeList"
              @change="handleCLickChange"
              v-model:value="modelRef.productType"
              allowClear
            />
          </FormItem>
          <FormItem label="厂商ID" name="manufacturerId" v-bind=validateInfos.manufacturerId>
            <Input v-model:value="modelRef.manufacturerId"/>
          </FormItem>
          <FormItem label="厂商名称" name="manufacturerName"
                    v-bind=validateInfos.manufacturerName>
            <Input v-model:value="modelRef.manufacturerName"/>
          </FormItem>
          <FormItem label="产品型号" name="model" v-bind=validateInfos.model>
            <Input v-model:value="modelRef.model"/>
          </FormItem>
        </Form>
      </Spin>
    </div>
  </BasicModal>
</template>
<script lang="ts" setup>
import {reactive, ref} from 'vue';
import {BasicModal, useModalInner} from '@/components/Modal';
import {Form, FormItem, Input, Select, Spin,} from 'ant-design-vue';
import {useMessage} from '@/hooks/web/useMessage';
import {batchAddDeviceTestList, fetchWhiteGroupList, fetchWhiteList} from "@/api/device/ota";
import {useTable} from "@/components/Table";
import {getBasicColumns, getFormConfig} from "./Data";
import {useRoute} from "vue-router";
import {productTypeList} from "@/views/product/Data";

defineOptions({name: 'ChannelModal'})

const {createMessage} = useMessage();
const route = useRoute()

const state = reactive({
  groupList: [],
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
  groupId: '',
  deviceIdentification: '',
});

const checkedKeys = ref<Array<string | number>>([]);

const [
  registerTable, {reload}
] = useTable({
  canResize: false,
  showIndexColumn: false,
  title: '',
  api: fetchWhiteList,
  beforeFetch(params) {
    return {
      ...params,
      productIdentification: route.params.productIdentification,
      deviceIdentification: modelRef.deviceIdentification,
      groupId: modelRef.groupId,
    };
  },
  columns: getBasicColumns(),
  useSearchForm: false,
  showTableSetting: false,
  formConfig: getFormConfig(),
  fetchSetting: {
    listField: 'data',
    totalField: 'total',
  },
  rowSelection: {
    type: 'checkbox',
    selectedRowKeys: checkedKeys,
    onSelect: onSelect,
    onSelectAll: onSelectAll,
    getCheckboxProps(record) {
      if (record.default || record.referencedByDevice) {
        return {disabled: true};
      } else {
        return {disabled: false};
      }
    },
  },
  rowKey: 'deviceIdentification',
});

const [register, {closeModal}] = useModalInner((data) => {
  initGroupList();
});

const emits = defineEmits(['success']);

async function initGroupList() {
  state.groupList = [];
  const record = await fetchWhiteGroupList({
    pageNo: 1,
    pageSize: 100,
    productIdentification: route.params.productIdentification
  });
  state.groupList = state.groupList.concat(
    record.data.map((item) => {
      item.value = item.id;
      item.label = item.groupName;
      return item;
    }),
  );
}

function onSelect(record, selected) {
  if (selected) {
    checkedKeys.value = [...checkedKeys.value, record.deviceIdentification];
  } else {
    checkedKeys.value = checkedKeys.value.filter((deviceIdentification) => deviceIdentification !== record.deviceIdentification);
  }
}

function onSelectAll(selected, selectedRows, changeRows) {
  const changeIds = changeRows.map((item) => item.deviceIdentification);
  if (selected) {
    checkedKeys.value = [...checkedKeys.value, ...changeIds];
  } else {
    checkedKeys.value = checkedKeys.value.filter((deviceIdentification) => {
      return !changeIds.includes(deviceIdentification);
    });
  }
}

const rulesRef = reactive({
  deviceVersion: [{required: true, message: '请输入设备版本号', trigger: ['change']}],
});

async function handleReload() {
  reload();
}

const useForm = Form.useForm;
const {validate, resetFields, validateInfos} = useForm(modelRef, rulesRef);

async function handleGroupCLickChange(value) {
  //console.log('handleCLickChange', value)
  handleReload();
}

function handleCancel() {
  //console.log('handleCancel');
  resetFields();
}

function handleOk() {//alert(modelRef?.id);
  if (checkedKeys === undefined || checkedKeys.value.length === 0) {
    createMessage.warning('请选择设备标识');
    return;
  }
  state.editLoading = true;
  let dataList = [];
  for (let i = 0; i < checkedKeys.value.length; i++) {
    dataList.push(checkedKeys.value[i]);
  }
  let params = {};
  params['versionId'] = route.params.versionId;
  params['deviceIdentificationList'] = dataList;
  batchAddDeviceTestList(params)
    .then(() => {
      createMessage.success('操作成功');
      closeModal();
      resetFields();
      emits('success');
    })
    .finally(() => {
      state.editLoading = false;
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
