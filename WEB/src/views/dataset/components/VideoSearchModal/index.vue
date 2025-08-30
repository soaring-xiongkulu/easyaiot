<template xmlns="">
  <BasicModal
      @register="register"
      :title="getTitle"
      @cancel="handleCancel"
      :width="1200"
      @ok="handleOk"
      :canFullscreen="false"
  >
    <div class="product-modal">
      <Spin :spinning="state.editLoading">
        <!-- ONVIF组件 -->
        <Form
            :labelCol="{ span: 6 }"
            :model="validateInfos"
            :wrapperCol="{ span: 16 }"
        >
          <BasicTable @register="registerTable"></BasicTable>
        </Form>
      </Spin>
    </div>
  </BasicModal>
</template>
<script lang="ts" setup>
import {computed, reactive, ref} from 'vue';
import {BasicModal, useModalInner} from '@/components/Modal';
import {Form, Spin,} from 'ant-design-vue';
import {useMessage} from '@/hooks/web/useMessage';
import {discoverDevices} from "@/api/device/camera";
import {BasicTable, useTable} from "@/components/Table";
import {getOnvifBasicColumns, getOnvifFormConfig} from "./Data";

defineOptions({name: 'VideoSearchModal'})

const {createMessage} = useMessage();

const state = reactive({
  isEdit: false,
  isView: false,
  type: null,
  record: null,
  editLoading: false,
  streamList: [
    {label: "主码流", value: 0},
    {label: "子码流", value: 1},
  ],
  enableForwardList: [
    {label: "启用", value: true},
    {label: "不启用", value: null},
  ],
  supportMoveList: [
    {label: "支持", value: true},
    {label: "不支持", value: false},
  ],
  supportZoomList: [
    {label: "支持", value: true},
    {label: "不支持", value: false},
  ],
});

const modelRef = reactive({
  id: null,
  name: null,
  source: null,
  ai_rtmp_stream: null,
  ai_http_stream: null,
  ai_rtc_stream: null,
  stream: null,
  ai_project_id: null,
  ai_task_enable: null,
  ai_task_args: null,
  ai_alert_config: null,
  ai_region: null,
  enable_forward: null,
  ip: null,
  port: null,
  username: null,
  password: null,
  mac: null,
  manufacturer: null,
  model: null,
  firmware_version: null,
  serial_number: null,
  hardware_id: null,
  support_move: null,
  support_zoom: null,
});

const getTitle = computed(() => '搜索局域网摄像头');

const [register, {closeModal}] = useModalInner((data) => {
  const {isEdit, isView, type, record} = data;
  state.isEdit = isEdit;
  state.isView = isView;
  state.type = type;
  if (state.isEdit || state.isView) {
    modelEdit(record);
  }
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

const [
  registerTable, {reload}
] = useTable({
  canResize: false,
  showIndexColumn: false,
  title: null,
  api: discoverDevices,
  columns: getOnvifBasicColumns(),
  useSearchForm: true,
  showTableSetting: false,
  formConfig: getOnvifFormConfig(),
  fetchSetting: {
    listField: 'list',
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
  rowKey: 'ip',
});

const rulesRef = reactive({
  deviceVersion: [{required: true, message: '请输入视频设备号', trigger: ['change']}],
});

const useForm = Form.useForm;
const {validate, resetFields, validateInfos} = useForm(modelRef, rulesRef);

async function modelEdit(record) {
  try {
    console.log(JSON.stringify(record));
    state.editLoading = true;
    Object.keys(modelRef).forEach((item) => {
      modelRef[item] = record[item];
    });
    state.editLoading = false;
    state.record = record;
  } catch (error) {
    console.error(error)
    //console.log('modelEdit ...', error);
  }
}

function handleCancel() {
  //console.log('handleCancel');
  resetFields();
}

function handleOk() {//alert(modelRef?.id);
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
