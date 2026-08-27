<template>
  <div class="ota-pane">
    <BasicTable v-if="isTableMode" @register="registerTable">
      <template #toolbar>
        <Button type="primary" preIcon="ant-design:plus-outlined" @click="openAddDrawer">
          批量添加测试设备
        </Button>
        <Button type="default" @click="toggleView">
          <Icon :icon="isTableMode ? 'ant-design:appstore-outlined' : 'ant-design:bars-outlined'" :size="14"/>
          {{ isTableMode ? '卡片视图' : '切换视图' }}
        </Button>
      </template>
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
    <div v-else class="card-wrap">
      <OtaWhiteListCards :api="fetchWhiteList" @remove="handleDelete" @getMethod="onCardMethod">
        <template #header>
          <Button type="primary" preIcon="ant-design:plus-outlined" @click="openAddDrawer">
            批量添加测试设备
          </Button>
          <Button type="default" @click="toggleView">
            <Icon :icon="isTableMode ? 'ant-design:appstore-outlined' : 'ant-design:bars-outlined'" :size="14"/>
            {{ isTableMode ? '卡片视图' : '切换视图' }}
          </Button>
        </template>
      </OtaWhiteListCards>
    </div>

    <!-- 批量添加抽屉 -->
    <BasicDrawer
      @register="registerAddDrawer"
      title="批量添加测试白名单设备"
      width="1400"
      placement="right"
      :showFooter="true"
      :showCancelBtn="false"
      :showOkBtn="false"
      destroy-on-close
    >
      <template #footer>
        <div class="footer-buttons">
          <Button @click="closeAddDrawer">取消</Button>
          <Button type="primary" :loading="adding" @click="handleAddOk">添加</Button>
        </div>
      </template>
      <div class="add-drawer-content">
        <Divider orientation="left">选择版本包与设备</Divider>
        <Form :label-col="{style: {width: '150px'}}" :wrapper-col="{span: 21}">
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
      </div>
    </BasicDrawer>
  </div>
</template>

<script lang="ts" setup>
import {nextTick, onMounted, reactive, ref} from 'vue';
import {Alert, Divider, Form, FormItem, Popconfirm, Select, Tag} from 'ant-design-vue';
import {BasicDrawer, useDrawer} from '@/components/Drawer';
import {BasicTable, useTable} from '@/components/Table';
import {Button} from '@/components/Button';
import {Icon} from '@/components/Icon';
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
import OtaWhiteListCards from '../OtaWhiteListCards/index.vue';

defineOptions({name: 'OtaWhiteList'});

const {createMessage} = useMessage();

const isTableMode = ref(false);

function toggleView() {
  isTableMode.value = !isTableMode.value;
  //表格首次挂载后重新同步搜索表单的版本包选项
  if (isTableMode.value) {
    nextTick(() => loadPkgOptions());
  }
}

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

//版本包下拉选项（表格搜索与批量添加共用）
const pkgOptions = ref<any[]>([]);

async function loadPkgOptions() {
  try {
    const res = await fetchPkgList({pageNo: 1, pageSize: 500});
    pkgOptions.value = (res.data || []).map((p) => {
      const meta = TYPE_MAP[p.type] || TYPE_MAP[Number(p.type)];
      return {label: `${p.name}（v${p.version} · ${meta ? meta.label : '-'}）`, value: p.id};
    });
    //卡片模式下表格未挂载，同步搜索表单选项会失败，跳过即可
    try {
      getForm().updateSchema({
        field: 'pkgId',
        componentProps: {options: pkgOptions.value},
      });
    } catch (e) {
      // ignore
    }
  } catch (e) {
    console.error(e);
  }
}

const [registerTable, {reload, getForm}] = useTable({
  canResize: true,
  showIndexColumn: false,
  title: '测试白名单',
  api: fetchWhiteList,
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
        field: 'pkgId',
        label: '版本包',
        component: 'Select',
        componentProps: {
          placeholder: '全部版本包',
          allowClear: true,
          showSearch: true,
          optionFilterProp: 'label',
          options: [],
        },
      },
    ],
  },
  fetchSetting: {
    listField: 'data',
    totalField: 'total',
  },
  rowKey: 'id',
});

let cardListReload = () => {
};

function onCardMethod(m: any) {
  cardListReload = m;
}

//批量添加抽屉
const [registerAddDrawer, {openDrawer: openAddModal, closeDrawer: closeAddDrawer}] = useDrawer();
const adding = ref(false);
const addForm = reactive({
  pkgId: undefined as number | undefined,
  devices: [] as string[],
});
const deviceOptions = ref<any[]>([]);

function openAddDrawer() {
  addForm.pkgId = undefined;
  addForm.devices = [];
  deviceOptions.value = [];
  openAddModal(true);
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
    closeAddDrawer();
    await reload({page: 1});
    cardListReload();
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
    cardListReload();
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
.ota-pane {
  display: flex;
  flex-direction: column;
  min-height: calc(100vh - 200px);
  background: #fff;

  .card-wrap {
    flex: 1;
    display: flex;
    flex-direction: column;
    min-height: 0;
  }

  .sub-text {
    color: #999;
    font-size: 12px;
  }
}

.add-drawer-content {
  padding: 8px 16px 0;
}

.footer-buttons {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

:deep(.ant-form-item) {
  margin-bottom: 10px;
}

:deep(.iot-basic-table-form-container) {
  padding: 0;
  background: #fff;

  .ant-form {
    margin-bottom: 0;
    border-radius: 0;
    background: transparent;
    padding: 16px 16px 0;
  }
}

:deep(.ant-table-wrapper) {
  border-radius: 0;
  background: #fff;
  padding: 8px 16px 16px;
}
</style>
