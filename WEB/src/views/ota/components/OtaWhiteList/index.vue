<template>
  <div class="ota-white-pane">
    <div class="pane-toolbar">
      <Select
        v-model:value="filterPkgId"
        class="pkg-filter"
        placeholder="按版本包过滤"
        allowClear
        show-search
        option-filter-prop="label"
        :options="pkgOptions"
        @change="handleFilterChange"
      />
      <Button type="primary" preIcon="ant-design:plus-outlined" @click="openAddModal">
        批量添加测试设备
      </Button>
    </div>
    <BasicTable @register="registerTable">
      <template #bodyCell="{ column, record }">
        <template v-if="column.dataIndex === 'deviceIdentification'">
          {{ record.deviceIdentification }}
          <span v-if="record.deviceName && record.deviceName !== record.deviceIdentification"
                class="sub-text">（{{ record.deviceName }}）</span>
        </template>
        <template v-if="column.dataIndex === 'status'">
          <Tag color="success">有效</Tag>
        </template>
        <template v-if="column.dataIndex === 'action'">
          <Popconfirm title="确认将该设备移出测试白名单？" @confirm="handleDelete(record)">
            <Button type="link" danger size="small">移出</Button>
          </Popconfirm>
        </template>
      </template>
    </BasicTable>

    <!-- 批量添加弹窗 -->
    <Modal
      v-model:visible="addModalVisible"
      title="批量添加测试白名单设备"
      width="640px"
      :confirm-loading="adding"
      @ok="handleAddOk"
      destroy-on-close
    >
      <Form :label-col="{style: {width: '110px'}}" :wrapper-col="{span: 18}">
        <FormItem label="版本包" required>
          <Select
            v-model:value="addForm.pkgId"
            placeholder="选择要测试的版本包"
            show-search
            option-filter-prop="label"
            :options="pkgOptions"
          />
        </FormItem>
        <FormItem label="测试设备" required>
          <Select
            v-model:value="addForm.devices"
            mode="tags"
            placeholder="输入设备标识搜索选择，或直接粘贴多个标识（回车确认）"
            :options="deviceOptions"
            @search="handleDeviceSearch"
            :filter-option="false"
            :token-separators="[',']"
          />
        </FormItem>
      </Form>
      <Alert message="加入白名单后，这些设备会通过测试通道优先检测到该包（即使还未正式发布）。" type="info" show-icon/>
    </Modal>
  </div>
</template>

<script lang="ts" setup>
import {onMounted, reactive, ref} from 'vue';
import {Alert, Form, FormItem, Modal, Popconfirm, Select, Tag} from 'ant-design-vue';
import {BasicTable, useTable} from '@/components/Table';
import {Button} from '@/components/Button';
import {useMessage} from '@/hooks/web/useMessage';
import moment from 'moment';
import {
  batchAddDeviceTestList,
  deleteOtaVerification,
  fetchPkgList,
  fetchWhiteList,
} from '/@/api/device/ota';
import {getDevicesList} from '@/api/device/devices';
import {TYPE_MAP} from '../../Data';

defineOptions({name: 'OtaWhiteList'});

const {createMessage} = useMessage();

const columns = [
  {
    title: '版本包',
    dataIndex: 'pkgName',
    width: 150,
  },
  {
    title: '设备标识',
    dataIndex: 'deviceIdentification',
    width: 160,
  },
  {
    title: '设备名称',
    dataIndex: 'deviceName',
    width: 120,
    customRender: ({text}) => text || '-',
  },
  {
    title: '状态',
    dataIndex: 'status',
    width: 70,
  },
  {
    title: '备注',
    dataIndex: 'remark',
    width: 100,
    customRender: ({text}) => text || '-',
  },
  {
    title: '添加时间',
    dataIndex: 'createdTime',
    width: 110,
    customRender: ({text}) => (text ? moment(text).format('YYYY-MM-DD HH:mm') : '-'),
  },
  {
    title: '操作',
    dataIndex: 'action',
    width: 80,
  },
];

//包过滤与选项
const filterPkgId = ref();
const pkgOptions = ref<any[]>([]);

async function loadPkgOptions() {
  try {
    const res = await fetchPkgList({pageNo: 1, pageSize: 500});
    pkgOptions.value = (res.data || []).map((p) => ({
      label: `${p.name}（v${p.version} · ${typeLabel(p.type)}）`,
      value: p.id,
    }));
  } catch (e) {
    console.error(e);
  }
}

function typeLabel(type) {
  const meta = TYPE_MAP[type] || TYPE_MAP[Number(type)];
  return meta ? meta.label : '-';
}

function handleFilterChange() {
  reload({page: 1});
}

const [registerTable, {reload}] = useTable({
  canResize: true,
  showIndexColumn: false,
  api: fetchWhiteList,
  columns,
  useSearchForm: false,
  showTableSetting: false,
  pagination: true,
  fetchSetting: {
    listField: 'data',
    totalField: 'total',
  },
  beforeFetch(data) {
    if (filterPkgId.value) {
      data.pkgId = filterPkgId.value;
    }
    return data;
  },
  rowKey: 'id',
});

//批量添加
const addModalVisible = ref(false);
const adding = ref(false);
const addForm = reactive({
  pkgId: undefined as number | undefined,
  devices: [] as string[],
});
const deviceOptions = ref<any[]>([]);

function openAddModal() {
  addForm.pkgId = undefined;
  addForm.devices = [];
  deviceOptions.value = [];
  addModalVisible.value = true;
}

async function handleDeviceSearch(keyword: string) {
  try {
    const res = await getDevicesList({
      deviceIdentification: keyword,
      pageNo: 1,
      pageSize: 20,
    });
    deviceOptions.value = (res.data || []).map((d) => ({
      label: d.deviceIdentification + (d.deviceName ? `（${d.deviceName}）` : ''),
      value: d.deviceIdentification,
    }));
  } catch (e) {
    console.error(e);
  }
}

async function handleAddOk() {
  if (!addForm.pkgId) {
    createMessage.warning('请选择版本包');
    return;
  }
  if (!addForm.devices.length) {
    createMessage.warning('请至少添加一个设备');
    return;
  }
  adding.value = true;
  try {
    await batchAddDeviceTestList({
      pkgId: addForm.pkgId,
      deviceIdentificationList: addForm.devices.map((d) => String(d).trim()).filter(Boolean),
    });
    createMessage.success('添加成功');
    addModalVisible.value = false;
    //若当前过滤器不是该包，切换过去方便查看结果
    if (!filterPkgId.value || filterPkgId.value !== addForm.pkgId) {
      filterPkgId.value = addForm.pkgId;
    }
    await reload({page: 1});
  } catch (e) {
    console.error(e);
  } finally {
    adding.value = false;
  }
}

async function handleDelete(record) {
  try {
    await deleteOtaVerification([record.id]);
    createMessage.success('移出成功');
    await reload();
  } catch (e) {
    console.error(e);
    createMessage.error('移出失败');
  }
}

onMounted(() => {
  loadPkgOptions();
});
</script>

<style lang="less" scoped>
.ota-white-pane {
  padding: 8px 16px 16px;

  .pane-toolbar {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 8px;

    .pkg-filter {
      width: 280px;
    }
  }

  .sub-text {
    color: #999;
    font-size: 12px;
  }
}

:deep(.ant-table-wrapper) {
  border-radius: 0;
  background: #fff;
}
</style>
