<template>
  <div class="upload-warpper">
    <BasicTable @register="registerTable">
      <template #toolbar>
        <a-button type="primary" :loading="exportLoading" @click="handleClickExport()"
          >导出Excel</a-button
        >
      </template>
    </BasicTable>
  </div>
</template>
<script lang="ts" setup>
  import { saveAs } from 'file-saver';
  import { ref, defineProps } from 'vue';
  import { formatToDateTime } from '@/utils/dateUtil';
  import { BasicTable, useTable, BasicColumn, FormProps } from '@/components/Table';
  import { getIotData, postIotDataExport } from '@/api/device/entity-views';
  import { useMessage } from '@/hooks/web/useMessage';

  const { createMessage } = useMessage();
  const columns: BasicColumn[] = [
    {
      title: '数据',
      dataIndex: 'value',
      width: 150,
    },
    {
      title: '设备编号',
      dataIndex: 'name',
      width: 150,
    },
    {
      title: '采集日期',
      dataIndex: 'start',
      width: 150,
    },
    {
      title: '创建时间',
      dataIndex: 'time',
      width: 150,
    },
  ];
  const getFormConfig: Partial<FormProps> = {
    labelWidth: 70,
    baseColProps: { span: 9 },
    schemas: [
      {
        field: `name`,
        label: `设备编号`,
        // labelWidth: 90,
        component: 'Input',
        // colProps: {
        //   xl: 12,
        //   xxl: 8,
        // },
      },
      {
        field: '[createTimeFrom, createTimeTo]',
        label: '创建时间',
        // labelWidth: 70,
        component: 'RangePicker',
        // defaultValue: [new Date(new Date().getFullYear(), new Date().getMonth(), 1), new Date()],
        componentProps: {
          placeholder: ['开始时间', '结束时间'],
        },
        // colProps: {
        //   xl: 12,
        //   xxl: 10,
        // },
      },
    ],
  };

  defineProps({
    id: { type: String, default: '' },
    info: { type: Object },
    module: {
      type: String,
      default: 'RULE_CHAIN',
    },
  });

  const [registerTable, { getForm }] = useTable({
    // title: '数据上传',
    api: getIotData,
    beforeFetch: (data) => {
      // 接口请求前 参数处理
      //console.log('-------', data);
      const { name, page, pageSize, createTimeFrom, createTimeTo } = data;
      let params = {
        name: name ? name : '1#B_POWER_RUN',
        page,
        pageSize,
        createTimeFrom: createTimeFrom ? new Date(createTimeFrom) : '2023-05-17T03:10:05.888Z',
        createTimeTo: createTimeTo ? new Date(createTimeTo) : '2023-05-17T03:10:08.888Z',
      };
      return params;
    },
    afterFetch: (data) => {
      //请求之后对返回值进行处理
      //console.log('-------！', data);
      let list = data.map((res) => {
        res.start = formatToDateTime(res.start);
        res.time = formatToDateTime(res.time);
        return res;
      });
      return list;
    },
    columns: columns,
    formConfig: getFormConfig,
    useSearchForm: true,
    showIndexColumn: false,
    showTableSetting: false,
    fetchSetting: {
      listField: 'data',
      totalField: 'total',
    },
    tableSetting: { fullScreen: true },
  });

  const exportLoading = ref(false);
  async function handleClickExport() {
    const { createTimeFrom, createTimeTo } = getForm().getFieldsValue();
    let params = {
      // name: name ? name : '1#B_POWER_RUN',
      createTimeFrom: createTimeFrom ? new Date(createTimeFrom) : '2023-05-17T03:10:05.888Z',
      createTimeTo: createTimeTo ? new Date(createTimeTo) : '2023-05-17T03:10:08.888Z',
    };
    exportLoading.value = true;
    const { status, data, headers } = await postIotDataExport(params);
    exportLoading.value = false;
    if (status === 200) {
      saveAs(new Blob([data]), headers['content-disposition'].split('fileName=')[1]);
      createMessage.success('下载成功');
    } else {
      createMessage.error('下载失败');
    }
  }
</script>

<style lang="less" scoped>
  .ant-form-horizontal .ant-form-item-control {
    flex: none;
  }
  .upload-warpper {
    background-color: #FFFFFF;
  }
</style>
