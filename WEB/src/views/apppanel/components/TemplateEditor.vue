<template>
  <BasicDrawer
    v-bind="$attrs"
    @register="register"
    :title="getTitle"
    width="95%"
    placement="right"
    :showFooter="true"
    :showCancelBtn="false"
    :showOkBtn="false"
    destroy-on-close
    class="panel-editor-drawer"
  >
    <template #footer>
      <div class="footer-buttons">
        <Button v-if="!isView" @click="handleClose">取消</Button>
        <Button v-if="!isView" type="primary" :loading="saving" @click="handleSave">
          {{ editingId ? '保存修改' : '保存为草稿' }}
        </Button>
        <Button v-else type="primary" @click="handleClose">关闭</Button>
      </div>
    </template>

    <div class="panel-editor">
      <!-- 基本信息（绑定产品与产品管理打通） -->
      <div class="panel-meta">
        <BasicForm @register="registerForm" :compact="true" />
        <Alert
          v-if="!isView && productBindInfo"
          :type="productBindType"
          show-icon
          class="meta-alert"
          :message="productBindInfo"
        />
      </div>

      <div class="panel-workspace">
        <!-- 左：组件库与组件列表 -->
        <div class="workspace-left">
          <div class="left-section">
            <h4>组件库</h4>
            <div class="palette-grid">
              <Tooltip v-for="t in WIDGET_TYPES" :key="t.type" :title="t.desc">
                <div class="palette-item" :class="{disabled: isView}" @click="!isView && addWidget(t.type)">
                  <span class="palette-icon">{{ t.icon }}</span>
                  <span>{{ t.label }}</span>
                </div>
              </Tooltip>
            </div>
          </div>

          <div class="left-section left-section-grow">
            <h4>
              面板组件（{{ widgets.length }}）
              <Select
                v-if="widgets.length === 0"
                size="small"
                placeholder="插入示例"
                style="width: 120px"
                :options="PRESET_OPTIONS"
                @change="applyPreset"
              />
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
                <span v-if="!isView" class="widget-item-actions stop">
                  <UpOutlined class="op" @click.stop="move(idx, -1)" />
                  <DownOutlined class="op" @click.stop="move(idx, 1)" />
                  <DeleteOutlined class="op danger" @click.stop="removeWidget(idx)" />
                </span>
              </div>
            </TransitionGroup>
          </div>

          <div class="left-section">
            <Checkbox v-if="!isView" :checked="sourceMode" @change="(e) => (sourceMode = e.target.checked)">JSON 源码模式</Checkbox>
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
          <template v-if="isView">
            <h4>模板信息</h4>
            <div class="form-item">
              <span class="form-label">模板编码</span>
              <span class="view-text">{{ formView.templateCode || '-' }}</span>
            </div>
            <div class="form-item">
              <span class="form-label">模板版本</span>
              <span class="view-text">v{{ formView.version ?? '-' }}</span>
            </div>
            <div class="form-item">
              <span class="form-label">模板状态</span>
              <span class="view-text">{{ formView.statusText }}</span>
            </div>
            <div class="form-item">
              <span class="form-label">备注</span>
              <span class="view-text">{{ formView.remark || '无' }}</span>
            </div>
            <p class="form-help">只读预览 · 点击「设计面板」可进入编辑</p>
          </template>
          <template v-else-if="activeWidget">
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
  </BasicDrawer>
</template>

<script lang="ts" setup name="appPanelTemplateEditor">
import {computed, reactive, ref, watch} from 'vue';
import {BasicDrawer, useDrawerInner} from '@/components/Drawer';
import {BasicForm, useForm} from '@/components/Form';
import {Button} from '@/components/Button';
import {
  Alert,
  Checkbox,
  Empty,
  Input,
  InputNumber,
  Select,
  Space,
  Switch,
  Textarea,
  Tooltip,
} from 'ant-design-vue';
import {DownOutlined, UpOutlined, DeleteOutlined} from '@ant-design/icons-vue';
import {createAppPanelTemplate, getAppPanelTemplatePage, updateAppPanelTemplate} from '@/api/device/appPanelTemplate';
import {getDeviceProfiles} from '@/api/device/product';
import {useMessage} from '@/hooks/web/useMessage';

const emit = defineEmits(['success']);
const {createMessage} = useMessage();

const saving = ref(false);
const sourceMode = ref(false);
const editingId = ref<number | null>(null);
const isView = ref(false);

// 只读模式下的模板摘要信息
const formView = reactive({
  templateCode: '',
  version: null as number | null,
  statusText: '',
  remark: '',
});

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

const widgets = ref<any[]>([]);
const activeUid = ref<string | null>(null);
const activeWidget = computed(() => widgets.value.find((w) => w.uid === activeUid.value));
const schemaText = ref('');
const productOptions = ref<{label: string; value: string}[]>([]);
// 产品 -> 已有模板映射（同一产品仅保留一个模板，联动提示）
const templateMap = ref<Record<string, {id: number; templateName: string; status: string; version: number}>>({});

const [register, {closeDrawer}] = useDrawerInner((data) => {
  isView.value = !!data?.isView;
  openLogic(data?.record ?? null);
});

// 表单值响应式镜像（BasicForm 无 formModel，经组件 onChange 同步）
const selectedName = ref('');
const selectedProduct = ref<string | undefined>(undefined);

const [registerForm, {setFieldsValue, validate, updateSchema, setProps}] = useForm({
  labelWidth: 100,
  baseColProps: {span: 6},
  showActionButtonGroup: false,
  compact: true,
  schemas: [
    {
      field: 'templateName',
      label: '模板名称',
      component: 'Input',
      required: true,
      componentProps: {
        placeholder: '如：智能插座控制面板',
        onChange: (v: any) => {
          selectedName.value = v?.target?.value ?? v ?? '';
        },
      },
    },
    {
      field: 'templateCode',
      label: '模板编码',
      component: 'Input',
      required: true,
      componentProps: {placeholder: '如：plug-panel-v1'},
    },
    {
      field: 'productIdentification',
      label: '绑定产品',
      component: 'Select',
      required: true,
      componentProps: {
        showSearch: true,
        optionFilterProp: 'label',
        placeholder: '选择要下发面板的产品',
        options: [] as any[],
        onChange: (v: string) => {
          selectedProduct.value = v;
        },
      },
    },
    {
      field: 'remark',
      label: '备注',
      component: 'Input',
      componentProps: {placeholder: '选填'},
    },
  ],
});

const getTitle = computed(() =>
  isView.value ? '查看面板模板' : editingId.value ? '编辑面板模板' : '新建面板模板',
);

const STATUS_TEXT: Record<string, string> = {DRAFT: '草稿', PUBLISHED: '已发布', DISABLED: '已停用'};

const previewDeviceName = computed(() => {
  const p = productOptions.value.find((o) => o.value === selectedProduct.value);
  return `${selectedName.value || '我的设备'} · ${p ? p.label.split('（')[0] : '已绑定产品'}`;
});

// 当前绑定产品的已有模板提示（与产品管理逻辑打通）
const productBindInfo = computed(() => {
  const pid = selectedProduct.value;
  if (!pid) return '';
  const t = templateMap.value[pid];
  if (!t) return '';
  const isSelf = editingId.value && t.id === editingId.value;
  const statusText = STATUS_TEXT[t.status] || t.status;
  return isSelf
    ? `该产品当前绑定模板：${t.templateName}（v${t.version} · ${statusText}）`
    : `该产品已存在模板「${t.templateName}」（v${t.version} · ${statusText}）。同一产品仅保留一个模板，保存后需发布才会对 App 生效`;
});
const productBindType = computed(() => {
  const t = selectedProduct.value ? templateMap.value[selectedProduct.value] : null;
  return t && (!editingId.value || t.id !== editingId.value) ? 'warning' : 'info';
});

async function loadProducts() {
  try {
    const [profilesRes, templatesRes] = await Promise.all([
      getDeviceProfiles({pageNum: 1, pageSize: 500}),
      getAppPanelTemplatePage({pageNum: 1, pageSize: 100}),
    ]);
    const rows = profilesRes?.data ?? profilesRes ?? [];
    productOptions.value = (rows || [])
      .filter((r) => r.productIdentification)
      .map((r) => ({label: `${r.productName}（${r.productIdentification}）`, value: r.productIdentification}));
    updateSchema([{field: 'productIdentification', componentProps: {options: productOptions.value}}]);
    const list = templatesRes?.data ?? templatesRes?.rows ?? templatesRes ?? [];
    templateMap.value = {};
    (list || []).forEach((t) => {
      if (t?.productIdentification) templateMap.value[t.productIdentification] = t;
    });
  } catch (e) {
    console.warn('加载产品/模板信息失败', e);
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

function applyPreset(kind: string) {
  const maker = presets[kind];
  if (!maker) return;
  maker().forEach((w) => widgets.value.push(w));
  syncSchemaText();
}

// 快速起步的行业常见面板示例
const PRESET_OPTIONS = [
  {label: '智能插座', value: 'plug'},
  {label: '环境监测', value: 'env'},
  {label: '智能安防', value: 'security'},
  {label: '智能家居', value: 'home'},
  {label: '储能电站', value: 'energy'},
];

const presets: Record<string, () => any[]> = {
  plug: () => [
    {uid: genUid(), type: 'switch', title: '电源开关', span: 'half', propertyCode: 'power', enumText: '开启:1\n关闭:0'},
    {uid: genUid(), type: 'status', title: '工作状态', span: 'half', propertyCode: 'work_status', enumText: '运行:RUNNING:#16c2a2\n待机:STANDBY:#8c8c8c\n故障:FAULT:#f5222d'},
    {uid: genUid(), type: 'text', title: '实时功率', span: 'half', propertyCode: 'power_consumption', unit: 'W'},
    {uid: genUid(), type: 'slider', title: '定时电量阈值', span: 'half', propertyCode: 'threshold', min: 0, max: 100, step: 5, unit: '%'},
    {uid: genUid(), type: 'button', title: '重启设备', span: 'full', serviceId: 'reboot', confirm: true},
  ],
  env: () => [
    {uid: genUid(), type: 'chart', title: '温度趋势', span: 'full', propertyCode: 'temperature', min: 0, max: 60, unit: '℃', color: '#2f6bff', maxPoints: 20},
    {uid: genUid(), type: 'gauge', title: '空气湿度', span: 'half', propertyCode: 'humidity', min: 0, max: 100, unit: '%', color: '#16c2a2'},
    {uid: genUid(), type: 'text', title: 'PM2.5', span: 'half', propertyCode: 'pm25', unit: 'μg/m³'},
    {uid: genUid(), type: 'status', title: '空气质量', span: 'full', propertyCode: 'air_quality', enumText: '优:EXCELLENT:#16c2a2\n良:GOOD:#52c41a\n轻度污染:LIGHT:#faad14\n重度污染:HEAVY:#f5222d'},
    {uid: genUid(), type: 'button', title: '一键巡检', span: 'full', serviceId: 'inspect', confirm: true},
  ],
  security: () => [
    {uid: genUid(), type: 'video', title: '门口摄像头', span: 'full'},
    {uid: genUid(), type: 'status', title: '布防状态', span: 'half', propertyCode: 'arm_status', enumText: '已布防:ARMED:#16c2a2\n已撤防:DISARMED:#8c8c8c'},
    {uid: genUid(), type: 'switch', title: '声光报警', span: 'half', propertyCode: 'siren', enumText: '开启:1\n关闭:0'},
    {uid: genUid(), type: 'button', title: '一键布防', span: 'half', serviceId: 'arm', confirm: true},
    {uid: genUid(), type: 'button', title: '紧急抓拍', span: 'half', serviceId: 'snapshot', confirm: false},
  ],
  home: () => [
    {uid: genUid(), type: 'switch', title: '客厅灯光', span: 'half', propertyCode: 'light', enumText: '开启:1\n关闭:0'},
    {uid: genUid(), type: 'slider', title: '灯光亮度', span: 'half', propertyCode: 'brightness', min: 0, max: 100, step: 5, unit: '%'},
    {uid: genUid(), type: 'gauge', title: '室内温度', span: 'half', propertyCode: 'temperature', min: 10, max: 40, unit: '℃', color: '#fa8c16'},
    {uid: genUid(), type: 'progress', title: '窗帘开度', span: 'half', propertyCode: 'curtain', min: 0, max: 100, unit: '%', color: '#2f6bff'},
    {uid: genUid(), type: 'chart', title: '用电功率', span: 'full', propertyCode: 'power', min: 0, max: 3000, unit: 'W', color: '#2f6bff', maxPoints: 20},
  ],
  energy: () => [
    {uid: genUid(), type: 'chart', title: '充放电功率', span: 'full', propertyCode: 'power', min: -100, max: 100, unit: 'kW', color: '#16c2a2', maxPoints: 20},
    {uid: genUid(), type: 'gauge', title: '电池电量', span: 'half', propertyCode: 'soc', min: 0, max: 100, unit: '%', color: '#16c2a2'},
    {uid: genUid(), type: 'status', title: '运行状态', span: 'half', propertyCode: 'run_status', enumText: '充电:CHARGING:#16c2a2\n放电:DISCHARGING:#fa8c16\n待机:STANDBY:#8c8c8c'},
    {uid: genUid(), type: 'progress', title: '负载率', span: 'half', propertyCode: 'load', min: 0, max: 100, unit: '%', color: '#2f6bff'},
    {uid: genUid(), type: 'text', title: '今日发电', span: 'half', propertyCode: 'today_kwh', unit: 'kWh'},
    {uid: genUid(), type: 'button', title: '紧急停机', span: 'full', serviceId: 'emergency_stop', confirm: true},
  ],
};

function buildWidgetsFromParsed(parsed): any[] {
  const rawList = parsed?.pages?.[0]?.widgets ?? [];
  return rawList.map((raw, i) => {
    const cfg = raw.config || {};
    return {
      uid: genUid(),
      id: raw.id || `${raw.type}_${i}`,
      type: raw.type,
      title: raw.title ?? '',
      span: raw.span === 'half' ? 'half' : 'full',
      propertyCode: raw.propertyCode,
      serviceId: raw.serviceId,
      config: cfg,
      enumText: enumToText(raw),
      confirm: cfg.confirm === true,
      min: cfg.min,
      max: cfg.max,
      step: cfg.step,
      unit: cfg.unit,
      color: cfg.color,
      maxPoints: cfg.maxPoints,
    };
  });
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

async function openLogic(record) {
  await loadProducts();
  editingId.value = record?.id ?? null;
  updateSchema([{field: 'templateCode', componentProps: {disabled: !!record?.id}}]);
  setProps({disabled: isView.value});
  selectedName.value = record?.templateName ?? '';
  selectedProduct.value = record?.productIdentification || undefined;
  await setFieldsValue({
    templateName: record?.templateName ?? '',
    templateCode: record?.templateCode ?? '',
    productIdentification: record?.productIdentification || undefined,
    remark: record?.remark ?? '',
  });
  formView.templateCode = record?.templateCode ?? '';
  formView.version = record?.version ?? null;
  formView.statusText = STATUS_TEXT[record?.status] || record?.status || '草稿';
  formView.remark = record?.remark ?? '';
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
}

function handleClose() {
  closeDrawer();
}

async function handleSave() {
  let values;
  try {
    values = await validate();
  } catch (e) {
    return; // 表单校验失败，antd 已给出提示
  }
  saving.value = true;
  try {
    const payload = {
      id: editingId.value ?? undefined,
      templateCode: (values.templateCode || '').trim(),
      templateName: (values.templateName || '').trim(),
      productIdentification: values.productIdentification || '',
      remark: values.remark,
      panelSchema: buildSchemaPayload(),
    };
    if (editingId.value) {
      await updateAppPanelTemplate(payload);
      createMessage.success('保存成功');
    } else {
      await createAppPanelTemplate(payload);
      createMessage.success('模板已创建为草稿，发布后对 App 生效');
    }
    closeDrawer();
    emit('success');
  } catch (e: any) {
    createMessage.error(e?.message || '保存失败');
  } finally {
    saving.value = false;
  }
}
</script>

<style lang="less" scoped>
.panel-editor {
  display: flex;
  flex-direction: column;
  gap: 12px;
  height: calc(100vh - 190px);
  min-height: 0;
}

.panel-meta {
  display: flex;
  flex-direction: column;
  gap: 8px;

  .meta-alert {
    margin-bottom: 0;
  }
}

.footer-buttons {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  gap: 8px;
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

    &.disabled {
      cursor: not-allowed;
      opacity: 0.6;

      &:hover {
        border-color: #d9d9d9;
        color: inherit;
        background: transparent;
      }
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

  .view-text {
    font-size: 13px;
    color: rgba(0, 0, 0, 0.85);
    word-break: break-all;
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
