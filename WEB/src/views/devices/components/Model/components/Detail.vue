<template>
  <BasicModal
    @register="register"
    title="属性历史数据"
    width="96%"
    :min-height="720"
    :centered="true"
    wrap-class-name="property-history-modal"
    @cancel="handleCancel"
    @ok="handleSubmit"
  >
    <div class="history-modal">
      <div class="filter-bar">
        <div class="filter-group">
          <span class="filter-label">时间范围</span>
          <Segmented v-model:value="currentTime" :options="timeList" @change="handleQuickRangeChange" />
        </div>
        <div class="filter-divider"></div>
        <div class="filter-group custom-range">
          <span class="filter-label">自定义</span>
          <RangePicker
            v-model:value="customTime"
            :show-time="true"
            :disabled-date="disabledDate"
            format="YYYY-MM-DD HH:mm:ss"
            value-format="YYYY-MM-DD HH:mm:ss"
            :allow-clear="true"
            @calendar-change="calendarPriceRangeChange"
            @change="handleCustomRangeChange"
          />
        </div>
        <div class="filter-spacer"></div>
        <Segmented
          v-model:value="viewMode"
          :options="viewModeOptions"
          class="view-switch"
          @change="handleViewModeChange"
        />
      </div>

      <div v-if="viewMode === 'history'" class="history-content">
        <section class="trend-panel">
          <div class="panel-heading">
            <div>
              <div class="panel-title">{{ state.propertyName }}趋势</div>
              <div class="panel-subtitle">{{ activeRangeLabel }}</div>
            </div>
            <div v-if="latestPoint" class="latest-value">
              <span>最新值</span>
              <strong>{{ latestPoint.value }}{{ state.unit || '' }}</strong>
            </div>
          </div>
          <div class="chart-wrap">
            <div ref="chartRef" class="trend-chart"></div>
            <Empty
              v-if="!trendData.length"
              class="chart-empty"
              :image="Empty.PRESENTED_IMAGE_SIMPLE"
              description="暂无趋势数据"
            />
          </div>
        </section>

        <section class="table-panel">
          <div class="panel-heading compact-heading">
            <div>
              <div class="panel-title">数据明细</div>
              <div class="panel-subtitle">
                共 {{ tableRowCount }} 条记录
                <template v-if="trendData.length"> · 趋势点 {{ trendData.length }}</template>
                <template v-if="state.industrialPoint"> · 报文为响应 PDU，不含 MBAP 事务头</template>
              </div>
            </div>
          </div>
          <div class="table-body">
            <BasicTable @register="registerTable" />
          </div>
        </section>
      </div>

      <div v-else class="predict-content">
        <section class="trend-panel predict-chart-panel">
          <div class="panel-heading">
            <div>
              <div class="panel-title">采集预测 · {{ state.propertyName }}</div>
              <div class="panel-subtitle">融合原始历史运行数据与最新采样值，95% 预测区间</div>
            </div>
            <div v-if="predictResult.latestValue != null" class="latest-value">
              <span>最新值</span>
              <strong>{{ predictResult.latestValue }}{{ state.unit || '' }}</strong>
            </div>
          </div>
          <div class="chart-wrap">
            <div ref="predictChartRef" class="trend-chart"></div>
            <Empty
              v-if="!predictResult.predictReady"
              class="chart-empty"
              :image="Empty.PRESENTED_IMAGE_SIMPLE"
              :description="predictResult.message || '暂无预测数据'"
            />
          </div>
        </section>

        <section class="predict-side">
          <div class="panel-heading compact-heading">
            <div>
              <div class="panel-title">智能预测诊断</div>
              <div class="panel-subtitle">加权数据特征，实时偏差检测，阈值风险预测</div>
            </div>
            <Tag :color="riskTagColor">{{ predictResult.riskMessage || '待分析' }}</Tag>
          </div>

          <div class="predict-side-body">
            <div class="risk-card">
              <div class="risk-title">综合故障风险 {{ predictResult.failureRisk ?? 0 }}%</div>
              <Progress
                :percent="predictResult.failureRisk || 0"
                :stroke-color="riskTagColor === 'red' ? '#ff4d4f' : riskTagColor === 'orange' ? '#fa8c16' : '#52c41a'"
                :show-info="false"
              />
              <div class="risk-desc">{{ predictResult.failureMessage || '等待有效样本' }}</div>
            </div>

            <div class="diag-list">
              <div class="diag-item">
                <div class="diag-name">异常检测</div>
                <div class="diag-msg">{{ predictResult.anomalyMessage || '--' }}</div>
                <div class="diag-meta">异常占比 {{ predictResult.anomalyRatio ?? 0 }}% · 灵敏度 {{ predictResult.sensitivity ?? 0 }}%</div>
              </div>
              <div class="diag-item">
                <div class="diag-name">故障风险</div>
                <div class="diag-msg">{{ predictResult.failureMessage || '--' }}</div>
                <div class="diag-meta">预测窗口至 {{ predictEndLabel }}</div>
              </div>
              <div class="diag-item">
                <div class="diag-name">性能衰减</div>
                <div class="diag-msg">{{ predictResult.degradationMessage || '--' }}</div>
                <div class="diag-meta">衰减 {{ predictResult.degradationDegree ?? 0 }}% · 窗口变化 {{ predictResult.windowChange ?? 0 }}</div>
              </div>
              <div class="diag-item">
                <div class="diag-name">运转状态</div>
                <div class="diag-msg">{{ predictResult.runStateMessage || '未知' }}</div>
              </div>
            </div>

            <div class="summary-grid">
              <div><span>有效样本</span><strong>{{ predictResult.sampleCount ?? 0 }} 条</strong></div>
              <div><span>单位时间趋势</span><strong>{{ predictResult.hourlyTrend ?? '--' }}{{ state.unit || '' }}/时</strong></div>
              <div><span>设备状态</span><strong>{{ predictResult.deviceStatus || '--' }}</strong></div>
              <div><span>越限风险</span><strong>{{ predictResult.compressionRisk ?? 0 }}%</strong></div>
            </div>
          </div>
        </section>
      </div>
    </div>
  </BasicModal>
</template>

<script lang="ts" setup name="Detail">
import { computed, nextTick, reactive, ref, Ref, watch } from 'vue';
import moment from 'moment';
import { Empty, Progress, RangePicker, Segmented, Tag } from 'ant-design-vue';
import { BasicModal, useModalInner } from '@/components/Modal';
import { BasicTable, useTable } from '@/components/Table';
import { useECharts } from '@/hooks/web/useECharts';
import { getDevicethingmodelsHistory, predictPropertyTrend } from '@/api/device/devices';
import { detailColumns } from '../tableData';
import { useRoute } from 'vue-router';
import { buildPredictionAnalysis } from './predictionAnalysis';

interface TrendPoint {
  time: string;
  timestamp: number;
  value: number;
}

const route = useRoute();
const chartRef = ref<HTMLDivElement | null>(null);
const predictChartRef = ref<HTMLDivElement | null>(null);
const { setOptions, resize, dispose: disposeChart } = useECharts(chartRef as Ref<HTMLDivElement>);
const {
  setOptions: setPredictOptions,
  resize: resizePredict,
  dispose: disposePredictChart,
} = useECharts(predictChartRef as Ref<HTMLDivElement>);

const state = reactive({
  unit: '',
  propertyName: '',
  deviceIdentification: '',
  identifier: '',
  industrialPoint: null as Record<string, any> | null,
});

const viewMode = ref<'history' | 'predict'>('history');
const viewModeOptions = [
  { label: '历史运行数据', value: 'history' },
  { label: '预测诊断', value: 'predict' },
];

const predictResult = reactive<Record<string, any>>({
  predictReady: false,
  message: '',
  sampleCount: 0,
});

const riskTagColor = computed(() => {
  const level = predictResult.riskLevel;
  if (level === 'HIGH') return 'red';
  if (level === 'MEDIUM') return 'orange';
  if (level === 'LOW') return 'green';
  return 'default';
});

const predictEndLabel = computed(() => {
  if (!predictResult.predictEndTs) return '--';
  return moment(Number(predictResult.predictEndTs)).format('YYYY-MM-DD HH:mm:ss');
});

const currentTime = ref<number | string>(1);
const timeList = [
  { label: '1小时', value: 1 },
  { label: '12小时', value: 12 },
  { label: '24小时', value: 24 },
  { label: '7天', value: 168 },
  { label: '30天', value: 720 },
];
const customTime = ref<string[]>([]);
const selectPriceDate = ref<any>('');
const trendData = ref<TrendPoint[]>([]);
const tableRowCount = ref(0);

const activeRangeLabel = computed(() => {
  if (customTime.value?.length === 2) {
    return `${customTime.value[0]} 至 ${customTime.value[1]}`;
  }
  return timeList.find((item) => item.value === currentTime.value)?.label || '';
});

const latestPoint = computed(() => {
  if (!trendData.value.length) return null;
  return [...trendData.value].sort((a, b) => b.timestamp - a.timestamp)[0];
});

function getTimeRange() {
  if (customTime.value?.length === 2) {
    return [Date.parse(customTime.value[0]), Date.parse(customTime.value[1])];
  }
  const endTime = Date.now();
  return [endTime - 60 * 60 * 1000 * Number(currentTime.value), endTime];
}

function handleQuickRangeChange() {
  customTime.value = [];
  reload({ page: 1 }).then(() => {
    if (viewMode.value === 'predict') {
      loadPredict();
    }
  });
}

function calendarPriceRangeChange(date) {
  selectPriceDate.value = date?.[0];
}

function disabledDate(current) {
  if (!selectPriceDate.value) return false;
  return (
    current < moment(selectPriceDate.value).subtract(90, 'days') ||
    current > moment(selectPriceDate.value).add(90, 'days')
  );
}

function handleCustomRangeChange(dates) {
  customTime.value = dates || [];
  selectPriceDate.value = '';
  if (customTime.value.length === 2) {
    reload({ page: 1 }).then(() => {
      if (viewMode.value === 'predict') {
        loadPredict();
      }
    });
  }
}

function handleViewModeChange() {
  nextTick(async () => {
    if (viewMode.value === 'predict') {
      await loadPredict();
      nextTick(() => resizePredict());
    } else {
      disposePredictChart();
      if (!trendData.value.length) {
        await reload({ page: 1 });
      } else {
        await renderChart();
      }
      nextTick(() => {
        resize();
        redoHeight();
      });
    }
  });
}

/** 用已加载的历史点做本地预测，避免后端另查 TDEngine 偶发空数据 */
function applyLocalPredict() {
  const source = trendData.value.map((p) => ({ ts: p.timestamp, dataValue: p.value }));
  const analysis = buildPredictionAnalysis(
    source,
    latestPoint.value?.value,
    latestPoint.value?.timestamp,
    [],
    undefined,
  );

  Object.keys(predictResult).forEach((k) => delete predictResult[k]);

  if (!analysis.available) {
    predictResult.predictReady = false;
    predictResult.message = analysis.reason || '暂无预测数据';
    predictResult.sampleCount = analysis.sampleCount;
    predictResult.failureRisk = 0;
    predictResult.riskMessage = '待分析';
    predictResult.riskLevel = 'PENDING';
    return;
  }

  const riskLevelMap: Record<string, string> = {
    high: 'HIGH',
    medium: 'MEDIUM',
    low: 'LOW',
  };

  Object.assign(predictResult, {
    predictReady: true,
    message: '',
    sampleCount: analysis.sampleCount,
    latestValue: analysis.latestValue,
    latestTs: analysis.samples[analysis.samples.length - 1]?.ts,
    history: analysis.samples.map((s) => ({ ts: s.ts, value: s.value })),
    prediction: analysis.forecast.map((p) => ({ ts: p.ts, value: Number(p.value.toFixed(2)) })),
    upperBound: analysis.forecast.map((p) => ({ ts: p.ts, value: Number(p.upper.toFixed(2)) })),
    lowerBound: analysis.forecast.map((p) => ({ ts: p.ts, value: Number(p.lower.toFixed(2)) })),
    predictEndTs: analysis.forecastEndTs,
    hourlyTrend: Number(analysis.slopePerHour.toFixed(2)),
    anomalyRatio: analysis.anomalyScore,
    sensitivity: 35,
    anomalyMessage: analysis.anomalyText,
    failureRisk: analysis.faultRisk,
    compressionRisk: analysis.thresholdHitTs ? 40 : 0,
    riskLevel: riskLevelMap[analysis.riskLevel] || 'LOW',
    riskMessage:
      analysis.riskLevel === 'high' ? '高风险' : analysis.riskLevel === 'medium' ? '中风险' : '低风险',
    failureMessage: analysis.riskText,
    degradationDegree: analysis.degradationScore,
    degradationMessage: analysis.degradationText,
    windowChange: Number(
      (
        (analysis.predictedValue ?? 0) - (analysis.latestValue ?? 0)
      ).toFixed(2),
    ),
    deviceStatus: analysis.connectionStatusText,
    runStateMessage: analysis.connectionStatusText === '在线' ? '运转正常' : analysis.connectionText || '未知',
  });
}

async function loadPredict() {
  predictResult.predictReady = false;
  predictResult.message = '分析中...';

  // 与历史运行数据共用同一批样本，保证「有历史就能预测」
  if (!trendData.value.length) {
    try {
      await reload({ page: 1 });
    } catch (e) {
      console.error(e);
    }
  }

  applyLocalPredict();
  await renderPredictChart();

  // 后端预测作为增强：成功且样本更多时再覆盖；失败不影响展示
  try {
    const [startTime, endTime] = getTimeRange();
    const res = await predictPropertyTrend({
      deviceIdentification: state.deviceIdentification,
      propertyCode: state.identifier,
      propertyName: state.propertyName,
      unit: state.unit,
      startTime,
      endTime,
      predictPoints: 12,
    });
    const data = res?.data || res || {};
    if (data?.predictReady && (data.sampleCount || 0) >= (predictResult.sampleCount || 0)) {
      Object.keys(predictResult).forEach((k) => delete predictResult[k]);
      Object.assign(predictResult, data);
      await renderPredictChart();
    }
  } catch (e) {
    console.warn('后端预测不可用，已使用本地诊断结果', e);
  }
}

function buildTimeAxisZoom() {
  return [
    {
      type: 'inside',
      xAxisIndex: 0,
      filterMode: 'none',
      zoomOnMouseWheel: true,
      moveOnMouseMove: true,
      moveOnMouseWheel: false,
    },
    {
      type: 'slider',
      xAxisIndex: 0,
      filterMode: 'none',
      height: 28,
      bottom: 8,
      left: 56,
      right: 24,
      borderColor: '#e6edf5',
      backgroundColor: '#f8fafc',
      fillerColor: 'rgba(22, 119, 255, 0.15)',
      handleSize: '110%',
      handleStyle: {
        color: '#1677ff',
        borderColor: '#1677ff',
      },
      moveHandleSize: 8,
      moveHandleStyle: {
        color: '#91caff',
      },
      dataBackground: {
        lineStyle: { color: '#91caff', width: 1 },
        areaStyle: { color: 'rgba(22, 119, 255, 0.08)' },
      },
      selectedDataBackground: {
        lineStyle: { color: '#1677ff', width: 1.5 },
        areaStyle: { color: 'rgba(22, 119, 255, 0.2)' },
      },
      textStyle: {
        color: '#8c8c8c',
        fontSize: 11,
      },
      labelFormatter: (value: number) => moment(value).format('MM-DD HH:mm'),
      brushSelect: false,
      showDetail: true,
      realtime: true,
    },
  ];
}

async function renderPredictChart() {
  await nextTick();
  disposePredictChart();
  await nextTick();
  if (!predictResult.predictReady) return;

  const history = (predictResult.history || []).map((p: any) => [p.ts, p.value]);
  const prediction = (predictResult.prediction || []).map((p: any) => [p.ts, p.value]);
  const upper = (predictResult.upperBound || []).map((p: any) => [p.ts, p.value]);
  const lower = (predictResult.lowerBound || []).map((p: any) => [p.ts, p.value]);

  // 置信带：用堆叠面积近似
  const band = upper.map((u: any[], i: number) => {
    const l = lower[i]?.[1] ?? u[1];
    return [u[0], u[1] - l];
  });

  await setPredictOptions({
    color: ['#1677ff', '#722ed1', '#52c41a'],
    legend: {
      data: ['历史运行数据', '预测趋势', '实时数据'],
      top: 0,
      right: 8,
    },
    grid: { left: 56, right: 24, top: 36, bottom: 72 },
    tooltip: { trigger: 'axis' },
    dataZoom: buildTimeAxisZoom(),
    xAxis: {
      type: 'time',
      axisLabel: { formatter: (value: number) => moment(value).format('MM-DD HH:mm') },
    },
    yAxis: {
      type: 'value',
      name: state.unit ? `单位：${state.unit}` : undefined,
      scale: true,
    },
    series: [
      {
        name: '历史运行数据',
        type: 'line',
        showSymbol: history.length < 60,
        data: history,
        lineStyle: { width: 2.5, color: '#1677ff' },
        itemStyle: { color: '#1677ff' },
      },
      {
        name: '置信下界',
        type: 'line',
        data: lower,
        lineStyle: { opacity: 0 },
        stack: 'confidence',
        symbol: 'none',
        areaStyle: { color: 'transparent' },
      },
      {
        name: '95%区间',
        type: 'line',
        data: band,
        lineStyle: { opacity: 0 },
        stack: 'confidence',
        symbol: 'none',
        areaStyle: { color: 'rgba(114, 46, 209, 0.15)' },
      },
      {
        name: '预测趋势',
        type: 'line',
        data: prediction,
        showSymbol: true,
        symbol: 'circle',
        symbolSize: 7,
        lineStyle: { width: 2, type: 'dashed', color: '#722ed1' },
        itemStyle: { color: '#722ed1', borderColor: '#fff', borderWidth: 1 },
      },
      {
        name: '实时数据',
        type: 'scatter',
        data:
          predictResult.latestTs != null
            ? [[predictResult.latestTs, predictResult.latestValue]]
            : [],
        symbolSize: 10,
        itemStyle: { color: '#52c41a' },
      },
    ],
  } as any);
  resizePredict();
}

interface ParsedHistoryValue {
  display: string;
  numeric: number | null;
}

function toChartNumber(value: unknown): number | null {
  if (typeof value === 'boolean') return value ? 1 : 0;
  if (typeof value === 'number') return Number.isFinite(value) ? value : null;
  if (value == null || value === '') return null;
  const text = String(value).trim();
  if (!text) return null;
  if (text === 'true' || text === 'TRUE') return 1;
  if (text === 'false' || text === 'FALSE') return 0;
  const numeric = Number(text);
  return Number.isFinite(numeric) ? numeric : null;
}

function extractRawPayload(raw: unknown, identifier: string): string | null {
  if (raw == null || !identifier) return null;
  const text = String(raw).trim();
  if (!text.startsWith('{')) return null;
  try {
    const parsed = JSON.parse(text) as Record<string, unknown>;
    const rawMap = parsed?._raw;
    if (rawMap && typeof rawMap === 'object' && !Array.isArray(rawMap)) {
      const payload = (rawMap as Record<string, unknown>)[identifier];
      return payload == null ? null : String(payload);
    }
  } catch {
    // ignore
  }
  return null;
}

function extractLoosePropertyValue(text: string, identifier: string): string | null {
  if (!text || !identifier) return null;
  const escaped = identifier.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  const match = text.match(new RegExp(`(?:^|[,{\\s])${escaped}\\s*:\\s*([^,}]+)`));
  return match ? match[1].trim() : null;
}

function parseHistoryDataValue(raw: unknown, identifier: string): ParsedHistoryValue {
  if (raw == null || raw === '') {
    return { display: '--', numeric: null };
  }
  const text = String(raw).trim();
  if (!text) {
    return { display: '--', numeric: null };
  }

  if (!text.startsWith('{') && !text.startsWith('[')) {
    return { display: text, numeric: toChartNumber(text) };
  }

  try {
    const parsed = JSON.parse(text);
    if (parsed != null && typeof parsed === 'object' && !Array.isArray(parsed)) {
      const record = parsed as Record<string, unknown>;
      let value = identifier ? record[identifier] : undefined;
      const properties = record.properties;
      if (value == null && properties && typeof properties === 'object' && !Array.isArray(properties)) {
        value = (properties as Record<string, unknown>)[identifier];
      }
      const dataField = record.data;
      if (value == null && dataField && typeof dataField === 'object' && !Array.isArray(dataField)) {
        value = (dataField as Record<string, unknown>)[identifier];
      }
      if (value == null && record.value != null && Object.keys(record).length <= 2) {
        value = record.value;
      }
      if (value == null && record._value != null) {
        value = record._value;
      }
      if (value == null) {
        const candidates = Object.entries(record).filter(([key]) => !key.startsWith('_'));
        if (candidates.length === 1) {
          value = candidates[0][1];
        }
      }
      if (value != null) {
        return {
          display: String(value),
          numeric: toChartNumber(value),
        };
      }
    }
  } catch {
    // 非标准 JSON，尝试 {key:value} 宽松格式
  }

  const loose = extractLoosePropertyValue(text, identifier);
  if (loose != null) {
    return {
      display: loose,
      numeric: toChartNumber(loose),
    };
  }

  return {
    display: text,
    numeric: toChartNumber(text),
  };
}

async function renderChart() {
  // 弹窗 destroyOnClose 后 DOM 重建，先丢掉旧实例再绑定新节点
  await nextTick();
  disposeChart();
  await nextTick();

  if (!trendData.value.length) {
    return;
  }
  const sorted = [...trendData.value].sort((a, b) => a.timestamp - b.timestamp);
  await setOptions({
    grid: { left: 56, right: 24, top: 24, bottom: 72 },
    tooltip: {
      trigger: 'axis',
      valueFormatter: (value) => `${value}${state.unit || ''}`,
    },
    dataZoom: buildTimeAxisZoom(),
    xAxis: {
      type: 'time',
      axisLabel: {
        formatter: (value: number) => moment(value).format('MM-DD HH:mm'),
      },
    },
    yAxis: {
      type: 'value',
      name: state.unit ? `单位：${state.unit}` : undefined,
      scale: true,
    },
    series: [
      {
        type: 'line',
        name: state.propertyName,
        showSymbol: sorted.length < 80,
        data: sorted.map((item) => [item.timestamp, item.value]),
        lineStyle: { width: 2.5, color: '#1677ff' },
        itemStyle: { color: '#1677ff' },
      },
    ],
  } as any);
  resize();
}

const [register, { closeModal, getOpen }] = useModalInner(({ data }) => {
  state.unit = data.unit || '';
  state.propertyName = data.propertyName || data.propertyCode;
  state.deviceIdentification = String(
    data.deviceIdentification || route.params.deviceIdentification || '',
  );
  state.identifier = data.propertyCode;
  state.industrialPoint = data.industrialPoint || null;
  currentTime.value = 1;
  customTime.value = [];
  trendData.value = [];
  tableRowCount.value = 0;
  viewMode.value = 'history';
  Object.keys(predictResult).forEach((k) => delete predictResult[k]);
  predictResult.predictReady = false;
  disposeChart();
  disposePredictChart();

  const valueTitle = state.industrialPoint
    ? `解析值${state.unit ? `（${state.unit}）` : ''}`
    : `${state.propertyName}${state.unit ? `（${state.unit}）` : ''}`;
  const columns: any[] = [...detailColumns(), { title: valueTitle, dataIndex: 'dataValue' }];
  if (state.industrialPoint) {
    columns.push(
      {
        title: '寄存器值',
        dataIndex: 'rawRegister',
        width: 120,
        customRender: ({ record }) => buildRawDisplay(record.rawData, state.industrialPoint).register,
      },
      {
        title: '数值进制',
        dataIndex: 'valueRadix',
        width: 105,
        customRender: ({ record }) => buildRawDisplay(record.rawData, state.industrialPoint).radix,
      },
      {
        title: '报文原始数据（PDU）',
        dataIndex: 'rawPayload',
        width: 260,
        customRender: ({ record }) => record.rawData || '--',
      },
    );
  }
  setColumns(columns);
  reload({ page: 1 });
});

watch(getOpen, (open) => {
  if (!open) {
    disposeChart();
    disposePredictChart();
    trendData.value = [];
    tableRowCount.value = 0;
  }
});

const [registerTable, { setColumns, reload, redoHeight }] = useTable({
  canResize: false,
  scroll: { y: 520 },
  api: getDevicethingmodelsHistory,
  bordered: false,
  showIndexColumn: false,
  useSearchForm: false,
  pagination: { pageSize: 1000, hideOnSinglePage: true },
  fetchSetting: { listField: 'data', totalField: 'total' },
  beforeFetch(ext) {
    const [startTime, endTime] = getTimeRange();
    return {
      ...ext,
      pageSize: 1000,
      deviceIdentification: state.deviceIdentification,
      identifier: state.identifier,
      startTime,
      endTime,
    };
  },
  afterFetch(data) {
    const identifier = state.identifier;
    const rows = (data || []).map((item) => {
      const originalValue = item.dataValue ?? item.datavalue;
      const parsed = parseHistoryDataValue(originalValue, identifier);
      const rawData = item.rawData || extractRawPayload(originalValue, identifier);
      return {
        ...item,
        dataValue: parsed.display,
        rawData: rawData || undefined,
        _chartValue: parsed.numeric,
      };
    });

    tableRowCount.value = rows.length;
    trendData.value = rows
      .filter((item) => item._chartValue != null && Number.isFinite(item._chartValue))
      .map((item) => ({
        time: moment(Number(item.ts)).format('YYYY-MM-DD HH:mm:ss'),
        timestamp: Number(item.ts),
        value: item._chartValue as number,
      }))
      .filter((item) => Number.isFinite(item.timestamp));

    nextTick(() => {
      if (viewMode.value === 'history') {
        renderChart();
        resize();
        redoHeight();
      }
    });
    return rows.map(({ _chartValue, ...rest }) => rest);
  },
  immediate: false,
});

function resetAndClose() {
  trendData.value = [];
  tableRowCount.value = 0;
  customTime.value = [];
  state.industrialPoint = null;
  viewMode.value = 'history';
  disposeChart();
  disposePredictChart();
  closeModal();
}

const handleSubmit = resetAndClose;
const handleCancel = resetAndClose;

interface RawDisplay {
  register: string;
  radix: string;
}

function emptyRawDisplay(value: unknown = '--'): RawDisplay {
  const text = value == null || value === '' ? '--' : String(value);
  return { register: text, radix: '--' };
}

function buildRawDisplay(rawData: unknown, point: Record<string, any> | null): RawDisplay {
  if (!rawData || !point) return emptyRawDisplay();
  const tokens = String(rawData).trim().split(/\s+/);
  if (tokens.length < 4 || tokens.some((token) => !/^[0-9a-fA-F]{2}$/.test(token))) {
    return emptyRawDisplay();
  }
  const byteCount = Number.parseInt(tokens[2], 16);
  const dataTokens = tokens.slice(3, 3 + byteCount);
  if (!dataTokens.length) return emptyRawDisplay();
  const bytes = dataTokens.map((token) => Number.parseInt(token, 16));
  let registerValue = 0;
  for (const byte of bytes) {
    registerValue = (registerValue << 8) | byte;
  }
  const radix = Number(point.valueRadix || 16);
  const radixLabel =
    radix === 2 ? 'BIN / 2进制' : radix === 8 ? 'OCT / 8进制' : radix === 10 ? 'DEC / 10进制' : 'HEX / 16进制';
  const registerText =
    radix === 2
      ? `0b${registerValue.toString(2)}`
      : radix === 8
        ? `0o${registerValue.toString(8)}`
        : radix === 10
          ? String(registerValue)
          : `0x${registerValue.toString(16).toUpperCase().padStart(Math.max(2, bytes.length * 2), '0')}`;
  return { register: registerText, radix: radixLabel };
}
</script>

<style lang="less" scoped>
.history-modal {
  display: flex;
  flex-direction: column;
  gap: 16px;
  min-height: min(720px, calc(100vh - 140px));
  height: min(780px, calc(100vh - 120px));
  padding: 8px 8px 12px;
  box-sizing: border-box;
}

.filter-bar {
  flex-shrink: 0;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 16px;
  min-height: 58px;
  padding: 12px 18px;
  background: #f8fafc;
  border: 1px solid #e6edf5;
  border-radius: 8px;
}

.filter-group {
  display: flex;
  align-items: center;
  gap: 12px;
}

.filter-label {
  color: #52657a;
  white-space: nowrap;
  font-size: 14px;
}

.filter-divider {
  width: 1px;
  height: 28px;
  background: #e5e7eb;
}

.filter-spacer {
  flex: 1;
  min-width: 16px;
}

.view-switch {
  flex-shrink: 0;
}

.custom-range {
  :deep(.ant-picker-range) {
    width: min(360px, 42vw);
  }
}

.history-content,
.predict-content {
  flex: 1;
  min-height: 0;
  display: grid;
  gap: 16px;
}

/* 历史 / 预测统一左右结构，体量对齐 */
.history-content {
  grid-template-columns: minmax(0, 1.28fr) minmax(420px, 0.85fr);
}

.predict-content {
  grid-template-columns: minmax(0, 1.35fr) minmax(380px, 0.75fr);
}

.predict-side {
  display: flex;
  flex-direction: column;
  min-width: 0;
  min-height: 0;
  border: 1px solid #e6edf5;
  border-radius: 8px;
  background: #fff;
  overflow: hidden;
}

.predict-side-body {
  flex: 1;
  min-height: 0;
  overflow: auto;
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 14px 16px 16px;
}

.risk-card {
  padding: 14px 16px;
  border-radius: 8px;
  background: #f6ffed;
  border: 1px solid #b7eb8f;

  .risk-title {
    font-size: 16px;
    font-weight: 600;
    margin-bottom: 10px;
    color: #262626;
  }

  .risk-desc {
    margin-top: 10px;
    font-size: 13px;
    color: #8c8c8c;
    line-height: 1.5;
  }
}

.diag-list {
  display: flex;
  flex-direction: column;
  gap: 10px;

  .diag-item {
    padding: 12px 14px;
    border-radius: 8px;
    background: #fafafa;
    border: 1px solid #f0f0f0;
  }

  .diag-name {
    font-size: 12px;
    color: #8c8c8c;
  }

  .diag-msg {
    margin-top: 6px;
    font-size: 14px;
    font-weight: 500;
    color: #262626;
    line-height: 1.45;
  }

  .diag-meta {
    margin-top: 6px;
    font-size: 12px;
    color: #8c8c8c;
  }
}

.summary-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;

  div {
    padding: 10px 12px;
    background: #fafafa;
    border-radius: 8px;
    border: 1px solid #f0f0f0;

    span {
      display: block;
      font-size: 12px;
      color: #8c8c8c;
    }

    strong {
      display: block;
      margin-top: 4px;
      font-size: 14px;
      color: #262626;
    }
  }
}

.trend-panel,
.table-panel {
  display: flex;
  flex-direction: column;
  min-width: 0;
  min-height: 0;
  border: 1px solid #e6edf5;
  border-radius: 8px;
  overflow: hidden;
  background: #fff;
}

.panel-heading {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  min-height: 72px;
  padding: 14px 20px;
  border-bottom: 1px solid #edf1f5;
}

.compact-heading {
  min-height: 64px;
}

.panel-title {
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
  line-height: 24px;
}

.panel-subtitle {
  margin-top: 4px;
  color: #98a2b3;
  font-size: 12px;
  line-height: 18px;
}

.latest-value {
  display: flex;
  align-items: baseline;
  gap: 10px;
  flex-shrink: 0;
  color: #98a2b3;
  font-size: 12px;

  strong {
    max-width: 280px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    color: #1677ff;
    font-size: 26px;
    font-weight: 600;
    line-height: 32px;
  }
}

.chart-wrap {
  position: relative;
  flex: 1;
  min-height: 0;
  padding: 8px 12px 12px;
}

.trend-chart {
  width: 100%;
  height: 100%;
  min-height: 420px;
}

.chart-empty {
  position: absolute;
  inset: 8px 12px 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.92);
}

.table-body {
  flex: 1;
  min-height: 0;
  overflow: hidden;
  padding: 0 8px 8px;

  :deep(.ant-table-wrapper) {
    padding: 0;
    height: 100%;
  }

  :deep(.vben-basic-table) {
    height: 100%;
  }

  :deep(.ant-table-body) {
    max-height: 520px !important;
  }

  :deep(.ant-table-tbody > tr > td) {
    color: #262626;
  }

  :deep(.ellipsis-span) {
    color: inherit;
  }
}

@media (max-width: 1200px) {
  .history-modal {
    height: auto;
    min-height: 560px;
  }

  .history-content,
  .predict-content {
    grid-template-columns: 1fr;
  }

  .trend-chart {
    min-height: 320px;
  }
}
</style>

<style lang="less">
.property-history-modal {
  .ant-modal {
    max-width: 1600px;
    top: 40px;
    padding-bottom: 0;
  }

  .ant-modal-body {
    padding: 12px 16px 8px !important;
  }

  .scrollbar__wrap {
    margin-bottom: 0 !important;
  }
}
</style>
