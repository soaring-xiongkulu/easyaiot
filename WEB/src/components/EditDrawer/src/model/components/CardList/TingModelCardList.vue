<template>
  <div class="device-card-list-wrapper p-2">
    <div class="p-4 bg-white">
      <BasicForm @register="registerForm"/>
    </div>
    <div class="p-2 bg-white">
      <Spin :spinning="state.loading">
        <List
            :grid="{ gutter: 2, xs: 1, sm: 2, md: 6, lg: 6, xl: 6, xxl: 6 }"
            :data-source="data"
            :pagination="paginationProp"
        >
          <template #header>
            <div
                style="display: flex;align-items: center;justify-content: space-between;flex-direction: row;">
              <span style="padding-left: 7px;font-size: 16px;font-weight: 500;line-height: 24px;">设备运行状态</span>
              <div class="space-x-2">
                <slot name="header"></slot>
              </div>
            </div>
          </template>
          <template #renderItem="{ item }">
            <ListItem>
              <div class="properties">
                <div class="ant-card ant-card-bordered ant-card-hoverable" style="width: 100%">
                  <div class="ant-card-cover">
                    <div class="content">
                      <div class="name">
                        <div class="title">
                          <div class="title-txt">
                            {{ item.propertyName }}
                          </div>
                          <span role="img" aria-label="question-circle"
                                tabindex="-1"
                                class="anticon anticon-question-circle"><svg
                              focusable="false" class="" data-icon="question-circle" width="1em" height="1em"
                              fill="currentColor" aria-hidden="true" viewBox="64 64 896 896"><path
                              d="M512 64C264.6 64 64 264.6 64 512s200.6 448 448 448 448-200.6 448-448S759.4 64 512 64zm0 820c-205.4 0-372-166.6-372-372s166.6-372 372-372 372 166.6 372 372-166.6 372-372 372z"></path><path
                              d="M623.6 316.7C593.6 290.4 554 276 512 276s-81.6 14.5-111.6 40.7C369.2 344 352 380.7 352 420v7.6c0 4.4 3.6 8 8 8h48c4.4 0 8-3.6 8-8V420c0-44.1 43.1-80 96-80s96 35.9 96 80c0 31.1-22 59.6-56.1 72.7-21.2 8.1-39.2 22.3-52.1 40.9-13.1 19-19.9 41.8-19.9 64.9V620c0 4.4 3.6 8 8 8h48c4.4 0 8-3.6 8-8v-22.7a48.3 48.3 0 0130.9-44.8c59-22.7 97.1-74.7 97.1-132.5.1-39.3-17.1-76-48.3-103.3zM472 732a40 40 0 1080 0 40 40 0 10-80 0z"></path></svg></span>
                        </div>
                      </div>
                      <div class="value">
                        <span>{{ item.dataValue == null ? "null" : item.dataValue }} {{ item.unit }}</span>
                      </div>
                      <div class="time">
                        更新时间：{{ item.ts == 0 ? "" : item.ts }}
                      </div>
                    </div>
                  </div>
                  <ul class="ant-card-actions">
                    <li style="width: 50%;" :onclick="handleRefresh.bind(null, item)">
                      <span>
                        <span role="img" aria-label="redo" tabindex="-1"
                              class="anticon anticon-redo">
                          <svg focusable="false"
                               class=""
                               data-icon="redo"
                               width="1em"
                               height="1em"
                               fill="currentColor"
                               aria-hidden="true"
                               viewBox="64 64 896 896"><path
                              d="M758.2 839.1C851.8 765.9 912 651.9 912 523.9 912 303 733.5 124.3 512.6 124 291.4 123.7 112 302.8 112 523.9c0 125.2 57.5 236.9 147.6 310.2 3.5 2.8 8.6 2.2 11.4-1.3l39.4-50.5c2.7-3.4 2.1-8.3-1.2-11.1-8.1-6.6-15.9-13.7-23.4-21.2a318.64 318.64 0 01-68.6-101.7C200.4 609 192 567.1 192 523.9s8.4-85.1 25.1-124.5c16.1-38.1 39.2-72.3 68.6-101.7 29.4-29.4 63.6-52.5 101.7-68.6C426.9 212.4 468.8 204 512 204s85.1 8.4 124.5 25.1c38.1 16.1 72.3 39.2 101.7 68.6 29.4 29.4 52.5 63.6 68.6 101.7 16.7 39.4 25.1 81.3 25.1 124.5s-8.4 85.1-25.1 124.5a318.64 318.64 0 01-68.6 101.7c-9.3 9.3-19.1 18-29.3 26L668.2 724a8 8 0 00-14.1 3l-39.6 162.2c-1.2 5 2.6 9.9 7.7 9.9l167 .8c6.7 0 10.5-7.7 6.3-12.9l-37.3-47.9z"></path></svg></span></span>
                    </li>
                    <li style="width: 50%;" :onclick="handleView.bind(null, item)">
                      <span>
                        <span role="img" aria-label="unordered-list" tabindex="-1"
                              class="anticon anticon-unordered-list">
                          <svg
                              focusable="false" class="" data-icon="unordered-list" width="1em" height="1em"
                              fill="currentColor" aria-hidden="true" viewBox="64 64 896 896"><path
                              d="M912 192H328c-4.4 0-8 3.6-8 8v56c0 4.4 3.6 8 8 8h584c4.4 0 8-3.6 8-8v-56c0-4.4-3.6-8-8-8zm0 284H328c-4.4 0-8 3.6-8 8v56c0 4.4 3.6 8 8 8h584c4.4 0 8-3.6 8-8v-56c0-4.4-3.6-8-8-8zm0 284H328c-4.4 0-8 3.6-8 8v56c0 4.4 3.6 8 8 8h584c4.4 0 8-3.6 8-8v-56c0-4.4-3.6-8-8-8zM104 228a56 56 0 10112 0 56 56 0 10-112 0zm0 284a56 56 0 10112 0 56 56 0 10-112 0zm0 284a56 56 0 10112 0 56 56 0 10-112 0z"></path></svg></span></span>
                    </li>
                  </ul>
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
import {computed, onMounted, reactive, ref} from 'vue';
import {Card, List, Spin, Typography} from 'ant-design-vue';
import {BasicForm, useForm} from '@/components/Form';
import {propTypes} from '@/utils/propTypes';
import {isFunction} from '@/utils/is';
import {grid, useSlider} from './data';

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
const emit = defineEmits(['getMethod', 'refresh', 'view']);
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
      field: `name`,
      label: `健/名称`,
      component: 'Input',
    }
  ],
  labelWidth: 70,
  baseColProps: {span: 10},
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

async function handleRefresh(record: object) {
  emit('refresh', record);
}

async function handleView() {
  emit('view');
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
    padding: 0;
  }

  .properties {
    margin: 0 12px 12px 0;

    .ant-card-bordered {
      border: 1px solid #f0f0f0;
    }

    .ant-card-hoverable {
      cursor: pointer;
      transition: box-shadow .3s, border-color .3s;;
    }

    .ant-card:hover {
      border-color: transparent;
      box-shadow: 0 1px 2px -2px #00000029, 0 3px 6px #0000001f, 0 5px 12px 4px #00000017;
    }

    :deep(.ant-card-cover) {
      margin-top: -1px;
      margin-right: -1px;
      margin-left: -1px;

      .content {
        padding: 20px 20px 10px;

        .title {
          display: flex;
          align-items: center;
          justify-content: space-between;
        }

        .value {
          padding: 20px;
          font-size: 20px;
          font-weight: 700;
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
        }

        .time {
          color: #666;
        }
      }

      & > * {
        display: block;
        width: 100%;
      }
    }

    :deep(.ant-card-actions) {
      height: 50px;
      margin: 0;
      padding: 0;
      list-style: none;
      background: #fff;
      border-top: 1px solid #f0f0f0;

      & > li {
        float: left;
        margin: 12px 0;
        color: #00000073;
        text-align: center;
      }

      & > li:not(:last-child) {
        border-right: 1px solid #f0f0f0;
      }
    }
  }
}
</style>
