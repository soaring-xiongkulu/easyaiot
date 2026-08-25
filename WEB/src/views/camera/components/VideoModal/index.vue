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
        <!-- 单机局域网 ONVIF 发现：GET /video/camera/discovery -->
        <div v-if="state.type === 'onvif'" class="onvif-scan-modal-body">
          <BasicTable @register="registerOnvifTable">
            <template #bodyCell="{ column, record }">
              <template v-if="column.dataIndex === 'action'">
                <Button type="link" size="small" @click="openRegisterModal(record)">注册</Button>
              </template>
            </template>
          </BasicTable>
          <VideoRegisterModal @register="registerVideoRegisterModal" @success="handleRegisterSuccess" />
        </div>
        <!-- 直连设备表单（新增：摄像头类型选择） -->
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
          <FormItem label="接入节点">
            <Select
              v-model:value="modelRef.ingress_node_id"
              :options="ingressNodeOptions"
              :loading="ingressNodesLoading"
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
              <FormItem label="接入节点">
                <Select
                  v-model:value="modelRef.ingress_node_id"
                  :options="ingressNodeOptions"
                  :loading="ingressNodesLoading"
                />
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
              <FormItem label="AI推流地址" name="ai_rtmp_stream" v-bind=validateInfos.ai_rtmp_stream>
                <Input v-model:value="modelRef.ai_rtmp_stream"/>
              </FormItem>
            </Col>
            <Col :span="12">
              <FormItem label="AI HTTP地址" name="ai_http_stream" v-bind=validateInfos.ai_http_stream>
                <Input v-model:value="modelRef.ai_http_stream"/>
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
            <Col :span="12" v-if="isNvrChannel && modelRef.nvr_channel">
              <FormItem label="NVR通道号">
                <Input :value="`CH${modelRef.nvr_channel}`" disabled />
              </FormItem>
            </Col>
            <Col :span="12" v-else-if="state.isView && modelRef.nvr_label">
              <FormItem label="所属NVR">
                <Input :value="modelRef.nvr_label" disabled />
              </FormItem>
            </Col>
            <Col :span="24" v-if="!state.isView && !isNvrChannel">
              <NvrMountFields
                v-model:nvr-id="modelRef.nvr_id"
                v-model:nvr-channel="modelRef.nvr_channel"
                v-model:nvr="modelRef.nvr"
              />
            </Col>
            <Col v-if="state.isView" :span="24">
              <FormItem label="地图坐标">
                <Input :value="locationSummaryText" disabled placeholder="未设置" />
                <div class="location-hint">修改坐标请在设备列表中点击「设置坐标」</div>
              </FormItem>
            </Col>
          </Row>
        </Form>
      </Spin>
    </div>
  </BasicModal>
</template>
<script lang="ts" setup>
import {computed, nextTick, reactive, ref} from 'vue';
import { formatLocationSummary } from '@/views/camera/utils/deviceLocation';
import { isNvrChannelDevice } from '@/views/camera/utils/deviceLabel';
import {BasicModal, useModal, useModalInner} from '@/components/Modal';
import {BasicTable, useTable} from '@/components/Table';
import VideoRegisterModal from '../VideoRegisterModal/index.vue';
import NvrMountFields from '../NvrMountFields/index.vue';
import { Button } from '@/components/Button';
import {Col, Form, FormItem, Input, Row, Select, Spin,} from 'ant-design-vue';
import {CopyOutlined} from '@ant-design/icons-vue';
import {useMessage} from '@/hooks/web/useMessage';
import {copyText} from '@/utils/copyTextToClipboard';
import {discoverDevices, registerDevice, registerDeviceByOnvif, updateDevice} from "@/api/device/camera";
import {getOnvifBasicColumns, getOnvifFormConfig} from './Data';
import {ensureDeviceStreamForwardTask} from "@/api/device/stream_forward";
import { buildBrandRtspUrl, resolveRegisteredDeviceId } from '@/views/camera/utils/rtspUrl';
import { getEdgeNodePage } from '@/api/device/edge';
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
  ai_rtmp_stream: '',
  ai_http_stream: '',
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
  nvr_id: null as number | null,
  nvr_channel: 0,
  nvr: null as Record<string, unknown> | null,
  nvr_label: '',
  longitude: null as number | null,
  latitude: null as number | null,
  ingress_node_id: 0,
});

const ingressNodesLoading = ref(false);
const ingressNodeOptions = ref<Array<{ label: string; value: number }>>([
  { label: '本机（主节点）', value: 0 },
]);

async function loadIngressNodes() {
  ingressNodesLoading.value = true;
  try {
    const page = await getEdgeNodePage({ pageNo: 1, pageSize: 200, status: 'online', enabled: true });
    const list = Array.isArray(page?.list) ? page.list : [];
    ingressNodeOptions.value = [
      { label: '本机（主节点）', value: 0 },
      ...list
        .filter((node) => !!node.computeNodeId && node.status === 'online' && node.enabled !== false)
        .map((node) => ({
          label: `${node.name || `边缘节点 #${node.id}`}（${node.host || '未知地址'}）`,
          value: Number(node.computeNodeId),
        })),
    ];
  } finally {
    ingressNodesLoading.value = false;
  }
}

const locationSummaryText = computed(() =>
  formatLocationSummary({
    longitude: modelRef.longitude,
    latitude: modelRef.latitude,
  }),
);

/** NVR 下挂载的通道设备不可改挂其他 NVR */
const isNvrChannel = computed(() =>
  isNvrChannelDevice({
    device_kind: (state.record as { device_kind?: string } | null)?.device_kind,
    nvr_id: modelRef.nvr_id ?? (state.record as { nvr_id?: number } | null)?.nvr_id,
  }),
);

const getTitle = computed(() => {
  if (state.type === 'onvif') {
    return '扫描局域网ONVIF设备';
  }
  if (state.type === 'source' && !state.isEdit && !state.isView) {
    return '新增直连设备';
  }
  return state.isEdit ? '编辑视频设备' : state.isView ? '查看视频设备' : '新增视频设备';
});

function stripNvrMountFromPayload(data: Record<string, unknown>) {
  delete data.nvr;
  delete data.nvr_id;
  delete data.nvr_channel;
  delete data.nvr_label;
}

function stripReadOnlyFromPayload(data: Record<string, unknown>) {
  delete data.location_source;
  delete data.location_updated_at;
  delete data.has_location;
  delete data.nvr_label;
}

/** 坐标仅在「设置坐标」抽屉中维护，编辑设备时不通过本表单提交 */
function stripLocationFromPayload(data: Record<string, unknown>) {
  delete data.longitude;
  delete data.latitude;
  delete data.altitude;
  delete data.address;
  delete data.heading;
  delete data.location_source;
  delete data.location_updated_at;
  delete data.has_location;
}

/** 规范化布尔字段：空字符串转为 false，确保后端布尔字段不报错 */
function normalizeBoolFields(data: Record<string, unknown>) {
  const boolFields = ['support_move', 'support_zoom', 'enable_forward'];
  for (const field of boolFields) {
    if (field in data) {
      const val = data[field];
      if (val === '' || val === null || val === undefined) {
        data[field] = false;
      } else if (typeof val === 'string') {
        data[field] = val === 'true' || val === '1' || val === 'yes';
      }
    }
  }
}

const [registerVideoRegisterModal, {openModal: openVideoRegisterModal}] = useModal();

const [registerOnvifTable, {reload: reloadOnvifTable}] = useTable({
  canResize: true,
  showIndexColumn: false,
  title: '发现的设备',
  api: discoverDevices,
  columns: getOnvifBasicColumns(),
  useSearchForm: true,
  showTableSetting: false,
  formConfig: getOnvifFormConfig(),
  fetchSetting: {
    listField: 'data',
    totalField: 'total',
  },
  pagination: false,
  rowKey: 'ip',
  immediate: false,
});

const [register, {closeModal}] = useModalInner(async (data) => {
  const {isEdit, isView, type, record} = data;
  state.isEdit = isEdit;
  state.isView = isView;
  state.type = type;
  state.record = record ?? null;
  await loadIngressNodes();

  if (type === 'onvif') {
    await nextTick();
    reloadOnvifTable();
  }

  // 如果是新增直连设备，重置相关字段
  if (type === 'source' && !isEdit && !isView) {
    modelRef.cameraType = 'custom';
    modelRef.ip = '';
    modelRef.port = 554;
    modelRef.username = 'admin';
    modelRef.password = '';
    modelRef.source = '';
    modelRef.name = '';
    modelRef.stream = 0;
    modelRef.nvr_id = null;
    modelRef.nvr_channel = 0;
    modelRef.nvr = null;
    modelRef.ingress_node_id = 0;
  }

  // 更新验证规则
  applyRules();

  if (state.isEdit || state.isView) {
    modelEdit(record);
    // 编辑/查看时也需要更新验证规则
    applyRules();
  }
});

const emits = defineEmits(['success']);

// 动态验证规则函数
const getRules = () => {
  const baseRules: any = {
    name: [{required: true, message: '请输入设备名称', trigger: ['change']}],
    // 编辑模式下，cameraType 不是必填的（因为编辑的设备可能没有这个字段）
    // 只有新增直连设备时才需要 cameraType
    cameraType: state.isEdit ? [] : [{required: true, message: '请选择摄像头类型', trigger: ['change']}],
  };

  // 根据摄像头类型动态设置验证规则
  if (modelRef.cameraType === 'custom') {
    // 自定义类型：source必填，其余连接字段不参与校验
    baseRules.source = [{required: true, message: '请输入RTSP取流地址', trigger: ['change']}];
    baseRules.ip = [];
    baseRules.port = [];
    baseRules.username = [];
    baseRules.password = [];
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

/** 替换校验规则，避免 Object.assign 残留旧类型字段规则 */
function applyRules() {
  const nextRules = getRules();
  Object.keys(rulesRef).forEach((key) => {
    if (!(key in nextRules)) {
      delete rulesRef[key];
    }
  });
  Object.assign(rulesRef, nextRules);
}

/** 新增直连设备时仅校验当前类型可见字段 */
function getDirectDeviceValidateFields(): string[] {
  if (modelRef.cameraType === 'custom') {
    return ['cameraType', 'source', 'name'];
  }
  if (modelRef.cameraType === 'hikvision' || modelRef.cameraType === 'dahua' || modelRef.cameraType === 'uniview') {
    return ['cameraType', 'name', 'ip', 'port', 'username', 'password'];
  }
  return ['cameraType', 'name'];
}

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
  applyRules();
  // 清除验证错误，但不重置字段值
  clearValidate();
}

// 生成RTSP地址（海康/大华/宇视）
function generateRtspUrl() {
  if (
    modelRef.cameraType !== 'hikvision'
    && modelRef.cameraType !== 'dahua'
    && modelRef.cameraType !== 'uniview'
  ) {
    return;
  }
  if (!modelRef.ip || !modelRef.port || !modelRef.username || !modelRef.password) {
    return;
  }
  const url = buildBrandRtspUrl({
    cameraType: modelRef.cameraType,
    ip: modelRef.ip,
    port: parseInt(String(modelRef.port), 10) || 554,
    username: modelRef.username,
    password: modelRef.password,
    stream: modelRef.stream ?? 0,
  });
  if (url) {
    modelRef.source = url;
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
    // 编辑模式下，如果 cameraType 不存在，尝试通过设备特征判断
    if (!modelRef.cameraType) {
      // 如果设备有source但没有IP或IP为空，可能是自定义摄像头
      if (modelRef.source && (!modelRef.ip || !modelRef.ip.trim())) {
        modelRef.cameraType = 'custom';
      } else {
        modelRef.cameraType = '';
      }
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

function openRegisterModal(record: Record<string, unknown>) {
  openVideoRegisterModal(true, {record});
}

async function handleRegisterSuccess(payload: Record<string, unknown>) {
  const ip = String(payload.ip ?? '');
  const username = String(payload.username ?? '').trim();
  const password = String(payload.password ?? '');
  if (!ip || !password) {
    createMessage.error('IP 或密码不能为空');
    return;
  }
  if (!username) {
    createMessage.error('用户名不能为空');
    return;
  }
  const rawPort = payload.port;
  const port = rawPort !== undefined && rawPort !== null && rawPort !== ''
    ? Number(rawPort)
    : 80;
  state.editLoading = true;
  try {
    await registerDeviceByOnvif({
      ip,
      port: Number.isFinite(port) ? port : 80,
      username,
      password,
    });
    createMessage.success('设备注册成功');
    closeModal();
    resetFields();
    emits('success');
  } catch (error: unknown) {
    const err = error as { msg?: string; message?: string };
    createMessage.error(err?.msg || err?.message || '注册失败');
  } finally {
    state.editLoading = false;
  }
}

function handleOk() {
  if (state.type === 'onvif') {
    closeModal();
    return;
  }
  // 直连设备特殊处理：直接注册，不再通过ONVIF搜索
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
    applyRules();

    // 仅校验当前摄像头类型对应的字段，避免隐藏字段残留规则导致失败
    validate(getDirectDeviceValidateFields()).then(async () => {
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
          ingress_node_id: modelRef.ingress_node_id || undefined,
        };

        // 如果是海康、大华或宇视类型，需要传入IP、端口、用户名、密码
        if (modelRef.cameraType === 'hikvision' || modelRef.cameraType === 'dahua' || modelRef.cameraType === 'uniview') {
          registerData.ip = modelRef.ip;
          registerData.port = parseInt(modelRef.port) || 554;
          registerData.username = modelRef.username;
          registerData.password = modelRef.password;
        }

        // 直接调用注册接口，传入source字段
        const response = await registerDevice(registerData);
        const deviceId = resolveRegisteredDeviceId(response);
        createMessage.success('设备注册成功');
        
        // 检查并确保推流转发任务存在
        if (deviceId) {
          try {
            await ensureDeviceStreamForwardTask(deviceId);
          } catch (error) {
            // 静默处理，不影响主流程
            console.warn('检查推流转发任务失败:', error);
          }
        }
        
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
      const firstError = err?.errorFields?.[0]?.errors?.[0];
      createMessage.error(firstError || '表单验证失败');
      console.error(err);
    });
    return;
  }

  // 更新验证规则以确保使用最新的规则
  applyRules();

  validate().then(async () => {
    state.editLoading = true;
    try {
      // 编辑操作：如果有ID则更新，否则新增
      if (state.isEdit && modelRef.id) {
        // 编辑时，过滤掉不必要的字段（如空的 cameraType）
        const updateData = {...modelRef};
        // 如果 cameraType 是空字符串，则不发送该字段
        // 但对于自定义摄像头（cameraType === 'custom'），需要保留该字段以便后端识别
        if (updateData.cameraType === '') {
          delete updateData.cameraType;
        }
        // 如果是通过视频源添加的设备（type === 'source'），且是自定义类型，确保传递cameraType
        if (state.type === 'source' && modelRef.cameraType === 'custom') {
          updateData.cameraType = 'custom';
        }
        if (isNvrChannel.value) {
          stripNvrMountFromPayload(updateData);
        }
        stripReadOnlyFromPayload(updateData);
        stripLocationFromPayload(updateData);
        normalizeBoolFields(updateData);
        await updateDevice(modelRef.id, updateData);
      } else if (state.type === 'camera') {
        // 摄像头处理
        if (modelRef.id) {
          // 编辑时，过滤掉不必要的字段
          const updateData = {...modelRef};
          if (updateData.cameraType === '') {
            delete updateData.cameraType;
          }
          // 如果是自定义类型，确保传递cameraType
          if (modelRef.cameraType === 'custom') {
            updateData.cameraType = 'custom';
          }
          if (isNvrChannel.value) {
            stripNvrMountFromPayload(updateData);
          }
          stripReadOnlyFromPayload(updateData);
          stripLocationFromPayload(updateData);
          normalizeBoolFields(updateData);
          await updateDevice(modelRef.id, updateData);
        } else {
          const saveData = {...modelRef};
          normalizeBoolFields(saveData);
          const response = await registerDevice(saveData);
          const deviceId = resolveRegisteredDeviceId(response);
          
          // 检查并确保推流转发任务存在
          if (deviceId) {
            try {
              await ensureDeviceStreamForwardTask(deviceId);
            } catch (error) {
              // 静默处理，不影响主流程
              console.warn('检查推流转发任务失败:', error);
            }
          }
        }
      } else if (state.type === 'source') {
        // 独立摄像头处理
        const saveData = {...modelRef};
        normalizeBoolFields(saveData);
        const response = await registerDevice(saveData);
        const deviceId = resolveRegisteredDeviceId(response);
        
        // 检查并确保推流转发任务存在
        if (deviceId) {
          try {
            await ensureDeviceStreamForwardTask(deviceId);
          } catch (error) {
            // 静默处理，不影响主流程
            console.warn('检查推流转发任务失败:', error);
          }
        }
      } else {
        // 默认处理：如果有ID则更新，否则新增
        if (modelRef.id) {
          // 编辑时，过滤掉不必要的字段
          const updateData = {...modelRef};
          if (updateData.cameraType === '') {
            delete updateData.cameraType;
          }
          // 如果是自定义类型，确保传递cameraType
          if (modelRef.cameraType === 'custom') {
            updateData.cameraType = 'custom';
          }
          if (isNvrChannel.value) {
            stripNvrMountFromPayload(updateData);
          }
          stripReadOnlyFromPayload(updateData);
          stripLocationFromPayload(updateData);
          normalizeBoolFields(updateData);
          await updateDevice(modelRef.id, updateData);
          
          // 检查并确保推流转发任务存在
          try {
            await ensureDeviceStreamForwardTask(modelRef.id);
          } catch (error) {
            // 静默处理，不影响主流程
            console.warn('检查推流转发任务失败:', error);
          }
        } else {
          const saveData = {...modelRef};
          normalizeBoolFields(saveData);
          const response = await registerDevice(saveData);
          const deviceId = resolveRegisteredDeviceId(response);
          
          // 检查并确保推流转发任务存在
          if (deviceId) {
            try {
              await ensureDeviceStreamForwardTask(deviceId);
            } catch (error) {
              // 静默处理，不影响主流程
              console.warn('检查推流转发任务失败:', error);
            }
          }
        }
      }

      createMessage.success('操作成功');
      closeModal();
      resetFields();
      // 延迟一下再触发刷新，确保后端状态已更新
      setTimeout(() => {
        emits('success');
      }, 100);
    } catch (error) {
      createMessage.error('操作失败');
      console.error(error);
    } finally {
      state.editLoading = false;
    }
  }).catch((err) => {
    const firstError = err?.errorFields?.[0]?.errors?.[0];
    createMessage.error(firstError || '表单验证失败');
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
  
  .onvif-scan-modal-body {
    min-height: 200px;
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

  .location-hint {
    margin-top: 4px;
    font-size: 12px;
    color: rgba(0, 0, 0, 0.45);
    line-height: 1.5;
  }
}
</style>
