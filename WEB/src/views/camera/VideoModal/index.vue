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
          v-if="state.type=='onvif' && !state.isView && !state.isEdit"
        >
          <BasicTable @register="registerTable">
            <template #bodyCell="{ column, record }">
              <template v-if="column.dataIndex === 'action'">
                <TableAction
                  :stopButtonPropagation="true"
                  :actions="[
                    {
                      icon: 'famicons:bag-add-outline',
                      tooltip: {
                        title: '注册设备',
                        placement: 'top',
                      },
                      label: '注册设备',
                      onClick: openRegisterModal.bind(null, true, { record })
                    },
                  ]"
                />
              </template>
            </template>
          </BasicTable>
        </Form>
        <!-- 其他组件 -->
        <Form
          :labelCol="{ span: 6 }"
          :model="validateInfos"
          :wrapperCol="{ span: 16 }"
          :disabled="state.isView"
          v-else
        >
          <Row :gutter="0">
            <Col :span="12">
              <FormItem label="设备名称" name="name" v-bind=validateInfos.name>
                <Input v-model:value="modelRef.name"/>
              </FormItem>
            </Col>
            <Col :span="12">
              <FormItem label="制造商" name="manufacturer" v-bind=validateInfos.manufacturer>
                <Input v-model:value="modelRef.manufacturer"/>
              </FormItem>
            </Col>
            <Col :span="12">
              <FormItem label="设备型号" name="model" v-bind=validateInfos.model>
                <Input v-model:value="modelRef.model"/>
              </FormItem>
            </Col>
            <Col :span="12">
              <FormItem label="MAC地址" name="mac" v-bind=validateInfos.mac>
                <Input v-model:value="modelRef.mac"/>
              </FormItem>
            </Col>
            <Col :span="12">
              <FormItem label="码流索引" name="stream" v-bind=validateInfos.stream>
                <Select
                  placeholder="码流索引"
                  :options="state.streamList"
                  @change="handleCLickChange"
                  v-model:value="modelRef.stream"
                  allowClear
                />
              </FormItem>
            </Col>
            <Col :span="12">
              <FormItem label="rtsp取流地址" name="source" v-bind=validateInfos.source>
                <Input v-model:value="modelRef.source"/>
              </FormItem>
            </Col>
            <Col :span="12">
              <FormItem label="rtmp推流地址" name="rtmp_stream" v-bind=validateInfos.rtmp_stream>
                <Input v-model:value="modelRef.rtmp_stream"/>
              </FormItem>
            </Col>
            <Col :span="12">
              <FormItem label="http流地址" name="http_stream" v-bind=validateInfos.http_stream>
                <Input v-model:value="modelRef.http_stream"/>
              </FormItem>
            </Col>
            <Col :span="12">
              <FormItem label="IP地址" name="ip" v-bind=validateInfos.ip>
                <Input v-model:value="modelRef.ip"/>
              </FormItem>
            </Col>
            <Col :span="12">
              <FormItem label="端口" name="port" v-bind=validateInfos.port>
                <Input v-model:value="modelRef.port"/>
              </FormItem>
            </Col>
            <Col :span="12">
              <FormItem label="用户名" name="username" v-bind=validateInfos.username>
                <Input v-model:value="modelRef.username"/>
              </FormItem>
            </Col>
            <Col :span="12">
              <FormItem label="密码" name="password" v-bind=validateInfos.password>
                <Input v-model:value="modelRef.password" type="password"/>
              </FormItem>
            </Col>
            <Col :span="12">
              <FormItem label="支持云台" name="support_move"
                        v-bind=validateInfos.support_move>
                <Select
                  :options="state.supportMoveList"
                  @change="handleCLickChange"
                  v-model:value="modelRef.support_move"
                  allowClear
                />
              </FormItem>
            </Col>
            <Col :span="12">
              <FormItem label="支持变焦" name="support_zoom"
                        v-bind=validateInfos.support_zoom>
                <Select
                  :options="state.supportZoomList"
                  @change="handleCLickChange"
                  v-model:value="modelRef.support_zoom"
                  allowClear
                />
              </FormItem>
            </Col>
            <Col :span="12" v-if="state.type === 'nvr'">
              <FormItem label="NVR ID" name="nvr_id" v-bind=validateInfos.nvr_id>
                <Input v-model:value="modelRef.nvr_id" :disabled="state.isEdit"/>
              </FormItem>
            </Col>
            <Col :span="12" v-if="state.type === 'nvr'">
              <FormItem label="NVR通道" name="nvr_channel" v-bind=validateInfos.nvr_channel>
                <Input v-model:value="modelRef.nvr_channel"/>
              </FormItem>
            </Col>
          </Row>
        </Form>
      </Spin>
      <VideoRegisterModal title="注册设备" @register="registerRegisterModel"
                          @success="handleRegisterSuccess"/>
    </div>
  </BasicModal>
</template>
<script lang="ts" setup>
import {computed, reactive, ref} from 'vue';
import {BasicModal, useModal, useModalInner} from '@/components/Modal';
import {Col, Form, FormItem, Input, Row, Select, Spin,} from 'ant-design-vue';
import {useMessage} from '@/hooks/web/useMessage';
// 导入新的API函数
import {discoverDevices, getDeviceList, registerDevice, updateDevice} from "@/api/device/camera";
import {BasicTable, TableAction, useTable} from "@/components/Table";
import {getOnvifBasicColumns, getOnvifFormConfig} from "@/views/camera/VideoModal/Data";
import VideoRegisterModal from "@/views/camera/VideoRegisterModal/index.vue";

const [registerRegisterModel, {openModal: openRegisterModal}] = useModal();

defineOptions({name: 'VideoModal'})

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
    {label: "不启用", value: false},
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
  id: '',
  name: '',
  source: '',
  rtmp_stream: '',
  http_stream: '',
  stream: 0,
  enable_forward: '',
  ip: '',
  port: 80,
  username: '',
  password: '',
  mac: '',
  manufacturer: '',
  model: '',
  firmware_version: '',
  serial_number: '',
  hardware_id: '',
  support_move: '',
  support_zoom: '',
  nvr_id: '',
  nvr_channel: 0,
});


const getTitle = computed(() => {
  if (state.type === 'nvr') {
    return state.isEdit ? '编辑NVR设备' : state.isView ? '查看NVR设备' : '新增NVR设备';
  } else {
    return state.isEdit ? '编辑视频设备' : state.isView ? '查看视频设备' : '新增视频设备';
  }
});

const [register, {closeModal}] = useModalInner(async (data) => {
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
  name: [{required: true, message: '请输入设备名称', trigger: ['change']}],
  source: [{required: true, message: '请输入RTSP取流地址', trigger: ['change']}],
  ip: [{required: true, message: '请输入IP地址', trigger: ['change']}],
});

function handleCLickChange(value) {
  //console.log('handleCLickChange', value)
}

function handleRegisterSuccess(value) {
  const ip = value['ip'];
  const mac = value['mac'];
  const name = value['name'];
  const stream = value['stream'];
  const username = value['username'];
  const password = value['password'];
  if (ip == null || ip === '') {
    createMessage.error('IP地址不能为空');
    return;
  }
  if (name == null || name === '') {
    createMessage.error('设备名称不能为空');
    return;
  }
  if (username == null || username === '' || password === null || password === '') {
    createMessage.error('用户名与密码不能为空');
    return;
  }

  state.editLoading = true;

  if (state.type === 'nvr') {
    // 注册NVR设备
    registerDevice(modelRef)
      .then(() => {
        createMessage.success('NVR设备注册成功');
        closeModal();
        resetFields();
        emits('success');
      })
      .catch(error => {
        createMessage.error('NVR设备注册失败');
        console.error(error);
      })
      .finally(() => {
        state.editLoading = false;
      });
  } else if (state.type === 'onvif') {
    let port = 80;
    let arr = ip.split(":");
    if (arr.length > 1) {
      port = arr[1];
    }
    modelRef.ip = arr[0];
    modelRef.port = port;
    modelRef.name = name;
    modelRef.stream = stream;
    modelRef.username = username;
    modelRef.password = password;

    registerDevice(modelRef)
      .then(() => {
        createMessage.success('设备注册成功');
        closeModal();
        resetFields();
        emits('success');
      })
      .finally(() => {
        state.editLoading = false;
      });
    return;
  }
}

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

function handleOk() {
  if (state.type == 'onvif') {
    closeModal();
    resetFields();
    return;
  }

  validate().then(async () => {
    state.editLoading = true;
    try {
      if (state.type === 'nvr') {
        if (modelRef.id) {
          await updateDevice(modelRef.id, modelRef);
        } else {
          await registerDevice(modelRef);
        }
      } else if (state.type === 'camera') {
        // 摄像头处理
        if (modelRef.id) {
          await updateDevice(modelRef.id, modelRef);
        } else {
          await registerDevice(modelRef);
        }
      } else if (state.type === 'source') {
        // 独立摄像头处理
        await registerDevice(modelRef);
      }

      createMessage.success('操作成功');
      closeModal();
      resetFields();
      emits('success');
    } catch (error) {
      createMessage.error('操作失败');
      console.error(error);
    } finally {
      state.editLoading = false;
    }
  }).catch((err) => {
    createMessage.error('表单验证失败');
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
