<template>
  <div class="device-card-list-wrapper p-2">
    <div class="p-4 bg-white">
      <BasicForm @register="registerForm"/>
    </div>
    <div class="p-2 bg-white">
      <Spin :spinning="state.loading">
        <List
          :grid="{ gutter: 2, xs: 1, sm: 2, md: 4, lg: 4, xl: 4, xxl: 4}"
          :data-source="data"
          :pagination="paginationProp"
        >
          <template #header>
            <div
              style="display: flex;align-items: center;justify-content: space-between;flex-direction: row;">
              <span style="padding-left: 7px;font-size: 16px;font-weight: 500;line-height: 24px;">设备信息档案列表</span>
              <div class="space-x-2">
                <slot name="header"></slot>
              </div>
            </div>
          </template>
          <template #renderItem="{ item }">
            <ListItem class="device-item">
              <div class="device-info">
                <img
                  :src="item.deviceType == 'COMMON'? DEVICE_IMAGE : item.deviceType == 'GATEWAY'? GATEWAY_IMAGE : item.deviceType == 'VIDEO_COMMON'? VIDEO_IMAGE : SUBDEVICE_IMAGE"
                  alt="" class="img" :onclick="handleView.bind(null, item)">
                <div class="info">
                  <div class="device-name">{{ item.deviceName }}</div>
                  <div class="device-form">
                    <span class="label">设备类型</span>
                    <span
                      class="value">{{
                        item.deviceType == 'COMMON' ? '普通设备' : item.deviceType == 'GATEWAY' ? '网关设备' : item.deviceType == 'VIDEO_COMMON' ? '视频设备' : '子设备'
                      }}</span>
                  </div>
                  <div class="device-form">
                    <span class="label">设备标识</span>
                    <span class="value">{{ item.deviceSn }}</span>
                  </div>
                  <div class="device-form">
                    <span class="label">产品标识</span>
                    <span class="value">{{ item.productIdentification }}</span>
                  </div>
                </div>
              </div>
              <div class="device-btns">
                <div class="device-status">
                <span class="red" v-if="item.connectStatus == 'ONLINE'"><img
                  src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABIAAAASCAYAAABWzo5XAAAAAXNSR0IArs4c6QAAAXVJREFUOE+tlDFWwkAQhmeCSxIqbiDcQAsNnXACoDJa4QnQE6gnEE+gVoANcIJgJ7HQG4A3oGIJS3Z8Swwv8ICE99hy38y3M//8swgHOnggDuwF4gU7lyKtTDT/1d33brSIxKCpdXWLQHWN4JUQcgB0wkyvhP3uWAETgbyC/YBE5WjizLJfNML+kdt8SwTaBFGJ4ty+J6RxetB+jgWF7UiEkvnZGoWaULGSFdz49iP3W1ujYi0rOHd8xOriRaKKMWg3AojuEGFXd1uPIXwrSBTsopRU1912dQGdeEOW4XnBjSciGEUhG1sLNIFjZhp3YsKHLOPl1WSEddkBqTXYV/Njk/dWKloXdmZd132UPZWYIuwwky/HvQ5bgpTZNAInbU5PQ2+o4MCE4EighvE/oZ0VqdeRZJZFBNwm7G7QmV0DDS7Sg9aNCtwHsiJ2MG7PAaAfJBgRQi2unZ27Nreuy1JCzk/JXtSEcb9Eol2Lg8SuSBJAGPMHDI/PE7ztinEAAAAASUVORK5CYII="
                  alt="" class="img">在线</span>
                  <span class="gray" v-else><img
                    src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABIAAAASCAYAAABWzo5XAAAAAXNSR0IArs4c6QAAASxJREFUOE+tlH9RA0EMhb9UQR1QHIACQEGpg6KgYOD2rQIOBYCCFgUFBeCA4qAOltnObme5uV/M9P7MJN/lvSRrnOizE3H4F0jSzMzmIYQfSZuyidEgSffAysxeQggz4AK4kbSPwFEgSQLmZaGkZzN7d869jgK1QWKh994Be+fc0yAoy0md7LInkqbAZxnvlJaSt8AiAW4l1TluZhvnnM/wPtB1NFfSIhV/A+fAo5ntSkirtOTJGfAAHIrjZCStJ5NJXVXVR9vu/emoaaz3fhVCeEuF63JqTdgRFJcNiJ5c5t2IyTluZnWeUG9H8e/AtNTeZWwvSNISuJJ0lzqJI942p9N1m6W0QyHwFacSQlgOyem9Ne99PIVZNFnScQmHXolRtzYEGTyRMYCc8wurKooTLDOIRQAAAABJRU5ErkJggg=="
                    alt="" class="img">离线</span>
                  <div class="ant-divider ant-divider-vertical" role="separator"></div>
                  <span class="green" v-if="item.activeStatus == 1">已激活</span>
                  <span class="red" v-else>未激活</span>
                </div>
                <div class="btn primary" :onclick="handleEdit.bind(null, item)">编辑</div>
                <Popconfirm
                  title="是否确认删除？"
                  ok-text="是"
                  cancel-text="否"
                  @confirm="handleDelete(item)"
                >
                  <div class="btn danger">删除</div>
                </Popconfirm>
              </div>
            </ListItem>
          </template>
        </List>
      </Spin>
    </div>
  </div>
</template>
<script lang="ts" setup>
import {computed, onMounted, reactive, ref} from 'vue';
import {Card, List, Popconfirm, Spin, Typography} from 'ant-design-vue';
import {BasicForm, useForm} from '@/components/Form';
import {propTypes} from '@/utils/propTypes';
import {isFunction} from '@/utils/is';
import {grid, useSlider} from './data';
import {getDeviceProfiles} from "@/api/device/product";
import DEVICE_IMAGE from "@/assets/images/device/device.png";
import GATEWAY_IMAGE from "@/assets/images/device/gateway.png";
import SUBDEVICE_IMAGE from "@/assets/images/device/subDevice.png";
import VIDEO_IMAGE from "@/assets/images/device/video.png";

const ListItem = List.Item;
const CardMeta = Card.Meta;
const TypographyParagraph = Typography.Paragraph;
// 获取slider属性
const sliderProp = computed(() => useSlider(4));
// 组件接收参数
const props = defineProps({
  // 请求API的参数
  params: propTypes.object.def({}),
  //api
  api: propTypes.func,
});
//暴露内部方法
const emit = defineEmits(['getMethod', 'delete', 'edit', 'view']);
//数据
const data = ref([]);
const title = "设备列表";
// 切换每行个数
// cover图片自适应高度
//修改pageSize并重新请求数据

const height = computed(() => {
  return `h-${120 - grid.value * 6}`;
});

const state = reactive({
  loading: true,
});

//表单
const [registerForm, {validate}] = useForm({
  schemas: [
    {
      field: `deviceName`,
      label: `设备名称`,
      component: 'Input',
    },
    {
      field: `productIdentification`,
      label: `所属产品`,
      component: 'ApiSelect',
      componentProps: {
        api: getDeviceProfiles,
        beforeFetch: () => {
          return {
            page: 1,
            pageSize: 100,
          };
        },
        resultField: 'data',
        // use name as label
        labelField: 'productName',
        // use id as value
        valueField: 'productIdentification',
      },
    },
    {
      field: `deviceIdentification`,
      label: `设备标识`,
      component: 'Input',
    },
    {
      field: `deviceSn`,
      label: `设备SN号`,
      component: 'Input',
    },
    {
      field: `connectStatus`,
      label: `连接状态`,
      component: 'Select',
      componentProps: {
        options: [
          {value: '', label: '全部'},
          {value: 'ONLINE', label: '在线'},
          {value: 'OFFLINE', label: '离线'},
        ],
      },
      defaultValue: '',
    },
    {
      field: `deviceType`,
      label: `产品类型`,
      component: 'Select',
      componentProps: {
        options: [
          {value: '', label: '全部'},
          {value: 'COMMON', label: '普通产品'},
          {value: 'GATEWAY', label: '网关产品'},
          {value: 'SUBSET', label: '子设备'},
        ],
      },
      defaultValue: '',
    },
    {
      field: `activeStatus`,
      label: `激活状态`,
      component: 'Select',
      componentProps: {
        options: [
          {value: '', label: '全部'},
          {value: 1, label: '已激活'},
          {value: 0, label: '未激活'},
        ],
      },
      defaultValue: '',
    },
  ],
  labelWidth: 80,
  baseColProps: {span: 6},
  actionColOptions: {span: 6},
  autoSubmitOnEnter: true,
  submitFunc: handleSubmit,
});

//表单提交
async function handleSubmit() {
  const data = await validate();
  await fetch(data);
}

function sliderChange(n) {
  pageSize.value = n * 4;
  fetch();
}

// 自动请求并暴露内部方法
onMounted(() => {
  fetch();
  emit('getMethod', fetch);
});

async function fetch(p = {}) {
  const {api, params} = props;
  if (api && isFunction(api)) {
    const res = await api({...params, pageNo: page.value, pageSize: pageSize.value, ...p});
    data.value = res.data;
    total.value = res.total;
    hideLoading();
  }
}

function hideLoading() {
  state.loading = false;
}

//分页相关
const page = ref(1);
const pageSize = ref(20);
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

async function handleView(record: object) {
  emit('view', record);
}

async function handleEdit(record: object) {
  emit('edit', record);
}

async function handleDelete(record: object) {
  emit('delete', record);
}
</script>
<style lang="less" scoped>
.device-card-list-wrapper {

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

  :deep(.device-item) {
    display: flex;
    align-items: center;
    justify-content: space-between;
    overflow: hidden;
    box-shadow: 0 0 4px #00000026;
    border-radius: 8px;
    padding-bottom: 16px;
    cursor: pointer;
    position: relative;
    background-color: #fff;
    transition: all .5s;
    border: 2px solid transparent;

    .device-info {
      flex: 1;
      display: flex;
      flex-direction: column;
      align-items: center;
      max-width: calc(100% - 140px);
      padding: 10px 10px 0;

      img {
        width: 70%;
        border-radius: 10px;
      }

      .info {
        max-width: 100%;

        .device-name {
          font-size: 18px;
          font-weight: 700;
          margin-bottom: 16px;
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
          max-width: 100%;
        }

        .device-form {
          display: flex;
          align-items: center;
          width: 100%;
          line-height: 20px;

          .label {
            width: 50px;
            text-align: right;
            font-size: 12px;
            font-weight: 500;
            color: #b6b6b6;
          }

          .value {
            width: calc(100% - 46px);
            font-size: 14px;
            font-weight: 500;
            color: #2a2a2a;
            padding-left: 8px;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
          }
        }
      }
    }

    .device-btns {
      width: 148px;
      display: flex;
      flex-direction: column;
      justify-content: center;
      align-items: center;
      border-left: 1px dashed #d4d4d4;

      .btn {
        width: 92px;
        height: 32px;
        background: #266CFBFF;
        opacity: 1;
        text-align: center;
        font-size: 14px;
        line-height: 28px;
        color: #fff;
        border: 2px solid #266CFBFF;
        border-radius: 6px;
        margin-top: 18px;
      }

      .btn.danger {
        background-color: #fff;
        color: #d43030;
        border: 2px solid #d43030;
      }

      .device-status {
        padding-top: 6px;
        padding-bottom: 14px;
        border-bottom: 1px dashed #d4d4d4;
        display: flex;
        align-items: center;
        font-size: 16px;

        img {
          width: 18px;
          height: 18px;
          margin-right: 2px;
        }

        span.red {
          color: #fa3758;
        }

        span.gray {
          color: gray;
        }

        span.green {
          color: #43cf7c;
        }

        .ant-divider {
          box-sizing: border-box;
          margin: 0;
          padding: 0;
          color: #000000d9;
          font-size: 16px;
          font-variant: tabular-nums;
          line-height: 1.5715;
          list-style: none;
          font-feature-settings: tnum;
          border-top: 1px solid rgba(0, 0, 0, .06);
        }

        .ant-divider-vertical {
          position: relative;
          top: -.06em;
          display: inline-block;
          height: .9em;
          margin: 0 8px;
          vertical-align: middle;
          border-top: 0;
          border-left: 1px solid rgba(0, 0, 0, .06);
        }
      }
    }
  }
}
</style>
