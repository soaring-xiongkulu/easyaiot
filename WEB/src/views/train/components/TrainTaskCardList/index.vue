<template>
  <div class="train-task-card-list-wrapper">
    <div class="p-4 bg-white" style="margin-bottom: 10px">
      <BasicForm @register="registerForm" @reset="handleSubmit"/>
    </div>
    <div class="bg-white">
      <Spin :spinning="state.loading">
        <List
          :grid="{ gutter: 12, xs: 1, sm: 2, md: 3, lg: 4, xl: 4, xxl: 4 }"
          :data-source="data"
          :pagination="paginationProp"
        >
          <template #header>
            <div
              style="display: flex;align-items: center;justify-content: space-between;flex-direction: row;">
              <span style="padding-left: 7px;font-size: 16px;font-weight: 500;line-height: 24px;">训练任务列表</span>
              <div style="display: flex; gap: 8px;">
                <slot name="header"></slot>
              </div>
            </div>
          </template>
          <template #renderItem="{ item }">
            <ListItem :class="getItemClass(item)">
              <div class="task-info">
                <div class="status" :style="getStatusBadgeStyle(item)">{{ getStatusText(item) }}</div>
                <div class="title o2" :title="item.name">{{ item.name || 'train' }}</div>
                <div class="props">
                  <div class="flex" style="justify-content: space-between;">
                    <div class="prop">
                      <div class="label">数据集</div>
                      <div class="value" :title="getDatasetDisplay(item)">{{ getDatasetDisplay(item) }}</div>
                    </div>
                    <div class="prop">
                      <div class="label">开始时间</div>
                      <div class="value">{{ formatTrainTaskTime(item.start_time) }}</div>
                    </div>
                  </div>
                  <div class="flex" style="justify-content: space-between;">
                    <div class="prop progress-prop">
                      <div class="label">训练进度</div>
                      <div class="progress-block">
                        <div class="progress-bar">
                          <div
                            class="progress-bar-inner"
                            :style="{
                              width: `${getProgressPercent(item)}%`,
                              backgroundColor: getProgressColor(item),
                            }"
                          />
                        </div>
                        <div
                          class="value progress-value"
                          :style="getProgressTextStyle(item)"
                        >
                          {{ getProgressPercent(item) }}%
                        </div>
                      </div>
                      <div v-if="formatTrainProgressDetail(item)" class="progress-detail">
                        {{ formatTrainProgressDetail(item) }}
                      </div>
                    </div>
                  </div>
                </div>
                <div class="btns">
                  <div class="btn" @click="handleViewLogs(item)" title="查看日志">
                    <Icon icon="mdi:file-document-outline" :size="15" color="#3B82F6" />
                  </div>
                  <div class="btn" @click="handleViewResults(item)" title="查看训练结果">
                    <Icon icon="mdi:image-outline" :size="15" color="#3B82F6" />
                  </div>
                  <Popconfirm
                    v-if="isTrainTaskActive(String(item.status))"
                    title="确定停止此训练任务? 停止后可从断点继续训练。"
                    ok-text="是"
                    cancel-text="否"
                    @confirm="handleStop(item)"
                  >
                    <div class="btn" title="停止训练">
                      <Icon icon="ant-design:pause-circle-outlined" :size="15" color="#FAAD14" />
                    </div>
                  </Popconfirm>
                  <div
                    v-if="canResumeTrainTask(item)"
                    class="btn"
                    title="继续训练"
                    @click="handleResume(item)"
                  >
                    <Icon icon="mdi:play-circle-outline" :size="15" color="#52C41A" />
                  </div>
                  <div
                    v-if="canRetrainTrainTask(String(item.status))"
                    class="btn"
                    title="重新训练"
                    @click="handleRetrain(item)"
                  >
                    <Icon icon="mdi:restart" :size="15" color="#3B82F6" />
                  </div>
                  <div
                    v-if="item.minio_model_path"
                    class="btn"
                    @click="handleDownload(item)"
                    title="下载训练权重"
                  >
                    <Icon icon="ant-design:download-outlined" :size="15" color="#3B82F6" />
                  </div>
                  <div
                    v-if="canPublishTrainTask(item)"
                    class="btn"
                    :title="getPublishTooltip(item)"
                    @click="handlePublish(item)"
                  >
                    <Icon icon="ant-design:cloud-upload-outlined" :size="15" color="#722ED1" />
                  </div>
                  <Popconfirm
                    title="确定删除此训练任务?"
                    ok-text="是"
                    cancel-text="否"
                    @confirm="handleDelete(item)"
                  >
                    <div class="btn delete-btn">
                      <Icon icon="material-symbols:delete-outline-rounded" :size="15" color="#DC2626" />
                    </div>
                  </Popconfirm>
                </div>
              </div>
              <div class="task-img">
                <img
                  src="@/assets/images/video/push-stream.png"
                  alt=""
                  class="img"
                  @click="handleViewLogs(item)"
                >
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
import {List, Popconfirm, Spin} from 'ant-design-vue';
import {BasicForm, useForm} from '@/components/Form';
import {propTypes} from '@/utils/propTypes';
import {isFunction} from '@/utils/is';
import {Icon} from '@/components/Icon';
import {getFormConfig} from '../TrainTaskList/Data';
import {canPublishTrainTask, canResumeTrainTask, canRetrainTrainTask, formatTrainProgressDetail, formatTrainTaskTime, getPublishedModelId, isTrainTaskActive} from '../TrainTaskList/trainTaskUtils';

defineOptions({name: 'TrainTaskCardList'});

const ListItem = List.Item;

const props = defineProps({
  params: propTypes.object.def({}),
  api: propTypes.func,
});

const emit = defineEmits(['getMethod', 'viewLogs', 'viewResults', 'download', 'stop', 'resume', 'retrain', 'delete', 'publish']);

const data = ref<Record<string, unknown>[]>([]);
const state = reactive({
  loading: true,
});

const statusConfig: Record<string, string> = {
  idle: '等待开始',
  preparing: '准备中',
  Train: '训练中',
  train: '训练中',
  running: '训练中',
  completed: '已完成',
  stopped: '已停止',
  stopping: '停止中',
  error: '失败',
  failed: '失败',
};

const [registerForm, {validate}] = useForm({
  schemas: getFormConfig()?.schemas || [],
  labelWidth: 80,
  baseColProps: {span: 6},
  actionColOptions: {span: 6, offset: 0, style: {textAlign: 'right'}},
  autoSubmitOnEnter: true,
  submitFunc: handleSubmit,
});

onMounted(() => {
  fetch();
  emit('getMethod', (opts?: { silent?: boolean }) => fetch({}, opts));
});

watch(() => props.params, () => {
  fetch();
}, {deep: true});

async function handleSubmit() {
  const formData = await validate();
  page.value = 1;
  await fetch(formData);
}

async function fetch(p: Record<string, unknown> = {}, opts?: { silent?: boolean }) {
  const {api, params} = props;
  if (!api || !isFunction(api)) return;

  if (!opts?.silent) {
    state.loading = true;
  }
  try {
    const res = await api({
      ...params,
      pageNo: page.value,
      pageSize: pageSize.value,
      ...p,
    });
    data.value = res?.data ?? res?.list ?? [];
    total.value = res?.total ?? 0;
  } catch (error) {
    console.error('获取训练任务列表失败:', error);
    data.value = [];
    total.value = 0;
  } finally {
    state.loading = false;
  }
}

const page = ref(1);
const pageSize = ref(8);
const total = ref(0);
const paginationProp = ref({
  showSizeChanger: false,
  showQuickJumper: true,
  pageSize,
  current: page,
  total,
  showTotal: (t: number) => `总 ${t} 条`,
  onChange: pageChange,
  onShowSizeChange: pageSizeChange,
});

function pageChange(p: number, pz: number) {
  page.value = p;
  pageSize.value = pz;
  fetch();
}

function pageSizeChange(_current: number, size: number) {
  pageSize.value = size;
  page.value = 1;
  fetch();
}

type StatusVariant = 'idle' | 'preparing' | 'training' | 'completed' | 'stopped' | 'resumable' | 'error';

const statusVariantMap: Record<string, StatusVariant> = {
  idle: 'idle',
  preparing: 'preparing',
  Train: 'training',
  train: 'training',
  running: 'training',
  completed: 'completed',
  stopped: 'stopped',
  stopping: 'stopped',
  error: 'error',
  failed: 'error',
};

const statusTheme: Record<StatusVariant, { badgeBg: string; badgeColor: string; progressColor: string; prominent?: boolean }> = {
  idle: {badgeBg: '#f5f5f5', badgeColor: '#8c8c8c', progressColor: '#8c8c8c'},
  preparing: {badgeBg: '#08979c', badgeColor: '#ffffff', progressColor: '#006d75', prominent: true},
  training: {badgeBg: '#f6ffed', badgeColor: '#52c41a', progressColor: '#52c41a'},
  completed: {badgeBg: '#0958d9', badgeColor: '#ffffff', progressColor: '#003eb3', prominent: true},
  stopped: {badgeBg: '#f5f5f5', badgeColor: '#595959', progressColor: '#8c8c8c'},
  resumable: {badgeBg: '#f9f0ff', badgeColor: '#722ed1', progressColor: '#9254de', prominent: true},
  error: {badgeBg: '#cf1322', badgeColor: '#ffffff', progressColor: '#a8071a', prominent: true},
};

function getStatusVariant(item: Record<string, unknown>): StatusVariant {
  const status = String(item.status || '');
  if (status === 'stopped' && canResumeTrainTask(item as { status?: string; can_resume?: boolean; checkpoint_dir?: string })) {
    return 'resumable';
  }
  return statusVariantMap[status] || 'idle';
}

function getItemClass(item: Record<string, unknown>) {
  return `task-item status-${getStatusVariant(item)}`;
}

function getStatusBadgeStyle(item: Record<string, unknown>) {
  const theme = statusTheme[getStatusVariant(item)];
  return {
    background: theme.badgeBg,
    color: theme.badgeColor,
    fontWeight: theme.prominent ? 600 : 500,
    boxShadow: theme.prominent ? '0 2px 6px rgba(0, 0, 0, 0.15)' : undefined,
  };
}

function getStatusText(item: Record<string, unknown>) {
  const status = String(item.status || '');
  let base = statusConfig[status] || status || '未知';
  if (canResumeTrainTask(item as { status?: string; can_resume?: boolean; checkpoint_dir?: string })) {
    base = status === 'stopped' ? '已停止(可续训)' : '失败(可续训)';
  }
  if (['Train', 'train', 'running'].includes(status)) {
    return `${base} (${item.progress ?? 0}%)`;
  }
  return base;
}

function getDatasetDisplay(item: Record<string, unknown>) {
  const name = item.dataset_name as string;
  const version = item.dataset_version as string;
  if (name && version) return `${name}（${version}）`;
  if (name) return name;
  if (version) return version;
  return '--';
}

function getProgressPercent(item: Record<string, unknown>) {
  const status = String(item.status || '');
  if (status === 'completed') return 100;
  const raw = Number(item.progress);
  if (Number.isNaN(raw)) return 0;
  return Math.min(100, Math.max(0, Math.round(raw)));
}

function getProgressColor(item: Record<string, unknown>) {
  const variant = getStatusVariant(item);

  if (variant === 'preparing') return statusTheme.preparing.progressColor;
  if (variant === 'completed') return statusTheme.completed.progressColor;
  if (variant === 'stopped') return statusTheme.stopped.progressColor;
  if (variant === 'resumable') return statusTheme.resumable.progressColor;
  if (variant === 'error') return statusTheme.error.progressColor;
  if (variant === 'idle') return statusTheme.idle.progressColor;

  const percent = getProgressPercent(item);
  if (percent === 0) return '#8c8c8c';
  if (percent <= 25) return '#1890ff';
  if (percent <= 50) return '#13c2c2';
  if (percent <= 75) return '#52c41a';
  return '#389e0d';
}

function getProgressTextStyle(item: Record<string, unknown>) {
  const variant = getStatusVariant(item);
  const theme = statusTheme[variant];
  return {
    color: getProgressColor(item),
    fontWeight: theme.prominent ? 700 : 600,
  };
}

function handleViewLogs(record: Record<string, unknown>) {
  emit('viewLogs', record);
}

function handleViewResults(record: Record<string, unknown>) {
  emit('viewResults', record);
}

function handleDownload(record: Record<string, unknown>) {
  emit('download', record);
}

function handleStop(record: Record<string, unknown>) {
  emit('stop', record);
}

function handleRetrain(record: Record<string, unknown>) {
  emit('retrain', record);
}

function handleResume(record: Record<string, unknown>) {
  emit('resume', record);
}

function handleDelete(record: Record<string, unknown>) {
  emit('delete', record);
}

function getPublishTooltip(record: Record<string, unknown>) {
  const publishedModelId = getPublishedModelId(record as { published_model_id?: number; hyperparameters?: unknown });
  return publishedModelId
    ? `更新发布到模型管理（模型 ID: ${publishedModelId}）`
    : '发布到模型管理';
}

function handlePublish(record: Record<string, unknown>) {
  emit('publish', record);
}
</script>

<style lang="less" scoped>
.train-task-card-list-wrapper {
  :deep(.ant-list-header) {
    border-block-end: 0;
    padding-top: 0;
    padding-bottom: 8px;
  }

  :deep(.ant-list) {
    padding: 6px;
  }

  :deep(.ant-list-item) {
    margin: 6px;
  }

  :deep(.task-item) {
    overflow: hidden;
    box-shadow: 0 0 4px #00000026;
    border-radius: 8px;
    padding: 16px 0;
    position: relative;
    background-color: #fff;
    background-repeat: no-repeat;
    background-position: center center;
    background-size: 104% 104%;
    transition: all 0.5s;
    min-height: 208px;
    height: 100%;

    &.status-idle,
    &.status-preparing,
    &.status-training,
    &.status-completed,
    &.status-stopped,
    &.status-resumable {
      background-image: url('@/assets/images/product/blue-bg.719b437a.png');
    }

    &.status-error {
      background-image: url('@/assets/images/product/red-bg.101af5ac.png');
    }

    .task-info {
      flex-direction: column;
      max-width: calc(100% - 128px);
      padding-left: 16px;

      .status {
        min-width: 90px;
        height: 26px;
        border-radius: 6px 0 0 6px;
        font-size: 12px;
        font-weight: 500;
        line-height: 26px;
        text-align: center;
        position: absolute;
        right: 0;
        top: 16px;
        padding: 0 10px;
        white-space: nowrap;
      }

      .title {
        font-size: 16px;
        font-weight: 600;
        color: #050708;
        line-height: 20px;
        height: 40px;
        padding-right: 90px;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
      }

      .props {
        margin-top: 10px;

        .flex {
          display: flex;
        }

        .prop {
          flex: 1;
          margin-bottom: 10px;

          .label {
            font-size: 12px;
            font-weight: 400;
            color: #666;
            line-height: 14px;
          }

          .value {
            font-size: 14px;
            font-weight: 600;
            color: #050708;
            line-height: 14px;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            margin-top: 6px;
          }

          &.progress-prop {
            flex: 1;

            .progress-block {
              display: flex;
              align-items: center;
              gap: 6px;
              margin-top: 6px;
              padding-right: 16px;
              box-sizing: border-box;
            }

            .progress-bar {
              flex: 1;
              height: 8px;
              background: #e8e8e8;
              border-radius: 4px;
              overflow: hidden;
            }

            .progress-bar-inner {
              height: 100%;
              border-radius: 4px;
              transition: width 0.3s ease, background-color 0.3s ease;
              box-shadow: 0 1px 3px rgba(0, 0, 0, 0.12);
            }

            .progress-value {
              flex-shrink: 0;
              min-width: 36px;
              font-size: 14px;
              font-weight: 700;
              line-height: 14px;
              text-align: right;
            }

            .progress-detail {
              margin-top: 4px;
              color: #8c8c8c;
              font-size: 12px;
              line-height: 18px;
              white-space: normal;
            }
          }
        }
      }

      .btns {
        display: flex;
        position: absolute;
        left: 16px;
        bottom: 16px;
        margin-top: 20px;
        min-width: 220px;
        max-width: calc(100% - 32px);
        height: 28px;
        border-radius: 45px;
        justify-content: space-around;
        padding: 0 10px;
        align-items: center;
        border: 2px solid #266cfbff;

        .btn {
          width: 28px;
          text-align: center;
          position: relative;
          cursor: pointer;

          &:before {
            content: '';
            display: block;
            position: absolute;
            width: 1px;
            height: 7px;
            background-color: #e2e2e2;
            left: 0;
            top: 9px;
          }

          &:first-child:before {
            display: none;
          }

          &:hover :deep(.anticon) {
            color: #5BA3F5;
          }

          &.delete-btn:hover :deep(.anticon) {
            color: #DC2626;
          }
        }
      }
    }

    .task-img {
      position: absolute;
      right: 20px;
      top: 50px;

      img {
        cursor: pointer;
        width: 120px;
      }
    }
  }
}
</style>
