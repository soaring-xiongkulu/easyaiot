<template>
  <Drawer
    v-model:visible="visible"
    :title="editingId ? '设计面板模板' : '新建面板模板'"
    width="1080"
    destroyOnClose
    :maskClosable="false"
    class="panel-editor-drawer"
    @close="handleClose"
  >
    <div class="panel-editor">
      <!-- 基本信息 -->
      <div class="panel-meta">
        <div class="meta-item">
          <span class="meta-label">模板名称</span>
          <Input v-model:value="form.templateName" placeholder="如：智能插座控制面板" style="width: 200px" />
        </div>
        <div class="meta-item">
          <span class="meta-label">模板编码</span>
          <Input v-model:value="form.templateCode" :disabled="!!editingId" placeholder="如：plug-panel-v1" style="width: 180px" />
        </div>
        <div class="meta-item">
          <span class="meta-label">绑定产品</span>
          <Select
            v-model:value="form.productIdentification"
            show-search
            option-filter-prop="label"
            placeholder="选择要下发面板的产品"
            style="width: 220px"
            :options="productOptions"
          />
        </div>
        <div class="meta-item meta-item-grow">
          <span class="meta-label">备注</span>
          <Input v-model:value="form.remark" placeholder="选填" style="flex: 1" />
        </div>
      </div>

      <div class="panel-workspace">
        <!-- 左：组件库与组件列表 -->
        <div class="workspace-left">
          <div class="left-section">
            <h4>组件库</h4>
            <div class="palette-grid">
              <Tooltip v-for="t in WIDGET_TYPES" :key="t.type" :title="t.desc">
                <div class="palette-item" @click="addWidget(t.type)">
                  <span class="palette-icon">{{ t.icon }}</span>
                  <span>{{ t.label }}</span>
                </div>
              </Tooltip>
            </div>
          </div>

          <div class="left-section left-section-grow">
            <h4>
              面板组件（{{ widgets.length }}）
              <Popconfirm
                v-if="widgets.length === 0"
                title="使用智能插座示例模板快速开始？"
                @confirm="applyPreset('plug')"
              >
                <a class="preset-link">插入示例</a>
              </Popconfirm>
            </h4>
            <Empty v-if="!widgets.length" description="从上方组件库添加组件" :image-style="{height: '48px'}" />
            <TransitionGroup v-else name="widget-list" tag="div" class="widget-list">
              <div
                v-for="(w, idx) in widgets"
                :key="w.uid"
                class="widget-item"
                :class="{active: w.uid === activeUid}"
                @click="activeUid = w.uid"
              >
                <span class="widget-item-icon">{{ typeMeta(w.type).icon }}</span>
                <span class="widget-item-title">{{ w.title || typeMeta(w.type).label }}</span>
                <span class="widget-item-actions stop">
                  <UpOutlined class="op" @click.stop="move(idx, -1)" />
                  <DownOutlined class="op" @click.stop="move(idx, 1)" />
                  <DeleteOutlined class="op danger" @click.stop="removeWidget(idx)" />
                </span>
              </div>
            </TransitionGroup>
          </div>

          <div class="left-section">
            <Checkbox :checked="sourceMode" @change="(e) => (sourceMode = e.target.checked)">JSON 源码模式</Checkbox>
          </div>
        </div>

        <!-- 中：手机预览 / JSON -->
        <div class="workspace-center">
          <template v-if="!sourceMode">
            <div class="phone-frame">
              <div class="phone-notch"></div>
              <div class="phone-status"><span>9:41</span><span>●●●</span></div>
              <div class="phone-navbar">
                <span class="phone-back">‹</span>
                <div class="phone-title">{{ previewDeviceName }}</div>
                <span class="phone-online">在线</span>
              </div>
              <div class="phone-body">
                  <div
                    v-for="w in widgets"
                    :key="w.uid"
                    class="mock-card"
                    :class="{half: w.span === 'half', selected: w.uid === activeUid}"
                    @click="activeUid = w.uid"
                  >
                  <!-- 开关 -->
                  <template v-if="w.type === 'switch'">
                    <div class="mock-row">
                      <span class="mock-label">{{ w.title }}</span>
                      <span class="mock-switch" :class="{on: true}"><i></i></span>
                    </div>
                  </template>
                  <!-- 滑条 / 数值 -->
                  <template v-else-if="w.type === 'slider' || w.type === 'number'">
                    <div class="mock-col">
                      <div class="mock-row">
                        <span class="mock-label">{{ w.title }}</span>
                        <span class="mock-value">42<span class="mock-unit">{{ w.unit }}</span></span>
                      </div>
                      <div v-if="w.type === 'slider'" class="mock-slider"><i style="width: 42%"></i></div>
                      <div v-else class="mock-stepper"><b>-</b><span>42</span><b>+</b></div>
                    </div>
                  </template>
                  <!-- 状态 -->
                  <template v-else-if="w.type === 'status'">
                    <div class="mock-row">
                      <span class="mock-label">{{ w.title }}</span>
                      <span class="mock-tag" :style="{background: optionColor(w)}">{{ optionLabel(w) }}</span>
                    </div>
                  </template>
                  <!-- 文本 -->
                  <template v-else-if="w.type === 'text'">
                    <div class="mock-row">
                      <span class="mock-label">{{ w.title }}</span>
                      <span class="mock-value">25.4<span class="mock-unit">{{ w.unit }}</span></span>
                    </div>
                  </template>
                  <!-- 按钮 -->
                  <template v-else-if="w.type === 'button'">
                    <div class="mock-col center">
                      <span class="mock-btn">{{ w.title }}</span>
                    </div>
                  </template>
                  <!-- 折线图 -->
                  <template v-else-if="w.type === 'chart'">
                    <div class="mock-col">
                      <div class="mock-row">
                        <span class="mock-label">{{ w.title }}</span>
                        <span class="mock-value">42<span class="mock-unit">{{ w.unit }}</span></span>
                      </div>
                      <svg class="mock-chart" viewBox="0 0 200 60" preserveAspectRatio="none">
                        <defs>
                          <linearGradient id="mockChartFill" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="0%" stop-color="#2f6bff" stop-opacity="0.25" />
                            <stop offset="100%" stop-color="#2f6bff" stop-opacity="0" />
                          </linearGradient>
                        </defs>
                        <polygon
                          fill="url(#mockChartFill)"
                          points="0,48 25,40 50,44 75,30 100,36 125,22 150,28 175,14 200,20 200,60 0,60"
                        />
                        <polyline
                          fill="none" stroke="#2f6bff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"
                          points="0,48 25,40 50,44 75,30 100,36 125,22 150,28 175,14 200,20"
                        />
                        <circle cx="200" cy="20" r="3" fill="#2f6bff" />
                      </svg>
                    </div>
                  </template>
                  <!-- 仪表盘 -->
                  <template v-else-if="w.type === 'gauge'">
                    <div class="mock-col">
                      <div class="mock-row">
                        <span class="mock-label">{{ w.title }}</span>
                        <span class="mock-value">68<span class="mock-unit">{{ w.unit }}</span></span>
                      </div>
                      <div class="mock-gauge">
                        <div class="mock-gauge-fill" :style="{background: w.color || '#16c2a2'}">
                          <span class="mock-gauge-knob"></span>
                        </div>
                      </div>
                    </div>
                  </template>
                  <!-- 进度条 -->
                  <template v-else-if="w.type === 'progress'">
                    <div class="mock-col">
                      <div class="mock-row">
                        <span class="mock-label">{{ w.title }}</span>
                        <span class="mock-value">68<span class="mock-unit">{{ w.unit }}</span></span>
                      </div>
                      <div class="mock-progress">
                        <i :style="{width: '68%', background: w.color || '#2f6bff'}"></i>
                      </div>
                    </div>
                  </template>
                  <!-- 视频 -->
                  <template v-else-if="w.type === 'video'">
                    <div class="mock-col">
                      <span class="mock-label">{{ w.title }}</span>
                      <div class="mock-video">▶ 实时画面</div>
                    </div>
                  </template>
                </div>
                <div v-if="!widgets.length" class="phone-empty">左侧添加组件<br />此处实时预览 App 控制页</div>
              </div>
            </div>
            <p class="preview-tip">App 端实际效果预览 · 点击卡片可编辑</p>
          </template>
          <template v-else>
            <Textarea
              v-model:value="schemaText"
              class="schema-textarea"
              :rows="26"
              placeholder='{"version":1,"pages":[{"name":"控制台","widgets":[]}]}'
            />
            <Space class="schema-actions">
              <Button @click="formatSchema">格式化</Button>
              <Button type="primary" @click="applySchemaText">应用到设计器</Button>
            </Space>
          </template>
        </div>

        <!-- 右：属性配置 -->
        <div class="workspace-right">
          <template v-if="activeWidget">
            <h4>组件配置 · {{ typeMeta(activeWidget.type).label }}</h4>
            <div class="form-item">
              <span class="form-label">标题</span>
              <Input v-model:value="activeWidget.title" placeholder="显示在 App 的标题" />
            </div>
            <div class="form-item">
              <span class="form-label">布局宽度</span>
              <Select
                v-model:value="activeWidget.span"
                :options="[{label: '整行', value: 'full'}, {label: '半行', value: 'half'}]"
              />
            </div>

            <template v-if="usesProperty.includes(activeWidget.type)">
              <div class="form-item">
                <span class="form-label">物模型属性</span>
                <Input v-model:value="activeWidget.propertyCode" placeholder="属性标识符，如 power" />
                <p class="form-help">读写数据均按此属性标识符访问设备影子</p>
              </div>
              <div v-if="writableTypes.includes(activeWidget.type)" class="form-item">
                <span class="form-label">写入服务（可选）</span>
                <Input v-model:value="activeWidget.serviceId" placeholder="如 setPower" />
                <p class="form-help">不填时 App 默认调用 setProperty 属性写服务</p>
              </div>
            </template>

            <template v-if="['slider', 'number'].includes(activeWidget.type)">
              <div class="form-grid">
                <div class="form-item">
                  <span class="form-label">最小值</span>
                  <InputNumber v-model:value="activeWidget.min" style="width: 100%" />
                </div>
                <div class="form-item">
                  <span class="form-label">最大值</span>
                  <InputNumber v-model:value="activeWidget.max" style="width: 100%" />
                </div>
                <div class="form-item">
                  <span class="form-label">步长</span>
                  <InputNumber v-model:value="activeWidget.step" style="width: 100%" />
                </div>
                <div class="form-item">
                  <span class="form-label">单位</span>
                  <Input v-model:value="activeWidget.unit" placeholder="如 %、℃" />
                </div>
              </div>
            </template>

            <template v-if="['status'].includes(activeWidget.type)">
              <div class="form-item">
                <span class="form-label">枚举映射</span>
                <Textarea v-model:value="activeWidget.enumText" :rows="3" placeholder="每行一条：显示文本:值:颜色(可选)&#10;开启:OPEN:#16c2a2&#10;关闭:CLOSE" />
                <p class="form-help">将属性原始值翻译成 App 上展示的标签</p>
              </div>
            </template>

            <template v-if="['button'].includes(activeWidget.type)">
              <div class="form-item">
                <span class="form-label">服务/命令标识</span>
                <Input v-model:value="activeWidget.serviceId" placeholder="服务标识符，如 toggle" />
                <p class="form-help">点击按钮即向设备下发该命令</p>
              </div>
              <div class="form-item">
                <span class="form-label">确认提示</span>
                <Switch v-model:checked="activeWidget.confirm" checked-children="开" un-checked-children="关" />
              </div>
            </template>

            <template v-if="['chart', 'gauge', 'progress'].includes(activeWidget.type)">
              <div class="form-grid">
                <div class="form-item">
                  <span class="form-label">最小值</span>
                  <InputNumber v-model:value="activeWidget.min" style="width: 100%" />
                </div>
                <div class="form-item">
                  <span class="form-label">最大值</span>
                  <InputNumber v-model:value="activeWidget.max" style="width: 100%" />
                </div>
                <div class="form-item">
                  <span class="form-label">单位</span>
                  <Input v-model:value="activeWidget.unit" placeholder="如 %、℃" />
                </div>
                <div class="form-item">
                  <span class="form-label">主题色</span>
                  <Input v-model:value="activeWidget.color" placeholder="如 #2f6bff" />
                </div>
              </div>
              <div v-if="activeWidget.type === 'chart'" class="form-item">
                <span class="form-label">采样点数</span>
                <InputNumber v-model:value="activeWidget.maxPoints" :min="5" :max="60" style="width: 100%" />
                <p class="form-help">App 端每 10s 采样一次属性值并绘制实时曲线</p>
              </div>
            </template>

            <template v-if="['switch'].includes(activeWidget.type)">
              <div class="form-item">
                <span class="form-label">开/关取值</span>
                <Textarea v-model:value="activeWidget.enumText" :rows="2" placeholder="每行一条：显示文本:值&#10;开启:OPEN&#10;关闭:CLOSE" />
                <p class="form-help">默认识别 1/0、true/false、OPEN/CLOSE、ON/OFF</p>
              </div>
            </template>
          </template>
          <Empty v-else description="选中左侧或预览中的组件进行配置" />
        </div>
      </div>
    </div>

    <template #footer>
      <Space>
        <Button @click="handleClose">取消</Button>
        <Button type="primary" :loading="saving" @click="handleSave">
          {{ editingId ? '保存修改' : '保存为草稿' }}
        </Button>
      </Space>
    </template>
  </Drawer>
</template>

<script lang="ts" setup name="appPanelTemplateEditor">
import {computed, reactive, ref, watch} from 'vue';
import {
  Button,
  Checkbox,
  Drawer,
  Empty,
  Input,
  InputNumber,
  Popconfirm,
  Select,
  Space,
  Switch,
  Textarea,
  Tooltip,
} from 'ant-design-vue';
import {DownOutlined, UpOutlined, DeleteOutlined} from '@ant-design/icons-vue';
import {createAppPanelTemplate, updateAppPanelTemplate} from '@/api/device/appPanelTemplate';
import {getDeviceProfiles} from '@/api/device/product';
import {useMessage} from '@/hooks/web/useMessage';

const emit = defineEmits(['success']);
const {createMessage} = useMessage();

const visible = ref(false);
const saving = ref(false);
const sourceMode = ref(false);
const editingId = ref<number | null>(null);

const WIDGET_TYPES = [
  {type: 'switch', label: '开关', icon: '⏻', desc: '布尔开关，绑定可写属性'},
  {type: 'slider', label: '滑条', icon: '🎚️', desc: '数值调节滑条，绑定数值属性'},
  {type: 'number', label: '步进器', icon: '➕', desc: '加减步进调节数值属性'},
  {type: 'status', label: '状态标签', icon: '🏷️', desc: '只读属性值并映射为彩色标签'},
  {type: 'text', label: '数值文本', icon: '🔢', desc: '只读数值/文本展示'},
  {type: 'button', label: '命令按钮', icon: '🔘', desc: '点击下发设备服务命令'},
  {type: 'chart', label: '折线图', icon: '📈', desc: '属性值实时采样曲线（每 10s 采样）'},
  {type: 'gauge', label: '仪表盘', icon: '🌀', desc: '弧形仪表盘展示数值占比'},
  {type: 'progress', label: '进度条', icon: '📊', desc: '数值进度条展示'},
  {type: 'video', label: '视频画面', icon: '📹', desc: '当前设备的实时画面（摄像头）'},
] as const;

const usesProperty = ['switch', 'slider', 'number', 'status', 'text', 'chart', 'gauge', 'progress'];
// 可写属性组件（开关/滑条/步进器）支持自定义写入服务
const writableTypes = ['switch', 'slider', 'number'];

const typeMeta = (type) => WIDGET_TYPES.find((t) => t.type === type) || {icon: '🧩', label: type};

let uidSeed = 1;
const genUid = () => `w${Date.now().toString(36)}${uidSeed++}`;

const form = reactive({
  templateName: '',
  templateCode: '',
  productIdentification: undefined as string | undefined,
  remark: '',
});
const widgets = ref<any[]>([]);
const activeUid = ref<string | null>(null);
const activeWidget = computed(() => widgets.value.find((w) => w.uid === activeUid.value));
const schemaText = ref('');
const productOptions = ref<{ label: string; value: string }[]>([]);

const previewDeviceName = computed(() => {
  const p = productOptions.value.find((o) => o.value === form.productIdentification);
  return `${form.templateName || '我的设备'} · ${p ? p.label : '已绑定产品'}`;
});

async function loadProducts() {
  if (productOptions.value.length) return;
  try {
    const res = await getDeviceProfiles({pageNum: 1, pageSize: 500});
    const rows = res?.data ?? res ?? [];
    productOptions.value = (rows || [])
      .filter((r) => r.productIdentification)
      .map((r) => ({label: r.productName, value: r.productIdentification}));
  } catch (e) {
    console.warn('加载产品列表失败', e);
  }
}

function addWidget(type) {
  const defaults: Record<string, any> = {
    switch: {title: '电源开关', enumText: '开启:1\n关闭:0'},
    slider: {title: '亮度', min: 0, max: 100, step: 1, unit: '%'},
    number: {title: '目标温度', min: 16, max: 30, step: 1, unit: '℃'},
    status: {title: '工作模式', enumText: '制冷:COOL:#1890ff\n制热:HEAT:#fa541c'},
    text: {title: '实时功率', unit: 'W'},
    button: {title: '一键执行', serviceId: '', confirm: false},
    chart: {title: '温度趋势', min: 0, max: 60, unit: '℃', color: '#2f6bff', maxPoints: 20},
    gauge: {title: '电量', min: 0, max: 100, unit: '%', color: '#16c2a2'},
    progress: {title: '任务进度', min: 0, max: 100, unit: '%', color: '#2f6bff'},
    video: {title: '实时画面'},
  };
  widgets.value.push({
    uid: genUid(),
    type,
    span: 'full',
    ...defaults[type],
  });
  activeUid.value = widgets.value[widgets.value.length - 1].uid;
  syncSchemaText();
}

function removeWidget(idx) {
  if (widgets.value[idx]?.uid === activeUid.value) activeUid.value = null;
  widgets.value.splice(idx, 1);
  syncSchemaText();
}

function move(idx, dir) {
  const target = idx + dir;
  if (target < 0 || target >= widgets.value.length) return;
  [widgets.value[idx], widgets.value[target]] = [widgets.value[target], widgets.value[idx]];
  syncSchemaText();
}

function applyPreset(kind: 'plug') {
  if (kind !== 'plug') return;
  presets.plug().forEach((w) => widgets.value.push(w));
  syncSchemaText();
}

// 快速起步的行业常见面板
const presets = {
  plug: () => [
    {uid: genUid(), type: 'switch', title: '电源开关', span: 'half', propertyCode: 'power', enumText: '开启:1\n关闭:0'},
    {uid: genUid(), type: 'status', title: '工作状态', span: 'half', propertyCode: 'work_status', enumText: '运行:RUNNING:#16c2a2\n待机:STANDBY:#8c8c8c\n故障:FAULT:#f5222d'},
    {uid: genUid(), type: 'text', title: '实时功率', span: 'half', propertyCode: 'power_consumption', unit: 'W'},
    {uid: genUid(), type: 'slider', title: '定时电量阈值', span: 'half', propertyCode: 'threshold', min: 0, max: 100, step: 5, unit: '%'},
    {uid: genUid(), type: 'button', title: '重启设备', span: 'full', serviceId: 'reboot', confirm: true},
  ],
};

function buildWidgetsFromParsed(parsed): any[] {
  const rawList = parsed?.pages?.[0]?.widgets ?? [];
  return rawList.map((raw, i) => ({
    uid: genUid(),
    id: raw.id || `${raw.type}_${i}`,
    type: raw.type,
    title: raw.title ?? '',
    span: raw.span === 'half' ? 'half' : 'full',
    propertyCode: raw.propertyCode,
    serviceId: raw.serviceId,
    config: raw.config || {},
    enumText: enumToText(raw),
    confirm: raw.config?.confirm === true,
  }));
}

function enumToText(raw) {
  const opts = raw?.config?.options;
  if (!Array.isArray(opts)) return '';
  return opts.map((o) => [o.label, o.value, o.color].filter((x) => x !== undefined && x !== '').join(':')).join('\n');
}

function parseEnumText(enumText?: string) {
  if (!enumText) return [];
  return enumText
    .split('\n')
    .map((line) => line.trim())
    .filter(Boolean)
    .map((line) => {
      const [label, value, color] = line.split(':').map((s) => s.trim());
      return {label, value, ...(color ? {color} : {})};
    });
}

function buildSchemaPayload() {
  const normalized = widgets.value.map((w, i) => ({
    id: w.id || `${w.type}_${i}`,
    type: w.type,
    title: w.title,
    span: w.span,
    ...(w.propertyCode ? {propertyCode: w.propertyCode} : {}),
    ...(w.serviceId ? {serviceId: w.serviceId} : {}),
    config: {
      ...(w.min !== undefined ? {min: w.min} : {}),
      ...(w.max !== undefined ? {max: w.max} : {}),
      ...(w.step !== undefined ? {step: w.step} : {}),
      ...(w.unit ? {unit: w.unit} : {}),
      ...(w.color ? {color: w.color} : {}),
      ...(w.maxPoints ? {maxPoints: w.maxPoints} : {}),
      ...(['switch', 'status'].includes(w.type) ? {options: parseEnumText(w.enumText)} : {}),
      ...(w.type === 'button' ? {confirm: !!w.confirm} : {}),
    },
  }));
  return JSON.stringify(
    {version: 1, pages: [{name: '控制台', layout: 'grid', widgets: normalized}]},
    null,
    2,
  );
}

function syncSchemaText() {
  if (!sourceMode.value) return;
  schemaText.value = buildSchemaPayload();
}

watch(sourceMode, (on) => {
  if (on) schemaText.value = buildSchemaPayload();
});

function formatSchema() {
  try {
    schemaText.value = JSON.stringify(JSON.parse(schemaText.value || '{}'), null, 2);
  } catch (e: any) {
    createMessage.error('JSON 格式错误：' + e.message);
  }
}

function applySchemaText() {
  try {
    const parsed = JSON.parse(schemaText.value);
    widgets.value = buildWidgetsFromParsed(parsed);
    createMessage.success(`已应用，共 ${widgets.value.length} 个组件`);
    sourceMode.value = false;
  } catch (e: any) {
    createMessage.error('JSON 解析失败：' + e.message);
  }
}

const optionLabel = (w) => parseEnumText(w.enumText)[0]?.label || w.options?.[0]?.label || '--';
const optionColor = (w) => parseEnumText(w.enumText)[0]?.color || '#0957de';

async function open(record) {
  await loadProducts();
  editingId.value = record?.id ?? null;
  form.templateName = record?.templateName ?? '';
  form.templateCode = record?.templateCode ?? '';
  form.productIdentification = record?.productIdentification || undefined;
  form.remark = record?.remark ?? '';
  if (record?.panelSchema) {
    let parsed;
    try {
      parsed = typeof record.panelSchema === 'string' ? JSON.parse(record.panelSchema) : record.panelSchema;
    } catch (e) {
      parsed = null;
    }
    widgets.value = parsed ? buildWidgetsFromParsed(parsed) : [];
  } else {
    widgets.value = [];
  }
  activeUid.value = widgets.value[0]?.uid ?? null;
  sourceMode.value = false;
  visible.value = true;
}

function handleClose() {
  visible.value = false;
}

async function handleSave() {
  if (!form.templateName.trim()) {
    createMessage.warning('请填写模板名称');
    return;
  }
  if (!editingId.value && !form.templateCode.trim()) {
    createMessage.warning('请填写模板编码（英文/数字/中划线）');
    return;
  }
  saving.value = true;
  try {
    const payload = {
      id: editingId.value ?? undefined,
      templateCode: form.templateCode.trim(),
      templateName: form.templateName.trim(),
      productIdentification: form.productIdentification || '',
      remark: form.remark,
      panelSchema: buildSchemaPayload(),
    };
    if (editingId.value) {
      await updateAppPanelTemplate(payload);
      createMessage.success('保存成功');
    } else {
      await createAppPanelTemplate(payload);
      createMessage.success('模板已创建为草稿，发布后对 App 生效');
    }
    visible.value = false;
    emit('success');
  } catch (e: any) {
    createMessage.error(e?.message || '保存失败');
  } finally {
    saving.value = false;
  }
}

defineExpose({open});
</script>

<style lang="less" scoped>
.panel-editor {
  display: flex;
  flex-direction: column;
  gap: 12px;
  height: calc(100vh - 240px);
}

.panel-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;

  .meta-item {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .meta-item-grow {
    flex: 1;
  }

  .meta-label {
    white-space: nowrap;
    color: rgba(0, 0, 0, 0.65);

    &::after {
      content: '：';
    }
  }
}

.panel-workspace {
  display: grid;
  grid-template-columns: 300px 1fr 320px;
  gap: 12px;
  flex: 1;
  min-height: 0;
}

.workspace-left,
.workspace-right {
  border: 1px solid #f0f0f0;
  border-radius: 8px;
  padding: 12px;
  overflow-y: auto;

  h4 {
    margin-bottom: 10px;
    font-weight: 600;
    display: flex;
    align-items: center;
    justify-content: space-between;
  }

  .preset-link {
    font-size: 12px;
    font-weight: normal;
  }
}

.workspace-left {
  display: flex;
  flex-direction: column;

  .left-section + .left-section {
    margin-top: 14px;
  }

  .left-section-grow {
    flex: 1;
    overflow-y: auto;
  }
}

.palette-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;

  .palette-item {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 4px;
    padding: 10px 4px;
    border: 1px dashed #d9d9d9;
    border-radius: 8px;
    cursor: pointer;
    font-size: 12px;
    transition: all 0.2s;

    &:hover {
      border-color: #1677ff;
      color: #1677ff;
      background: rgba(22, 119, 255, 0.04);
    }

    .palette-icon {
      font-size: 18px;
    }
  }
}

.widget-list {
  display: flex;
  flex-direction: column;
  gap: 6px;

  .widget-item {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 8px 10px;
    border-radius: 8px;
    background: #fafafa;
    cursor: pointer;
    font-size: 13px;

    &.active {
      background: rgba(22, 119, 255, 0.08);
      outline: 1px solid #1677ff;
    }

    .widget-item-icon {
      font-size: 15px;
    }

    .widget-item-title {
      flex: 1;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }

    .widget-item-actions {
      display: flex;
      gap: 8px;

      .op {
        opacity: 0.45;

        &:hover {
          opacity: 1;
        }

        &.danger:hover {
          color: #f5222d;
        }
      }
    }
  }
}

.widget-list-enter-active,
.widget-list-leave-active,
.widget-list-move {
  transition: all 0.25s ease;
}

.widget-list-enter-from,
.widget-list-leave-to {
  opacity: 0;
  transform: translateY(-6px);
}

.workspace-center {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 8px 0 0;
  border-radius: 8px;
  min-width: 340px;

  .preview-tip {
    color: rgba(0, 0, 0, 0.45);
    font-size: 12px;
  }
}

.phone-frame {
  width: 326px;
  height: 640px;
  background: linear-gradient(180deg, #eef3fb 0%, #f7f9fc 60%);
  border: 10px solid #10131a;
  border-radius: 44px;
  position: relative;
  overflow: hidden;
  box-shadow: 0 24px 48px rgba(16, 19, 26, 0.18);
  display: flex;
  flex-direction: column;

  .phone-notch {
    position: absolute;
    top: 10px;
    left: 50%;
    transform: translateX(-50%);
    width: 90px;
    height: 22px;
    border-radius: 12px;
    background: #10131a;
    z-index: 3;
  }

  .phone-status {
    display: flex;
    justify-content: space-between;
    padding: 10px 22px 0;
    font-size: 12px;
    font-weight: 600;
    color: #1a1d29;
  }

  .phone-navbar {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 8px 14px;

    .phone-back {
      font-size: 20px;
      line-height: 1;
    }

    .phone-title {
      flex: 1;
      text-align: center;
      font-size: 13px;
      font-weight: 600;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }

    .phone-online {
      font-size: 10px;
      color: #16a377;
      background: rgba(22, 163, 119, 0.12);
      border-radius: 99px;
      padding: 1px 8px;
    }
  }

  .phone-body {
    flex: 1;
    overflow-y: auto;
    padding: 4px 14px 18px;
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    align-content: flex-start;

    .phone-empty {
      width: 100%;
      text-align: center;
      color: rgba(0, 0, 0, 0.35);
      font-size: 12px;
      line-height: 2;
      margin-top: 120px;
    }
  }
}

.mock-card {
  width: 100%;
  background: #fff;
  border-radius: 14px;
  padding: 14px;
  box-shadow: 0 2px 8px rgba(31, 45, 74, 0.06);
  cursor: pointer;
  transition: box-shadow 0.2s;

  &.half {
    width: calc(50% - 4px);
  }

  &.selected {
    outline: 2px solid #1677ff;
    outline-offset: -2px;
  }
}

.mock-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.mock-col {
  display: flex;
  flex-direction: column;
  gap: 8px;

  &.center {
    align-items: center;
  }
}

.mock-label {
  font-size: 13px;
  font-weight: 600;
  color: #1a1d29;
}

.mock-value {
  font-size: 18px;
  font-weight: 700;
  color: #0957de;

  .mock-unit {
    font-size: 11px;
    font-weight: 400;
    color: #98a2b3;
    margin-left: 2px;
  }
}

.mock-switch {
  width: 44px;
  height: 24px;
  border-radius: 99px;
  background: #d8dee9;
  position: relative;

  i {
    position: absolute;
    right: 2px;
    top: 2px;
    width: 20px;
    height: 20px;
    background: #fff;
    border-radius: 50%;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
  }

  &.on {
    background: linear-gradient(135deg, #34b3fe, #0957de);
  }
}

.mock-slider {
  height: 6px;
  border-radius: 3px;
  background: #edeff5;
  overflow: hidden;

  i {
    display: block;
    height: 100%;
    border-radius: 3px;
    background: linear-gradient(90deg, #34b3fe, #0957de);
    position: relative;

    &::after {
      content: '';
      position: absolute;
      right: -5px;
      top: 50%;
      transform: translateY(-50%);
      width: 12px;
      height: 12px;
      border-radius: 50%;
      background: #fff;
      box-shadow: 0 1px 4px rgba(0, 0, 0, 0.25);
    }
  }
}

.mock-stepper {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #f2f4f8;
  border-radius: 10px;
  padding: 4px 12px;
  font-weight: 700;

  b {
    color: #0957de;
  }
}

.mock-tag {
  color: #fff;
  font-size: 11px;
  border-radius: 99px;
  padding: 2px 10px;
}

.mock-btn {
  background: linear-gradient(135deg, #34b3fe, #0957de);
  color: #fff;
  border-radius: 99px;
  padding: 8px 28px;
  font-size: 13px;
  font-weight: 600;
}

.mock-video {
  height: 110px;
  border-radius: 10px;
  background: #10131a;
  color: rgba(255, 255, 255, 0.75);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  letter-spacing: 1px;
}

.mock-chart {
  width: 100%;
  height: 64px;
  display: block;
}

.mock-gauge {
  position: relative;
  width: 100%;
  height: 52px;
  border-radius: 52px 52px 0 0;
  background: #edeff5;
  overflow: hidden;
  margin-top: 4px;

  .mock-gauge-fill {
    position: absolute;
    left: 0;
    bottom: 0;
    width: 68%;
    height: 100%;
    border-radius: 52px 52px 0 0;
    display: flex;
    align-items: flex-end;
    justify-content: flex-end;

    .mock-gauge-knob {
      width: 12px;
      height: 12px;
      border-radius: 50%;
      background: #fff;
      box-shadow: 0 1px 3px rgba(0, 0, 0, 0.25);
      margin: -6px -4px 6px 0;
    }
  }
}

.mock-progress {
  height: 10px;
  border-radius: 5px;
  background: #edeff5;
  overflow: hidden;

  i {
    display: block;
    height: 100%;
    border-radius: 5px;
  }
}

.schema-textarea {
  width: 100%;
  font-family: 'JetBrains Mono', Consolas, monospace;
  font-size: 12px;
}

.schema-actions {
  margin-top: 8px;
}

.workspace-right {
  .form-item {
    display: flex;
    flex-direction: column;
    gap: 6px;
    margin-bottom: 12px;
  }

  .form-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 0 10px;
  }

  .form-label {
    font-size: 12px;
    color: rgba(0, 0, 0, 0.65);
  }

  .form-help {
    margin-bottom: 0;
    font-size: 11px;
    color: rgba(0, 0, 0, 0.35);
    line-height: 1.5;
  }
}
</style>
