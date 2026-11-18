<template>
  <div class="point-management">
    <div class="toolbar">
      <div>
        <h3>点位管理</h3>
        <p>
          {{
            isOpcUa
              ? '管理 OPC UA 采集节点，点击点位可查看最新值与历史趋势'
              : '管理设备采集点位，点击点位可查看最新值与历史趋势'
          }}
        </p>
      </div>
      <Space>
        <Button :loading="loading" @click="loadRuntimeValues">
          <template #icon><ReloadOutlined /></template>
          刷新数据
        </Button>
        <Button type="primary" @click="openEditor()">
          <template #icon><PlusOutlined /></template>
          添加点位
        </Button>
      </Space>
    </div>

    <Alert
      v-if="parseError"
      type="warning"
      show-icon
      message="设备点位配置无法解析，请编辑设备并重新保存协议配置。"
    />

    <Table
      v-else
      class="point-table"
      :columns="columns"
      :data-source="points"
      :loading="loading"
      :pagination="false"
      :row-key="(_, index) => String(index)"
      :custom-row="customRow"
      :scroll="{ x: 1080 }"
    >
      <template #emptyText>
        <Empty :image="Empty.PRESENTED_IMAGE_SIMPLE" description="暂无点位，点击右上角添加" />
      </template>
      <template #bodyCell="{ column, record, index }">
        <template v-if="column.key === 'index'">
          <span class="row-index">{{ String(index + 1).padStart(2, "0") }}</span>
        </template>
        <template v-else-if="column.key === 'binding'">
          <div class="identifier-cell">
            <strong>{{ resolvePropertyCode(record) || '--' }}</strong>
            <span v-if="propertyLabel(resolvePropertyCode(record))">
              {{ propertyLabel(resolvePropertyCode(record)) }}
            </span>
            <Tag v-else-if="!resolvePropertyCode(record)" color="error">未绑定</Tag>
          </div>
        </template>
        <template v-else-if="column.key === 'identifier'">
          <div class="identifier-cell">
            <strong>{{ record.identifier || resolvePropertyCode(record) || '--' }}</strong>
            <span>{{ isOpcUa ? record.nodeId || '--' : functionLabel(record.function) }}</span>
          </div>
        </template>
        <template v-else-if="column.key === 'latestValue'">
          <div class="value-cell">
            <strong>{{ formatPointValue(record) }}</strong>
            <span>{{ formatTime(runtimeMap[resolvePropertyCode(record)]?.ts) }}</span>
          </div>
        </template>
        <template v-else-if="column.key === 'writable'">
          <Tag :color="record.writable ? 'green' : 'default'">
            {{ record.writable ? "读写" : "只读" }}
          </Tag>
        </template>
        <template v-else-if="column.key === 'valueRadix'">
          {{ radixLabel(record.valueRadix) }}
        </template>
        <template v-else-if="column.key === 'action'">
          <Space @click.stop>
            <Button type="link" size="small" @click="viewPoint(record)">数据</Button>
            <Button type="link" size="small" @click="openEditor(record, index)">编辑</Button>
            <Popconfirm title="确定删除该点位吗？" @confirm="removePoint(index)">
              <Button type="link" danger size="small">删除</Button>
            </Popconfirm>
          </Space>
        </template>
      </template>
    </Table>

    <Modal
      v-model:open="editorOpen"
      :width="'72vw'"
      :style="{ maxWidth: '1040px', top: '48px' }"
      wrap-class-name="point-editor-modal"
      :body-style="{ padding: 0 }"
      :confirm-loading="saving"
      ok-text="保存"
      cancel-text="取消"
      destroy-on-close
      @ok="savePoint"
      @cancel="resetEditor"
    >
      <template #title>
        <div class="point-editor-title">
          <span class="point-editor-title-main">
            {{ editingIndex < 0 ? '添加点位' : '编辑点位' }}
          </span>
          <span class="point-editor-title-sub">
            {{
              isOpcUa
                ? '将 OPC UA NodeId 映射到物模型属性，保存后立即生效'
                : '将寄存器地址映射到物模型属性，保存后立即生效'
            }}
          </span>
        </div>
      </template>

      <div class="point-editor-shell">
        <div class="point-editor-context">
          <div class="point-editor-context-left">
            <span class="point-editor-context-item">
              设备 <strong>{{ device.deviceName || '--' }}</strong>
            </span>
            <span class="point-editor-context-badge">
              {{ isOpcUa ? 'OPC UA' : protocolType || 'Modbus' }}
            </span>
          </div>
          <span class="point-editor-context-item">
            {{ editingIndex < 0 ? '新建' : `编辑第 ${editingIndex + 1} 个` }}点位
          </span>
        </div>

        <div class="point-editor-body">
          <Form layout="vertical" :model="formState" class="point-form">
            <div class="point-editor-section">
              <div class="point-editor-section-head">
                <div class="point-editor-section-title">基础映射</div>
                <div class="point-editor-section-desc">选择物模型属性进行显式绑定；上行按绑定属性上报，下行按绑定属性写点位</div>
              </div>
              <Row :gutter="[24, 8]">
                <Col :span="12">
                  <FormItem label="绑定物模型属性" required>
                    <Select
                      v-model:value="formState.propertyCode"
                      size="large"
                      show-search
                      option-filter-prop="label"
                      :options="propertyOptions"
                      :loading="propertyLoading"
                      placeholder="请选择产品物模型属性"
                      class="w-full"
                      @change="handlePropertyBindChange"
                    />
                    <div class="field-hint">同一设备内不可重复绑定同一属性</div>
                  </FormItem>
                </Col>
                <Col :span="12">
                  <FormItem label="点位名称">
                    <Input
                      v-model:value="formState.identifier"
                      size="large"
                      placeholder="默认与绑定属性相同"
                    />
                    <div class="field-hint">本地显示名，上报键以绑定属性为准</div>
                  </FormItem>
                </Col>
                <template v-if="isOpcUa">
                  <Col :span="12">
                    <FormItem label="NodeId" required>
                      <Input
                        v-model:value="formState.nodeId"
                        size="large"
                        placeholder="例如 ns=2;s=Temperature"
                      />
                    </FormItem>
                  </Col>
                </template>
                <template v-else>
                  <Col :span="12">
                    <FormItem label="功能区" required>
                      <Select
                        v-model:value="formState.function"
                        size="large"
                        :options="functionOptions"
                        class="w-full"
                      />
                    </FormItem>
                  </Col>
                </template>
              </Row>
            </div>

            <div class="point-editor-section">
              <div class="point-editor-section-head">
                <div class="point-editor-section-title">采集参数</div>
                <div class="point-editor-section-desc">
                  {{ isOpcUa ? '指定节点数据类型' : '寄存器地址、数据类型与换算' }}
                </div>
              </div>
              <Row v-if="isOpcUa" :gutter="[24, 8]">
                <Col :span="12">
                  <FormItem label="数据类型" required>
                    <Select
                      v-model:value="formState.dataType"
                      size="large"
                      :options="opcUaDataTypeOptions"
                      class="w-full"
                    />
                  </FormItem>
                </Col>
                <Col :span="12">
                  <FormItem label="访问权限">
                    <RadioGroup v-model:value="formState.writable" class="point-permission">
                      <Radio :value="false">只读采集</Radio>
                      <Radio :value="true">允许平台写入</Radio>
                    </RadioGroup>
                  </FormItem>
                </Col>
              </Row>
              <Row v-else :gutter="[24, 8]">
                <Col :span="8">
                  <FormItem label="寄存器地址" required>
                    <InputNumber
                      v-model:value="formState.address"
                      size="large"
                      :min="0"
                      :max="65535"
                      class="w-full"
                      placeholder="0"
                    />
                  </FormItem>
                </Col>
                <Col :span="8">
                  <FormItem label="数据类型" required>
                    <Select
                      v-model:value="formState.dataType"
                      size="large"
                      :options="dataTypeOptions"
                      class="w-full"
                    />
                  </FormItem>
                </Col>
                <Col :span="8">
                  <FormItem label="数值进制" required>
                    <Select
                      v-model:value="formState.valueRadix"
                      size="large"
                      :options="radixOptions"
                      class="w-full"
                    />
                  </FormItem>
                </Col>
                <Col :span="8">
                  <FormItem label="倍率">
                    <InputNumber
                      v-model:value="formState.scale"
                      size="large"
                      :step="0.1"
                      class="w-full"
                      placeholder="1"
                    />
                  </FormItem>
                </Col>
                <Col :span="8">
                  <FormItem label="显示小数位">
                    <InputNumber
                      v-model:value="formState.decimalPlaces"
                      size="large"
                      :min="0"
                      :max="10"
                      :precision="0"
                      class="w-full"
                      placeholder="2"
                    />
                  </FormItem>
                </Col>
                <Col :span="8">
                  <FormItem label="访问权限">
                    <RadioGroup v-model:value="formState.writable" class="point-permission">
                      <Radio :value="false">只读采集</Radio>
                      <Radio :value="true" :disabled="isReadOnlyFunction">允许平台写入</Radio>
                    </RadioGroup>
                    <div v-if="isReadOnlyFunction" class="field-hint">
                      当前功能区为只读区，不可开启写入
                    </div>
                  </FormItem>
                </Col>
              </Row>
            </div>
          </Form>
        </div>
      </div>
    </Modal>

    <PointHistory @register="registerHistory" />
  </div>
</template>

<script lang="ts" setup>
import { computed, onMounted, reactive, ref, watch } from "vue";
import {
  Alert,
  Button,
  Col,
  Empty,
  Form,
  FormItem,
  Input,
  InputNumber,
  Modal,
  Popconfirm,
  Radio,
  RadioGroup,
  Row,
  Select,
  Space,
  Table,
  Tag,
} from "ant-design-vue";
import { PlusOutlined, ReloadOutlined } from "@ant-design/icons-vue";
import { getDevicethingModels, updateDevices } from "@/api/device/devices";
import { getPropertiesList } from "@/api/device/phsyicalModal";
import { useMessage } from "@/hooks/web/useMessage";
import { formatToDateTime } from "@/utils/dateUtil";
import { formatDeviceValue } from "@/utils/deviceValue";
import { useModal } from "@/components/Modal";
import PointHistory from "../Model/components/Detail.vue";

interface PointConfig {
  propertyCode?: string;
  identifier: string;
  function?: string;
  address?: number;
  nodeId?: string;
  dataType: string;
  scale?: number;
  decimalPlaces?: number;
  writable: boolean;
  [key: string]: any;
}

const props = defineProps<{ device: Record<string, any> }>();
const emit = defineEmits<{ updated: [extension: string] }>();
const { createMessage } = useMessage();

const loading = ref(false);
const saving = ref(false);
const parseError = ref(false);
const points = ref<PointConfig[]>([]);
const runtimeMap = reactive<Record<string, any>>({});
const editorOpen = ref(false);
const editingIndex = ref(-1);
const protocolType = ref("");
const propertyLoading = ref(false);
const productProperties = ref<any[]>([]);
const lastBoundPropertyCode = ref("");

const emptyModbusPoint = (): PointConfig => ({
  propertyCode: undefined,
  identifier: "",
  function: "HOLDING_REGISTER",
  address: 0,
  dataType: "UINT16",
  valueRadix: 16,
  scale: 1,
  decimalPlaces: 2,
  writable: false,
  quantity: 1,
  byteOrder: "BIG_ENDIAN",
  wordOrder: "BIG_ENDIAN",
  offset: 0,
});

const emptyOpcUaPoint = (): PointConfig => ({
  propertyCode: undefined,
  identifier: "",
  nodeId: "",
  dataType: "AUTO",
  writable: false,
});

function resolvePropertyCode(
  point?: { propertyCode?: unknown; identifier?: unknown } | null,
) {
  return String(point?.propertyCode || point?.identifier || "").trim();
}

const propertyOptions = computed(() =>
  productProperties.value.map((item) => ({
    label: `${item.propertyName || item.propertyCode}（${item.propertyCode}）`,
    value: item.propertyCode,
  })),
);

function propertyLabel(code?: string) {
  if (!code) return "";
  const found = productProperties.value.find((item) => item.propertyCode === code);
  return found?.propertyName || "";
}

const formState = reactive<PointConfig>(emptyModbusPoint());

const isOpcUa = computed(() => protocolType.value === "OPCUA");

const functionOptions = [
  { label: "保持寄存器", value: "HOLDING_REGISTER" },
  { label: "输入寄存器", value: "INPUT_REGISTER" },
  { label: "线圈", value: "COIL" },
  { label: "离散输入", value: "DISCRETE_INPUT" },
];
const dataTypeOptions = ["INT16", "UINT16", "INT32", "UINT32", "FLOAT32", "INT64", "FLOAT64"].map(
  (value) => ({
    label: value,
    value,
  }),
);
const opcUaDataTypeOptions = ["AUTO", "BOOLEAN", "INT32", "INT64", "FLOAT", "DOUBLE", "STRING"].map(
  (value) => ({ label: value, value }),
);
const radixOptions = [
  { label: "二进制（BIN）", value: 2 },
  { label: "八进制（OCT）", value: 8 },
  { label: "十进制（DEC）", value: 10 },
  { label: "十六进制（HEX）", value: 16 },
];

const columns = computed(() => {
  if (isOpcUa.value) {
    return [
      { title: "序号", key: "index", width: 64 },
      { title: "绑定属性", key: "binding", width: 200 },
      { title: "点位", key: "identifier", width: 180 },
      { title: "NodeId", dataIndex: "nodeId", width: 220 },
      { title: "数据类型", dataIndex: "dataType", width: 110 },
      { title: "最新数据", key: "latestValue", width: 160 },
      { title: "权限", key: "writable", width: 90 },
      { title: "操作", key: "action", width: 170, fixed: "right" },
    ];
  }
  return [
    { title: "序号", key: "index", width: 64 },
    { title: "绑定属性", key: "binding", width: 200 },
    { title: "点位", key: "identifier", width: 160 },
    { title: "地址", dataIndex: "address", width: 90 },
    { title: "数据类型", dataIndex: "dataType", width: 110 },
    { title: "数值进制", key: "valueRadix", width: 120 },
    { title: "倍率", dataIndex: "scale", width: 80 },
    { title: "小数位", dataIndex: "decimalPlaces", width: 90 },
    { title: "最新数据", key: "latestValue", width: 160 },
    { title: "权限", key: "writable", width: 90 },
    { title: "操作", key: "action", width: 170, fixed: "right" },
  ];
});

const isReadOnlyFunction = computed(() =>
  ["INPUT_REGISTER", "DISCRETE_INPUT"].includes(formState.function || ""),
);
watch(isReadOnlyFunction, (readOnly) => {
  if (readOnly) formState.writable = false;
});

function getExtension() {
  if (!props.device.extension || props.device.extension === "--") return {};
  return JSON.parse(props.device.extension);
}

function loadPoints() {
  try {
    const extension = getExtension();
    protocolType.value =
      extension.protocolConfig?.type || props.device.protocolType || "MODBUS_TCP";
    points.value = (extension.protocolConfig?.points || []).map((point) => {
      const propertyCode = point.propertyCode || point.identifier || "";
      return {
        ...point,
        propertyCode,
        identifier: point.identifier || propertyCode,
      };
    });
    parseError.value = false;
  } catch (_) {
    points.value = [];
    parseError.value = true;
  }
}

async function loadProductProperties() {
  const productIdentification = props.device.productIdentification;
  if (!productIdentification || productIdentification === "--") {
    productProperties.value = [];
    return;
  }
  propertyLoading.value = true;
  try {
    const response: any = await getPropertiesList({
      productIdentification,
      pageNum: 1,
      pageSize: 1000,
    });
    productProperties.value = response?.data || response?.rows || response?.list || [];
  } catch (_) {
    productProperties.value = [];
  } finally {
    propertyLoading.value = false;
  }
}

function handlePropertyBindChange(code: string) {
  formState.propertyCode = code;
  if (!formState.identifier || formState.identifier === lastBoundPropertyCode.value) {
    formState.identifier = code;
  }
  lastBoundPropertyCode.value = code;
}

async function loadRuntimeValues() {
  if (!props.device.id) return;
  loading.value = true;
  try {
    const response: any = await getDevicethingModels({
      id: props.device.id,
      pageNum: 1,
      pageSize: 1000,
    });
    Object.keys(runtimeMap).forEach((key) => delete runtimeMap[key]);
    (response?.data || []).forEach((item) => {
      runtimeMap[item.propertyCode] = item;
    });
  } finally {
    loading.value = false;
  }
}

function openEditor(point?: PointConfig | Record<string, any>, index = -1) {
  editingIndex.value = index;
  const base = isOpcUa.value ? emptyOpcUaPoint() : emptyModbusPoint();
  const merged = { ...base, ...(point || {}) };
  const propertyCode = resolvePropertyCode(merged);
  Object.assign(formState, merged, {
    propertyCode: propertyCode || undefined,
    identifier: merged.identifier || propertyCode,
  });
  lastBoundPropertyCode.value = propertyCode;
  editorOpen.value = true;
  loadProductProperties();
}

function resetEditor() {
  editorOpen.value = false;
  editingIndex.value = -1;
  Object.assign(formState, isOpcUa.value ? emptyOpcUaPoint() : emptyModbusPoint());
}

async function persistPoints(nextPoints: PointConfig[]) {
  const extension = getExtension();
  extension.protocolConfig = extension.protocolConfig || {};
  extension.protocolConfig.points = nextPoints;
  const extensionText = JSON.stringify(extension);
  saving.value = true;
  try {
    await updateDevices({ id: props.device.id, extension: extensionText });
    points.value = nextPoints.map((point) => ({ ...point }));
    emit("updated", extensionText);
    createMessage.success("点位配置已保存");
    resetEditor();
  } finally {
    saving.value = false;
  }
}

async function savePoint() {
  const propertyCode = String(formState.propertyCode || "").trim();
  if (!propertyCode) {
    createMessage.warning("请选择绑定的物模型属性");
    return;
  }
  if (isOpcUa.value && !String(formState.nodeId || "").trim()) {
    createMessage.warning("请输入 NodeId");
    return;
  }
  const duplicate = points.value.some(
    (point, index) =>
      resolvePropertyCode(point) === propertyCode && index !== editingIndex.value,
  );
  if (duplicate) {
    createMessage.warning("该物模型属性已被其他点位绑定");
    return;
  }
  const identifier = String(formState.identifier || propertyCode).trim() || propertyCode;
  const nextPoints = points.value.map((point) => ({ ...point }));
  const nextPoint = {
    ...formState,
    propertyCode,
    identifier,
    nodeId: isOpcUa.value ? String(formState.nodeId || "").trim() : formState.nodeId,
  };
  if (editingIndex.value < 0) nextPoints.push(nextPoint);
  else nextPoints.splice(editingIndex.value, 1, nextPoint);
  await persistPoints(nextPoints);
}

async function removePoint(index: number) {
  const nextPoints = points.value.filter((_, pointIndex) => pointIndex !== index);
  await persistPoints(nextPoints);
}

const [registerHistory, { openModal: openHistory }] = useModal();
function viewPoint(point: PointConfig | Record<string, any>) {
  let protocolConfig: Record<string, any> = {};
  try {
    protocolConfig = getExtension().protocolConfig || {};
  } catch (_) {
    protocolConfig = {};
  }
  const type = String(protocolConfig.type || protocolType.value || "");
  const code = resolvePropertyCode(point);
  openHistory(true, {
    data: {
      propertyCode: code,
      propertyName: propertyLabel(code) || code,
      pointName: point.identifier && point.identifier !== code ? point.identifier : "",
      decimalPlaces: point.decimalPlaces,
      unit: runtimeMap[code]?.unit || "",
      deviceIdentification: props.device?.deviceIdentification || "",
      industrialPoint: type.startsWith("MODBUS")
        ? { ...point, unitId: protocolConfig.unitId ?? 1, protocolType: type }
        : type === "OPCUA"
          ? { ...point, protocolType: type }
          : null,
    },
  });
}

function customRow(record: PointConfig | Record<string, any>) {
  return {
    class: "clickable-row",
    onClick: () => viewPoint(record),
  };
}

function functionLabel(value: string) {
  return functionOptions.find((option) => option.value === value)?.label || value;
}

function radixLabel(value?: number) {
  return radixOptions.find((option) => option.value === Number(value || 16))?.label || "十六进制（HEX）";
}

function formatTime(value?: number) {
  return value ? formatToDateTime(value) : "暂无上报";
}

function formatPointValue(point: PointConfig | Record<string, any>) {
  const runtime = runtimeMap[resolvePropertyCode(point)];
  const value = formatDeviceValue(runtime?.dataValue, point.decimalPlaces);
  if (value === "--") return value;
  return `${value}${runtime?.unit || ""}`;
}

onMounted(() => {
  loadPoints();
  loadProductProperties();
  loadRuntimeValues();
});
</script>

<style lang="less" scoped>
.point-management {
  min-height: 480px;
  padding: 8px 4px 16px;
}

.toolbar {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 24px;
  margin-bottom: 24px;
  padding-bottom: 4px;

  h3 {
    margin: 0;
    color: #141414;
    font-size: 18px;
    font-weight: 600;
    line-height: 26px;
  }

  p {
    margin: 6px 0 0;
    color: #8c8c8c;
    font-size: 13px;
    line-height: 1.5;
  }
}

.point-table {
  border: 1px solid #eef0f4;
  border-radius: 8px;
  overflow: hidden;

  :deep(.ant-table-thead > tr > th) {
    padding: 14px 16px;
    background: #fafbfc;
  }

  :deep(.ant-table-tbody > tr > td) {
    padding: 16px;
  }

  :deep(.clickable-row) {
    cursor: pointer;
  }

  :deep(.clickable-row:hover > td) {
    background: #f5f8fc !important;
  }
}

.row-index {
  color: #98a2b3;
  font-size: 12px;
  font-variant-numeric: tabular-nums;
}

.identifier-cell,
.value-cell {
  display: flex;
  flex-direction: column;
  gap: 4px;

  strong {
    color: #141414;
    font-weight: 600;
  }

  span {
    color: #98a2b3;
    font-size: 12px;
  }
}

.value-cell strong {
  font-size: 16px;
  font-variant-numeric: tabular-nums;
}

.point-form {
  :deep(.ant-form-item) {
    margin-bottom: 20px;
  }

  :deep(.ant-form-item-label > label) {
    font-size: 14px;
    color: #262626;
  }

  :deep(.ant-input-number),
  :deep(.ant-select) {
    width: 100%;
  }
}

.point-permission {
  display: flex;
  flex-wrap: wrap;
  gap: 8px 24px;
  padding-top: 6px;
}

.field-hint {
  margin-top: 6px;
  color: #98a2b3;
  font-size: 12px;
  line-height: 18px;
}

.w-full {
  width: 100%;
}

@media (max-width: 720px) {
  .toolbar {
    align-items: flex-start;
    flex-direction: column;
  }
}
</style>

<style lang="less">
@import '../styles/point-editor-modal.less';
</style>
