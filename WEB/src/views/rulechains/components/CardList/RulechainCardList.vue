<template>
  <div class="rulechain-card-list-wrapper p-2">
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
              <span style="padding-left: 7px;font-size: 16px;font-weight: 500;line-height: 24px;">链式规则列表</span>
              <div class="space-x-2">
                <slot name="header"></slot>
              </div>
            </div>
          </template>
          <template #renderItem="{ item }">
            <ListItem :class="!item.disabled? 'product-item normal' : 'product-item error'">
              <div class="product-info">
                <div class="status">{{ !item.disabled ? '启用' : '禁用' }}</div>
                <div class="title o2">{{ item.label }}</div>
                <div class="props">
                  <div class="flex" style="justify-content: space-between;">
                    <div class="prop">
                      <div class="label">规则链ID</div>
                      <div class="value">{{ item.id }}</div>
                    </div>
                    <div class="prop">
                      <div class="label">规则状态</div>
                      <div class="value">{{ !item.disabled ? '启用' : '禁用' }}</div>
                    </div>
                  </div>
                  <div class="prop">
                    <div class="label">规则名称</div>
                    <div class="value">{{ item.label }}</div>
                  </div>
                </div>
                <div class="btns">
                  <PopConfirmButton
                    @confirm="handleDelete"
                    type="default"
                    placement="topRight"
                    title="是否确认删除？"
                  >
                    <img
                      src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAA8AAAAQCAYAAADJViUEAAAAAXNSR0IArs4c6QAAAi1JREFUOE+Nk89rE0EUx9/bzSZtJNSCBCvoxUhMstmdaYoIlnopglAs6iVC/wJB8SLFi3cVRPSmB0EE6an4owerIuqhIt3OjyRgq15EEHIr2tSYZp5kayTWlDi3N28+7/t+DUKXs1goxPubzYcEMI4Az9dte3IkCGpbn2I3uML5eTLmhKvUeIWxOUB8mhPi5rawYGxnFHGMjPEQ8QwB9AHAZwDYhwA/AHEGAORGs/nC13qtFQhLvn8MEM8hwCgiBgSwYAGsGGOqhFhHophlWUkiSgPiYSI6BACvbMu6jRXGZoHo0WAkMrOnS11bU1WetyOCeBIQT4c1/1b381Je69aDzrsSYxeBSOWVmg/hiu9PAWIxJ+VEy/7oeUl0nPr+IFj9VCgMUKMRS2ldDYUYm7OIHuSUur8Jc36cAC65QoyFNmM3iOirq9SVsu9PI+JQTsoLLV+Z89e2MVczSj1pK48S4i1XSt4TZkzYiGczQiyEsM7n81YkMusKkfoPeMUy5lRW6/Jmw1x3LzrOO1eIoV5wibFqnzHDB7T+EsLv0+nERjxedYXo7wVXOF+3a7XkweXlb3/Ws8zYz13GDO7Wek15XrLhOPWRIFhdLBQGnEYj5mtdrWSzUYpGv7tSRsMNa8+wzNhLQLzrCnFvu1mXOS8i0VR7pJ3wEQB4bBMVM0rNdwb4kErF6onEBBDdQcuazC0tvflLOew650dtgOtENPzPD0J8a4gu56V81vb9Ami8GYzeLnHJAAAAAElFTkSuQmCC"
                      alt="">
                  </PopConfirmButton>
                  <div class="btn" :onclick="handleView.bind(null, item)">
                    <img
                      src="data:image/png;base64,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"
                      alt=""></div>
                  <div class="btn" :onclick="handleEdit.bind(null, item)">
                    <img
                      src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACIAAAAeCAYAAABJ/8wUAAAAAXNSR0IArs4c6QAAAwpJREFUWEftV0Fu00AUfd8hXVQs0l1IinBPQHoCnBuEExCk1i1sak7Q9AQNCyRoKjWcoPQEgRMknKBGokkQmyBBBWkzD41Tp67r2A4JEgu8tP//8+bPm/+eBf/II4vCUdxkSRl4IkQFgBlRtwNBRwn2+q/FDX9fCJDiBh0a2E+5KfeCePy1IZ1g/NxAipusUnCkixKoI4t675V8CoPKP+MjYwQHQAXEQGWwHuzMXEDMKnPDJbT1UYwI50tDXiZ1pWhzn4BD4n2vIWU/fi4gfjfCRePAaPAXWZxSkGMWpt89D0jBZkWInaTd0IDbfSNP/bjA7pxeim74eYUtHkOTmugIMNDvPSB+wSQg+vv5ECuDpnjJhS0egagKUD07kLdp8oN5kWTVZEoqlLnEt7MA21c3uaMEdU3S3oG8SMoPdLJNoETC4R14t2cujuS3aRkKrahbMA3UfZuVEXBMwO0dyNpCyKqL3NtiSwgLgKsMlKOGlb/Y6jYtpbyrbiqFWv9Q9hYGJF+lKUtoyfU0fQeM232DAwKLY8BQRLPfuCb93EfjL6TBGFnsQlCN5YkeZEQ92ImFdSS4sAaELCxD8CAMSAHuzyFO/Bt3q2Npmf634+a6NYsE9x/IH3FE33+M8FAJcsECBjEA8fHzobyf95hij+ZKDI+0UiYslDjMkoBOBVKwWQOwqwtomdc2z1fKSVHCpMDyhhkxuADKYeeVBCB2juS3aRoKpzoojeEJqLd7PsT6tFkRByqyI75fCOtBXKGJ5ijUugENmakjOYe5u99R8pOUgZanCUOs9Zu3HXdU8YmqhixguPY0YHHGyO0GZDppZ4HjvJFXtOl5j6R8D0h+g5ZkxsTUjyfrxKDbkJWkAv734nOWeIk2iU6vIev++7zNXZGx6s7OEZuaqNozlPspZ8SEsESzG5L4JBDe5qOCCjZ1d/T1TTUf9LFkRmjreaMIq9+QD2kWD8ZEAtGW/9cS2ldmxxWg9mMZJ4P62DT7jybi8jkc/Qfg/R7M6F0TgXi8ue28YjcZ5bpm6cpvMNhsJB8wSzUAAAAASUVORK5CYII="
                      alt=""></div>
                </div>
              </div>
              <div class="product-img">
                <img
                  :src="item.ruleType == 'LAYOUT'? RULE_C3 : item.ruleType == 'FORWARD'? RULE_C2 : RULE_C1"
                  alt="" class="img" :onclick="handleGo.bind(null, item)">
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
import {Card, List, Spin, Typography} from 'ant-design-vue';
import {BasicForm, useForm} from '@/components/Form';
import {propTypes} from '@/utils/propTypes';
import {isFunction} from '@/utils/is';
import {grid, useSlider} from './data';
import {PopConfirmButton} from '@/components/Button';

import RULE_C1 from "@/assets/images/rule/rule_c1.png";
import RULE_C2 from "@/assets/images/rule/rule_c2.png";
import RULE_C3 from "@/assets/images/rule/rule_c3.png";
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
const {createConfirm, createMessage} = useMessage()
//暴露内部方法
const emit = defineEmits(['getMethod', 'delete', 'edit', 'view', 'go']);
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
      label: `规则名称`,
      component: 'Input',
    },
    {
      field: `model`,
      label: `规则型号`,
      component: 'Input',
    },
    {
      field: `manufacturerName`,
      label: `规则描述`,
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
    let list = [];
    res['data'].forEach((element) => {
      if (element.type == 'tab') {
        list.push(element);
      }
    });
    data.value = list;
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

async function handleGo(record: object) {
  emit('go', record);
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
.rulechain-card-list-wrapper {

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
        border: 2px solid #266CFBFF;

        .ant-btn-default {
          background: none;
          border: none;
          box-shadow: none;
        }

        .ant-btn {
          padding: 0;
          width: 28px;
        }

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
            left: -5px;
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
