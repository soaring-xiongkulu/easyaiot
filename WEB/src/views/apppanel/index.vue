<template>
  <div class="apppanel-list-container">
    <BasicTable v-if="state.isTableMode" @register="registerTable">
      <template #toolbar>
        <Button type="primary" @click="handleCreate" preIcon="ant-design:plus-outlined">新增面板</Button>
        <Button type="default" @click="handleClickSwap" preIcon="ant-design:swap-outlined">切换视图</Button>
        <PopConfirmButton
          placement="topRight"
          @confirm="handleDeleteAll"
          type="primary"
          color="error"
          :disabled="!checkedKeys.length"
          :title="`您确定要批量删除选中的 ${checkedKeys.length} 个模板?`"
          preIcon="ant-design:delete-outlined"
        >批量删除
        </PopConfirmButton>
      </template>
      <template #bodyCell="{ column, record }">
        <template v-if="column.dataIndex === 'templateName'">
          <a class="panel-name-link" @click="handleView(record)">{{ record.templateName }}</a>
        </template>
        <template v-else-if="column.dataIndex === 'productIdentification'">
          <span>{{ productLabel(record.productIdentification) }}</span>
        </template>
        <template v-else-if="column.dataIndex === 'status'">
          <Tag :color="statusMeta(record.status).color">{{ statusMeta(record.status).text }}</Tag>
        </template>
        <template v-else-if="column.dataIndex === 'version'">
          v{{ record.version ?? '-' }}
        </template>
        <template v-else-if="column.dataIndex === 'widgetSummary'">
          {{ summarizeWidgets(record) }}
        </template>
        <template v-else-if="column.dataIndex === 'action'">
          <TableAction :actions="getActions(record)" />
        </template>
      </template>
    </BasicTable>

    <PanelCardList
      v-else
      :params="params"
      :api="getAppPanelTemplatePage"
      @get-method="getMethod"
      @delete="handleDelete"
      @edit="handleEdit"
      @view="handleView"
      @publish-toggle="handleTogglePublish"
    >
      <template #header>
        <Button type="primary" @click="handleCreate" preIcon="ant-design:plus-outlined">新增面板</Button>
        <Button type="default" @click="handleClickSwap" preIcon="ant-design:swap-outlined">切换视图</Button>
        <PopConfirmButton
          placement="topRight"
          @confirm="handleDeleteAll"
          type="primary"
          color="error"
          :disabled="!checkedKeys.length"
          :title="`您确定要批量删除选中的 ${checkedKeys.length} 个模板?`"
          preIcon="ant-design:delete-outlined"
        >批量删除
        </PopConfirmButton>
      </template>
    </PanelCardList>

    <TemplateEditor @register="registerEditor" @success="handleSuccess" />
  </div>
</template>

<script lang="ts" setup name="appPanelTemplatePage">
import {nextTick, onMounted, reactive, ref} from 'vue';
import {BasicTable, TableAction, useTable} from '@/components/Table';
import {useDrawer} from '@/components/Drawer';
import {Button, PopConfirmButton} from '@/components/Button';
import {Tag} from 'ant-design-vue';
import {
  deleteAppPanelTemplate,
  getAppPanelTemplatePage,
  publishAppPanelTemplate,
  unpublishAppPanelTemplate,
} from '@/api/device/appPanelTemplate';
import {getDeviceProfiles} from '@/api/device/product';
import {useMessage} from '@/hooks/web/useMessage';
import type {ActionItem} from '@/components/Table/src/types/tableAction';
import TemplateEditor from './components/TemplateEditor.vue';
import PanelCardList from './components/PanelCardList/index.vue';

defineOptions({name: 'AppPanelTemplate'})

const {createMessage} = useMessage();

// 全屏抽屉（新建/编辑/查看模板，与产品管理强关联）
const [registerEditor, {openDrawer: openEditor}] = useDrawer();

const state = reactive({
  isTableMode: false,
});

// 批量删除勾选项（与产品管理一致：勾选后工具栏按钮才可点）
const checkedKeys = ref<Array<string | number>>([]);

const statusColorMap: Record<string, { color: string; text: string }> = {
  DRAFT: {color: 'default', text: '草稿'},
  PUBLISHED: {color: 'success', text: '已发布'},
  DISABLED: {color: 'error', text: '已停用'},
};
const statusMeta = (status?: string) => statusColorMap[status || 'DRAFT'] || statusColorMap.DRAFT;

// 产品映射（产品名 + 标识），与产品管理数据同源
const productNameMap = ref<Record<string, string>>({});
const productLabel = (pid?: string) => {
  if (!pid) return '-';
  return productNameMap.value[pid] ? `${productNameMap.value[pid]}（${pid}）` : pid;
};

// 解析 panelSchema 统计组件数，便于运营侧直观了解模板内容
function parseSchema(record): any[] {
  try {
    const parsed = typeof record?.panelSchema === 'string' ? JSON.parse(record.panelSchema) : record?.panelSchema;
    return parsed?.pages?.[0]?.widgets ?? [];
  } catch (e) {
    return [];
  }
}

const WIDGET_LABELS: Record<string, string> = {
  switch: '开关',
  slider: '滑条',
  number: '数值',
  status: '状态',
  text: '文本',
  button: '按钮',
  video: '视频',
};

const summarizeWidgets = (record) => {
  const widgets = parseSchema(record);
  if (!widgets.length) return '空模板';
  const counts: Record<string, number> = {};
  widgets.forEach((w) => {
    const key = WIDGET_LABELS[w.type] || w.type;
    counts[key] = (counts[key] || 0) + 1;
  });
  return `${widgets.length} 个组件：${Object.entries(counts).map(([k, v]) => `${k}×${v}`).join(' ')}`;
};

const params = {};
let cardListReload: (opts?: { resetPage?: boolean }) => void = () => {};

function getMethod(m: any) {
  cardListReload = m;
}

const [registerTable, {reload, getForm}] = useTable({
  canResize: true,
  showIndexColumn: false,
  title: 'APP面板',
  api: getAppPanelTemplatePage,
  beforeFetch: (data) => {
    const {pageNo, pageSize, ...rest} = data;
    return {pageNum: pageNo, pageSize, ...rest};
  },
  columns: [
    {title: '模板名称', dataIndex: 'templateName', width: 160},
    {title: '模板编码', dataIndex: 'templateCode', width: 140},
    {title: '绑定产品', dataIndex: 'productIdentification', width: 200},
    {title: '状态', dataIndex: 'status', width: 90},
    {title: '版本', dataIndex: 'version', width: 70},
    {title: '面板组成', dataIndex: 'widgetSummary', width: 240},
    {title: '备注', dataIndex: 'remark', width: 140},
    {title: '更新时间', dataIndex: 'updatedTime', width: 150},
    {title: '操作', dataIndex: 'action', width: 210},
  ],
  useSearchForm: true,
  formConfig: {
    labelWidth: 80,
    baseColProps: {span: 6},
    schemas: [
      {field: 'templateName', label: '模板名称', component: 'Input'},
      {
        field: 'productIdentification',
        label: '绑定产品',
        component: 'Select',
        componentProps: {
          showSearch: true,
          optionFilterProp: 'label',
          allowClear: true,
          placeholder: '全部产品',
          options: [] as any[],
        },
      },
      {
        field: 'status',
        label: '状态',
        component: 'Select',
        componentProps: {
          allowClear: true,
          placeholder: '全部状态',
          options: [
            {label: '草稿', value: 'DRAFT'},
            {label: '已发布', value: 'PUBLISHED'},
            {label: '已停用', value: 'DISABLED'},
          ],
        },
      },
    ],
  },
  fetchSetting: {
    listField: 'data',
    totalField: 'total',
  },
  rowKey: 'id',
  onChange: () => {
    // 分页/排序变化时保留已勾选项（与产品管理一致）
  },
  rowSelection: {
    type: 'checkbox',
    // selectedRowKeys 由 ref 驱动（与产品管理一致，运行时由 Vben 解包）
    selectedRowKeys: checkedKeys as any,
    onSelect: onSelect,
    onSelectAll: onSelectAll,
  },
});

// 加载产品列表：供搜索下拉与"绑定产品"列展示（与产品管理数据同源）
async function loadProducts() {
  try {
    const res = await getDeviceProfiles({pageNum: 1, pageSize: 500});
    const rows = res?.data ?? res ?? [];
    const map: Record<string, string> = {};
    (rows || []).forEach((r) => {
      if (r?.productIdentification) map[r.productIdentification] = r.productName;
    });
    productNameMap.value = map;
    await nextTick();
    const form = getForm();
    const options = (rows || [])
      .filter((r) => r.productIdentification)
      .map((r) => ({label: `${r.productName}（${r.productIdentification}）`, value: r.productIdentification}));
    form?.updateSchema?.([{field: 'productIdentification', componentProps: {options}}]);
  } catch (e) {
    console.warn('加载产品列表失败', e);
  }
}

onMounted(() => {
  loadProducts();
});

/** 刷新当前视图列表（表格第 1 页 / 卡片重置分页） */
function handleSuccess() {
  if (state.isTableMode) {
    reload({page: 1});
  } else {
    cardListReload({resetPage: true});
  }
}

async function handleClickSwap() {
  state.isTableMode = !state.isTableMode;
  await nextTick();
  if (state.isTableMode) {
    await nextTick();
    reload({page: 1});
  } else {
    cardListReload({resetPage: true});
  }
}

const handleCreate = () => {
  openEditor(true, {record: null, isView: false});
};

const handleEdit = (record) => {
  openEditor(true, {record, isView: false});
};

const handleView = (record) => {
  openEditor(true, {record, isView: true});
};

// 表格操作列：详情/设计/发布停用/删除（发布与停用按状态二选一显示，比产品管理多出发布下发能力）
function getActions(record): ActionItem[] {
  const actions: ActionItem[] = [
    {
      icon: 'ant-design:eye-outlined',
      tooltip: {title: '详情', placement: 'top'},
      onClick: () => handleView(record),
    },
    {
      icon: 'ant-design:edit-filled',
      tooltip: {title: '设计面板', placement: 'top'},
      onClick: () => handleEdit(record),
    },
  ];
  if (record.status === 'PUBLISHED') {
    actions.push({
      icon: 'ant-design:pause-circle-outlined',
      tooltip: {title: '停用', placement: 'top'},
      popConfirm: {
        placement: 'topRight',
        title: '停用后该产品 App 端将恢复默认控制页，确认停用？',
        confirm: () => handleTogglePublish(record),
      },
    });
  } else {
    actions.push({
      icon: 'ant-design:rocket-outlined',
      tooltip: {title: '发布下发', placement: 'top'},
      popConfirm: {
        placement: 'topRight',
        title: '发布后同产品其他已发布模板将自动下线，且立即对 App 生效，确认发布？',
        confirm: () => handleTogglePublish(record),
      },
    });
  }
  actions.push({
    icon: 'material-symbols:delete-outline-rounded',
    tooltip: {title: '删除', placement: 'top'},
    popConfirm: {
      placement: 'topRight',
      title: '删除后不可恢复，确认删除？',
      confirm: () => handleDelete(record),
    },
  });
  return actions;
}

const handleTogglePublish = async (record) => {
  try {
    if (record.status === 'PUBLISHED') {
      await unpublishAppPanelTemplate(record.id);
      createMessage.success('模板已停用');
    } else {
      await publishAppPanelTemplate(record.id);
      createMessage.success(`模板已发布并下发（v${Number(record?.version || 0) + 1}）`);
    }
    checkedKeys.value = [];
    handleSuccess();
  } catch (e: any) {
    createMessage.error(e?.message || '操作失败');
  }
};

const handleDelete = async (record) => {
  try {
    await deleteAppPanelTemplate(record.id);
    checkedKeys.value = checkedKeys.value.filter((id) => id !== record.id);
    createMessage.success('删除成功');
    handleSuccess();
  } catch (e: any) {
    createMessage.error(e?.message || '删除失败');
  }
};

// ==================== 批量删除（与产品管理一致） ====================
function onSelect(record, selected) {
  if (selected) {
    checkedKeys.value = [...checkedKeys.value, record.id];
  } else {
    checkedKeys.value = checkedKeys.value.filter((id) => id !== record.id);
  }
}

function onSelectAll(selected, _selectedRows, changeRows) {
  const changeIds = changeRows.map((item) => item.id);
  if (selected) {
    checkedKeys.value = [...checkedKeys.value, ...changeIds];
  } else {
    checkedKeys.value = checkedKeys.value.filter((id) => {
      return !changeIds.includes(id);
    });
  }
}

async function handleDeleteAll() {
  const ids = [...checkedKeys.value];
  if (!ids.length) return;
  try {
    await Promise.all(ids.map((id) => deleteAppPanelTemplate(id)));
    createMessage.success(`已删除 ${ids.length} 个模板`);
  } catch (e: any) {
    console.error(e);
    createMessage.error(e?.message || '批量删除失败');
  }
  checkedKeys.value = [];
  handleSuccess();
}
</script>

<style lang="less" scoped>
.apppanel-list-container {
  height: 100%;
  min-height: 0;
  display: flex;
  flex-direction: column;
}

.panel-name-link {
  color: #266cfb;
  cursor: pointer;

  &:hover {
    color: #4d8afb;
  }
}
</style>
