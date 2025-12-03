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
              <div class="alert-info">
                <div class="title o2">{{ item.event || '未知事件' }}</div>
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
                      <div class="label">告警对象</div>
                      <div class="value">{{ item.object || '-' }}</div>
                    </div>
                  </div>
                </div>
                <div class="btns">
                  <div class="btn" @click="handleCopy(item)">
                    <Icon icon="tdesign:copy-filled" :size="15" color="#3B82F6" />
                  </div>
                  <div class="btn" @click="handleViewImage(item)" v-if="item.image_path">
                    <Icon icon="ion:image-sharp" :size="15" color="#3B82F6" />
                  </div>
                  <div class="btn" @click="handleViewVideo(item)" v-if="item.device_id && item.time">
                    <Icon icon="icon-park-outline:video" :size="15" color="#3B82F6" />
                  </div>
                </div>
              </div>
              <div class="alert-img">
                <img :src="ALERT"alt="" class="img">
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
import { List, Spin } from 'ant-design-vue';
import { BasicForm, useForm } from '@/components/Form';
import { propTypes } from '@/utils/propTypes';
import { isFunction } from '@/utils/is';
import { useMessage } from '@/hooks/web/useMessage';
import { Icon } from '@/components/Icon';
import moment from 'moment';
import ALERT from "@/assets/images/alert/alert.png";

const ListItem = List.Item;

// 组件接收参数
const props = defineProps({
  // 请求API的参数
  params: propTypes.object.def({}),
  // api
  api: propTypes.func,
});

const { createMessage } = useMessage();

// 暴露内部方法
const emit = defineEmits(['getMethod', 'viewImage', 'viewVideo']);

// 数据
const data = ref([]);
const state = reactive({
  loading: true,
});

// 表单
const [registerForm, { validate }] = useForm({
  schemas: [
    {
      field: `object`,
      label: `告警对象`,
      component: 'Select',
      componentProps: {
        options: [
          {value: null, label: '全部'},
          {value: "人", label: "人"},
          {value: "自行车", label: "自行车"},
          {value: "汽车", label: "汽车"},
          {value: "摩托车", label: "摩托车"},
          {value: "飞机", label: "飞机"},
          {value: "公共汽车", label: "公共汽车"},
          {value: "火车", label: "火车"},
          {value: "卡车", label: "卡车"},
          {value: "船", label: "船"},
          {value: "交通灯", label: "交通灯"},
          {value: "消防栓", label: "消防栓"},
          {value: "停车标志", label: "停车标志"},
          {value: "停车收费表", label: "停车收费表"},
          {value: "长凳", label: "长凳"},
          {value: "鸟", label: "鸟"},
          {value: "猫", label: "猫"},
          {value: "狗", label: "狗"},
          {value: "马", label: "马"},
          {value: "羊", label: "羊"},
          {value: "母牛", label: "母牛"},
          {value: "大象", label: "大象"},
          {value: "熊", label: "熊"},
          {value: "斑马", label: "斑马"},
          {value: "长颈鹿", label: "长颈鹿"},
          {value: "背包", label: "背包"},
          {value: "雨伞", label: "雨伞"},
          {value: "手提包", label: "手提包"},
          {value: "领带", label: "领带"},
          {value: "手提箱", label: "手提箱"},
          {value: "飞盘", label: "飞盘"},
          {value: "滑雪板", label: "滑雪板"},
          {value: "运动用球", label: "运动用球"},
          {value: "风筝", label: "风筝"},
          {value: "棒球棍", label: "棒球棍"},
          {value: "棒球手套", label: "棒球手套"},
          {value: "滑板", label: "滑板"},
          {value: "冲浪板", label: "冲浪板"},
          {value: "网球拍", label: "网球拍"},
          {value: "瓶子", label: "瓶子"},
          {value: "酒杯", label: "酒杯"},
          {value: "杯子", label: "杯子"},
          {value: "叉", label: "叉"},
          {value: "刀", label: "刀"},
          {value: "勺子", label: "勺子"},
          {value: "碗", label: "碗"},
          {value: "香蕉", label: "香蕉"},
          {value: "苹果", label: "苹果"},
          {value: "三明治", label: "三明治"},
          {value: "橙子", label: "橙子"},
          {value: "西兰花", label: "西兰花"},
          {value: "胡萝卜", label: "胡萝卜"},
          {value: "热狗", label: "热狗"},
          {value: "披萨", label: "披萨"},
          {value: "甜甜圈", label: "甜甜圈"},
          {value: "糕饼", label: "糕饼"},
          {value: "椅子", label: "椅子"},
          {value: "沙发", label: "沙发"},
          {value: "盆栽植物", label: "盆栽植物"},
          {value: "床", label: "床"},
          {value: "餐桌", label: "餐桌"},
          {value: "马桶", label: "马桶"},
          {value: "显示器", label: "显示器"},
          {value: "笔记本电脑", label: "笔记本电脑"},
          {value: "鼠标", label: "鼠标"},
          {value: "遥控器", label: "遥控器"},
          {value: "键盘", label: "键盘"},
          {value: "手机", label: "手机"},
          {value: "微波炉", label: "微波炉"},
          {value: "烤箱", label: "烤箱"},
          {value: "烤面包机", label: "烤面包机"},
          {value: "洗手池", label: "洗手池"},
          {value: "冰箱", label: "冰箱"},
          {value: "书", label: "书"},
          {value: "时钟", label: "时钟"},
          {value: "花瓶", label: "花瓶"},
          {value: "剪刀", label: "剪刀"},
          {value: "泰迪熊", label: "泰迪熊"},
          {value: "吹风机", label: "吹风机"},
          {value: "牙刷", label: "牙刷"},
        ],
      },
      defaultValue: null,
    },
    {
      field: `event`,
      label: `告警事件`,
      component: 'Select',
      componentProps: {
        options: [
          {value: null, label: '全部'},
          {value: "行人检测", label: "行人检测"},
        ]
      },
      defaultValue: null,
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
    },
  ],
  labelWidth: 120,
  baseColProps: { span: 6 },
  actionColOptions: { span: 6 },
  autoSubmitOnEnter: true,
  submitFunc: handleSubmit,
});

// 表单提交
async function handleSubmit() {
  const formData = await validate();
  // 处理时间范围参数
  const timeRangeKey = '[begin_datetime, end_datetime]';
  if (formData[timeRangeKey] && Array.isArray(formData[timeRangeKey])) {
    const [begin, end] = formData[timeRangeKey];
    formData.begin_datetime = begin;
    formData.end_datetime = end;
    delete formData[timeRangeKey];
  }
  await fetch(formData);
}

// 自动请求并暴露内部方法
onMounted(() => {
  fetch();
  emit('getMethod', fetch);
});

async function fetch(p = {}) {
  const { api, params } = props;
  if (api && isFunction(api)) {
    try {
      state.loading = true;
      const res = await api({ ...params, pageNo: page.value, pageSize: pageSize.value, ...p });
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

// 分页相关
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

function formatTime(time: string) {
  if (!time) return '-';
  return moment(time).format('YYYY-MM-DD HH:mm:ss');
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
  if (!record['image_path']) {
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

// 图片处理
const imageUrls = reactive<Record<string, string>>({});
const imageLoading = new Set<string>();

function getImageUrl(imagePath: string) {
  if (!imagePath) return '';
  if (imageUrls[imagePath]) {
    return imageUrls[imagePath];
  }
  // 异步加载图片
  if (!imageLoading.has(imagePath)) {
    imageLoading.add(imagePath);
    loadImage(imagePath);
  }
  return '';
}

async function loadImage(imagePath: string) {
  try {
    const blob = await getAlertImage(imagePath);
    const url = window.URL.createObjectURL(blob);
    imageUrls[imagePath] = url;
  } catch (error) {
    console.error('加载图片失败:', error);
    imageLoading.delete(imagePath);
  }
}

function handleImageError(event: Event) {
  const img = event.target as HTMLImageElement;
  img.style.display = 'none';
}

// 清理图片 URL
onUnmounted(() => {
  Object.values(imageUrls).forEach((url) => {
    window.URL.revokeObjectURL(url);
  });
  Object.keys(imageUrls).forEach((key) => {
    delete imageUrls[key];
  });
  imageLoading.clear();
});
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
    padding: 6px;
  }
  :deep(.ant-list-item) {
    margin: 6px;
  }
  :deep(.alert-item) {
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

    &.normal {
      background-image: url('@/assets/images/product/blue-bg.719b437a.png');
    }

    &.error {
      background-image: url('@/assets/images/product/red-bg.101af5ac.png');
    }

    .alert-info {
      flex-direction: column;
      max-width: calc(100% - 128px);
      padding-left: 16px;

      .title {
        font-size: 16px;
        font-weight: 600;
        color: #050708;
        line-height: 20px;
        height: 40px;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
      }

      .props {
        margin-top: 10px;

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
            display: flex;
            align-items: center;
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

          :deep(.anticon) {
            display: flex;
            align-items: center;
            justify-content: center;
            color: #87CEEB;
            transition: color 0.3s;
          }

          &:hover :deep(.anticon) {
            color: #5BA3F5;
          }
        }
      }
    }

    .alert-img {
      position: absolute;
      right: 20px;
      top: 50px;

      img {
        cursor: pointer;
        width: 120px;
        height: 90px;
        object-fit: cover;
        border-radius: 4px;
      }

      .no-image {
        width: 120px;
        height: 90px;
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

