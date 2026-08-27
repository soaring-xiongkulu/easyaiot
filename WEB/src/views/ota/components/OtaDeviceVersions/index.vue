<template>
  <div class="ota-pane">
    <BasicTable v-if="isTableMode" @register="registerTable">
      <template #toolbar>
        <Button type="primary" preIcon="ant-design:plus-outlined" @click="openEditDrawer(null)">
          新增版本档案
        </Button>
        <Button type="default" @click="toggleView">
          <Icon :icon="isTableMode ? 'ant-design:appstore-outlined' : 'ant-design:bars-outlined'" :size="14"/>
          {{ isTableMode ? '卡片视图' : '切换视图' }}
        </Button>
      </template>
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
    <div v-else class="card-wrap">
      <OtaVersionCards :api="fetchVersionList" @edit="openEditDrawer" @delete="handleDelete" @getMethod="onCardMethod">
        <template #header>
          <Button type="primary" preIcon="ant-design:plus-outlined" @click="openEditDrawer(null)">
            新增版本档案
          </Button>
          <Button type="default" @click="toggleView">
            <Icon :icon="isTableMode ? 'ant-design:appstore-outlined' : 'ant-design:bars-outlined'" :size="14"/>
            {{ isTableMode ? '卡片视图' : '切换视图' }}
          </Button>
        </template>
      </OtaVersionCards>
    </div>

    <!-- 新增/编辑抽屉（对齐模型管理的大气样式） -->
    <BasicDrawer
      @register="registerDrawer"
      :title="editRecord ? '编辑版本档案' : '新增版本档案'"
      width="1400"
      placement="right"
      :showFooter="true"
      :showCancelBtn="false"
      :showOkBtn="false"
      destroy-on-close
    >
      <template #footer>
        <div class="footer-buttons">
          <Button @click="closeDrawerFn">取消</Button>
          <Button type="primary" :loading="saving" @click="handleSave">保存</Button>
        </div>
      </template>
      <div class="version-drawer-content">
        <Divider orientation="left">基础信息</Divider>
        <Form :label-col="{style: {width: '150px'}}" :wrapper-col="{span: 21}">
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
          <FormItem label="升级方式">
            <RadioGroup v-model:value="form.upgradeMode">
              <Radio :value="0">非强制升级</Radio>
              <Radio :value="1">强制升级</Radio>
            </RadioGroup>
          </FormItem>
        </Form>
        <Divider orientation="left">绑定升级包</Divider>
        <Form :label-col="{style: {width: '150px'}}" :wrapper-col="{span: 21}">
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
          <FormItem label="升级描述">
            <Textarea v-model:value="form.remark" :maxlength="500" :rows="4" showCount/>
          </FormItem>
        </Form>
        <Alert
          message="版本档案定义「某产品 + 某设备整机版本号」对应的升级包组合，设备检测时按产品与版本匹配。"
          type="info"
          show-icon
        />
      </div>
    </BasicDrawer>
  </div>
</template>

<script lang="ts" setup>
import {nextTick, onMounted, reactive, ref} from 'vue';
import {Alert, Divider, Form, FormItem, Input, Popconfirm, Radio, RadioGroup, Select, Textarea} from 'ant-design-vue';
import {BasicDrawer, useDrawer} from '@/components/Drawer';
import {BasicTable, useTable} from '@/components/Table';
import {Button} from '@/components/Button';
import {Icon} from '@/components/Icon';
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
import OtaVersionCards from '../OtaVersionCards/index.vue';

defineOptions({name: 'OtaDeviceVersions'});

const {createMessage} = useMessage();

const isTableMode = ref(false);

function toggleView() {
  isTableMode.value = !isTableMode.value;
  //表格首次挂载后重新同步搜索表单的产品选项
  if (isTableMode.value) {
    nextTick(() => loadProducts());
  }
}

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

//产品下拉选项（表格搜索、卡片搜索与抽屉共用）
const productOptions = ref<any[]>([]);

async function loadProducts() {
  try {
    const res = await getDeviceProfiles({page: 1, pageSize: 200});
    productOptions.value = (res.data || []).map((p) => ({
      label: p.productName,
      value: p.productIdentification,
    }));
    //卡片模式下表格未挂载，同步搜索表单选项会失败，跳过即可
    try {
      getForm().updateSchema({
        field: 'productIdentification',
        componentProps: {options: productOptions.value},
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
  title: '设备版本档案',
  api: fetchVersionList,
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
        field: 'productIdentification',
        label: '产品',
        component: 'Select',
        componentProps: {
          placeholder: '全部产品',
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
    cardListReload();
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
    cardListReload();
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

  .pkg-cell {
    .pkg-label {
      color: #888;
    }
  }
}

.version-drawer-content {
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
