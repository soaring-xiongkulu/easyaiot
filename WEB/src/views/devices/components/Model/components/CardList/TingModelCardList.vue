<template>
  <div class="model-card-list-wrapper">
    <Spin :spinning="state.loading">
      <List
        :grid="{ gutter: 16, xs: 1, sm: 2, md: 2, lg: 3, xl: 4, xxl: 4 }"
        :data-source="data"
        :pagination="paginationProp"
        class="model-list"
      >
        <template #renderItem="{ item }">
          <ListItem class="model-item">
            <div class="prop-card" :class="{ 'is-breach': isBreached(item) }">
              <div class="card-header">
                <div class="title-wrap">
                  <Tooltip :title="fullTitle(item)" placement="topLeft">
                    <span class="title">
                      <span class="name">{{ item.pointName || item.propertyName || '--' }}</span>
                      <span v-if="item.propertyCode" class="code">({{ item.propertyCode }})</span>
                    </span>
                  </Tooltip>
                </div>
                <span class="type-tag">属性</span>
              </div>

              <div class="card-body">
                <Tooltip :title="fullValue(item)" placement="top">
                  <div class="value-line" :class="[valueClass(item), { 'is-breach-value': isBreached(item) }]">
                    <span class="value">{{ fullValue(item) }}</span>
                  </div>
                </Tooltip>
              </div>

              <div class="card-footer">
                <div class="time">
                  <Icon icon="ant-design:clock-circle-outlined" class="time-icon" />
                  <span>{{ hasValidTs(item.ts) ? formatTime(item.ts) : '--' }}</span>
                </div>
                <div class="footer-actions" @click.stop>
                  <button type="button" class="history-btn" @click="handleThreshold(item)">
                    <Icon icon="ant-design:setting-outlined" />
                    <span>阈值</span>
                  </button>
                  <button type="button" class="history-btn" @click="handleView(item)">
                    <Icon icon="ant-design:line-chart-outlined" />
                    <span>历史</span>
                  </button>
                  <Tooltip title="刷新">
                    <button type="button" class="icon-btn" @click="handleRefresh(item)">
                      <Icon icon="ant-design:reload-outlined" />
                    </button>
                  </Tooltip>
                </div>
              </div>
            </div>
          </ListItem>
        </template>
      </List>
    </Spin>
  </div>
</template>
<script lang="ts" setup>
import {onMounted, reactive, ref, watch} from 'vue';
import {List, Spin, Tooltip} from 'ant-design-vue';
import {Icon} from '@/components/Icon';
import {propTypes} from '@/utils/propTypes';
import {isFunction} from '@/utils/is';
import {formatToDateTime} from '@/utils/dateUtil';
import {formatDeviceValue} from '@/utils/deviceValue';

const ListItem = List.Item;

const props = defineProps({
  params: propTypes.object.def({}),
  api: propTypes.func,
  activeKey: propTypes.string.def('card'),
  searchParams: propTypes.object.def({}),
  /** propertyCode -> { minValue, maxValue, enabled } */
  thresholdMap: propTypes.object.def({}),
  onlyThreshold: propTypes.bool.def(false),
});

const emit = defineEmits(['getMethod', 'refresh', 'view', 'threshold', 'tabChange', 'loaded']);

function isBreached(item: any) {
  const th = props.thresholdMap?.[item?.propertyCode];
  if (!th || th.enabled === 0) return false;
  const num = Number(item?.dataValue);
  if (!Number.isFinite(num)) return false;
  if (th.minValue != null && num < Number(th.minValue)) return true;
  if (th.maxValue != null && num > Number(th.maxValue)) return true;
  return false;
}

const data = ref<any[]>([]);
const total = ref(0);

const state = reactive({
  loading: true,
});

function formatTime(ts: number | string | null | undefined) {
  const n = Number(ts);
  if (!Number.isFinite(n) || n <= 0) return '--';
  return formatToDateTime(n);
}

function hasValidTs(ts: unknown) {
  const n = Number(ts);
  return Number.isFinite(n) && n > 0;
}

function mergeRuntimeList(nextList: any[], prevList: any[]) {
  if (!Array.isArray(nextList) || !nextList.length) return nextList || [];
  const prevMap = new Map<string, any>();
  (prevList || []).forEach((item) => {
    if (item?.propertyCode) prevMap.set(String(item.propertyCode), item);
  });
  return nextList.map((item) => {
    const prev = item?.propertyCode ? prevMap.get(String(item.propertyCode)) : null;
    if (!prev) return item;
    const merged = { ...item };
    // 新接口偶发丢时间戳时，保留上一轮有效时间，避免卡片时间闪烁成 --
    if (!hasValidTs(merged.ts) && hasValidTs(prev.ts)) {
      merged.ts = prev.ts;
    }
    // 值短暂为空时也保留上一轮，减少整卡闪烁
    if ((merged.dataValue == null || merged.dataValue === '') && prev.dataValue != null && prev.dataValue !== '') {
      merged.dataValue = prev.dataValue;
      if (prev.unit != null) merged.unit = prev.unit;
    }
    return merged;
  });
}

function displayValue(item: any) {
  return formatDeviceValue(item?.dataValue, item?.decimalPlaces);
}

function fullValue(item: any) {
  const val = displayValue(item);
  if (val === '--') return '--';
  return item.unit ? `${val}${item.unit}` : val;
}

function fullTitle(item: any) {
  const displayName = item?.pointName || item?.propertyName || '--';
  if (item?.propertyCode) {
    return `${displayName} (${item.propertyCode})`;
  }
  return displayName;
}

function valueClass(item: any) {
  const val = fullValue(item);
  if (val === '--') return 'is-empty';
  if (val.length > 20) return 'is-long';
  if (val.length > 12) return 'is-medium';
  return 'is-short';
}

async function fetch(p: Record<string, any> = {}, options: { silent?: boolean } = {}) {
  const {api, params, searchParams} = props;
  if (api && isFunction(api)) {
    const silent = !!options.silent;
    if (!silent) {
      state.loading = true;
    }
    try {
      const res = await api({
        ...params,
        ...searchParams,
        pageNo: page.value,
        pageSize: pageSize.value,
        ...p,
      });
      let list = res.data || [];
      if (props.onlyThreshold) {
        list = list.filter((item: any) => props.thresholdMap?.[item?.propertyCode]);
      }
      data.value = mergeRuntimeList(list, data.value);
      total.value = props.onlyThreshold ? list.length : res.total;
      emit('loaded', total.value ?? 0);
    } finally {
      state.loading = false;
    }
  }
}

function reload(p: Record<string, any> = {}, options: { silent?: boolean } = {}) {
  return fetch(p, options);
}

onMounted(() => {
  fetch();
  emit('getMethod', reload);
});

watch(() => props.searchParams, () => {
  page.value = 1;
  fetch();
}, { deep: true });

watch(() => [props.onlyThreshold, props.thresholdMap], () => {
  page.value = 1;
  fetch();
}, { deep: true });

const page = ref(1);
const pageSize = ref(12);
const paginationProp = ref({
  showSizeChanger: true,
  showQuickJumper: true,
  pageSize,
  current: page,
  total,
  pageSizeOptions: ['12', '24', '48'],
  showTotal: (t: number) => `共 ${t} 条`,
  onChange: pageChange,
  onShowSizeChange: pageSizeChange,
});

function pageChange(p: number, pz: number) {
  page.value = p;
  pageSize.value = pz;
  fetch();
}

function pageSizeChange(_current, size: number) {
  page.value = 1;
  pageSize.value = size;
  fetch();
}

async function handleRefresh(record: object) {
  emit('refresh', record);
}

async function handleView(record: object) {
  emit('view', record);
}

async function handleThreshold(record: object) {
  emit('threshold', record);
}
</script>
<style lang="less" scoped>
@primary: #1890ff;
@title: #262626;
@secondary: #8c8c8c;
@border: #e8e8e8;
@bg: #fafafa;

.model-card-list-wrapper {
  background: transparent;

  :deep(.ant-list) {
    padding: 0;
    background: transparent;
  }

  :deep(.ant-list-pagination) {
    margin-top: 16px;
    text-align: right;
  }

  :deep(.ant-list-item) {
    margin: 0 0 16px;
    padding: 0;
    border: none;
    height: 100%;
  }

  :deep(.model-item) {
    height: 100%;
  }

  .prop-card {
    height: 156px;
    display: flex;
    flex-direction: column;
    padding: 16px 18px 12px;
    border-radius: 6px;
    border: 1px solid @border;
    background: #fff;
    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.03);
    transition: box-shadow 0.2s ease, border-color 0.2s ease;
    overflow: hidden;

    &:hover {
      border-color: #91caff;
      box-shadow: 0 2px 8px rgba(24, 144, 255, 0.12);
    }

    &.is-breach {
      border-color: #ffa39e;
      background: #fff2f0;
    }

    .card-header {
      display: flex;
      align-items: flex-start;
      justify-content: space-between;
      gap: 10px;
      margin-bottom: 8px;

      .title-wrap {
        flex: 1;
        min-width: 0;
      }

      .title {
        display: block;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
        line-height: 22px;

        .name {
          font-size: 14px;
          font-weight: 500;
          color: @title;
        }

        .code {
          margin-left: 4px;
          font-size: 13px;
          font-weight: 400;
          color: @secondary;
        }
      }

      .type-tag {
        flex-shrink: 0;
        height: 22px;
        padding: 0 8px;
        border-radius: 11px;
        background: #e6f4ff;
        color: @primary;
        font-size: 12px;
        line-height: 22px;
        font-weight: 400;
      }
    }

    .card-body {
      flex: 1;
      display: flex;
      align-items: center;
      justify-content: center;
      min-width: 0;
      min-height: 0;
      padding: 4px 0 8px;

      .value-line {
        display: flex;
        align-items: baseline;
        justify-content: center;
        max-width: 100%;
        min-width: 0;
        color: @primary;
        line-height: 1.25;

        .value {
          min-width: 0;
          max-width: 100%;
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
          font-weight: 500;
          font-variant-numeric: tabular-nums;
        }

        &.is-short .value {
          font-size: 28px;
        }

        &.is-medium .value {
          font-size: 20px;
        }

        &.is-long .value {
          font-size: 15px;
          font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Courier New', monospace;
        }

        &.is-empty {
          color: #bfbfbf;

          .value {
            font-size: 24px;
            font-weight: 400;
          }
        }

        &.is-breach-value {
          color: #cf1322;
        }
      }
    }

    .card-footer {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 8px;
      padding-top: 10px;
      border-top: 1px solid #f0f0f0;
      min-width: 0;

      .time {
        display: flex;
        align-items: center;
        gap: 4px;
        min-width: 0;
        font-size: 12px;
        color: @secondary;
        line-height: 20px;

        .time-icon {
          flex-shrink: 0;
          font-size: 12px;
          color: #bfbfbf;
        }

        span {
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
        }
      }

      .footer-actions {
        display: flex;
        align-items: center;
        gap: 6px;
        flex-shrink: 0;
      }

      .history-btn {
        display: inline-flex;
        align-items: center;
        gap: 4px;
        height: 24px;
        padding: 0 8px;
        border: none;
        border-radius: 4px;
        background: #e6f4ff;
        color: @primary;
        font-size: 12px;
        line-height: 24px;
        cursor: pointer;
        transition: background 0.2s ease;

        &:hover {
          background: #bae0ff;
        }
      }

      .icon-btn {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 24px;
        height: 24px;
        padding: 0;
        border: 1px solid @border;
        border-radius: 4px;
        background: #fff;
        color: @secondary;
        cursor: pointer;
        transition: color 0.2s ease, border-color 0.2s ease;

        &:hover {
          color: @primary;
          border-color: #91caff;
        }
      }
    }
  }
}
</style>
