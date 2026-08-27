<template>
  <div class="ota-records-pane">
    <BasicTable @register="registerTable">
      <template #bodyCell="{ column, record }">
        <template v-if="column.dataIndex === 'pkgName'">
          {{ record.pkgName || '-' }}
        </template>
        <template v-if="column.dataIndex === 'deviceIdentification'">
          {{ record.deviceIdentification }}
          <span v-if="record.deviceName && record.deviceName !== record.deviceIdentification"
                class="sub-text">（{{ record.deviceName }}）</span>
        </template>
        <template v-if="column.dataIndex === 'versionRange'">
          {{ record.fromVersion || '-' }} → <b>{{ record.toVersion }}</b>
        </template>
      </template>
    </BasicTable>
  </div>
</template>

<script lang="ts" setup>
import {BasicTable, useTable} from '@/components/Table';
import moment from 'moment';
import {fetchUpgradeRecords} from '/@/api/device/ota';
import {RECORD_PHASE_OPTIONS, RECORD_TYPE_OPTIONS, renderPhaseTag, renderTypeTag} from '../../Data';

defineOptions({name: 'OtaUpgradeRecords'});

const columns = [
  {
    title: '包类型',
    dataIndex: 'type',
    width: 70,
    customRender: ({text}) => renderTypeTag(text),
  },
  {
    title: '版本包',
    dataIndex: 'pkgName',
    width: 110,
  },
  {
    title: '设备',
    dataIndex: 'deviceIdentification',
    width: 140,
  },
  {
    title: '产品标识',
    dataIndex: 'productIdentification',
    width: 120,
    customRender: ({text}) => text || '-',
  },
  {
    title: '版本变化',
    dataIndex: 'versionRange',
    width: 150,
  },
  {
    title: '通道',
    dataIndex: 'channel',
    width: 60,
    customRender: ({text}) => (Number(text) === 1 ? '测试' : Number(text) === 2 ? '正式' : '-'),
  },
  {
    title: '阶段',
    dataIndex: 'phase',
    width: 90,
    customRender: ({text}) => renderPhaseTag(text),
  },
  {
    title: '进度',
    dataIndex: 'progress',
    width: 60,
    customRender: ({record}) => `${record.progress ?? 0}%`,
  },
  {
    title: '结果',
    dataIndex: 'success',
    width: 60,
    customRender: ({text}) => (Number(text) === 1 ? '成功' : Number(text) === 0 ? '失败' : '-'),
  },
  {
    title: '错误码/耗时',
    dataIndex: 'errorCode',
    width: 130,
    customRender: ({record}) => {
      const parts: string[] = [];
      if (record.errorCode) {
        parts.push(String(record.errorCode));
      }
      if (record.costMs != null) {
        parts.push(`${(record.costMs / 1000).toFixed(1)}s`);
      }
      return parts.join(' / ') || '-';
    },
  },
  {
    title: '升级时间',
    dataIndex: 'upgradeTime',
    width: 100,
    customRender: ({text}) => (text ? moment(text).format('MM-DD HH:mm:ss') : '-'),
  },
];

const [registerTable] = useTable({
  canResize: true,
  showIndexColumn: false,
  api: fetchUpgradeRecords,
  columns,
  useSearchForm: true,
  showTableSetting: false,
  pagination: true,
  formConfig: {
    labelWidth: 80,
    baseColProps: {span: 6},
    schemas: [
      {
        field: 'type',
        label: '包类型',
        component: 'Select',
        componentProps: {
          options: RECORD_TYPE_OPTIONS,
        },
        defaultValue: '',
      },
      {
        field: 'phase',
        label: '阶段',
        component: 'Select',
        componentProps: {
          options: RECORD_PHASE_OPTIONS,
        },
        defaultValue: '',
      },
      {
        field: 'deviceIdentification',
        label: '设备标识',
        component: 'Input',
      },
    ],
  },
  fetchSetting: {
    listField: 'data',
    totalField: 'total',
  },
  rowKey: 'id',
});
</script>

<style lang="less" scoped>
.ota-records-pane {
  padding: 8px 16px 16px;

  .sub-text {
    color: #999;
    font-size: 12px;
  }
}

:deep(.ant-form-item) {
  margin-bottom: 10px;
}

:deep(.iot-basic-table-form-container) {
  padding: 0;

  .ant-form {
    margin-bottom: 0;
    background: transparent;
    padding: 12px 12px 0;
  }
}
</style>
