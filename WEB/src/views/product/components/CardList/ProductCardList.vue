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
              <span style="padding-left: 7px;font-size: 16px;font-weight: 500;line-height: 24px;">产品列表</span>
              <div class="space-x-2">
                <slot name="header"></slot>
              </div>
            </div>
          </template>
          <template #renderItem="{ item }">
            <ListItem :class="item.status == 0? 'product-item normal' : 'product-item error'">
              <div class="product-info">
                <div class="status">{{item.status == 0? '启用' : '禁用'}}</div>
                <div class="title o2">{{item.productName}}</div>
                <div class="props">
                  <div class="flex" style="justify-content: space-between;">
                    <div class="prop">
                      <div class="label">产品类型</div>
                      <div class="value">{{item.productType == 'COMMON' ? '普通产品' : item.productType == 'GATEWAY' ? '网关产品' : item.productType == 'VIDEO_COMMON' ? '视频设备' : '子设备'}}</div>
                    </div>
                    <div class="prop">
                      <div class="label">协议类型</div>
                      <div class="value">{{item.protocolType}}</div>
                    </div>
                  </div>
                  <div class="prop">
                    <div class="label">产品标识</div>
                    <div class="value">{{item.productIdentification}}</div>
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
                  <div class="btn">
                    <img src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACEAAAAgCAYAAACcuBHKAAAAAXNSR0IArs4c6QAAAyxJREFUWEe9WFFS2zAQ3fUHTL4KJwBukJ6g5ATAp6Vhik9AOAFwgoYTmH5Y5q/0BMAJSk9AeoLmjzEz8TLPSKA4dqIEiGbyEVvafVqt3r41U8vI83ybmfdEpIsfM29gqohst62pP2fmoYiMmHkkIvdEdM/Md3EcD/25XF8I50SUishuqLMl5g2KojhPkmSEtRMgAEBE/hARdg3018x8S0TYUYVea/0v1GmWZVtEtMnMX6Io6pZluU9EbnPDoii+AsgrCAvghogQieuiKBKHNNRpyLw0TbfX19edn1ulVO8VRJZlZ8x8il0rpXZCDC47xwKpIj4ej99AGGMebBR2lVJ3yzoIXZfn+amIYOOXVSSyLEP2A9mnR8GBtMf/UN0ePDTGIGF+EVF1RqG7ee88Y8x/HEkF4urq6rgsywERDZRSJ23Gsyw7Yubj8Xh8cnh4iFvzrmGMQfS7FQjvfM7iOD5vsmyM6RPRD/vuSCn1810IXvzegI/cccB4X0T6WuuLunHv5oAxz7TWjUAXBZXnOUjxyEWi+kNEUzusARhFUQT6nTmQbOCaedEKBuHObZ7jlvdg2gOtdSPwYBA1hsNxJMwMTmkdIrJjiQ9lAFHpNQEJBgFPNSBDZu7VK2FLMle51sY/C4GwQDYs54PYWm9RHYxjYtBz/VovDMIB6XQ63x4fH+9Ci9ssDloKxDLJaQkuRY2I4zjxbawMhCPCJjZeCYg0TZFHoGZolKnq/OkgLADUo+9Bt8MYM5O267mQ5znYtXWUZQmRfOxkopVxE+IWi40xqNz7wQXMefTKfkie3lqZOAXAFs63AhZayj2+gCqqWoCmAYlva8dMhTZRyr3doegchGzxI+ZMiBpfammtNz/CwTwbvqR8VdsOVRO9zjO4zHuXAiLyInRtklTqdxU6s9bjvCgrL+EcsaDzOgmplItGwR4DribK/KXWOploA/0JMF71BMz3IvIXhINniwCzfS00SDeKoi0R2fd6XLSBvSRJhlMNMbTD2traKTPPJKRFI+DNR487eHp6umhsiH3DANPpdPbKskQDC05wnwSCPw246LmGGs11URS/6zLgGVPPclyYq0cCAAAAAElFTkSuQmCC"
                         alt=""></div>
                  <div class="btn" :onclick="handleEdit.bind(null, item)">
                    <img src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACIAAAAeCAYAAABJ/8wUAAAAAXNSR0IArs4c6QAAAwpJREFUWEftV0Fu00AUfd8hXVQs0l1IinBPQHoCnBuEExCk1i1sak7Q9AQNCyRoKjWcoPQEgRMknKBGokkQmyBBBWkzD41Tp67r2A4JEgu8tP//8+bPm/+eBf/II4vCUdxkSRl4IkQFgBlRtwNBRwn2+q/FDX9fCJDiBh0a2E+5KfeCePy1IZ1g/NxAipusUnCkixKoI4t675V8CoPKP+MjYwQHQAXEQGWwHuzMXEDMKnPDJbT1UYwI50tDXiZ1pWhzn4BD4n2vIWU/fi4gfjfCRePAaPAXWZxSkGMWpt89D0jBZkWInaTd0IDbfSNP/bjA7pxeim74eYUtHkOTmugIMNDvPSB+wSQg+vv5ECuDpnjJhS0egagKUD07kLdp8oN5kWTVZEoqlLnEt7MA21c3uaMEdU3S3oG8SMoPdLJNoETC4R14t2cujuS3aRkKrahbMA3UfZuVEXBMwO0dyNpCyKqL3NtiSwgLgKsMlKOGlb/Y6jYtpbyrbiqFWv9Q9hYGJF+lKUtoyfU0fQeM232DAwKLY8BQRLPfuCb93EfjL6TBGFnsQlCN5YkeZEQ92ImFdSS4sAaELCxD8CAMSAHuzyFO/Bt3q2Npmf634+a6NYsE9x/IH3FE33+M8FAJcsECBjEA8fHzobyf95hij+ZKDI+0UiYslDjMkoBOBVKwWQOwqwtomdc2z1fKSVHCpMDyhhkxuADKYeeVBCB2juS3aRoKpzoojeEJqLd7PsT6tFkRByqyI75fCOtBXKGJ5ijUugENmakjOYe5u99R8pOUgZanCUOs9Zu3HXdU8YmqhixguPY0YHHGyO0GZDppZ4HjvJFXtOl5j6R8D0h+g5ZkxsTUjyfrxKDbkJWkAv734nOWeIk2iU6vIev++7zNXZGx6s7OEZuaqNozlPspZ8SEsESzG5L4JBDe5qOCCjZ1d/T1TTUf9LFkRmjreaMIq9+QD2kWD8ZEAtGW/9cS2ldmxxWg9mMZJ4P62DT7jybi8jkc/Qfg/R7M6F0TgXi8ue28YjcZ5bpm6cpvMNhsJB8wSzUAAAAASUVORK5CYII="
                         alt=""></div>
                </div>
              </div>
              <div class="product-img">
                <img
                  :src="item.productType == 'COMMON'? PRODUCT_NORMAL : item.productType == 'GATEWAY'? PRODUCT_GATEWAY : item.productType == 'VIDEO_COMMON'? PRODUCT_VIDEO : PRODUCT_SUB"
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

import PRODUCT_NORMAL from "@/assets/images/product/product_normal.png";
import PRODUCT_GATEWAY from "@/assets/images/product/product_gateway.png";
import PRODUCT_SUB from "@/assets/images/product/product_sub.png";
import PRODUCT_VIDEO from "@/assets/images/product/product_video.png";
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
      field: `productName`,
      label: `产品名称`,
      component: 'Input',
    },
    {
      field: `model`,
      label: `产品型号`,
      component: 'Input',
    },
    {
      field: `manufacturerName`,
      label: `厂商名称`,
      component: 'Input',
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

  :deep(.product-item) {
    overflow: hidden;
    box-shadow: 0 0 4px #00000026;
    border-radius: 8px;
    padding: 16px 0;
    position: relative;
    background-color: #fff;
    background-repeat: no-repeat;
    background-position: center center;
    background-size: 104% 104%;
    transition: all .5s;
    min-height: 208px;
    height: 100%;

    &.normal {
      background-image: url('@/assets/images/product/blue-bg.719b437a.png');

      .status {
        background: #d9dffd;
        color: #266CFBFF;
      }
    }

    &.error {
      background-image: url('@/assets/images/product/red-bg.101af5ac.png');

      .status {
        background: #fad7d9;
        color: #d43030;
      }
    }

    .product-info {
      flex-direction: column;
      max-width: calc(100% - 128px);
      padding-left: 16px;

      .status {
        width: 57px;
        height: 25px;
        border-radius: 6px 0 0 6px;
        font-size: 12px;
        font-weight: 500;
        line-height: 25px;
        text-align: center;
        position: absolute;
        right: 0;
        top: 16px;
      }

      .title {
        font-size: 16px;
        font-weight: 600;
        color: #050708;
        line-height: 20px;
        height: 40px;
      }

      .props{
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
        border: 2px solid #266CFBFF;

        .btn {
          width: 28px;
          text-align: center;
          position: relative;

          &:before {
            content: "";
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

          img {
            width: 15px;
            height: 15px;
            margin: 0 auto;
            cursor: pointer;
          }
        }
      }
    }

    .product-img {
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
