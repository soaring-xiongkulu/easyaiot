<template>
  <div class="ota-versions-pane">
    <div class="pane-toolbar">
      <Select
        v-model:value="filterProduct"
        class="product-filter"
        placeholder="按产品过滤"
        allowClear
        show-search
        option-filter-prop="label"
        :options="productOptions"
        @change="handleFilterChange"
      />
      <Button type="primary" preIcon="ant-design:plus-outlined" @click="openEditDrawer(null)">
        新增版本档案
      </Button>
    </div>
    <BasicTable @register="registerTable">
      <template #bodyCell="{ column, record }">
        <template v-if="column.dataIndex === 'pkgs'">
          <div class="pkg-cell">
            <div><span class="pkg-label">软件包：</span>{{ record.appPkgName || '-' }}</div>
            <div><span class="pkg-label">固件包：</span>{{ record.osPkgName || '-' }}</div>
          </div>
        </template>
        <template v-if="column.dataIndex === 'upgradeMode'">
          {{ Number(record.upgradeMode) === 1 ? '强制升级' : '非强制升级' }}
        </template>
        <template v-if="column.dataIndex === 'action'">
          <Button type="link" size="small" @click="openEditDrawer(record)">编辑</Button>
          <Popconfirm title="确认删除该版本档案？" @confirm="handleDelete(record)">
            <Button type="link" danger size="small">删除</Button>
          </Popconfirm>
        </template>
      </template>
    </BasicTable>

    <!-- 新增/编辑抽屉 -->
    <BasicDrawer
      v-bind="$attrs"
      @register="registerDrawer"
      :title="editRecord ? '编辑版本档案' : '新增版本档案'"
      width="640"
      :showFooter="true"
      destroy-on-close
    >
      <Form :label-col="{style: {width: '130px'}}" :wrapper-col="{span: 18}">
        <FormItem label="所属产品" required>
          <Select
            v-model:value="form.productIdentification"
            placeholder="选择产品"
            show-search
            option-filter-prop="label"
            :options="productOptions"
          />
        </FormItem>
        <FormItem label="设备版本号" required>
          <Input v-model:value="form.deviceVersion" placeholder="例如 V1.2.0"/>
        </FormItem>
        <FormItem label="软件包">
          <Select
            v-model:value="form.appPkgId"
            placeholder="绑定软件包（type=0）"
            allowClear
            show-search
            option-filter-prop="label"
            :options="appPkgOptions"
          />
        </FormItem>
        <FormItem label="固件包">
          <Select
            v-model:value="form.osPkgId"
            placeholder="绑定固件包（type=1）"
            allowClear
            show-search
            option-filter-prop="label"
            :options="osPkgOptions"
          />
        </FormItem>
        <FormItem label="升级方式">
          <RadioGroup v-model:value="form.upgradeMode">
            <Radio :value="0">非强制升级</Radio>
            <Radio :value="1">强制升级</Radio>
          </RadioGroup>
        </FormItem>
        <FormItem label="升级描述">
          <Textarea v-model:value="form.remark" :maxlength="500" :rows="3" showCount/>
        </FormItem>
      </Form>
      <Alert
        message="版本档案定义「某产品 + 某设备整机版本号」对应的升级包组合，设备检测时按产品与版本匹配。"
        type="info"
        show-icon
      />
      <template #footer>
        <div class="footer-buttons">
          <Button @click="closeDrawerFn">取消</Button>
          <Button type="primary" :loading="saving" @click="handleSave">保存</Button>
        </div>
      </template>
    </BasicDrawer>
  </div>
</template>

<script lang="ts" setup>
import {onMounted, reactive, ref} from 'vue';
import {Alert, Form, FormItem, Input, Popconfirm, Radio, RadioGroup, Select, Textarea} from 'ant-design-vue';
import {BasicDrawer, useDrawer} from '@/components/Drawer';
import {BasicTable, useTable} from '@/components/Table';
import {Button} from '@/components/Button';
import {useMessage} from '@/hooks/web/useMessage';
import moment from 'moment';
import {
  addVersion,
  deleteVersion,
  fetchPkgList,
  fetchVersionList,
  updateVersion,
} from '/@/api/device/ota';
import {getDeviceProfiles} from '@/api/device/product';

defineOptions({name: 'OtaDeviceVersions'});

const {createMessage} = useMessage();

const columns = [
  {
    title: '产品',
    dataIndex: 'productIdentification',
    width: 120,
  },
  {
    title: '设备版本号',
    dataIndex: 'deviceVersion',
    width: 100,
  },
  {
    title: '绑定升级包',
    dataIndex: 'pkgs',
    width: 200,
  },
  {
    title: '升级方式',
    dataIndex: 'upgradeMode',
    width: 90,
  },
  {
    title: '描述',
    dataIndex: 'remark',
    width: 140,
    customRender: ({text}) => text || '-',
  },
  {
    title: '更新时间',
    dataIndex: 'updatedTime',
    width: 110,
    customRender: ({text}) => (text ? moment(text).format('YYYY-MM-DD HH:mm') : '-'),
  },
  {
    title: '操作',
    dataIndex: 'action',
    width: 100,
  },
];

//产品过滤与选项
const filterProduct = ref();
const productOptions = ref<any[]>([]);

async function loadProducts() {
  try {
    const res = await getDeviceProfiles({page: 1, pageSize: 200});
    productOptions.value = (res.data || []).map((p) => ({
      label: p.productName,
      value: p.productIdentification,
    }));
  } catch (e) {
    console.error(e);
  }
}

function handleFilterChange() {
  reload({page: 1});
}

const [registerTable, {reload}] = useTable({
  canResize: true,
  showIndexColumn: false,
  api: fetchVersionList,
  columns,
  useSearchForm: false,
  showTableSetting: false,
  pagination: true,
  fetchSetting: {
    listField: 'data',
    totalField: 'total',
  },
  beforeFetch(data) {
    if (filterProduct.value) {
      data.productIdentification = filterProduct.value;
    }
    return data;
  },
  rowKey: 'id',
});

const [registerDrawer, {openDrawer, closeDrawer}] = useDrawer();

const editRecord = ref<any>(null);
const saving = ref(false);
const form = reactive({
  productIdentification: undefined as string | undefined,
  deviceVersion: '',
  appPkgId: undefined as number | undefined,
  osPkgId: undefined as number | undefined,
  upgradeMode: 0,
  remark: '',
});

const appPkgOptions = ref<any[]>([]);
const osPkgOptions = ref<any[]>([]);

async function loadPkgOptions(type: number, target: any) {
  try {
    const res = await fetchPkgList({type, pageNo: 1, pageSize: 200});
    target.value = (res.data || []).map((p) => ({
      label: `${p.name}（v${p.version}）`,
      value: p.id,
    }));
  } catch (e) {
    console.error(e);
  }
}

async function openEditDrawer(record: any) {
  editRecord.value = record;
  if (record) {
    form.productIdentification = record.productIdentification;
    form.deviceVersion = record.deviceVersion;
    form.appPkgId = record.appPkgId ?? undefined;
    form.osPkgId = record.osPkgId ?? undefined;
    form.upgradeMode = Number(record.upgradeMode || 0);
    form.remark = record.remark || '';
  } else {
    form.productIdentification = undefined;
    form.deviceVersion = '';
    form.appPkgId = undefined;
    form.osPkgId = undefined;
    form.upgradeMode = 0;
    form.remark = '';
  }
  await Promise.all([
    loadPkgOptions(0, appPkgOptions),
    loadPkgOptions(1, osPkgOptions),
    loadProducts(),
  ]);
  openDrawer(true);
}

function closeDrawerFn() {
  closeDrawer();
}

async function handleSave() {
  if (!form.productIdentification) {
    createMessage.warning('请选择产品');
    return;
  }
  if (!form.deviceVersion.trim()) {
    createMessage.warning('请填写设备版本号');
    return;
  }
  const payload: any = {
    productIdentification: form.productIdentification,
    deviceVersion: form.deviceVersion.trim(),
    upgradeMode: form.upgradeMode,
    remark: form.remark,
  };
  if (form.appPkgId != null) {
    payload.appPkgId = form.appPkgId;
  }
  if (form.osPkgId != null) {
    payload.osPkgId = form.osPkgId;
  }
  saving.value = true;
  try {
    if (editRecord.value) {
      payload.id = editRecord.value.id;
      await updateVersion(payload);
      createMessage.success('编辑成功');
    } else {
      await addVersion(payload);
      createMessage.success('新增成功');
    }
    closeDrawer();
    await reload({page: 1});
  } catch (e) {
    console.error(e);
  } finally {
    saving.value = false;
  }
}

async function handleDelete(record) {
  try {
    await deleteVersion(record.id);
    createMessage.success('删除成功');
    await reload();
  } catch (e) {
    console.error(e);
    createMessage.error('删除失败');
  }
}

onMounted(() => {
  loadProducts();
});
</script>

<style lang="less" scoped>
.ota-versions-pane {
  padding: 8px 16px 16px;

  .pane-toolbar {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 8px;

    .product-filter {
      width: 280px;
    }
  }

  .pkg-cell {
    .pkg-label {
      color: #888;
    }
  }
}

.footer-buttons {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

:deep(.ant-table-wrapper) {
  border-radius: 0;
  background: #fff;
}
</style>
