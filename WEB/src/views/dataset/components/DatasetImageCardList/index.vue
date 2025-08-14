<template>
  <div class="device-card-list-wrapper p-2">
    <div class="p-4 bg-white" style="margin-bottom: 10px">
      <BasicForm @register="registerForm" @reset="handleSubmit"/>
    </div>
    <div class="p-2 bg-white">
      <Spin :spinning="state.loading">
        <List
          :grid="{ gutter: 2, xs: 1, sm: 4, md: 6, lg: 6, xl: 8, xxl: 8 }"
          :data-source="data"
          :pagination="paginationProp"
        >
          <template #header>
            <div
              style="display: flex;align-items: center;justify-content: space-between;flex-direction: row;">
              <span style="padding-left: 7px;font-size: 16px;font-weight: 500;line-height: 24px;">图片数据集列表</span>
              <div class="space-x-2">
                <slot name="header"></slot>
              </div>
            </div>
          </template>
          <template #renderItem="{ item }">
            <ListItem style="padding: 0;
                background: #FFFFFF;
                box-shadow: 0px 0px 4px 0px rgba(24, 24, 24, 0.1);
                height: 100%;
                transition: all 0.3s;
            }">
              <div class="list5-box imgh">
                <a class="img-box" :title="item['path']"
                   :onclick="handleView.bind(null, item)">
                  <img
                    :src="item['path']"
                    alt="" style="height: 188px; width: 100%;">
                </a>
                <div class="list5-cont" style="padding: 15px">
                  <div>
                    <!-- 标注状态标签 - 使用更加协调的颜色 -->
                    <Tag :color="item['completed'] == 1 ? '#52c41a' : '#f5222d'">
                      {{ item['completed'] == 1 ? '已标注' : '待标注' }}
                    </Tag>

                    <!-- 数据集类型标签 - 使用区分度更高的颜色 -->
                    <Tag color="#096dd9" v-if="item['isTrain'] == 1">训练集</Tag>
                    <Tag color="#fa8c16" v-if="item['isValidation'] == 1">验证集</Tag>
                    <Tag color="#722ed1" v-if="item['isTest'] == 1">测试集</Tag>

                    <!-- 辅助信息标签 - 使用更柔和的色调 -->
                    <Tag color="#13c2c2">{{
                        dateFormat(item['createTime'], 'yyyy-MM-dd hh:mm:ss')
                      }}
                    </Tag>
                    <Tag color="#597ef7">{{
                        item['name']
                      }}
                    </Tag>
                  </div>
                  <div class="btns" style="padding-top: 5px;">
                    <Popconfirm
                      title="是否确认删除？"
                      ok-text="是"
                      cancel-text="否"
                      @confirm="handleDelete(item)"
                    >
                      <div class="btn">
                        <img
                          src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAA8AAAAQCAYAAADJViUEAAAAAXNSR0IArs4c6QAAAi1JREFUOE+Nk89rE0EUx9/bzSZtJNSCBCvoxUhMstmdaYoIlnopglAs6iVC/wJB8SLFi3cVRPSmB0EE6an4owerIuqhIt3OjyRgq15EEHIr2tSYZp5kayTWlDi3N28+7/t+DUKXs1goxPubzYcEMI4Az9dte3IkCGpbn2I3uML5eTLmhKvUeIWxOUB8mhPi5rawYGxnFHGMjPEQ8QwB9AHAZwDYhwA/AHEGAORGs/nC13qtFQhLvn8MEM8hwCgiBgSwYAGsGGOqhFhHophlWUkiSgPiYSI6BACvbMu6jRXGZoHo0WAkMrOnS11bU1WetyOCeBIQT4c1/1b381Je69aDzrsSYxeBSOWVmg/hiu9PAWIxJ+VEy/7oeUl0nPr+IFj9VCgMUKMRS2ldDYUYm7OIHuSUur8Jc36cAC65QoyFNmM3iOirq9SVsu9PI+JQTsoLLV+Z89e2MVczSj1pK48S4i1XSt4TZkzYiGczQiyEsM7n81YkMusKkfoPeMUy5lRW6/Jmw1x3LzrOO1eIoV5wibFqnzHDB7T+EsLv0+nERjxedYXo7wVXOF+3a7XkweXlb3/Ws8zYz13GDO7Wek15XrLhOPWRIFhdLBQGnEYj5mtdrWSzUYpGv7tSRsMNa8+wzNhLQLzrCnFvu1mXOS8i0VR7pJ3wEQB4bBMVM0rNdwb4kErF6onEBBDdQcuazC0tvflLOew650dtgOtENPzPD0J8a4gu56V81vb9Ami8GYzeLnHJAAAAAElFTkSuQmCC"
                          alt="">
                      </div>
                    </Popconfirm>
                    <div class="btn" :onclick="handleCopy.bind(null, item)">
                      <img
                        src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACAAAAAgCAYAAABzenr0AAAAAXNSR0IArs4c6QAABDpJREFUWEetV0FyWkcQff0VK1VKFningFOFbgAnAJ3A+ATGVQHJ2ZicAHQCS7sEVGVyAqETgE4gfAKziABXFmZjWQViXqpHf74+X4MEOOyomd/zpvu91z2CDX6pGlM716gBeA0gG4boQ9AXojcPcDH+UwarhJZVNsX3vDhkkXOcUZB64tsBBD0Q59c76E2OZeLbvxaATIU5Ci41EIkegca4JRf6X9cMUBBBEUQRDwF2BOhcNeXvOJC1AKSr/KQpNwaN8akcPZaB3bcsyC1yCFASBRT+LPAtvHElWhnAr1WW5sAZgcGoKXvrlG63zCyeoSiCutxxZnA9RX7SlsnKANIH/ACiTKI2asnJOgDcXgUi2+haEAaN4akcrQQgZL3WPmum2Bu3V2O4D+TuIYuBQRfE5HqGvaUAlO3G2LQVGNZwk/T7QPxywK7ywhjsLwDYPWRWiHeBQdkrM6I9bMmbTdIf/8aVU4ByBCDzG2sM8D5iK6BG0hFBT4gGgdzcoPT5VM7/BwBnIEoazwJIV9kAULeBibYB2k7f2TJT02180aXrKZ4rc78bQCjnGZEXTXtgoPqGAcrjhFGEXOiqfkct2f/ew6PziMmwJc/F1UNv7qtvpsr3BGoEjkdN+SOS1CGzW3NcUjCgoLc1x/k/p9J7CmCmQuXXBwKdUVNeiXM3Tce/LeknA2SqvNT6G6LoyuKsF0A3SVZtRmq5BC6uPPGSfqIAqAGHTXkgyXj9fev6nbXcuSWT2m0ufgFf2ZIXlkyFX/QWPoKtW/9UmamdH1GAQYmComYjXtbM78zxFprRyM4lSrHB/jhRwxcVvjOCY2/9iTpo2+1HX6p9XHDx4nxTAJZkzpsXDKNKlaZKtDFs3ne/KND9Ztv7ZwYnPh65bZkDqpqKcbVJ1OU8MnOMhaA9/GvRAXcrLAeCl0rQsMPpjNAftSS/TAmu3PF+IhHRwuYQN5r4mtlCftmY5YaRYIaLq/ZDJSmgGJ8WQFrmx5tDkgfpKs8AlAj0v02xv6kTRvJL+ImzYlvrJNmszOI9HBgI0Pi6g/NlM96SFqxu2/W1cwvA9ehlNUyAsGc8ZTgJMrssWveLr1kAWuvZM3xa5geR/VZYlgCv4zNeuKads68O6GSpQ8zPN8gZYztsTgcQM0M+OcxE7ud4oD06Obkm0+pmvAAoWMO5fxt4BaDGE0zxykfQCECkbY/kVmgwuTmQU1mGDxVryUpcGnRubnGyjLwRgHib1FltY7aHs4XemlPsPzU/LjSgdcqQzIp9MRF1Nz/OidrnFabnxZnwzt10/J48Zjx6uJLsp68oIYiaz91TjZjMgcYqh1s1JW/ijEcDkTjiD+ioA2YPmZ0a6NOsEKpgsfVqyg3aj9XbxyXvDDDbRt02qMd+ChDQAaYTLBk+niKvNwPuo/QBX+pLKHpougMFfRKdmxk+bkrUOLD/AJnzscretOw/AAAAAElFTkSuQmCC"
                        alt="复制">
                    </div>
                    <div class="btn" :onclick="handleEdit.bind(null, item)">
                      <img
                        src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACIAAAAeCAYAAABJ/8wUAAAAAXNSR0IArs4c6QAAAwpJREFUWEftV0Fu00AUfd8hXVQs0l1IinBPQHoCnBuEExCk1i1sak7Q9AQNCyRoKjWcoPQEgRMknKBGokkQmyBBBWkzD41Tp67r2A4JEgu8tP//8+bPm/+eBf/II4vCUdxkSRl4IkQFgBlRtwNBRwn2+q/FDX9fCJDiBh0a2E+5KfeCePy1IZ1g/NxAipusUnCkixKoI4t675V8CoPKP+MjYwQHQAXEQGWwHuzMXEDMKnPDJbT1UYwI50tDXiZ1pWhzn4BD4n2vIWU/fi4gfjfCRePAaPAXWZxSkGMWpt89D0jBZkWInaTd0IDbfSNP/bjA7pxeim74eYUtHkOTmugIMNDvPSB+wSQg+vv5ECuDpnjJhS0egagKUD07kLdp8oN5kWTVZEoqlLnEt7MA21c3uaMEdU3S3oG8SMoPdLJNoETC4R14t2cujuS3aRkKrahbMA3UfZuVEXBMwO0dyNpCyKqL3NtiSwgLgKsMlKOGlb/Y6jYtpbyrbiqFWv9Q9hYGJF+lKUtoyfU0fQeM232DAwKLY8BQRLPfuCb93EfjL6TBGFnsQlCN5YkeZEQ92ImFdSS4sAaELCxD8CAMSAHuzyFO/Bt3q2Npmf634+a6NYsE9x/IH3FE33+M8FAJcsECBjEA8fHzobyf95hij+ZKDI+0UiYslDjMkoBOBVKwWQOwqwtomdc2z1fKSVHCpMDyhhkxuADKYeeVBCB2juS3aRoKpzoojeEJqLd7PsT6tFkRByqyI75fCOtBXKGJ5ijUugENmakjOYe5u99R8pOUgZanCUOs9Zu3HXdU8YmqhixguPY0YHHGyO0GZDppZ4HjvJFXtOl5j6R8D0h+g5ZkxsTUjyfrxKDbkJWkAv734nOWeIk2iU6vIev++7zNXZGx6s7OEZuaqNozlPspZ8SEsESzG5L4JBDe5qOCCjZ1d/T1TTUf9LFkRmjreaMIq9+QD2kWD8ZEAtGW/9cS2ldmxxWg9mMZJ4P62DT7jybi8jkc/Qfg/R7M6F0TgXi8ue28YjcZ5bpm6cpvMNhsJB8wSzUAAAAASUVORK5CYII="
                        alt="编辑">
                    </div>
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
import {onMounted, reactive, ref} from 'vue';
import {List, Popconfirm, Spin, Tag} from 'ant-design-vue';
import {BasicForm, useForm} from '@/components/Form';
import {propTypes} from '@/utils/propTypes';
import {isFunction} from '@/utils/is';
import {useMessage} from "@/hooks/web/useMessage";
import {dateFormat} from "@/utils/dateUtil";
import {useRoute} from "vue-router";

const route = useRoute()

defineOptions({name: 'DatasetImageCardList'})

const {createMessage} = useMessage()

const ListItem = List.Item;
// 组件接收参数
const props = defineProps({
  // 请求API的参数
  params: propTypes.object.def({}),
  //api
  api: propTypes.func,
});
//暴露内部方法
const emit = defineEmits(['getMethod', 'delete', 'edit', 'view']);

const data = ref([]);
const state = reactive({
  loading: true,
});

//表单
const [registerForm, {validate}] = useForm({
  schemas: [
    {
      field: `name`,
      label: `图片名称`,
      component: 'Input',
    },
    // 新增搜索条件
    {
      field: `usageType`,
      label: `数据集类型`,
      component: 'Select',
      componentProps: {
        options: [
          {label: '全部', value: 0},
          {label: '训练集', value: 1},
          {label: '验证集', value: 2},
          {label: '测试集', value: 3},
        ],
      },
    },
    {
      field: `completed`,
      label: `标注状态`,
      component: 'Select',
      componentProps: {
        options: [
          {label: '全部', value: -1},
          {label: '待标注', value: 0},
          {label: '已标注', value: 1},
        ],
      },
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

  // 转换参数：将usageType转换为后端需要的字段
  const transformedParams = {...p};

  transformedParams['datasetId'] = route.params['id']
  if (transformedParams['usageType'] !== undefined) {
    transformedParams['isTrain'] = transformedParams['usageType'] === 1 ? 1 : undefined;
    transformedParams['isValidation'] = transformedParams['usageType'] === 2 ? 1 : undefined;
    transformedParams['isTest'] = transformedParams['usageType'] === 3 ? 1 : undefined;
    delete transformedParams['usageType'];
  }

  if (api && isFunction(api)) {
    const res = await api({
      ...params,
      pageNo: page.value,
      pageSize: pageSize.value,
      ...transformedParams  // 使用转换后的参数
    });
    data.value = res.list;
    total.value = res.total;
    hideLoading();
  }
}

function hideLoading() {
  state.loading = false;
}

//分页相关
const page = ref(1);
const pageSize = ref(16);
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

async function handleDelete(record: object) {
  emit('delete', record);
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
</script>

<style lang="less" scoped>
img {
  border: none;
  border: 0;
  max-width: 100%;
  vertical-align: top;
  object-fit: fill;
}

.lw-w-3 {
  width: 20%;
}

.device-card-list-wrapper {
  :deep(.ant-list-header) {
    border: 0;
  }
}

.device-card-list-wrapper .list5 {
  padding-top: var(--gap);

  .img-box {
    --imgpt: 56.1403%;
    display: block;
  }

  .more-box-c {
    --size: var(--jtw);
    transform: translate(-25%, 0);
    margin-left: 1em;
    flex-shrink: 0;
    opacity: 0;
    transition: all 0.3s;
  }

  .tags {
    color: #999999;
  }

  .tags-more {
    --jtw: 30px;
    --lh: 1.57145em;
    margin-top: 4px;
    font-size: var(--fs14);
    line-height: var(--lh);
  }


  .list5-cont {
    position: relative;
    padding: var(--gap) var(--gap) calc(var(--gap) * 0.833);

    .icon-box {
      transform: translate(0, -50%);
      position: absolute;
      top: 0;
      right: var(--gap);

      img {
        border: none;
        border: 0;
        max-width: 100%;
        vertical-align: top;
        object-fit: fill;
      }
    }

    .list5-title {
      font-size: var(--fs22);
      font-weight: 600;
      line-height: 1.36em;
      color: #181818;
    }
  }

  .list5-li {
    padding: calc(var(--gap) * 0.5);
  }
}

:deep(.ant-list-item) {


  .list5-box {
    background: #FFFFFF;
    box-shadow: 0px 0px 4px 0px rgba(24, 24, 24, 0.1);
    height: 100%;
    transition: all 0.3s;

    .btns {
      display: flex;
      margin-top: 20px;
      width: 140px;
      height: 28px;
      border-radius: 45px;
      justify-content: space-around;
      padding: 0 10px;
      align-items: center;
      border: 2px solid #266CFBFF;

      .btn {
        width: 28px;
        height: 22px;
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

        svg {
          width: 15px;
          height: 15px;
          cursor: pointer;
          margin-top: 4px;
        }
      }
    }

    .icon-span-box {
      display: flex;
      position: absolute;
      left: 0;
      bottom: 0;
      font-size: var(--fs12);
      line-height: 1.83334em;
      font-weight: 600;
      color: #FFFFFF;

      .hot {
        background-color: #d80000;
      }
    }

    .img-box {
      --imgpt: 56.1403%;
      display: block;

      img {
        display: inline-block;
        width: 100%;
        height: 100%;
        transform: scale(1);
        -webkit-transform: scale(1);
        -moz-transform: scale(1);
        -ms-transform: scale(1);
        -o-transform: scale(1);
        transition: all 0.3s;
        -webkit-transition: all 0.3s;
        -moz-transition: all 0.3s;
        -ms-transition: all 0.3s;
        -o-transition: all 0.3s;
      }
    }
  }
}
</style>
