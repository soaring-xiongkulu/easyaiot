<template>
  <div class="device-card-list-wrapper p-2">
    <div class="p-4 bg-white" style="margin-bottom: 10px">
      <BasicForm @register="registerForm"/>
    </div>
    <div class="p-2 bg-white">
      <Spin :spinning="state.loading">
        <List
          :grid="{ gutter: 8, xs: 1, sm: 2, md: 4, lg: 4, xl: 4, xxl: 4}"
          :data-source="data"
          :pagination="paginationProp"
          class="device-list"
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
                <div class="title">{{ item.deviceName }}</div>
                <div class="props">
                  <div class="flex" style="justify-content: space-between;">
                    <div class="prop">
                      <div class="label">设备类型</div>
                      <div class="value">{{item.deviceType == 'COMMON' ? '普通设备' : item.deviceType == 'GATEWAY' ? '网关设备' : item.deviceType == 'VIDEO_COMMON' ? '视频设备' : '子设备'}}</div>
                    </div>
                    <div class="prop">
                      <div class="label">设备标识</div>
                      <div class="value single-line">{{ item.deviceSn }}</div>
                    </div>
                  </div>
                  <div class="prop product-identification">
                    <div class="label">产品标识</div>
                    <div class="value">{{ item.productIdentification }}</div>
                  </div>
                </div>
                <div class="btns">
                  <Popconfirm
                    title="是否确认删除？"
                    ok-text="是"
                    cancel-text="否"
                    @confirm="handleDelete(item)"
                  >
                    <div class="btn">
                      <img src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAA8AAAAQCAYAAADJViUEAAAAAXNSR0IArs4c6QAAAi1JREFUOE+Nk89rE0EUx9/bzSZtJNSCBCvoxUhMstmdaYoIlnopglAs6iVC/wJB8SLFi3cVRPSmB0EE6an4owerIuqhIt3OjyRgq15EEHIr2tSYZp5kayTWlDi3N28+7/t+DUKXs1goxPubzYcEMI4Az9dte3IkCGpbn2I3uML5eTLmhKvUeIWxOUB8mhPi5rawYGxnFHGMjPEQ8QwB9AHAZwDYhwA/AHEGAORGs/nC13qtFQhLvn8MEM8hwCgiBgSwYAGsGGOqhFhHophlWUkiSgPiYSI6BACvbMu6jRXGZoHo0WAkMrOnS11bU1WetyOCeBIQT4c1/1b381Je69aDzrsSYxeBSOWVmg/hiu9PAWIxJ+VEy/7oeUl0nPr+IFj9VCgMUKMRS2ldDYUYm7OIHuSUur8Jc36cAC65QoyFNmM3iOirq9SVsu9PI+JQTsoLLV+Z89e2MVczSj1pK48S4i1XSt4TZkzYiGczQiyEsM7n81YkMusKkfoPeMUy5lRW6/Jmw1x3LzrOO1eIoV5wibFqnzHDB7T+EsLv0+nERjxedYXo7wVXOF+3a7XkweXlb3/Ws8zYz13GDO7Wek15XrLhOPWRIFhdLBQGnEYj5mtdrWSzUYpGv7tSRsMNa8+wzNhLQLzrCnFvu1mXOS8i0VR7pJ3wEQB4bBMVM0rNdwb4kErF6onEBBDdQcuazC0tvflLOew650dtgOtENPzPD0J8a4gu56V81vb9Ami8GYzeLnHJAAAAAElFTkSuQmCC"
                           alt="">
                    </div>
                  </Popconfirm>
                  <div class="btn" :onclick="handleCopy.bind(null, item)">
                    <img src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACAAAAAgCAYAAABzenr0AAAAAXNSR0IArs4c6QAABDpJREFUWEetV0FyWkcQff0VK1VKFningFOFbgAnAJ3A+ATGVQHJ2ZicAHQCS7sEVGVyAqETgE4gfAKziABXFmZjWQViXqpHf74+X4MEOOyomd/zpvu91z2CDX6pGlM716gBeA0gG4boQ9AXojcPcDH+UwarhJZVNsX3vDhkkXOcUZB64tsBBD0Q59c76E2OZeLbvxaATIU5Ci41EIkegca4JRf6X9cMUBBBEUQRDwF2BOhcNeXvOJC1AKSr/KQpNwaN8akcPZaB3bcsyC1yCFASBRT+LPAtvHElWhnAr1WW5sAZgcGoKXvrlG63zCyeoSiCutxxZnA9RX7SlsnKANIH/ACiTKI2asnJOgDcXgUi2+haEAaN4akcrQQgZL3WPmum2Bu3V2O4D+TuIYuBQRfE5HqGvaUAlO3G2LQVGNZwk/T7QPxywK7ywhjsLwDYPWRWiHeBQdkrM6I9bMmbTdIf/8aVU4ByBCDzG2sM8D5iK6BG0hFBT4gGgdzcoPT5VM7/BwBnIEoazwJIV9kAULeBibYB2k7f2TJT02180aXrKZ4rc78bQCjnGZEXTXtgoPqGAcrjhFGEXOiqfkct2f/ew6PziMmwJc/F1UNv7qtvpsr3BGoEjkdN+SOS1CGzW3NcUjCgoLc1x/k/p9J7CmCmQuXXBwKdUVNeiXM3Tce/LeknA2SqvNT6G6LoyuKsF0A3SVZtRmq5BC6uPPGSfqIAqAGHTXkgyXj9fev6nbXcuSWT2m0ufgFf2ZIXlkyFX/QWPoKtW/9UmamdH1GAQYmComYjXtbM78zxFprRyM4lSrHB/jhRwxcVvjOCY2/9iTpo2+1HX6p9XHDx4nxTAJZkzpsXDKNKlaZKtDFs3ne/KND9Ztv7ZwYnPh65bZkDqpqKcbVJ1OU8MnOMhaA9/GvRAXcrLAeCl0rQsMPpjNAftSS/TAmu3PF+IhHRwuYQN5r4mtlCftmY5YaRYIaLq/ZDJSmgGJ8WQFrmx5tDkgfpKs8AlAj0v02xv6kTRvJL+ImzYlvrJNmszOI9HBgI0Pi6g/NlM96SFqxu2/W1cwvA9ehlNUyAsGc8ZTgJMrssWveLr1kAWuvZM3xa5geR/VZYlgCv4zNeuKads68O6GSpQ8zPN8gZYztsTgcQM0M+OcxE7ud4oD06Obkm0+pmvAAoWMO5fxt4BaDGE0zxykfQCECkbY/kVmgwuTmQU1mGDxVryUpcGnRubnGyjLwRgHib1FltY7aHs4XemlPsPzU/LjSgdcqQzIp9MRF1Nz/OidrnFabnxZnwzt10/J48Zjx6uJLsp68oIYiaz91TjZjMgcYqh1s1JW/ijEcDkTjiD+ioA2YPmZ0a6NOsEKpgsfVqyg3aj9XbxyXvDDDbRt02qMd+ChDQAaYTLBk+niKvNwPuo/QBX+pLKHpougMFfRKdmxk+bkrUOLD/AJnzscretOw/AAAAAElFTkSuQmCC"
                         alt=""></div>
                  <div class="btn" :onclick="handleEdit.bind(null, item)">
                    <img src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACIAAAAeCAYAAABJ/8wUAAAAAXNSR0IArs4c6QAAAwpJREFUWEftV0Fu00AUfd8hXVQs0l1IinBPQHoCnBuEExCk1i1sak7Q9AQNCyRoKjWcoPQEgRMknKBGokkQmyBBBWkzD41Tp67r2A4JEgu8tP//8+bPm/+eBf/II4vCUdxkSRl4IkQFgBlRtwNBRwn2+q/FDX9fCJDiBh0a2E+5KfeCePy1IZ1g/NxAipusUnCkixKoI4t675V8CoPKP+MjYwQHQAXEQGWwHuzMXEDMKnPDJbT1UYwI50tDXiZ1pWhzn4BD4n2vIWU/fi4gfjfCRePAaPAXWZxSkGMWpt89D0jBZkWInaTd0IDbfSNP/bjA7pxeim74eYUtHkOTmugIMNDvPSB+wSQg+vv5ECuDpnjJhS0egagKUD07kLdp8oN5kWTVZEoqlLnEt7MA21c3uaMEdU3S3oG8SMoPdLJNoETC4R14t2cujuS3aRkKrahbMA3UfZuVEXBMwO0dyNpCyKqL3NtiSwgLgKsMlKOGlb/Y6jYtpbyrbiqFWv9Q9hYGJF+lKUtoyfU0fQeM232DAwKLY8BQRLPfuCb93EfjL6TBGFnsQlCN5YkeZEQ92ImFdSS4sAaELCxD8CAMSAHuzyFO/Bt3q2Npmf634+a6NYsE9x/IH3FE33+M8FAJcsECBjEA8fHzobyf95hij+ZKDI+0UiYslDjMkoBOBVKwWQOwqwtomdc2z1fKSVHCpMDyhhkxuADKYeeVBCB2juS3aRoKpzoojeEJqLd7PsT6tFkRByqyI75fCOtBXKGJ5ijUugENmakjOYe5u99R8pOUgZanCUOs9Zu3HXdU8YmqhixguPY0YHHGyO0GZDppZ4HjvJFXtOl5j6R8D0h+g5ZkxsTUjyfrxKDbkJWkAv734nOWeIk2iU6vIev++7zNXZGx6s7OEZuaqNozlPspZ8SEsESzG5L4JBDe5qOCCjZ1d/T1TTUf9LFkRmjreaMIq9+QD2kWD8ZEAtGW/9cS2ldmxxWg9mMZJ4P62DT7jybi8jkc/Qfg/R7M6F0TgXi8ue28YjcZ5bpm6cpvMNhsJB8wSzUAAAAASUVORK5CYII="
                         alt=""></div>
                </div>
              </div>
              <div class="device-img">
                <img
                  :src="item.deviceType == 'COMMON'? DEVICE_IMAGE : item.deviceType == 'GATEWAY'? GATEWAY_IMAGE : item.deviceType == 'VIDEO_COMMON'? VIDEO_IMAGE : SUBDEVICE_IMAGE"
                  alt="" class="img" :onclick="handleView.bind(null, item)">
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
import {useMessage} from "@/hooks/web/useMessage";

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
const { createConfirm, createMessage } = useMessage()
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

async function handleCopy(record: object) {
  await navigator.clipboard.writeText(JSON.stringify(record));
  createMessage.success('复制成功');
}

async function handleDelete(record: object) {
  emit('delete', record);
}
</script>
<style lang="less" scoped>
.device-card-list-wrapper {
  background: transparent;

  :deep(.ant-list-header) {
    border-block-end: 0;
    padding: 0 0 20px 0;
    margin-bottom: 0;
  }

  :deep(.ant-list) {
    padding: 0;
    background: transparent;
  }

  :deep(.ant-list-item) {
    margin: 0 0 16px 0;
    padding: 0;
    border: none;
  }

  :deep(.device-item) {
    overflow: hidden;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
    border-radius: 10px;
    padding: 14px;
    position: relative;
    background: linear-gradient(135deg, #ffffff 0%, #fafbfc 100%);
    background-repeat: no-repeat;
    background-position: right center;
    background-size: cover;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    min-height: 180px;
    height: 100%;
    border: 1px solid rgba(0, 0, 0, 0.06);
    display: flex;
    align-items: stretch;

    &:hover {
      box-shadow: 0 4px 16px rgba(0, 0, 0, 0.12);
      transform: translateY(-2px);
    }

    &.normal {
      background-image: linear-gradient(135deg, rgba(217, 223, 253, 0.1) 0%, rgba(230, 240, 255, 0.1) 100%),
                        url('@/assets/images/product/blue-bg.719b437a.png');
      background-size: 100% 100%, 100% 100%;
      background-position: center, right center;
      background-repeat: no-repeat, no-repeat;

      .status {
        background: linear-gradient(135deg, #d9dffd 0%, #c4d0fc 100%);
        color: #1890ff;
        box-shadow: 0 2px 4px rgba(24, 144, 255, 0.2);
      }
    }

    &.error {
      background-image: linear-gradient(135deg, rgba(250, 215, 217, 0.1) 0%, rgba(255, 230, 230, 0.1) 100%),
                        url('@/assets/images/product/red-bg.101af5ac.png');
      background-size: 100% 100%, 100% 100%;
      background-repeat: no-repeat, no-repeat;
      background-position: center, right center;

      .status {
        background: linear-gradient(135deg, #fad7d9 0%, #f5b8bb 100%);
        color: #ff4d4f;
        box-shadow: 0 2px 4px rgba(255, 77, 79, 0.2);
      }
    }

    .device-info {
      flex-direction: column;
      max-width: calc(100% - 130px);
      padding-left: 14px;
      padding-right: 8px;
      flex: 1;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      overflow: hidden;
      min-width: 0;

      .status {
        width: auto;
        min-width: 80px;
        height: 24px;
        border-radius: 6px;
        font-size: 11px;
        font-weight: 600;
        line-height: 24px;
        text-align: center;
        position: absolute;
        right: 16px;
        top: 16px;
        transition: all 0.3s ease;
        padding: 0 10px;
      }

      .title {
        font-size: 18px;
        font-weight: 700;
        color: #1a1a1a;
        line-height: 1.4;
        margin-bottom: 8px;
        padding-right: 90px;
        word-break: break-word;
        overflow: hidden;
        text-overflow: ellipsis;
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
      }

      .props {
        margin-top: 0;
        flex: 1;
        overflow: hidden;

        .flex {
          display: flex;
          gap: 8px;
          margin-bottom: 8px;
        }

        .prop {
          flex: 1;
          margin-bottom: 8px;
          padding: 4px 0;
          background: transparent;
          border-radius: 0;
          transition: all 0.3s ease;
          min-width: 0;

          &:nth-child(2) {
            flex: 1.2;
            margin-left: 4px;
            min-width: fit-content;
          }

          &:hover {
            transform: translateY(-1px);
          }

          &.product-identification {
            margin-bottom: 40px;
            margin-left: 0;
            padding-left: 0;
          }

          .label {
            font-size: 12px;
            font-weight: 500;
            color: rgba(0, 0, 0, 0.65);
            line-height: 1.4;
            margin-bottom: 3px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
          }

          .value {
            font-size: 15px;
            font-weight: 600;
            color: #1a1a1a;
            line-height: 1.4;
            word-break: break-word;
            overflow: hidden;
            text-overflow: ellipsis;
            display: -webkit-box;
            -webkit-line-clamp: 2;
            -webkit-box-orient: vertical;
            margin-top: 0;

            &.single-line {
              white-space: nowrap;
              display: block;
              -webkit-line-clamp: unset;
              -webkit-box-orient: unset;
              word-break: keep-all;
              overflow: visible;
            }
          }
        }
      }

      .btns {
        display: flex;
        position: absolute;
        left: 28px;
        bottom: 16px;
        width: 110px;
        height: 30px;
        border-radius: 15px;
        justify-content: space-around;
        padding: 0 10px;
        align-items: center;
        border: 2px solid #1890ff;
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(10px);
        transition: all 0.3s ease;

        &:hover {
          background: #1890ff;
          box-shadow: 0 4px 12px rgba(24, 144, 255, 0.3);

          .btn img {
            filter: brightness(0) invert(1);
          }
        }

        .btn {
          width: 26px;
          height: 26px;
          text-align: center;
          position: relative;
          display: flex;
          align-items: center;
          justify-content: center;
          cursor: pointer;
          transition: all 0.3s ease;
          border-radius: 5px;

          &:hover {
            background: rgba(24, 144, 255, 0.1);
            transform: scale(1.1);
          }

          &:before {
            content: "";
            display: block;
            position: absolute;
            width: 1px;
            height: 16px;
            background-color: #e8e8e8;
            left: 0;
            top: 50%;
            transform: translateY(-50%);
          }

          &:first-child:before {
            display: none;
          }

          img {
            width: 14px;
            height: 14px;
            margin: 0 auto;
            cursor: pointer;
            transition: all 0.3s ease;
          }
        }
      }
    }

    .device-img {
      position: absolute;
      right: 12px;
      top: 50%;
      transform: translateY(-50%);
      z-index: 1;

      img {
        cursor: pointer;
        width: 120px;
        height: 120px;
        object-fit: contain;
        transition: transform 0.3s ease;
        filter: drop-shadow(0 4px 8px rgba(0, 0, 0, 0.1));

        &:hover {
          transform: scale(1.05);
        }
      }
    }
  }
}
</style>
