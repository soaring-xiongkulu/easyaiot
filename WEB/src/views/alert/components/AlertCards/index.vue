<template>
  <div class="alert-card-list-wrapper p-2">
    <div class="p-4 bg-white" style="margin-bottom: 10px">
      <BasicForm @register="registerForm" />
    </div>

    <div class="p-2 bg-white">
      <Spin :spinning="state.loading">
        <List
          :grid="{ gutter: 2, xs: 1, sm: 2, md: 4, lg: 4, xl: 4, xxl: 4 }"
          :data-source="data"
          :pagination="paginationProp"
        >
          <template #header>
            <div
              style="display: flex;align-items: center;justify-content: space-between;flex-direction: row;"
            >
              <span style="padding-left: 7px;font-size: 16px;font-weight: 500;line-height: 24px;"
                >告警事件列表</span
              >
              <div class="space-x-2">
                <slot name="header"></slot>
              </div>
            </div>
          </template>

          <template #renderItem="{ item }">
            <ListItem class="alert-item normal">
              <span class="corner-tags">
                <span
                  v-if="isLlmSampled(item.llm_judge_status)"
                  class="llm-judge-tag"
                  :class="`llm-judge-tag--${item.llm_judge_status}`"
                  title="该告警已被大模型抽检，点击图片可查看研判结论"
                >
                  {{ formatLlmJudgeStatus(item.llm_judge_status) }}
                </span>
                <span class="task-type-tag" :class="getTaskTypeClass(item)">
                  {{ getTaskTypeText(item) }}
                </span>
              </span>
              <div class="alert-info">
                <div class="title-wrapper">
                  <div class="title o2">
                    <span class="event-name">{{ formatAlertEvent(item.event) }}</span>
                  </div>
                </div>
                <div v-if="item.business_tags?.length" class="alert-business-tags">
                  <a-tag v-for="tag in item.business_tags" :key="tag" color="blue" size="small">{{ tag }}</a-tag>
                </div>
                <div class="props">
                  <div class="flex" style="justify-content: space-between;">
                    <div class="prop">
                      <div class="label">设备ID</div>
                      <div class="value" @click="handleCopyDeviceId(item.device_id)" style="cursor: pointer;">
                        <Icon icon="tdesign:copy-filled" color="#4287FCFF" :size="12" style="margin-right: 4px;"/>
                        {{ formatDeviceId(item.device_id) }}
                      </div>
                    </div>
                    <div class="prop">
                      <div class="label">告警时间</div>
                      <div class="value">{{ formatTime(item.time) }}</div>
                    </div>
                  </div>
                  <div class="flex" style="justify-content: space-between;">
                    <div class="prop">
                      <div class="label">摄像头</div>
                      <div class="value">{{ item.device_name || '-' }}</div>
                    </div>
                    <div class="prop">
                      <div class="label">{{ item.event === 'face_library_match' ? '匹配人员' : '告警对象' }}</div>
                      <div class="value">{{ getAlertObjectLabel(item) }}</div>
                    </div>
                  </div>
                  <div v-if="item.event === 'face_library_match'" class="flex" style="justify-content: space-between;">
                    <div class="prop">
                      <div class="label">触发告警</div>
                      <div class="value">{{ formatAlertEvent(getAlertSourceEvent(item)) || '-' }}</div>
                    </div>
                  </div>
                </div>
                <div class="btns">
                  <div class="btn" @click="handleCopy(item)">
                    <Icon icon="tdesign:copy-filled" :size="15" color="#3B82F6" />
                  </div>
                  <div class="btn" @click="handleViewImage(item)" v-if="item.image_url">
                    <Icon icon="ion:image-sharp" :size="15" color="#3B82F6" />
                  </div>
                  <div class="btn" @click="handleViewVideo(item)" v-if="item.device_id && item.time && !isSnapTask(item)">
                    <Icon icon="icon-park-outline:video" :size="15" color="#3B82F6" />
                  </div>
                </div>
              </div>
              <div class="alert-img">
                <img :src="thumbUrl(item.image_url) || ALERT" alt="" class="img">
              </div>
            </ListItem>
          </template>
        </List>
      </Spin>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { onMounted, onUnmounted, reactive, ref } from 'vue';
import { useRouter } from 'vue-router';
import { List, Spin } from 'ant-design-vue';
import { BasicForm, useForm } from '@/components/Form';
import { propTypes } from '@/utils/propTypes';
import { isFunction } from '@/utils/is';
import { useMessage } from '@/hooks/web/useMessage';
import { Icon } from '@/components/Icon';
import moment from 'moment';
import ALERT from "@/assets/images/alert/alert.png";
import { alertCameraSelectProps, alertFilterActionColOptions } from '@/views/alert/Data';
import { ALERT_EVENT_OPTIONS, formatAlertEvent, getAlertMatchedPersonName, getAlertSourceEvent, normalizeAlertBusinessTagsParam, formatLlmJudgeStatus, isLlmSampled } from '@/views/alert/alertDisplay';
import { resolveAlertImageDisplayUrl } from '@/utils/alertMinioImage';

const ListItem = List.Item;

// 组件接收参数
const props = defineProps({
  // 请求API的参数
  params: propTypes.object.def({}),
  // api
  api: propTypes.func,
});

const { createMessage } = useMessage();
const router = useRouter();

// 暴露内部方法
const emit = defineEmits(['getMethod', 'viewImage', 'viewVideo']);

// 数据
const data = ref([]);
const state = reactive({
  loading: true,
});

const lastFormParams = ref<Record<string, any>>({});

const page = ref(1);
const pageSize = ref(8);
const total = ref(0);

function processFormData(formData: Record<string, any>): Record<string, any> {
  const processedData = { ...formData };
  const timeRangeKey = '[begin_datetime, end_datetime]';
  if (processedData[timeRangeKey] && Array.isArray(processedData[timeRangeKey])) {
    const [begin, end] = processedData[timeRangeKey];
    if (begin && typeof begin.format === 'function') {
      processedData.begin_datetime = begin.format('YYYY-MM-DD HH:mm:ss');
    } else if (begin) {
      processedData.begin_datetime = begin;
    }
    if (end && typeof end.format === 'function') {
      processedData.end_datetime = end.format('YYYY-MM-DD HH:mm:ss');
    } else if (end) {
      processedData.end_datetime = end;
    }
    delete processedData[timeRangeKey];
  }
  if (processedData.task_name) {
    processedData.task_name = String(processedData.task_name).trim();
    if (!processedData.task_name) delete processedData.task_name;
  }
  const businessTagsParam = normalizeAlertBusinessTagsParam(processedData.business_tags);
  if (businessTagsParam) {
    processedData.business_tags = businessTagsParam;
  } else {
    delete processedData.business_tags;
  }
  const route = router.currentRoute.value;
  if (route.query.task_name && !processedData.task_name) {
    processedData.task_name = String(route.query.task_name).trim();
  }
  if (
    processedData.device_id !== undefined &&
    processedData.device_id !== null &&
    String(processedData.device_id).trim() === ''
  ) {
    delete processedData.device_id;
  }
  if (
    processedData.begin_datetime === null ||
    processedData.begin_datetime === undefined ||
    processedData.begin_datetime === ''
  ) {
    delete processedData.begin_datetime;
  }
  if (
    processedData.end_datetime === null ||
    processedData.end_datetime === undefined ||
    processedData.end_datetime === ''
  ) {
    delete processedData.end_datetime;
  }
  if (
    processedData.llm_judge_status === null ||
    processedData.llm_judge_status === undefined ||
    processedData.llm_judge_status === ''
  ) {
    delete processedData.llm_judge_status;
  }
  return processedData;
}

function snapshotFilters(processedData: Record<string, any>): Record<string, any> {
  const filterParams: Record<string, any> = {};
  if (processedData.begin_datetime) filterParams.begin_datetime = processedData.begin_datetime;
  if (processedData.end_datetime) filterParams.end_datetime = processedData.end_datetime;
  if (processedData.task_name) filterParams.task_name = processedData.task_name;
  if (processedData.device_id !== undefined && processedData.device_id !== '' && processedData.device_id !== null) {
    filterParams.device_id = processedData.device_id;
  }
  if (processedData.event !== undefined && processedData.event !== null && processedData.event !== '') {
    filterParams.event = processedData.event;
  }
  if (processedData.business_tags) {
    filterParams.business_tags = processedData.business_tags;
  }
  if (processedData.llm_judge_status !== undefined && processedData.llm_judge_status !== null && processedData.llm_judge_status !== '') {
    filterParams.llm_judge_status = processedData.llm_judge_status;
  }
  return filterParams;
}

async function handleSubmit() {
  let formData: Record<string, any>;
  try {
    formData = await validate();
  } catch (error: any) {
    // 摄像头下拉（ApiSelect）选项异步加载会让校验“过期”，
    // ant-design-vue 会以 { errorFields: [], outOfDate: true } 形式 reject，
    // 这并非真正的校验失败，吞掉避免未处理的 Promise 异常。
    if (error?.outOfDate && (!error?.errorFields || error.errorFields.length === 0))
      return;
    throw error;
  }
  const processedData = processFormData(formData);
  lastFormParams.value = snapshotFilters(processedData);
  page.value = 1;
  await fetch(processedData);
}

const [registerForm, { validate, setFieldsValue, getFieldsValue }] = useForm({
  schemas: [
    {
      field: 'task_name',
      label: '任务名称',
      component: 'Input',
      componentProps: {
        placeholder: '请输入任务名称（模糊匹配）',
      },
      colProps: { span: 8 },
    },
    {
      field: `device_id`,
      label: `摄像头`,
      component: 'ApiSelect',
      componentProps: alertCameraSelectProps,
      defaultValue: '',
      colProps: { span: 8 },
    },
    {
      field: `event`,
      label: `告警事件`,
      component: 'Select',
      componentProps: {
        options: [...ALERT_EVENT_OPTIONS],
      },
      defaultValue: null,
      colProps: { span: 8 },
    },
    {
      field: 'llm_judge_status',
      label: 'AI抽检',
      component: 'Select',
      componentProps: {
        options: [
          { label: '全部', value: '' },
          { label: '未抽检', value: 'not_sampled' },
          { label: '已抽检', value: 'confirmed,rejected,pending,error' },
          { label: '确认成立', value: 'confirmed' },
          { label: '误报', value: 'rejected' },
          { label: '研判中', value: 'pending' },
          { label: '研判失败', value: 'error' },
        ],
        placeholder: '全部',
      },
      colProps: { span: 8 },
    },
    {
      field: '[begin_datetime, end_datetime]',
      label: '告警时间',
      component: 'RangePicker',
      componentProps: {
        format: 'YYYY-MM-DD HH:mm:ss',
        placeholder: ['开始时间', '结束时间'],
        showTime: { format: 'HH:mm:ss' },
      },
      colProps: { span: 8 },
    },
  ],
  labelWidth: 120,
  baseColProps: { span: 8 },
  actionColOptions: alertFilterActionColOptions,
  showAdvancedButton: false,
  alwaysShowLines: 2,
  autoSubmitOnEnter: true,
  submitFunc: handleSubmit,
  submitOnReset: true,
});

// 自动请求并暴露内部方法
onMounted(() => {
  const route = router.currentRoute.value;
  if (route.query.task_name) {
    setFieldsValue({ task_name: route.query.task_name });
    setTimeout(() => {
      fetch({ task_name: String(route.query.task_name).trim() });
    }, 100);
  } else {
    fetch();
  }
  emit('getMethod', fetch);
});

async function fetch(p = {}) {
  const { api, params } = props;
  if (api && isFunction(api)) {
    try {
      state.loading = true;
      const requestParams = {
        ...params,
        pageNo: page.value,
        pageSize: pageSize.value,
        ...p,
      };
      const res = await api(requestParams);
      // 根据表格配置，返回格式为 { alert_list: [...], total: ... }
      data.value = res.alert_list || [];
      total.value = res.total || 0;
    } catch (error) {
      console.error('获取数据失败:', error);
      data.value = [];
      total.value = 0;
    } finally {
      hideLoading();
    }
  }
}

function hideLoading() {
  state.loading = false;
}

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

  const currentFormData = getFieldsValue();
  const processedData = processFormData(currentFormData);
  const hasFilterParams = !!(
    processedData.begin_datetime ||
    processedData.end_datetime ||
    processedData.task_name ||
    processedData.device_id ||
    processedData.event ||
    processedData.llm_judge_status
  );

  let formParams: Record<string, any> = {};
  if (hasFilterParams) {
    formParams = { ...processedData };
    lastFormParams.value = snapshotFilters(processedData);
  } else if (Object.keys(lastFormParams.value).length > 0) {
    formParams = { ...lastFormParams.value };
  }

  fetch(formParams);
}

function pageSizeChange(_current, size: number) {
  pageSize.value = size;
  page.value = 1;

  const currentFormData = getFieldsValue();
  const processedData = processFormData(currentFormData);
  const hasFilterParams = !!(
    processedData.begin_datetime ||
    processedData.end_datetime ||
    processedData.task_name ||
    processedData.device_id ||
    processedData.event ||
    processedData.llm_judge_status
  );

  let formParams: Record<string, any> = {};
  if (hasFilterParams) {
    formParams = { ...processedData };
    lastFormParams.value = snapshotFilters(processedData);
  } else if (Object.keys(lastFormParams.value).length > 0) {
    formParams = { ...lastFormParams.value };
  }

  fetch(formParams);
}

function formatTime(time: string) {
  if (!time) return '-';
  return moment(time).format('YYYY-MM-DD HH:mm:ss');
}

function getAlertObjectLabel(item: any): string {
  if (item?.event === 'face_library_match') {
    return getAlertMatchedPersonName(item) || '-';
  }
  return item?.object || '-';
}

// 获取任务类型
function getTaskType(item: any): string | null {
  // 优先从 information 字段中获取 task_type
  let taskType = null;
  if (item.information) {
    if (typeof item.information === 'object' && item.information.task_type) {
      taskType = item.information.task_type;
    } else if (typeof item.information === 'string') {
      try {
        const info = JSON.parse(item.information);
        taskType = info?.task_type;
      } catch (e) {
        // 解析失败，忽略
      }
    }
  }
  
  // 如果 information 中没有，尝试从 item 本身获取
  if (!taskType && item.task_type) {
    taskType = item.task_type;
  }
  
  return taskType;
}

// 判断是否是抓拍任务
function isSnapTask(item: any): boolean {
  const taskType = getTaskType(item);
  return taskType === 'snap' || taskType === 'snapshot';
}

// 获取任务类型文本
function getTaskTypeText(item: any): string {
  const taskType = getTaskType(item);
  
  // 根据 task_type 返回文本（不带括号，因为样式会处理）
  if (taskType === 'snap' || taskType === 'snapshot') {
    return '抓拍';
  } else {
    return '实时';
  }
}

// 获取任务类型样式类
function getTaskTypeClass(item: any): string {
  const taskType = getTaskType(item);
  
  // 根据 task_type 返回样式类
  if (taskType === 'snap' || taskType === 'snapshot') {
    return 'task-type-snap';
  } else {
    return 'task-type-realtime';
  }
}

// 格式化设备ID显示（超过8个字符省略）
function formatDeviceId(deviceId: string | null | undefined): string {
  if (!deviceId) return '-';
  if (deviceId.length <= 8) return deviceId;
  return deviceId.substring(0, 8) + '...';
}

// 复制设备ID（完整ID）
async function handleCopyDeviceId(deviceId: string | null | undefined) {
  if (!deviceId) {
    createMessage.warn('设备ID为空');
    return;
  }
  if (navigator.clipboard) {
    await navigator.clipboard.writeText(deviceId);
  } else {
    // 降级方案
    const textarea = document.createElement('textarea');
    textarea.value = deviceId;
    document.body.appendChild(textarea);
    textarea.select();
    document.execCommand('copy');
    document.body.removeChild(textarea);
  }
  createMessage.success('复制成功');
}

async function handleViewImage(record: object) {
  const r = record as Record<string, any>;
  if (!r['image_url'] || String(r['image_url']).trim() === '') {
    createMessage.warn('告警图片不存在');
    return;
  }
  emit('viewImage', record);
}

async function handleViewVideo(record: object) {
  if (!record['device_id'] || !record['time']) {
    createMessage.warn('缺少必要信息：设备ID或告警时间');
    return;
  }
  
  emit('viewVideo', record);
}

async function handleCopy(record: object) {
  const text = JSON.stringify(record, null, 2);
  if (navigator.clipboard) {
    await navigator.clipboard.writeText(text);
  } else {
    // 降级方案
    const textarea = document.createElement('textarea');
    textarea.value = text;
    document.body.appendChild(textarea);
    textarea.select();
    document.execCommand('copy');
    document.body.removeChild(textarea);
  }
  createMessage.success('复制成功');
}

function thumbUrl(imageUrl: string | null | undefined): string {
  return resolveAlertImageDisplayUrl(imageUrl);
}
</script>

<style lang="less" scoped>
.alert-card-list-wrapper {
  :deep(.ant-list-header) {
    border-block-end: 0;
  }
  :deep(.ant-list-header) {
    padding-top: 0;
    padding-bottom: 8px;
  }
  :deep(.ant-list) {
    padding: 8px;
  }
  :deep(.ant-list-item) {
    margin: 8px;
    transition: all 0.3s ease;
    
    &:hover {
      transform: translateY(-4px);
    }
  }
  :deep(.alert-item) {
    overflow: hidden;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
    border-radius: 12px;
    padding: 16px 0;
    position: relative;
    background-color: #fff;
    background-repeat: no-repeat;
    background-position: center center;
    background-size: 104% 104%;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    min-height: 208px;
    height: 100%;
    border: 1px solid rgba(0, 0, 0, 0.06);
    
    &:hover {
      box-shadow: 0 4px 16px rgba(0, 0, 0, 0.12);
      transform: translateY(-2px);
      border-color: rgba(59, 130, 246, 0.2);
    }

    &.normal {
      background-image: url('@/assets/images/product/blue-bg.719b437a.png');
    }

    &.error {
      background-image: url('@/assets/images/product/red-bg.101af5ac.png');
    }

    .corner-tags {
      position: absolute;
      top: 0;
      right: 0;
      z-index: 2;
      display: flex;
      flex-direction: row;
      align-items: center;
      gap: 4px;
    }

    .task-type-tag {
      position: relative;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      padding: 4px 10px;
      border-radius: 0 11px 0 8px;
      font-size: 12px;
      font-weight: 500;
      line-height: 1.2;      white-space: nowrap;
      transition: all 0.3s ease;
      box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);

      &.task-type-realtime {
        background: #3B82F6;
        color: #ffffff;
        border: 1px solid #2563EB;
        border-top: none;
        border-right: none;

        &:hover {
          box-shadow: 0 2px 6px rgba(59, 130, 246, 0.4);
          background: #2563EB;
        }
      }

      &.task-type-snap {
        background: #10B981;
        color: #ffffff;
        border: 1px solid #059669;

        &:hover {
          box-shadow: 0 2px 6px rgba(16, 185, 129, 0.4);
          background: #059669;
        }
      }
    }

    .llm-judge-tag {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      padding: 4px 10px;
      border-radius: 8px 0 0 8px;
      font-size: 12px;
      font-weight: 500;
      line-height: 1.2;
      white-space: nowrap;
      transition: all 0.3s ease;
      box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);

      &--confirmed {
        background: #10B981;
        color: #ffffff;
        border: 1px solid #059669;

        &:hover {
          box-shadow: 0 2px 6px rgba(16, 185, 129, 0.4);
          background: #059669;
        }
      }

      &--rejected {
        background: #F59E0B;
        color: #ffffff;
        border: 1px solid #D97706;

        &:hover {
          box-shadow: 0 2px 6px rgba(245, 158, 11, 0.4);
          background: #D97706;
        }
      }

      &--pending {
        background: #8B5CF6;
        color: #ffffff;
        border: 1px solid #7C3AED;

        &:hover {
          box-shadow: 0 2px 6px rgba(139, 92, 246, 0.4);
          background: #7C3AED;
        }
      }

      &--error {
        background: #EF4444;
        color: #ffffff;
        border: 1px solid #DC2626;

        &:hover {
          box-shadow: 0 2px 6px rgba(239, 68, 68, 0.4);
          background: #DC2626;
        }
      }
    }

    .alert-info {
      flex-direction: column;
      max-width: calc(100% - 108px);
      padding-left: 16px;
      padding-right: 4px;

      .title-wrapper {
        display: flex;
        align-items: center;
        height: 40px;
        margin-bottom: 2px;
        padding-right: 52px;

        .title {
          flex: 1;
          font-size: 16px;
          font-weight: 600;
          color: #050708;
          line-height: 20px;
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
          min-width: 0;
        }
      }

      .alert-business-tags {
        display: flex;
        flex-wrap: wrap;
        gap: 4px;
        margin-bottom: 8px;
        padding-left: 0;
      }

      .props {
        margin-top: 10px;

        .prop {
          flex: 1;
        margin-bottom: 12px;

          .label {
            font-size: 12px;
          font-weight: 500;
          color: #8B8B8B;
          line-height: 16px;
          margin-bottom: 4px;
          letter-spacing: 0.2px;
          }

          .value {
            font-size: 14px;
            font-weight: 600;
          color: #1F2937;
          line-height: 18px;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            display: flex;
            align-items: center;
          transition: color 0.2s ease;
          
          &:hover {
            color: #3B82F6;
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
        width: 130px;
        height: 28px;
        border-radius: 45px;
        justify-content: space-around;
        padding: 0 10px;
        align-items: center;
        border: 2px solid #266cfbff;
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(10px);
        transition: all 0.3s ease;
        
        &:hover {
          border-color: #3B82F6;
          box-shadow: 0 2px 8px rgba(59, 130, 246, 0.2);
        }

        .btn {
          width: 28px;
          height: 28px;
          text-align: center;
          position: relative;
          cursor: pointer;
          display: flex;
          align-items: center;
          justify-content: center;
          border-radius: 50%;
          transition: all 0.3s ease;

          &:before {
            content: '';
            display: block;
            position: absolute;
            width: 1px;
            height: 14px;
            background: linear-gradient(to bottom, transparent, #e2e2e2, transparent);
            left: 0;
            top: 50%;
            transform: translateY(-50%);
            opacity: 0.6;
          }

          &:first-child:before {
            display: none;
          }

          :deep(.anticon) {
            display: flex;
            align-items: center;
            justify-content: center;
            color: #3B82F6;
            transition: all 0.3s ease;
            font-size: 15px;
          }

          &:hover {
            background: rgba(59, 130, 246, 0.1);
            transform: scale(1.1);
            
            :deep(.anticon) {
              color: #2563EB;
            }
          }
          
          &:active {
            transform: scale(0.95);
          }
        }
      }
    }

    .alert-img {
      position: absolute;
      right: 20px;
      top: 50px;
      transition: transform 0.3s ease;

      &:hover {
        transform: scale(1.05);
      }

      img {
        cursor: pointer;
        width: 80px;
        height: 60px;
        object-fit: cover;
        border-radius: 6px;
        transition: all 0.3s ease;
      }

      .no-image {
        width: 80px;
        height: 60px;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        background-color: #f5f5f5;
        border-radius: 4px;

        &.loading {
          :deep(.anticon) {
            animation: spin 1s linear infinite;
          }
        }
      }

      @keyframes spin {
        from {
          transform: rotate(0deg);
        }
        to {
          transform: rotate(360deg);
        }
      }
    }
  }
}
</style>

