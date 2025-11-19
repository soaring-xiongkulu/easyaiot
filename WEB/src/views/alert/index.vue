<template>
  <div>
    <BasicTable v-if="state.isTableMode" @register="registerTable">
      <template #toolbar>
        <div style="display: flex; align-items: center; gap: 8px;">
          <a-button type="default" @click="handleClickSwap"
                    preIcon="ant-design:swap-outlined">切换视图
          </a-button>
        </div>
      </template>
      <template #bodyCell="{ column, record }">
        <template v-if="column.key === 'device_id'">
          <span style="cursor: pointer" @click="handleCopy(record['device_id'])"><Icon
            icon="tdesign:copy-filled" color="#4287FCFF"/> {{ record['device_id'] }}</span>
        </template>
        <template v-if="column.key === 'device_name'">
          <span style="cursor: pointer" @click="handleCopy(record['device_name'])"><Icon
            icon="tdesign:copy-filled" color="#4287FCFF"/> {{ record['device_name'] }}</span>
        </template>
        <template v-if="column.dataIndex === 'action'">
          <TableAction
            :actions="[
              {
                icon: 'ion:image-sharp',
                tooltip: {
                  title: '查看告警图片',
                  placement: 'top',
                },
                onClick: handleViewImage.bind(null, record),
              },
              {
                icon: 'icon-park-outline:video',
                tooltip: {
                  title: '查看告警录像',
                  placement: 'top',
                },
                onClick: handleViewVideo.bind(null, record),
              },
            ]"
          />
        </template>
      </template>
    </BasicTable>
    <div v-else>
      <AlertCards
        :api="queryAlarmList"
        :params="params"
        @getMethod="getMethod"
        @viewImage="handleCardViewImage"
        @viewVideo="handleCardViewVideo"
      >
        <template #header>
          <div style="display: flex; align-items: center; gap: 8px;">
            <a-button type="default" @click="handleClickSwap"
                      preIcon="ant-design:swap-outlined">切换视图
            </a-button>
          </div>
        </template>
      </AlertCards>
    </div>
  </div>
</template>
<script lang="ts" setup name="noticeSetting">
import {reactive} from 'vue';
import {BasicTable, TableAction, useTable} from '@/components/Table';
import {useMessage} from '@/hooks/web/useMessage';
import {getBasicColumns, getFormConfig} from "./Data";
import {useRouter} from "vue-router";
import {getAlertImage, getAlertRecord, queryAlarmList} from "@/api/device/calculate";
import {Icon} from "@/components/Icon";
import AlertCards from "@/views/alert/components/AlertCards/index.vue";

const router = useRouter();

defineOptions({name: 'Alarm'})

const state = reactive({
  isTableMode: false,
  activeKey: '1',
});

// 请求api时附带参数
const params = {};

let cardListReload = () => {
};

// 获取内部fetch方法;
function getMethod(m: any) {
  cardListReload = m;
}

// 切换视图
function handleClickSwap() {
  state.isTableMode = !state.isTableMode;
}

// 表格刷新
function handleSuccess() {
  reload({
    page: 0,
  });
  cardListReload();
}

// 卡片视图事件处理
function handleCardViewImage(record) {
  handleViewImage(record);
}

function handleCardViewVideo(record) {
  handleViewVideo(record);
}

const {createMessage} = useMessage();
const [
  registerTable,
  {
    // setLoading,
    // setColumns,
    // getColumns,
    // getDataSource,
    // getRawDataSource,
    reload,
    // getPaginationRef,
    // setPagination,
    // getSelectRows,
    // getSelectRowKeys,
    // setSelectedRowKeys,
    // clearSelectedRowKeys,
  },
] = useTable({
  canResize: true,
  showIndexColumn: false,
  title: '告警事件列表',
  api: queryAlarmList,
  columns: getBasicColumns(),
  useSearchForm: true,
  showTableSetting: false,
  formConfig: getFormConfig(),
  fetchSetting: {
    listField: 'alert_list',
    totalField: 'total',
  },
  beforeFetch: (params) => {
    // 处理时间范围参数
    // RangePicker 字段名为 [begin_datetime, end_datetime] 时，返回的可能是数组格式
    const timeRangeKey = '[begin_datetime, end_datetime]';
    if (params[timeRangeKey] && Array.isArray(params[timeRangeKey])) {
      const [begin, end] = params[timeRangeKey];
      params.begin_datetime = begin;
      params.end_datetime = end;
      delete params[timeRangeKey];
    }
    return params;
  },
  rowKey: 'id',
});

// 封装下载工具函数
const downloadImage = (data, fileName = 'image.png') => {
  // 二进制数据处理
  if (data instanceof ArrayBuffer || data instanceof Uint8Array) {
    const blob = new Blob([data], {type: 'image/png'}) // 可指定具体MIME类型
    return downloadImage(blob, fileName)
  }

  // 处理Blob数据
  if (data instanceof Blob) {
    const url = URL.createObjectURL(data)
    const link = document.createElement('a')
    link.href = url
    link.download = fileName
    document.body.appendChild(link)
    link.click()
    URL.revokeObjectURL(url)
    document.body.removeChild(link)
    return
  }

  // 处理Base64数据
  if (data.startsWith('data:image')) {
    alert(333)
    const arr = data.split(',')
    const mime = arr[0].match(/:(.*?);/)[1]
    const bstr = atob(arr[1])
    let n = bstr.length
    const u8arr = new Uint8Array(n)
    while (n--) u8arr[n] = bstr.charCodeAt(n)
    downloadImage(new Blob([u8arr], {type: mime}), fileName)
  }
}

const handleViewImage = async (record) => {
  try {
    if (record['image_path'] == null) {
      createMessage.warn('告警图片不存在');
      return;
    }
    const blob = await getAlertImage(record['image_path']);
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', record['image_path'].split('/').pop()); // 后端未指定文件名时前端定义
    document.body.appendChild(link);
    link.click();
    window.URL.revokeObjectURL(url); // 清理内存
    createMessage.success('获取告警图片成功');
    handleSuccess();
  } catch (error) {
    console.error(error)
    createMessage.error('获取告警图片失败');
    console.log('handleViewImage', error);
  }
};

const handleViewVideo = async (record) => {
  try {
    if (record['record_path'] == null) {
      createMessage.warn('告警录像不存在');
      return;
    }
    const blob = await getAlertRecord(record['record_path']);
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', record['record_path'].split('/').pop()); // 后端未指定文件名时前端定义
    document.body.appendChild(link);
    link.click();
    window.URL.revokeObjectURL(url); // 清理内存
    createMessage.success('获取告警录像成功');
    handleSuccess();
  } catch (error) {
    console.error(error)
    createMessage.error('获取告警录像失败');
    console.log('handleViewVideo', error);
  }
};

async function handleCopy(record: object) {
  if (navigator.clipboard) {
    await navigator.clipboard.writeText(record);
  } else {
    // 降级方案
    const textarea = document.createElement('textarea');
    textarea.value = record;
    document.body.appendChild(textarea);
    textarea.select();
    document.execCommand('copy');
    document.body.removeChild(textarea);
  }
  createMessage.success('复制成功');
}
</script>
