<template>
  <BasicDrawer
    v-bind="$attrs"
    @register="registerDrawer"
    :title="`升级记录 - ${pkg.name || ''}${pkg.version ? ' v' + pkg.version : ''}`"
    width="1400"
    placement="right"
    :showFooter="false"
    destroy-on-close
  >
    <BasicTable @register="registerTable">
      <template #bodyCell="{ column, record }">
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
  </BasicDrawer>
</template>

<script lang="ts" setup>
import {reactive, ref} from 'vue';
import {BasicDrawer, useDrawerInner} from '@/components/Drawer';
import {BasicTable, useTable} from '@/components/Table';
import moment from 'moment';
import {fetchUpgradeRecords} from '/@/api/device/ota';
import {RECORD_PHASE_OPTIONS, RECORD_SUCCESS_OPTIONS, renderPhaseTag, renderTypeTag} from '../../Data';

defineOptions({name: 'OtaPackageRecords'});

//当前查看的版本包
const pkg = ref<any>({});
const pkgId = ref<number | null>(null);

const columns = [
  {
    title: '包类型',
    dataIndex: 'type',
    width: 70,
    customRender: ({text}) => renderTypeTag(text),
  },
  {
    title: '设备',
    dataIndex: 'deviceIdentification',
    width: 150,
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
    width: 150,
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
    width: 110,
    customRender: ({text}) => (text ? moment(text).format('YYYY-MM-DD HH:mm:ss') : '-'),
  },
];

const [registerDrawer] = useDrawerInner((record) => {
  pkg.value = record || {};
  pkgId.value = record?.id ?? null;
});

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
    actionColOptions: {span: 6},
    schemas: [
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
        field: 'success',
        label: '结果',
        component: 'Select',
        componentProps: {
          options: RECORD_SUCCESS_OPTIONS,
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
  beforeFetch(data) {
    data.pkgId = pkgId.value;
    return data;
  },
  rowKey: 'id',
});
</script>

<style lang="less" scoped>
.sub-text {
  color: #999;
  font-size: 12px;
}

:deep(.ant-form-item) {
  margin-bottom: 10px;
}

:deep(.iot-basic-table-form-container) {
  padding: 0;

  .ant-form {
    margin-bottom: 0;
    background: transparent;
    padding: 8px 8px 0;
  }
}
</style>
