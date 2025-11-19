<template>
  <div class="device-card-list-wrapper p-2">
    <div class="p-4 bg-white" style="margin-bottom: 10px">
      <BasicForm @register="registerForm"/>
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
              style="display: flex;align-items: center;justify-content: space-between;flex-direction: row;">
              <span style="padding-left: 7px;font-size: 16px;font-weight: 500;line-height: 24px;">设备信息档案列表</span>
              <div class="space-x-2">
                <slot name="header"></slot>
              </div>
            </div>
          </template>
          <template #renderItem="{ item }">
            <ListItem :class="item.connectStatus == 'ONLINE' && item.activeStatus == 1? 'device-item normal' : 'device-item error'">
              <div class="device-info">
                <div class="status">{{item.connectStatus == 'ONLINE' ? '在线' : '离线'}} / {{item.activeStatus == 1 ? '已激活' : '未激活'}}</div>
                <div class="title o2">{{ item.deviceName }}</div>
                <div class="props">
                  <div class="flex" style="justify-content: space-between;">
                    <div class="prop">
                      <div class="label">设备类型</div>
                      <div class="value">{{item.deviceType == 'COMMON' ? '普通设备' : item.deviceType == 'GATEWAY' ? '网关设备' : item.deviceType == 'VIDEO_COMMON' ? '视频设备' : '子设备'}}</div>
                    </div>
                    <div class="prop">
                      <div class="label">设备标识</div>
                      <div class="value">{{ item.deviceSn || '-' }}</div>
                    </div>
                  </div>
                  <div class="prop">
                    <div class="label">产品标识</div>
                    <div class="value">{{ item.productIdentification || '-' }}</div>
                  </div>
                </div>
                <div class="btns">
                  <div class="btn" @click="handleView(item)">
                    <Icon icon="ant-design:eye-filled" :size="15" color="#3B82F6" />
                  </div>
                  <div class="btn" @click="handleEdit(item)">
                    <Icon icon="ant-design:edit-filled" :size="15" color="#3B82F6" />
                  </div>
                  <Popconfirm
                    title="是否确认删除？"
                    ok-text="是"
                    cancel-text="否"
                    @confirm="handleDelete(item)"
                  >
                    <div class="btn">
                      <Icon icon="material-symbols:delete-outline-rounded" :size="15" color="#DC2626" />
                    </div>
                  </Popconfirm>
                </div>
              </div>
              <div class="device-img">
                <img
                  :src="item.deviceType == 'COMMON'? DEVICE_IMAGE : item.deviceType == 'GATEWAY'? GATEWAY_IMAGE : item.deviceType == 'VIDEO_COMMON'? VIDEO_IMAGE : SUBDEVICE_IMAGE"
                  alt="" class="img" @click="handleView(item)">
              </div>
            </ListItem>
          </template>
        </List>
      </Spin>
    </div>
  </div>
</template>
<script lang="ts" setup>
import {onMounted, reactive, ref} from 'vue';
import {List, Popconfirm, Spin} from 'ant-design-vue';
import {BasicForm, useForm} from '@/components/Form';
import {propTypes} from '@/utils/propTypes';
import {isFunction} from '@/utils/is';
import {Icon} from '@/components/Icon';
import {getDeviceProfiles} from "@/api/device/product";
import DEVICE_IMAGE from "@/assets/images/device/device.png";
import GATEWAY_IMAGE from "@/assets/images/device/gateway.png";
import SUBDEVICE_IMAGE from "@/assets/images/device/subDevice.png";
import VIDEO_IMAGE from "@/assets/images/device/video.png";
import {useMessage} from "@/hooks/web/useMessage";

const ListItem = List.Item;

// 组件接收参数
const props = defineProps({
  // 请求API的参数
  params: propTypes.object.def({}),
  //api
  api: propTypes.func,
});
const { createMessage } = useMessage();

//暴露内部方法
const emit = defineEmits(['getMethod', 'delete', 'edit', 'view']);

//数据
const data = ref([]);
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

// 自动请求并暴露内部方法
onMounted(() => {
  fetch();
  emit('getMethod', fetch);
});

async function fetch(p = {}) {
  const {api, params} = props;
  if (api && isFunction(api)) {
    try {
      state.loading = true;
      const res = await api({...params, pageNo: page.value, pageSize: pageSize.value, ...p});
      // 根据表格配置，返回格式为 { data: [...], total: ... }
      data.value = res.data || [];
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

      .device-info .status {
        background: #d9dffd;
        color: #266CFBFF;
      }
    }

    &.error {
      background-image: url('@/assets/images/product/red-bg.101af5ac.png');

      .device-info .status {
        background: #fad7d9;
        color: #d43030;
      }
    }

    .device-info {
      flex-direction: column;
      max-width: calc(100% - 128px);
      padding-left: 16px;

      .status {
        min-width: 90px;
        height: 25px;
        border-radius: 6px 0 0 6px;
        font-size: 12px;
        font-weight: 500;
        line-height: 25px;
        text-align: center;
        position: absolute;
        right: 0;
        top: 16px;
        padding: 0 8px;
        white-space: nowrap;
      }

      .title {
        font-size: 16px;
        font-weight: 600;
        color: #050708;
        line-height: 20px;
        height: 40px;
        padding-right: 90px;
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

    .device-img {
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
