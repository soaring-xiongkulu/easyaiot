<template>
  <BasicDrawer
    v-bind="$attrs"
    @register="register"
    :title="getTitle"
    width="1400"
    placement="right"
    :showFooter="true"
    :showCancelBtn="false"
    :showOkBtn="false"
    destroy-on-close
  >
    <template #footer>
      <div class="footer-buttons">
        <Button @click="handleCancel">取消</Button>
        <Button type="primary" :loading="state.editLoading" @click="handleOk">保存</Button>
      </div>
    </template>

    <Spin :spinning="state.editLoading">
      <div class="device-drawer-content">
        <Divider orientation="left">基础信息</Divider>
        <Form
          :label-col="SETUP_FORM_LABEL_COL"
          :wrapper-col="SETUP_FORM_WRAPPER_COL"
          class="section-form"
        >
          <Row :gutter="16">
            <Col :span="12">
              <FormItem label="设备名称" required v-bind="validateInfos.deviceName">
                <Input v-model:value="modelRef.deviceName" placeholder="请输入设备名称" />
              </FormItem>
            </Col>
            <Col :span="12">
              <FormItem label="设备SN" required v-bind="validateInfos.deviceSn">
                <Input v-model:value="modelRef.deviceSn" placeholder="请输入设备SN" />
              </FormItem>
            </Col>
            <Col :span="12">
              <FormItem label="所属产品" required v-bind="validateInfos.productIdentification">
                <Select
                  v-model:value="modelRef.productIdentification"
                  placeholder="请选择所属产品"
                  :options="state.productList"
                  :disabled="state.lockProduct"
                  allowClear
                  show-search
                  :filter-option="filterProductOption"
                  @change="handleProductChange"
                />
              </FormItem>
            </Col>
            <Col :span="12">
              <FormItem label="应用场景" required v-bind="validateInfos.appId">
                <Input
                  v-model:value="modelRef.appId"
                  placeholder="选择产品后自动填充，也可手动输入"
                  :disabled="!!selectedProduct?.appId"
                />
              </FormItem>
            </Col>
            <Col v-if="state.isEdit" :span="12">
              <FormItem label="设备标识">
                <Input :value="modelRef.deviceIdentification" disabled />
              </FormItem>
            </Col>
            <Col v-if="state.isEdit" :span="12">
              <FormItem label="产品类型">
                <Input :value="deviceTypeLabel" disabled />
              </FormItem>
            </Col>
            <Col :span="12">
              <FormItem label="客户端 ID">
                <Input
                  v-model:value="modelRef.clientId"
                  placeholder="留空则系统自动生成"
                />
              </FormItem>
            </Col>
          </Row>
        </Form>

        <Divider orientation="left">接入配置</Divider>
        <Form
          :label-col="SETUP_FORM_LABEL_COL"
          :wrapper-col="SETUP_FORM_WRAPPER_COL"
          class="section-form"
        >
          <Alert
            v-if="selectedProtocol && !isIndustrialProtocol"
            class="protocol-alert"
            type="info"
            show-icon
            :message="`接入协议：${selectedProtocolLabel}`"
          />

          <template v-if="isModbusProtocol">
            <div class="protocol-toolbar">
              <span class="protocol-toolbar__title">{{ selectedProtocolLabel }} 连接配置</span>
              <div class="protocol-toolbar__actions">
                <Button type="link" size="small" @click="state.showProtocolGuide = !state.showProtocolGuide">
                  配置说明
                </Button>
                <Button size="small" :loading="state.testingConnection" @click="handleTestConnection">
                  测试连接
                </Button>
              </div>
            </div>
            <Alert
              v-if="state.showProtocolGuide"
              class="protocol-alert"
              type="info"
              show-icon
              :message="protocolGuide"
              closable
              @close="state.showProtocolGuide = false"
            />
            <Row v-if="selectedProtocol === 'MODBUS_TCP'" :gutter="16">
              <Col :span="10">
                <FormItem label="主机地址" required>
                  <Input v-model:value="protocolConfig.host" placeholder="192.168.1.100" />
                </FormItem>
              </Col>
              <Col :span="5">
                <FormItem label="端口">
                  <InputNumber v-model:value="protocolConfig.port" :min="1" :max="65535" class="w-full" />
                </FormItem>
              </Col>
              <Col :span="4">
                <FormItem label="站号">
                  <InputNumber v-model:value="protocolConfig.unitId" :min="0" :max="255" class="w-full" />
                </FormItem>
              </Col>
              <Col :span="5">
                <FormItem label="周期(ms)">
                  <InputNumber v-model:value="protocolConfig.pollIntervalMs" :min="1000" :step="1000" class="w-full" />
                </FormItem>
              </Col>
            </Row>
            <template v-else>
              <Row :gutter="16">
                <Col :span="8">
                  <FormItem label="串口" required>
                    <Input v-model:value="protocolConfig.serialPort" placeholder="COM3 或 /dev/ttyUSB0" />
                  </FormItem>
                </Col>
                <Col :span="6">
                  <FormItem label="波特率">
                    <Select v-model:value="protocolConfig.baudRate" :options="baudRateOptions" class="w-full" />
                  </FormItem>
                </Col>
                <Col :span="5">
                  <FormItem label="站号">
                    <InputNumber v-model:value="protocolConfig.unitId" :min="1" :max="247" class="w-full" />
                  </FormItem>
                </Col>
                <Col :span="5">
                  <FormItem label="周期(ms)">
                    <InputNumber v-model:value="protocolConfig.pollIntervalMs" :min="1000" :step="1000" class="w-full" />
                  </FormItem>
                </Col>
              </Row>
              <Row :gutter="16">
                <Col :span="6">
                  <FormItem label="数据位">
                    <Select v-model:value="protocolConfig.dataBits" :options="dataBitOptions" class="w-full" />
                  </FormItem>
                </Col>
                <Col :span="6">
                  <FormItem label="停止位">
                    <Select v-model:value="protocolConfig.stopBits" :options="stopBitOptions" class="w-full" />
                  </FormItem>
                </Col>
                <Col :span="6">
                  <FormItem label="校验">
                    <Select v-model:value="protocolConfig.parity" :options="parityOptions" class="w-full" />
                  </FormItem>
                </Col>
                <Col :span="6">
                  <FormItem label="发送延时">
                    <InputNumber v-model:value="protocolConfig.transmitDelayMs" :min="0" class="w-full" addon-after="ms" />
                  </FormItem>
                </Col>
              </Row>
            </template>
            <Alert
              v-if="state.connectionResult"
              class="protocol-alert"
              show-icon
              :type="state.connectionResult.success ? 'success' : 'error'"
              :message="state.connectionResult.message"
            />
            <div class="point-section">
              <div class="point-section__header">
                <div>
                  <div class="point-section__title">采集点位</div>
                  <div class="point-section__subtitle">
                    点位需绑定物模型属性 · 已配置 {{ protocolConfig.points.length }} 个
                  </div>
                </div>
                <Button type="primary" ghost preIcon="ant-design:plus-outlined" @click="addModbusPoint">
                  添加点位
                </Button>
              </div>

              <div v-if="!protocolConfig.points.length" class="point-empty">
                <div class="point-empty__title">暂无采集点位</div>
                <div class="point-empty__hint">点击右上角「添加点位」，将寄存器映射到物模型属性</div>
              </div>

              <div
                v-for="(point, index) in protocolConfig.points"
                :key="index"
                class="point-card"
              >
                <div class="point-card__header">
                  <div class="point-card__meta">
                    <span class="point-card__index">点位 {{ index + 1 }}</span>
                    <span v-if="resolvePointPropertyCode(point)" class="point-card__badge">
                      {{ resolvePointPropertyCode(point) }}
                    </span>
                  </div>
                  <div class="point-card__actions">
                    <span class="point-card__writable">
                      允许写入
                      <Switch v-model:checked="point.writable" />
                    </span>
                    <Tooltip title="删除点位">
                      <Button danger type="text" preIcon="ant-design:delete-outlined" @click="removePoint(index)" />
                    </Tooltip>
                  </div>
                </div>
                <Row :gutter="[20, 4]">
                  <Col :span="8">
                    <FormItem label="绑定物模型属性" required>
                      <Select
                        v-model:value="point.propertyCode"
                        show-search
                        option-filter-prop="label"
                        :options="propertyBindOptions"
                        :loading="propertyLoading"
                        placeholder="请选择物模型属性"
                        class="w-full"
                        @change="(code) => handlePointPropertyBind(point, code)"
                      />
                    </FormItem>
                  </Col>
                  <Col :span="8">
                    <FormItem label="点位名称">
                      <Input v-model:value="point.identifier" placeholder="默认与绑定属性相同" />
                    </FormItem>
                  </Col>
                  <Col :span="8">
                    <FormItem label="功能码" required>
                      <Select v-model:value="point.function" :options="modbusFunctionOptions" class="w-full" />
                    </FormItem>
                  </Col>
                  <Col :span="8">
                    <FormItem label="寄存器地址" required>
                      <InputNumber v-model:value="point.address" :min="0" :max="65535" class="w-full" placeholder="0" />
                    </FormItem>
                  </Col>
                  <Col :span="8">
                    <FormItem label="数据类型">
                      <Select v-model:value="point.dataType" :options="modbusDataTypeOptions" class="w-full" />
                    </FormItem>
                  </Col>
                  <Col :span="8">
                    <FormItem label="显示进制">
                      <Select v-model:value="point.valueRadix" :options="radixOptions" class="w-full" />
                    </FormItem>
                  </Col>
                  <Col :span="8">
                    <FormItem label="倍率">
                      <InputNumber v-model:value="point.scale" :step="0.1" class="w-full" placeholder="1" />
                    </FormItem>
                  </Col>
                  <Col :span="8">
                    <FormItem label="显示小数位">
                      <InputNumber
                        v-model:value="point.decimalPlaces"
                        :min="0"
                        :max="10"
                        :precision="0"
                        class="w-full"
                        placeholder="2"
                      />
                    </FormItem>
                  </Col>
                </Row>
              </div>
            </div>
          </template>

          <template v-else-if="selectedProtocol === 'OPCUA'">
            <Alert
              v-if="state.showProtocolGuide"
              class="protocol-alert"
              type="info"
              show-icon
              message="填写 OPC UA Endpoint（如 opc.tcp://host:4840）。匿名访问可留空用户名密码；NodeId 需与现场服务器一致，点位需绑定产品物模型属性。"
            />
            <div class="protocol-toolbar">
              <span class="protocol-toolbar__title">OPC UA 连接配置</span>
              <div class="protocol-toolbar__actions">
                <Button type="link" size="small" @click="state.showProtocolGuide = !state.showProtocolGuide">
                  配置说明
                </Button>
                <Button size="small" :loading="state.testingConnection" @click="handleTestConnection">
                  测试连接
                </Button>
              </div>
            </div>
            <FormItem label="Endpoint" required>
              <Input v-model:value="protocolConfig.endpointUrl" placeholder="opc.tcp://192.168.1.100:4840" />
            </FormItem>
            <Row :gutter="16">
              <Col :span="8">
                <FormItem label="用户名">
                  <Input v-model:value="protocolConfig.username" placeholder="匿名可留空" />
                </FormItem>
              </Col>
              <Col :span="8">
                <FormItem label="密码">
                  <InputPassword v-model:value="protocolConfig.password" />
                </FormItem>
              </Col>
              <Col :span="8">
                <FormItem label="周期(ms)">
                  <InputNumber v-model:value="protocolConfig.pollIntervalMs" :min="1000" :step="1000" class="w-full" />
                </FormItem>
              </Col>
            </Row>
            <Alert
              v-if="state.connectionResult"
              class="protocol-alert"
              show-icon
              :type="state.connectionResult.success ? 'success' : 'error'"
              :message="state.connectionResult.message"
            />
            <div class="point-section">
              <div class="point-section__header">
                <div>
                  <div class="point-section__title">采集节点</div>
                  <div class="point-section__subtitle">
                    点位需绑定物模型属性 · 已配置 {{ protocolConfig.points.length }} 个
                  </div>
                </div>
                <Button type="primary" ghost preIcon="ant-design:plus-outlined" @click="addOpcUaPoint">
                  添加节点
                </Button>
              </div>

              <div v-if="!protocolConfig.points.length" class="point-empty">
                <div class="point-empty__title">暂无采集节点</div>
                <div class="point-empty__hint">点击右上角「添加节点」，将 NodeId 映射到物模型属性</div>
              </div>

              <div
                v-for="(point, index) in protocolConfig.points"
                :key="index"
                class="point-card"
              >
                <div class="point-card__header">
                  <div class="point-card__meta">
                    <span class="point-card__index">节点 {{ index + 1 }}</span>
                    <span v-if="resolvePointPropertyCode(point)" class="point-card__badge">
                      {{ resolvePointPropertyCode(point) }}
                    </span>
                  </div>
                  <div class="point-card__actions">
                    <span class="point-card__writable">
                      允许写入
                      <Switch v-model:checked="point.writable" />
                    </span>
                    <Tooltip title="删除节点">
                      <Button danger type="text" preIcon="ant-design:delete-outlined" @click="removePoint(index)" />
                    </Tooltip>
                  </div>
                </div>
                <Row :gutter="[20, 4]">
                  <Col :span="8">
                    <FormItem label="绑定物模型属性" required>
                      <Select
                        v-model:value="point.propertyCode"
                        show-search
                        option-filter-prop="label"
                        :options="propertyBindOptions"
                        :loading="propertyLoading"
                        placeholder="请选择物模型属性"
                        class="w-full"
                        @change="(code) => handlePointPropertyBind(point, code)"
                      />
                    </FormItem>
                  </Col>
                  <Col :span="8">
                    <FormItem label="点位名称">
                      <Input v-model:value="point.identifier" placeholder="默认与绑定属性相同" />
                    </FormItem>
                  </Col>
                  <Col :span="8">
                    <FormItem label="数据类型">
                      <Select v-model:value="point.dataType" :options="opcUaDataTypeOptions" class="w-full" />
                    </FormItem>
                  </Col>
                  <Col :span="24">
                    <FormItem label="NodeId" required>
                      <Input v-model:value="point.nodeId" placeholder="ns=2;s=Temperature" />
                    </FormItem>
                  </Col>
                </Row>
              </div>
            </div>
          </template>

          <Alert
            v-else-if="selectedProtocol === 'TCP'"
            class="protocol-alert"
            type="success"
            show-icon
            message="设备通过 TCP 长连接接入网关 8091 端口，首包使用 auth 方法认证。"
          />
          <Alert
            v-else-if="selectedProtocol === 'MQTT'"
            class="protocol-alert"
            type="info"
            show-icon
            message="设备使用 MQTT 协议接入，凭据由平台根据产品认证配置自动生成。"
          />
          <Alert
            v-else-if="selectedProtocol === 'HTTP'"
            class="protocol-alert"
            type="info"
            show-icon
            message="设备使用 HTTP 协议上报数据，请确保产品物模型与协议脚本已配置。"
          />
          <div v-else-if="modelRef.productIdentification && !selectedProtocol" class="form-hint">
            所选产品未配置协议类型，请先在产品中设置接入协议。
          </div>
        </Form>

        <Divider orientation="left">其他信息</Divider>
        <Form
          :label-col="SETUP_FORM_LABEL_COL"
          :wrapper-col="SETUP_FORM_WRAPPER_COL"
          class="section-form"
        >
          <FormItem label="设备描述" v-bind="validateInfos.deviceDescription">
            <Input v-model:value="modelRef.deviceDescription" placeholder="请输入设备描述" />
          </FormItem>
          <FormItem label="备注" v-bind="validateInfos.remark">
            <Textarea
              v-model:value="modelRef.remark"
              placeholder="请输入备注"
              :maxlength="200"
              :rows="3"
              showCount
            />
          </FormItem>
        </Form>
      </div>
    </Spin>
  </BasicDrawer>
</template>

<script lang="ts" setup>
import { computed, reactive, ref, watch } from 'vue';
import { BasicDrawer, useDrawerInner } from '@/components/Drawer';
import {
  Alert, Col, Divider, Form, FormItem, Input, InputNumber, Row, Select, Spin, Switch, Textarea, Tooltip,
} from 'ant-design-vue';
import { Button } from '@/components/Button';
import { useMessage } from '@/hooks/web/useMessage';
import { getDeviceProfiles } from '@/api/device/product';
import { getDevicesInfo, saveDevices, testModbusConnection, updateDevices } from '@/api/device/devices';
import { getPropertiesList } from '@/api/device/phsyicalModal';
import { SETUP_FORM_LABEL_COL, SETUP_FORM_WRAPPER_COL } from '@/views/node/utils/constants';

defineOptions({ name: 'DeviceDrawer' });

const { createMessage } = useMessage();
const InputPassword = Input.Password;

const PRODUCT_TYPE_LABELS: Record<string, string> = {
  COMMON: '直连设备',
  GATEWAY: '网关设备',
  SUBSET: '网关子设备',
  VIDEO_COMMON: '视频设备',
};

const INDUSTRIAL_PROTOCOLS = ['MODBUS_TCP', 'MODBUS_RTU', 'OPCUA'];

const state = reactive({
  productList: [] as any[],
  isEdit: false,
  editLoading: false,
  lockProduct: false,
  testingConnection: false,
  showProtocolGuide: false,
  connectionResult: null as null | { success: boolean; message: string },
  propertyLoading: false,
});

const productProperties = ref<any[]>([]);
const propertyLoading = computed(() => state.propertyLoading);
const propertyBindOptions = computed(() =>
  productProperties.value.map((item) => ({
    label: `${item.propertyName || item.propertyCode}（${item.propertyCode}）`,
    value: item.propertyCode,
  })),
);

function createEmptyModel() {
  return {
    id: '' as string | number,
    clientId: '',
    deviceSn: '',
    appId: '',
    deviceName: '',
    deviceIdentification: '',
    deviceType: '',
    productIdentification: '',
    deviceDescription: '',
    ipAddress: '',
    extension: '',
    remark: '',
  };
}

const modelRef = reactive(createEmptyModel());
const protocolConfig = reactive<any>(createProtocolConfig(''));

const selectedProduct = computed(() =>
  state.productList.find((item: any) => item.value === modelRef.productIdentification),
);
const selectedProtocol = computed(() => selectedProduct.value?.protocolType || '');
const isModbusProtocol = computed(() =>
  ['MODBUS_TCP', 'MODBUS_RTU'].includes(selectedProtocol.value),
);
const isIndustrialProtocol = computed(() =>
  INDUSTRIAL_PROTOCOLS.includes(selectedProtocol.value),
);
const protocolLabels: Record<string, string> = {
  MQTT: 'MQTT',
  HTTP: 'HTTP',
  TCP: 'TCP',
  MODBUS_TCP: 'Modbus TCP',
  MODBUS_RTU: 'Modbus RTU',
  OPCUA: 'OPC UA',
};
const selectedProtocolLabel = computed(() => protocolLabels[selectedProtocol.value] || selectedProtocol.value);
const protocolGuide = computed(() =>
  selectedProtocol.value === 'MODBUS_RTU'
    ? '串口名称填写 Sink 服务所在主机可见的端口，例如 COM3 或 /dev/ttyUSB0。波特率、数据位、停止位和校验方式必须与从站一致；同一 RS-485 总线上的站号应保持唯一。测试连接仅验证串口能否打开。'
    : '填写设备或串口服务器的 IP 地址，端口通常为 502，站号通常为 1。请确认 Sink 服务所在网络能够访问该地址。测试连接验证主机端口可达，不校验具体寄存器地址。',
);
const deviceTypeLabel = computed(() =>
  PRODUCT_TYPE_LABELS[modelRef.deviceType] || modelRef.deviceType || '-',
);
const getTitle = computed(() => (state.isEdit ? '编辑设备' : '新增设备'));

const modbusFunctionOptions = [
  { label: '保持寄存器', value: 'HOLDING_REGISTER' },
  { label: '输入寄存器', value: 'INPUT_REGISTER' },
  { label: '线圈', value: 'COIL' },
  { label: '离散输入', value: 'DISCRETE_INPUT' },
];
const modbusDataTypeOptions = ['INT16', 'UINT16', 'INT32', 'UINT32', 'FLOAT32', 'INT64', 'FLOAT64']
  .map((value) => ({ label: value, value }));
const radixOptions = [
  { label: 'BIN', value: 2 },
  { label: 'OCT', value: 8 },
  { label: 'DEC', value: 10 },
  { label: 'HEX', value: 16 },
];
const baudRateOptions = [1200, 2400, 4800, 9600, 19200, 38400, 57600, 115200].map((value) => ({
  label: String(value),
  value,
}));
const dataBitOptions = [7, 8].map((value) => ({ label: String(value), value }));
const stopBitOptions = ['1', '1.5', '2'].map((value) => ({ label: value, value }));
const parityOptions = ['NONE', 'EVEN', 'ODD'].map((value) => ({ label: value, value }));
const opcUaDataTypeOptions = ['AUTO', 'BOOLEAN', 'INT32', 'INT64', 'FLOAT', 'DOUBLE', 'STRING']
  .map((value) => ({ label: value, value }));

watch(
  () => [
    protocolConfig.host,
    protocolConfig.port,
    protocolConfig.serialPort,
    protocolConfig.baudRate,
    protocolConfig.dataBits,
    protocolConfig.stopBits,
    protocolConfig.parity,
    protocolConfig.unitId,
  ],
  () => {
    state.connectionResult = null;
  },
);

watch(
  () => modelRef.productIdentification,
  (productIdentification) => {
    if (productIdentification && isIndustrialProtocol.value) {
      loadProductProperties(productIdentification);
    } else {
      productProperties.value = [];
    }
  },
);

function resolvePointPropertyCode(point?: { propertyCode?: string; identifier?: string } | null) {
  return String(point?.propertyCode || point?.identifier || '').trim();
}

function handlePointPropertyBind(point: any, code: string) {
  const previous = String(point._lastBoundPropertyCode || '').trim();
  point.propertyCode = code;
  if (!point.identifier || point.identifier === previous) {
    point.identifier = code;
  }
  point._lastBoundPropertyCode = code;
}

async function loadProductProperties(productIdentification?: string) {
  const code = productIdentification || modelRef.productIdentification;
  if (!code) {
    productProperties.value = [];
    return;
  }
  state.propertyLoading = true;
  try {
    const response: any = await getPropertiesList({
      productIdentification: code,
      pageNum: 1,
      pageSize: 1000,
    });
    productProperties.value = response?.data || response?.rows || response?.list || [];
  } catch (_) {
    productProperties.value = [];
  } finally {
    state.propertyLoading = false;
  }
}

const emits = defineEmits(['success', 'register']);

const rulesRef = reactive({
  deviceSn: [{ required: true, message: '请输入设备SN', trigger: ['change'] }],
  appId: [{ required: true, message: '请输入应用场景', trigger: ['change'] }],
  deviceName: [{ required: true, message: '请输入设备名称', trigger: ['change'] }],
  productIdentification: [{ required: true, message: '请选择所属产品', trigger: ['change'] }],
});
const { validate, resetFields, validateInfos } = Form.useForm(modelRef, rulesRef);

const [register, { closeDrawer }] = useDrawerInner(async (data) => {
  const { isEdit, record, lockProduct, productIdentification, appId } = data || {};
  state.isEdit = !!isEdit || !!record?.id;
  state.lockProduct = !!lockProduct || state.isEdit;

  await ensureProductList();

  if (state.isEdit && record?.id) {
    await loadDeviceForEdit(record.id);
  } else {
    resetModel();
    state.lockProduct = !!lockProduct;
    if (productIdentification) {
      modelRef.productIdentification = productIdentification;
      if (appId) {
        modelRef.appId = appId;
      }
      handleProductChange();
    }
  }
});

async function ensureProductList() {
  if (state.productList.length) return;
  const res = await getDeviceProfiles({ pageNum: 1, pageSize: 500 });
  const list = res?.data || [];
  state.productList = list.map((item: any) => ({
    ...item,
    value: item.productIdentification,
    label: `${item.productName} · ${item.protocolType || '未配置协议'}`,
  }));
}

function filterProductOption(input: string, option: any) {
  return (option?.label || '').toLowerCase().includes(input.toLowerCase());
}

function createProtocolConfig(type: string) {
  return {
    type,
    enabled: true,
    host: '',
    port: type === 'MODBUS_TCP' ? 502 : type === 'OPCUA' ? 4840 : undefined,
    unitId: 1,
    serialPort: '',
    baudRate: 9600,
    dataBits: 8,
    stopBits: '1',
    parity: 'NONE',
    transmitDelayMs: 0,
    rs485Mode: true,
    endpointUrl: '',
    username: '',
    password: '',
    pollIntervalMs: 5000,
    points: [],
  };
}

function replaceProtocolConfig(config: Record<string, any>) {
  Object.keys(protocolConfig).forEach((key) => delete protocolConfig[key]);
  Object.assign(protocolConfig, config);
}

function handleProductChange() {
  const product = selectedProduct.value;
  if (product?.appId) {
    modelRef.appId = product.appId;
  }
  if (!state.isEdit) {
    replaceProtocolConfig(createProtocolConfig(selectedProtocol.value));
  }
  state.connectionResult = null;
  state.showProtocolGuide = false;
  if (isIndustrialProtocol.value) {
    loadProductProperties(modelRef.productIdentification);
  } else {
    productProperties.value = [];
  }
}

async function handleTestConnection() {
  if (!isIndustrialProtocol.value) return;
  if (selectedProtocol.value === 'MODBUS_TCP' && !protocolConfig.host) {
    createMessage.warning('请先填写主机地址');
    return;
  }
  if (selectedProtocol.value === 'MODBUS_RTU' && !protocolConfig.serialPort) {
    createMessage.warning('请先填写串口名称');
    return;
  }
  if (selectedProtocol.value === 'OPCUA' && !protocolConfig.endpointUrl) {
    createMessage.warning('请先填写 Endpoint URL');
    return;
  }
  state.testingConnection = true;
  state.connectionResult = null;
  try {
    const result = await testModbusConnection({ ...protocolConfig, type: selectedProtocol.value });
    state.connectionResult = { success: true, message: result?.msg || '连接成功' };
  } catch (error: any) {
    const isTimeout = error?.code === 'ECONNABORTED' || /timeout/i.test(error?.message || '');
    state.connectionResult = {
      success: false,
      message: isTimeout
        ? '连接测试超时，请确认目标可达，且 Sink 服务可以访问该地址/串口'
        : error?.msg || error?.message || '连接失败，请检查参数和设备状态',
    };
  } finally {
    state.testingConnection = false;
  }
}

function addModbusPoint() {
  protocolConfig.points.push({
    propertyCode: undefined,
    identifier: '',
    function: 'HOLDING_REGISTER',
    address: 0,
    quantity: 1,
    dataType: 'UINT16',
    valueRadix: 16,
    byteOrder: 'BIG_ENDIAN',
    wordOrder: 'BIG_ENDIAN',
    scale: 1,
    decimalPlaces: 2,
    offset: 0,
    writable: false,
  });
}

function addOpcUaPoint() {
  protocolConfig.points.push({
    propertyCode: undefined,
    identifier: '',
    nodeId: '',
    dataType: 'AUTO',
    writable: false,
  });
}

function removePoint(index: number) {
  protocolConfig.points.splice(index, 1);
}

function resetModel() {
  Object.assign(modelRef, createEmptyModel());
  replaceProtocolConfig(createProtocolConfig(''));
  resetFields();
}

function loadProtocolConfig(record: any) {
  let extension: any = {};
  try {
    extension = record?.extension ? JSON.parse(record.extension) : {};
  } catch (_) {
    extension = {};
  }
  const points = (extension.protocolConfig?.points || []).map((point: any) => {
    const propertyCode = point.propertyCode || point.identifier || '';
    return {
      ...point,
      propertyCode: propertyCode || undefined,
      identifier: point.identifier || propertyCode,
      _lastBoundPropertyCode: propertyCode,
    };
  });
  replaceProtocolConfig({
    ...createProtocolConfig(selectedProtocol.value),
    ...(extension.protocolConfig || {}),
    points,
  });
  if (modelRef.productIdentification) {
    loadProductProperties(modelRef.productIdentification);
  }
}

async function loadDeviceForEdit(id: number | string) {
  try {
    state.editLoading = true;
    const info: any = await getDevicesInfo(id);
    const device = info?.device || {};
    Object.keys(modelRef).forEach((key) => {
      modelRef[key] = device[key] ?? '';
    });
    loadProtocolConfig(device);
  } catch (error) {
    console.error(error);
    createMessage.error('加载设备信息失败');
  } finally {
    state.editLoading = false;
  }
}

function handleCancel() {
  resetModel();
  closeDrawer();
}

function validateProtocolConfig() {
  if (selectedProtocol.value === 'MODBUS_TCP' && !protocolConfig.host) {
    createMessage.error('请输入 Modbus TCP 主机地址');
    return false;
  }
  if (selectedProtocol.value === 'MODBUS_RTU' && !protocolConfig.serialPort) {
    createMessage.error('请输入 Modbus RTU 串口名称');
    return false;
  }
  if (selectedProtocol.value === 'OPCUA' && !protocolConfig.endpointUrl) {
    createMessage.error('请输入 OPC UA Endpoint');
    return false;
  }
  if (INDUSTRIAL_PROTOCOLS.includes(selectedProtocol.value)) {
    if (!protocolConfig.points.length) {
      createMessage.error('请至少配置一个采集点位');
      return false;
    }
    const unbound = protocolConfig.points.some((point: any) => !resolvePointPropertyCode(point));
    if (unbound) {
      createMessage.error('请为每个点位绑定物模型属性');
      return false;
    }
    const codes = protocolConfig.points.map((point: any) => resolvePointPropertyCode(point));
    if (new Set(codes).size !== codes.length) {
      createMessage.error('同一设备内不可重复绑定同一物模型属性');
      return false;
    }
    if (selectedProtocol.value === 'OPCUA' && protocolConfig.points.some((point: any) => !point.nodeId)) {
      createMessage.error('OPC UA 节点 ID 不能为空');
      return false;
    }
  }
  return true;
}

async function handleOk() {
  try {
    await validate();
    if (!validateProtocolConfig()) return;

    const payload: any = { ...modelRef };
    let extension: any = {};
    try {
      extension = modelRef.extension ? JSON.parse(modelRef.extension) : {};
    } catch (_) {
      extension = {};
    }
    if (INDUSTRIAL_PROTOCOLS.includes(selectedProtocol.value)) {
      const points = (protocolConfig.points || []).map((point: any) => {
        const propertyCode = resolvePointPropertyCode(point);
        const { _lastBoundPropertyCode, ...rest } = point;
        return {
          ...rest,
          propertyCode,
          identifier: String(point.identifier || propertyCode).trim() || propertyCode,
        };
      });
      extension.protocolConfig = { ...protocolConfig, type: selectedProtocol.value, points };
      payload.extension = JSON.stringify(extension);
      if (selectedProtocol.value === 'MODBUS_TCP') payload.ipAddress = protocolConfig.host;
    } else {
      delete extension.protocolConfig;
      payload.extension = Object.keys(extension).length ? JSON.stringify(extension) : '';
    }

    state.editLoading = true;
    const api = modelRef.id ? updateDevices : saveDevices;
    await api(payload);
    createMessage.success('操作成功');
    closeDrawer();
    resetModel();
    emits('success');
  } catch (err: any) {
    if (!err?.errorFields) {
      createMessage.error(err?.message || '操作失败');
    }
  } finally {
    state.editLoading = false;
  }
}
</script>

<style lang="less" scoped>
.device-drawer-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
  padding-bottom: 8px;
}

.section-form {
  :deep(.ant-form-item) {
    margin-bottom: 18px;
  }

  :deep(.ant-input-number) {
    width: 100%;
  }
}

.protocol-alert {
  margin-bottom: 20px;
}

.protocol-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
  padding: 4px 0;
}

.protocol-toolbar__title {
  font-size: 15px;
  font-weight: 600;
  color: #141414;
}

.protocol-toolbar__actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.point-section {
  margin-top: 8px;
  padding: 20px 22px 8px;
  background: #fafbfc;
  border: 1px solid #eef0f4;
  border-radius: 10px;
}

.point-section__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 18px;
  padding-bottom: 16px;
  border-bottom: 1px solid #eef0f4;
}

.point-section__title {
  font-size: 16px;
  font-weight: 600;
  color: #141414;
  line-height: 24px;
}

.point-section__subtitle {
  margin-top: 4px;
  font-size: 13px;
  color: #8c8c8c;
  line-height: 20px;
}

.point-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  min-height: 140px;
  margin-bottom: 12px;
  padding: 24px;
  background: #fff;
  border: 1px dashed #d9d9d9;
  border-radius: 8px;
}

.point-empty__title {
  font-size: 15px;
  font-weight: 500;
  color: #595959;
}

.point-empty__hint {
  font-size: 13px;
  color: #bfbfbf;
}

.point-card {
  margin-bottom: 16px;
  padding: 18px 20px 4px;
  background: #fff;
  border: 1px solid #e8ecf1;
  border-radius: 8px;
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.03);
}

.point-card__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 12px;
  padding-bottom: 12px;
  border-bottom: 1px solid #f0f0f0;
}

.point-card__meta {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
}

.point-card__index {
  font-size: 14px;
  font-weight: 600;
  color: #141414;
}

.point-card__badge {
  max-width: 220px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  padding: 2px 10px;
  border-radius: 4px;
  background: #e6f4ff;
  color: #1677ff;
  font-size: 12px;
  font-weight: 500;
}

.point-card__actions {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-shrink: 0;
}

.point-card__writable {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: #595959;
}

.form-hint {
  color: rgba(0, 0, 0, 0.45);
  font-size: 13px;
  line-height: 1.5;
}

.footer-buttons {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  gap: 12px;
}

.w-full {
  width: 100%;
}
</style>
