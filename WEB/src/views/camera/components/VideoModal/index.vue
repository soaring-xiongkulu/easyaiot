<template xmlns="">
  <BasicModal
    @register="register"
    :title="getTitle"
    @cancel="handleCancel"
    :width="900"
    @ok="handleOk"
    :canFullscreen="false"
    :centered="true"
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
        <!-- 视频源设备表单（新增：摄像头类型选择） -->
        <Form
          :labelCol="{ span: 6 }"
          :model="validateInfos"
          :wrapperCol="{ span: 16 }"
          :disabled="state.isView"
          v-else-if="state.type === 'source' && !state.isEdit && !state.isView"
        >
          <FormItem label="摄像头类型" name="cameraType" v-bind=validateInfos.cameraType>
            <Select
              v-model:value="modelRef.cameraType"
              placeholder="请选择摄像头类型"
              :options="state.cameraTypeList"
              @change="handleCameraTypeChange"
            />
          </FormItem>
          <!-- 自定义类型：显示完整RTSP地址输入框 -->
          <template v-if="modelRef.cameraType === 'custom'">
            <FormItem label="RTSP地址" name="source" v-bind=validateInfos.source>
              <Input 
                v-model:value="modelRef.source" 
                placeholder="请输入完整的RTSP取流地址，如：rtsp://username:password@ip:port/path"
                style="width: 100%"
              >
                <template #addonAfter>
                  <CopyOutlined 
                    class="rtsp-copy-icon" 
                    @click="handleCopyRtsp"
                    :style="{ cursor: modelRef.source ? 'pointer' : 'not-allowed', opacity: modelRef.source ? 1 : 0.5 }"
                  />
                </template>
              </Input>
            </FormItem>
            <FormItem label="设备名称" name="name" v-bind=validateInfos.name>
              <Input v-model:value="modelRef.name" placeholder="请输入设备名称"/>
            </FormItem>
          </template>
          <!-- 海康/大华/宇视类型：显示IP、端口、用户名、密码输入框 -->
          <template v-else-if="modelRef.cameraType === 'hikvision' || modelRef.cameraType === 'dahua' || modelRef.cameraType === 'uniview'">
            <FormItem label="设备名称" name="name" v-bind=validateInfos.name>
              <Input v-model:value="modelRef.name" placeholder="请输入设备名称"/>
            </FormItem>
            <FormItem label="摄像头IP" name="ip" v-bind=validateInfos.ip>
              <Input v-model:value="modelRef.ip" placeholder="请输入摄像头IP地址" @blur="generateRtspUrl"/>
            </FormItem>
            <FormItem label="摄像头端口" name="port" v-bind=validateInfos.port>
              <Input v-model:value="modelRef.port" placeholder="请输入摄像头端口" type="number" @blur="generateRtspUrl"/>
            </FormItem>
            <FormItem label="用户名" name="username" v-bind=validateInfos.username>
              <Input v-model:value="modelRef.username" placeholder="请输入用户名" @blur="generateRtspUrl"/>
            </FormItem>
            <FormItem label="密码" name="password" v-bind=validateInfos.password>
              <Input.Password v-model:value="modelRef.password" placeholder="请输入密码" @blur="generateRtspUrl"/>
            </FormItem>
            <FormItem label="码流类型" name="stream" v-bind=validateInfos.stream>
              <Select
                v-model:value="modelRef.stream"
                placeholder="请选择码流类型"
                :options="state.streamList"
                @change="handleStreamChange"
              />
            </FormItem>
            <FormItem label="RTSP地址" name="source" v-bind=validateInfos.source>
              <Input 
                v-model:value="modelRef.source" 
                placeholder="根据输入信息自动生成" 
                disabled
                style="width: 100%"
              >
                <template #addonAfter>
                  <CopyOutlined 
                    class="rtsp-copy-icon" 
                    @click="handleCopyRtsp"
                    :style="{ cursor: modelRef.source ? 'pointer' : 'not-allowed', opacity: modelRef.source ? 1 : 0.5 }"
                  />
                </template>
              </Input>
            </FormItem>
          </template>
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
import {CopyOutlined} from '@ant-design/icons-vue';
import {useMessage} from '@/hooks/web/useMessage';
import {copyText} from '@/utils/copyTextToClipboard';
// 导入新的API函数
import {discoverDevices, getDeviceList, registerDevice, updateDevice} from "@/api/device/camera";
import {BasicTable, TableAction, useTable} from "@/components/Table";
import {getOnvifBasicColumns, getOnvifFormConfig} from "./Data";
import VideoRegisterModal from "../VideoRegisterModal/index.vue";

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
  cameraTypeList: [
    {label: "自定义", value: 'custom'},
    {label: "海康", value: 'hikvision'},
    {label: "大华", value: 'dahua'},
    {label: "宇视", value: 'uniview'},
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
  port: 554,
  username: 'admin',
  password: '',
  mac: '',
  manufacturer: '',
  model: '',
  firmware_version: '',
  serial_number: '',
  hardware_id: '',
  support_move: '',
  support_zoom: '',
  cameraType: 'custom', // 摄像头类型：custom, hikvision, dahua, uniview
});


const getTitle = computed(() => {
  return state.isEdit ? '编辑视频设备' : state.isView ? '查看视频设备' : '新增视频设备';
});

const [register, {closeModal}] = useModalInner(async (data) => {
  const {isEdit, isView, type, record} = data;
  state.isEdit = isEdit;
  state.isView = isView;
  state.type = type;

  // 如果是新增视频源设备，重置相关字段
  if (type === 'source' && !isEdit && !isView) {
    modelRef.cameraType = 'custom';
    modelRef.ip = '';
    modelRef.port = 554;
    modelRef.username = 'admin';
    modelRef.password = '';
    modelRef.source = '';
    modelRef.name = '';
    modelRef.stream = 0;
  }

  // 更新验证规则
  Object.assign(rulesRef, getRules());

  if (state.isEdit || state.isView) {
    modelEdit(record);
    // 编辑/查看时也需要更新验证规则
    Object.assign(rulesRef, getRules());
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

// 动态验证规则函数
const getRules = () => {
  const baseRules: any = {
    name: [{required: true, message: '请输入设备名称', trigger: ['change']}],
    // 编辑模式下，cameraType 不是必填的（因为编辑的设备可能没有这个字段）
    // 只有新增视频源设备时才需要 cameraType
    cameraType: state.isEdit ? [] : [{required: true, message: '请选择摄像头类型', trigger: ['change']}],
  };

  // 根据摄像头类型动态设置验证规则
  if (modelRef.cameraType === 'custom') {
    // 自定义类型：source必填，ip和port不需要验证
    baseRules.source = [{required: true, message: '请输入RTSP取流地址', trigger: ['change']}];
    baseRules.ip = [];
    baseRules.port = [];
  } else if (modelRef.cameraType === 'hikvision' || modelRef.cameraType === 'dahua' || modelRef.cameraType === 'uniview') {
    // 海康/大华/宇视类型：ip、port、username、password必填，source自动生成不需要验证
    baseRules.ip = [
      {required: true, message: '请输入摄像头IP地址', trigger: ['change']},
      {
        validator: (_rule, value) => {
          if (!value || value === '') {
            return Promise.reject('请输入摄像头IP地址');
          }
          // 接受localhost或IPv4地址格式
          const isLocalhost = value.toLowerCase() === 'localhost';
          const ipPattern = /^(\d{1,3}\.){3}\d{1,3}$/;
          if (isLocalhost || ipPattern.test(value)) {
            return Promise.resolve();
          }
          return Promise.reject('请输入正确的IP地址格式，localhost也是正确的');
        },
        trigger: ['change']
      }
    ];
    baseRules.port = [
      {required: true, message: '请输入摄像头端口', trigger: ['change']},
      {
        validator: (_rule, value) => {
          if (!value || value === '') {
            return Promise.reject('请输入摄像头端口');
          }
          const numValue = Number(value);
          if (isNaN(numValue)) {
            return Promise.reject('端口必须是数字');
          }
          if (numValue < 1 || numValue > 65535) {
            return Promise.reject('端口范围必须在1-65535之间');
          }
          return Promise.resolve();
        },
        trigger: ['change']
      }
    ];
    baseRules.username = [{required: true, message: '请输入用户名', trigger: ['change']}];
    baseRules.password = [{required: true, message: '请输入密码', trigger: ['change']}];
    baseRules.source = [];
  } else {
    // 默认情况：所有字段都是可选的，但如果有值则需要符合格式
    baseRules.source = [{required: false, message: '请输入RTSP取流地址', trigger: ['change']}];
    baseRules.ip = [
      {required: false, message: '请输入摄像头IP地址', trigger: ['change']},
      {
        validator: (_rule, value) => {
          if (!value || value === '') {
            return Promise.resolve();
          }
          // 接受localhost或IPv4地址格式
          const isLocalhost = value.toLowerCase() === 'localhost';
          const ipPattern = /^(\d{1,3}\.){3}\d{1,3}$/;
          if (isLocalhost || ipPattern.test(value)) {
            return Promise.resolve();
          }
          return Promise.reject('请输入正确的IP地址格式，localhost也是正确的');
        },
        trigger: ['change']
      }
    ];
    baseRules.port = [
      {required: false, message: '请输入摄像头端口', trigger: ['change']},
      {
        validator: (_rule, value) => {
          if (!value || value === '') {
            return Promise.resolve();
          }
          const numValue = Number(value);
          if (isNaN(numValue)) {
            return Promise.reject('端口必须是数字');
          }
          if (numValue < 1 || numValue > 65535) {
            return Promise.reject('端口范围必须在1-65535之间');
          }
          return Promise.resolve();
        },
        trigger: ['change']
      }
    ];
    baseRules.username = [{required: false, message: '请输入用户名', trigger: ['change']}];
    baseRules.password = [{required: false, message: '请输入密码', trigger: ['change']}];
  }

  return baseRules;
};

const rulesRef = reactive(getRules());

function handleCLickChange(value) {
  //console.log('handleCLickChange', value)
}

// 处理摄像头类型变化
function handleCameraTypeChange(value) {
  // 确保 cameraType 被正确设置
  modelRef.cameraType = value;
  
  if (value === 'custom') {
    // 自定义类型，清空自动生成的字段
    modelRef.source = '';
    modelRef.ip = '';
    modelRef.port = 554;
    modelRef.username = 'admin';
    modelRef.password = '';
  } else {
    // 海康、大华或宇视类型，清空source，等待自动生成
    modelRef.source = '';
    modelRef.stream = 0;
    // 重置为默认值
    if (!modelRef.ip) {
      modelRef.ip = '';
    }
    if (!modelRef.port) {
      modelRef.port = 554;
    }
    if (!modelRef.username) {
      modelRef.username = 'admin';
    }
    if (!modelRef.password) {
      modelRef.password = '';
    }
    
    // 切换类型后，立即检查是否能自动生成RTSP地址
    // 如果IP、端口、用户名、密码都已填写，则自动生成
    if (modelRef.ip && modelRef.port && modelRef.username && modelRef.password) {
      generateRtspUrl();
    }
  }
  
  // 更新验证规则
  Object.assign(rulesRef, getRules());
  // 清除验证错误，但不重置字段值
  clearValidate();
}

// 生成RTSP地址（海康/大华/宇视）
function generateRtspUrl() {
  if (modelRef.cameraType === 'hikvision') {
    // 海康威视RTSP地址格式：rtsp://username:password@ip:port/Streaming/Channels/10X
    // X: 1=主码流, 2=子码流
    // 前端streamList: 0=主码流, 1=子码流
    if (modelRef.ip && modelRef.port && modelRef.username && modelRef.password) {
      const streamType = modelRef.stream === 0 ? 1 : (modelRef.stream === 1 ? 2 : 1);
      modelRef.source = `rtsp://${modelRef.username}:${modelRef.password}@${modelRef.ip}:${modelRef.port}/Streaming/Channels/10${streamType}`;
    }
  } else if (modelRef.cameraType === 'dahua') {
    // 大华RTSP地址格式：rtsp://username:password@ip:port/cam/realmonitor?channel=1&subtype=X
    // X: 0=主码流, 1=辅码流
    // 前端streamList: 0=主码流, 1=子码流
    if (modelRef.ip && modelRef.port && modelRef.username && modelRef.password) {
      const streamType = modelRef.stream === 0 ? 0 : (modelRef.stream === 1 ? 1 : 0);
      modelRef.source = `rtsp://${modelRef.username}:${modelRef.password}@${modelRef.ip}:${modelRef.port}/cam/realmonitor?channel=1&subtype=${streamType}`;
    }
  } else if (modelRef.cameraType === 'uniview') {
    // 宇视RTSP地址格式：rtsp://username:password@ip:port/unicast/c<通道号>/s<码流类型>/live
    // 码流类型: 0=主码流, 1=辅码流
    // 前端streamList: 0=主码流, 1=子码流
    if (modelRef.ip && modelRef.port && modelRef.username && modelRef.password) {
      const streamType = modelRef.stream === 0 ? 0 : (modelRef.stream === 1 ? 1 : 0);
      const channel = 1; // 默认通道1
      modelRef.source = `rtsp://${modelRef.username}:${modelRef.password}@${modelRef.ip}:${modelRef.port}/unicast/c${channel}/s${streamType}/live`;
    }
  }
}

// 处理码流类型变化
function handleStreamChange(value) {
  if (modelRef.cameraType === 'hikvision' || modelRef.cameraType === 'dahua' || modelRef.cameraType === 'uniview') {
    generateRtspUrl();
  }
}

// 复制RTSP地址
function handleCopyRtsp() {
  if (!modelRef.source) {
    createMessage.warning('RTSP地址为空，无法复制');
    return;
  }
  copyText(modelRef.source, 'RTSP地址已复制到剪贴板');
}

function handleRegisterSuccess(value) {
  const ip = value['ip'];
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

  if (state.type === 'onvif') {
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
const {validate, resetFields, clearValidate, validateInfos} = useForm(modelRef, rulesRef);

async function modelEdit(record) {
  try {
    console.log(JSON.stringify(record));
    state.editLoading = true;
    Object.keys(modelRef).forEach((item) => {
      // 如果 record 中有该字段，则使用 record 的值；否则保留 modelRef 的默认值
      if (record.hasOwnProperty(item) && record[item] !== undefined && record[item] !== null) {
        modelRef[item] = record[item];
      }
    });
    // 编辑模式下，如果 cameraType 不存在，设置为空字符串，避免验证错误
    if (!modelRef.cameraType) {
      modelRef.cameraType = '';
    }
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

  // 视频源设备特殊处理：直接注册，不再通过ONVIF搜索
  if (state.type === 'source' && !state.isEdit && !state.isView) {
    // 先进行自定义验证
    let isValid = true;
    let errorMsg = '';

    if (!modelRef.cameraType) {
      isValid = false;
      errorMsg = '请选择摄像头类型';
    } else if (modelRef.cameraType === 'custom') {
      if (!modelRef.source) {
        isValid = false;
        errorMsg = '请输入RTSP取流地址';
      }
    } else if (modelRef.cameraType === 'hikvision' || modelRef.cameraType === 'dahua' || modelRef.cameraType === 'uniview') {
      if (!modelRef.ip) {
        isValid = false;
        errorMsg = '请输入摄像头IP地址';
      } else if (!modelRef.port) {
        isValid = false;
        errorMsg = '请输入摄像头端口';
      } else if (!modelRef.username) {
        isValid = false;
        errorMsg = '请输入用户名';
      } else if (!modelRef.password) {
        isValid = false;
        errorMsg = '请输入密码';
      }
    }

    if (!modelRef.name) {
      isValid = false;
      errorMsg = '请输入设备名称';
    }

    if (!isValid) {
      createMessage.error(errorMsg);
      return;
    }

    // 更新验证规则以确保使用最新的规则
    Object.assign(rulesRef, getRules());

    // 执行表单验证
    validate().then(async () => {
      state.editLoading = true;
      try {
        // 如果是海康、大华或宇视类型，确保RTSP地址已生成
        if ((modelRef.cameraType === 'hikvision' || modelRef.cameraType === 'dahua' || modelRef.cameraType === 'uniview') && !modelRef.source) {
          generateRtspUrl();
        }

        if (!modelRef.source) {
          createMessage.error('RTSP取流地址不能为空');
          state.editLoading = false;
          return;
        }

        // 构建注册数据
        const registerData: any = {
          name: modelRef.name,
          source: modelRef.source,
          stream: modelRef.stream || 0,
          cameraType: modelRef.cameraType, // 传递摄像头类型，用于判断是否需要ONVIF获取
        };

        // 如果是海康、大华或宇视类型，需要传入IP、端口、用户名、密码
        if (modelRef.cameraType === 'hikvision' || modelRef.cameraType === 'dahua' || modelRef.cameraType === 'uniview') {
          registerData.ip = modelRef.ip;
          registerData.port = parseInt(modelRef.port) || 554;
          registerData.username = modelRef.username;
          registerData.password = modelRef.password;
        }

        // 直接调用注册接口，传入source字段
        await registerDevice(registerData);
        createMessage.success('设备注册成功');
        closeModal();
        resetFields();
        emits('success');
      } catch (error: any) {
        createMessage.error(error?.msg || '设备注册失败');
        console.error(error);
      } finally {
        state.editLoading = false;
      }
    }).catch((err) => {
      createMessage.error('表单验证失败');
      console.error(err);
    });
    return;
  }

  // 更新验证规则以确保使用最新的规则
  Object.assign(rulesRef, getRules());

  validate().then(async () => {
    state.editLoading = true;
    try {
      // 编辑操作：如果有ID则更新，否则新增
      if (state.isEdit && modelRef.id) {
        // 编辑时，过滤掉不必要的字段（如空的 cameraType）
        const updateData = {...modelRef};
        // 如果 cameraType 是空字符串，则不发送该字段
        if (updateData.cameraType === '') {
          delete updateData.cameraType;
        }
        await updateDevice(modelRef.id, updateData);
      } else if (state.type === 'camera') {
        // 摄像头处理
        if (modelRef.id) {
          // 编辑时，过滤掉不必要的字段
          const updateData = {...modelRef};
          if (updateData.cameraType === '') {
            delete updateData.cameraType;
          }
          await updateDevice(modelRef.id, updateData);
        } else {
          await registerDevice(modelRef);
        }
      } else if (state.type === 'source') {
        // 独立摄像头处理
        await registerDevice(modelRef);
      } else {
        // 默认处理：如果有ID则更新，否则新增
        if (modelRef.id) {
          // 编辑时，过滤掉不必要的字段
          const updateData = {...modelRef};
          if (updateData.cameraType === '') {
            delete updateData.cameraType;
          }
          await updateDevice(modelRef.id, updateData);
        } else {
          await registerDevice(modelRef);
        }
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
  
  // RTSP地址输入框样式优化
  :deep(.ant-input-group-wrapper) {
    width: 100%;
  }
  
  :deep(.ant-input-group) {
    display: flex;
    width: 100%;
    
    .ant-input {
      flex: 1;
      min-width: 0; // 防止内容溢出
    }
  }
  
  .rtsp-copy-icon {
    color: #1890ff;
    font-size: 16px;
    padding: 0 8px;
    transition: all 0.2s;
    display: flex;
    align-items: center;
    justify-content: center;
    
    &:hover {
      color: #40a9ff;
      transform: scale(1.1);
    }
    
    &:active {
      color: #096dd9;
      transform: scale(0.95);
    }
  }
}
</style>
