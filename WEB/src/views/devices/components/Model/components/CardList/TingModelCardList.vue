<template>
  <div class="model-card-list-wrapper p-2">
    <div class="p-2 bg-white">
      <Spin :spinning="state.loading">
        <List
          :grid="{ gutter: 12, xs: 1, sm: 2, md: 4, lg: 6, xl: 8, xxl: 8 }"
          :data-source="data"
          :pagination="paginationProp"
          class="model-list"
        >
          <template #renderItem="{ item }">
            <ListItem class="model-item">
              <div class="model-info">
                <div class="title">
                  <span class="title-text">{{ item.propertyName }}</span>
                  <Icon icon="ant-design:question-circle-outlined" class="help-icon" />
                </div>
                <div class="value">
                  <span>{{ item.dataValue == null ? "null" : item.dataValue }}</span>
                  <span class="unit" v-if="item.unit">{{ item.unit }}</span>
                </div>
                <div class="props">
                  <div class="prop">
                    <div class="label">键</div>
                    <div class="value-text">{{ item.propertyCode || '--' }}</div>
                  </div>
                  <div class="prop">
                    <div class="label">更新时间</div>
                    <div class="value-text">{{ item.ts == 0 ? '--' : formatTime(item.ts) }}</div>
                  </div>
                </div>
                <div class="actions">
                  <div class="action-btn" @click="handleRefresh(item)">
                    <Icon icon="ant-design:redo-outlined" />
                    <span>刷新</span>
                  </div>
                  <div class="action-btn" @click="handleView(item)">
                    <Icon icon="ant-design:eye-filled" />
                    <span>详情</span>
                  </div>
                </div>
              </div>
            </ListItem>
          </template>
        </List>
      </Spin>
    </div>
  </div>
</template>
<script lang="ts" setup>
import {onMounted, reactive, ref, watch} from 'vue';
import {List, Spin, Button, ButtonGroup} from 'ant-design-vue';
import {Icon} from '@/components/Icon';
import {propTypes} from '@/utils/propTypes';
import {isFunction} from '@/utils/is';
import {formatToDateTime} from '@/utils/dateUtil';

const ListItem = List.Item;

// 组件接收参数
const props = defineProps({
  // 请求API的参数
  params: propTypes.object.def({}),
  //api
  api: propTypes.func,
  // 当前激活的视图
  activeKey: propTypes.string.def('card'),
  // 搜索参数
  searchParams: propTypes.object.def({}),
});
//暴露内部方法
const emit = defineEmits(['getMethod', 'refresh', 'view', 'tabChange']);

// 切换视图
function handleTabChange(key: string) {
  emit('tabChange', key);
}

//数据
const data = ref([]);

const state = reactive({
  loading: true,
});

// 格式化时间
function formatTime(ts: number) {
  if (!ts) return '--';
  return formatToDateTime(ts);
}

// 自动请求并暴露内部方法
onMounted(() => {
  fetch();
  emit('getMethod', fetch);
});

async function fetch(p = {}) {
  const {api, params, searchParams} = props;
  if (api && isFunction(api)) {
    const res = await api({
      ...params, 
      ...searchParams,
      pageNo: page.value, 
      pageSize: pageSize.value, 
      ...p
    });
    data.value = res.data;
    total.value = res.total;
    hideLoading();
  }
}

// 监听搜索参数变化
watch(() => props.searchParams, () => {
  fetch();
}, { deep: true });

function hideLoading() {
  state.loading = false;
}

//分页相关
const page = ref(1);
const pageSize = ref(8);
const total = ref(0);
const paginationProp = ref({
  showSizeChanger: false,
  showQuickJumper: true,
  pageSize,
  current: page,
  total,
  showTotal: (total: number) => `总 ${total} 条`,
  onChange: pageChange,
  onShowSizeChange: pageSizeChange,
});

function pageChange(p: number, pz: number) {
  page.value = p;
  pageSize.value = pz;
  fetch();
}

function pageSizeChange(_current, size: number) {
  pageSize.value = size;
  fetch();
}

async function handleRefresh(record: object) {
  emit('refresh', record);
}

async function handleView(record: object) {
  emit('view', record);
}
</script>
<style lang="less" scoped>
.model-card-list-wrapper {
  background: transparent;

  :deep(.ant-list) {
    padding: 0;
    background: transparent;
  }

  :deep(.ant-list-item) {
    margin: 0 0 12px 0;
    padding: 0;
    border: none;
  }

  :deep(.model-item) {
    overflow: hidden;
    // 浅灰色光幕阴影 - 柔和光感
    box-shadow: 
      0 2px 8px rgba(0, 0, 0, 0.04),
      0 4px 16px rgba(0, 0, 0, 0.03),
      0 8px 32px rgba(0, 0, 0, 0.02);
    border-radius: 12px;
    padding: 12px;
    position: relative;
    // 白淡灰背景
    background: #fafafa;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    min-height: 140px;
    height: 100%;
    // 浅灰色边框
    border: 1px solid rgba(0, 0, 0, 0.06);
    display: flex;
    align-items: stretch;

    // 悬停效果 - 光幕阴影增强
    &:hover {
      box-shadow: 
        0 4px 12px rgba(0, 0, 0, 0.06),
        0 8px 24px rgba(0, 0, 0, 0.04),
        0 16px 48px rgba(0, 0, 0, 0.03);
      transform: translateY(-2px);
      border-color: rgba(0, 0, 0, 0.1);
      background: #ffffff;
    }

    .model-info {
      flex: 1;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      min-width: 0;

      .title {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 8px;

        .title-text {
          font-size: 13px;
          font-weight: 600;
          color: #434343;
          line-height: 1.4;
          flex: 1;
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
          letter-spacing: 0.01em;
        }

        .help-icon {
          color: #8c8c8c;
          font-size: 13px;
          cursor: help;
          transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
          opacity: 0.6;
          margin-left: 6px;
          flex-shrink: 0;

          &:hover {
            color: #595959;
            opacity: 1;
            transform: scale(1.1);
          }
        }
      }

      .value {
        padding: 12px;
        font-size: 20px;
        font-weight: 700;
        color: #262626;
        text-align: center;
        background: #ffffff;
        border-radius: 8px;
        margin-bottom: 10px;
        // 浅灰色内部阴影和边框
        border: 1px solid rgba(0, 0, 0, 0.08);
        box-shadow: 
          inset 0 1px 2px rgba(0, 0, 0, 0.02),
          0 1px 3px rgba(0, 0, 0, 0.04);
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 4px;
        min-height: 50px;
        position: relative;
        // 白色背景
        background: #ffffff;

        .unit {
          font-size: 11px;
          font-weight: 500;
          color: #8c8c8c;
          letter-spacing: 0.02em;
        }
      }

      .props {
        margin-bottom: 10px;
        flex: 1;

        .prop {
          margin-bottom: 6px;

          &:last-child {
            margin-bottom: 0;
          }

          .label {
            font-size: 12px;
            font-weight: 600;
            color: #8c8c8c;
            line-height: 1.5;
            margin-bottom: 4px;
            letter-spacing: 0.01em;
            text-transform: uppercase;
          }

          .value-text {
            font-size: 13px;
            font-weight: 500;
            color: #434343;
            line-height: 1.5;
            word-break: break-word;
            overflow: hidden;
            text-overflow: ellipsis;
            display: -webkit-box;
            -webkit-line-clamp: 2;
            -webkit-box-orient: vertical;
          }
        }
      }

      .actions {
        display: flex;
        gap: 6px;
        padding-top: 10px;
        border-top: 1px solid rgba(0, 0, 0, 0.08);

        .action-btn {
          flex: 1;
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 4px;
          padding: 6px 10px;
          border-radius: 8px;
          // 白淡灰按钮背景
          background: #ffffff;
          color: #595959;
          font-size: 11px;
          font-weight: 500;
          cursor: pointer;
          transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
          border: 1px solid rgba(0, 0, 0, 0.08);
          // 浅灰色光幕按钮阴影
          box-shadow: 
            0 1px 3px rgba(0, 0, 0, 0.04),
            0 2px 6px rgba(0, 0, 0, 0.03);
          position: relative;
          overflow: hidden;

          // 悬停效果 - 浅灰色光幕
          &:hover {
            background: #f5f5f5;
            color: #262626;
            border-color: rgba(0, 0, 0, 0.12);
            box-shadow: 
              0 2px 6px rgba(0, 0, 0, 0.06),
              0 4px 12px rgba(0, 0, 0, 0.04);
            transform: translateY(-1px);
          }

          // 点击效果
          &:active {
            background: #f0f0f0;
            color: #1a1a1a;
            box-shadow: 
              0 1px 3px rgba(0, 0, 0, 0.05),
              inset 0 1px 2px rgba(0, 0, 0, 0.04);
            transform: translateY(0);
          }

          :deep(.anticon) {
            font-size: 12px;
            transition: transform 0.25s cubic-bezier(0.4, 0, 0.2, 1);
          }

          // 图标悬停动画
          &:hover :deep(.anticon) {
            transform: scale(1.1);
          }
        }
      }
    }
  }
}
</style>

