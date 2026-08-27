<template>
  <div class="device-wrapper">
    <div class="device-tab page-content-card">
      <div class="panel-page-header">
        <div>
          <h2 class="panel-page-title">App 控制面板模板</h2>
          <p class="panel-page-desc">云端定制每个产品在 App 内的控制页面，发布后自动下发到 App 动态渲染</p>
        </div>
        <Button type="primary" @click="handleCreate" preIcon="ant-design:plus-outlined">新建模板</Button>
      </div>

      <BasicTable @register="registerTable">
        <template #bodyCell="{ column, record }">
          <template v-if="column.dataIndex === 'status'">
            <Tag :color="statusMeta(record.status).color">{{ statusMeta(record.status).text }}</Tag>
          </template>
          <template v-else-if="column.dataIndex === 'version'">
            v{{ record.version ?? '-' }}
          </template>
          <template v-else-if="column.dataIndex === 'widgetSummary'">
            {{ summarizeWidgets(record) }}
          </template>
          <template v-else-if="column.dataIndex === 'action'">
            <TableAction
              :actions="[
                {
                  icon: 'ant-design:edit-outlined',
                  tooltip: { title: '设计面板', placement: 'top' },
                  onClick: handleEdit.bind(null, record),
                },
                {
                  icon: record.status === 'PUBLISHED' ? 'ant-design:pause-circle-outlined' : 'ant-design:rocket-outlined',
                  tooltip: { title: record.status === 'PUBLISHED' ? '停用' : '发布下发', placement: 'top' },
                  popConfirm: {
                    placement: 'topRight',
                    title: record.status === 'PUBLISHED'
                      ? '停用后该产品 App 端将恢复默认控制页，确认停用？'
                      : '发布后同产品其他已发布模板将自动下线，且立即对 App 生效，确认发布？',
                    confirm: handleTogglePublish.bind(null, record),
                  },
                },
              ]"
              :dropDownActions="[
                {
                  label: '删除',
                  popConfirm: {
                    placement: 'topRight',
                    title: '删除后不可恢复，确认删除？',
                    confirm: handleDelete.bind(null, record),
                  },
                },
              ]"
            />
          </template>
        </template>
      </BasicTable>

      <TemplateEditor ref="editorRef" @success="reload()" />
    </div>
  </div>
</template>

<script lang="ts" setup name="appPanelTemplatePage">
import {ref} from 'vue';
import {BasicTable, TableAction, useTable} from '@/components/Table';
import {Button, Tag} from 'ant-design-vue';
import {
  deleteAppPanelTemplate,
  getAppPanelTemplatePage,
  publishAppPanelTemplate,
  unpublishAppPanelTemplate,
} from '@/api/device/appPanelTemplate';
import {useMessage} from '@/hooks/web/useMessage';
import TemplateEditor from './components/TemplateEditor.vue';

defineOptions({name: 'AppPanelTemplate'})

const {createMessage} = useMessage();
const editorRef = ref();

const statusColorMap: Record<string, { color: string; text: string }> = {
  DRAFT: {color: 'default', text: '草稿'},
  PUBLISHED: {color: 'success', text: '已发布'},
  DISABLED: {color: 'error', text: '已停用'},
};
const statusMeta = (status?: string) => statusColorMap[status || 'DRAFT'] || statusColorMap.DRAFT;

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

const [registerTable, {reload}] = useTable({
  canResize: true,
  showIndexColumn: false,
  title: '模板列表',
  api: getAppPanelTemplatePage,
  beforeFetch: (data) => {
    const {pageNo, pageSize, ...rest} = data;
    return {pageNum: pageNo, pageSize, ...rest};
  },
  columns: [
    {title: '模板名称', dataIndex: 'templateName', width: 160},
    {title: '模板编码', dataIndex: 'templateCode', width: 140},
    {title: '绑定产品', dataIndex: 'productIdentification', width: 150},
    {title: '状态', dataIndex: 'status', width: 90},
    {title: '版本', dataIndex: 'version', width: 70},
    {title: '面板组成', dataIndex: 'widgetSummary', width: 240},
    {title: '备注', dataIndex: 'remark', width: 140},
    {title: '更新时间', dataIndex: 'updatedTime', width: 150},
  ],
  useSearchForm: true,
  formConfig: {
    labelWidth: 80,
    baseColProps: {span: 6},
    schemas: [
      {field: 'templateName', label: '模板名称', component: 'Input'},
      {field: 'productIdentification', label: '产品标识', component: 'Input'},
      {
        field: 'status',
        label: '状态',
        component: 'Select',
        componentProps: {
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
  actionColumn: {width: 120},
  rowKey: 'id',
});

const handleCreate = () => {
  editorRef.value?.open(null);
};

const handleEdit = (record) => {
  editorRef.value?.open(record);
};

const handleTogglePublish = async (record) => {
  try {
    if (record.status === 'PUBLISHED') {
      await unpublishAppPanelTemplate(record.id);
      createMessage.success('模板已停用');
    } else {
      await publishAppPanelTemplate(record.id);
      createMessage.success(`模板已发布并下发（v${Number(record?.version || 0) + 1}）`);
    }
    reload();
  } catch (e: any) {
    createMessage.error(e?.message || '操作失败');
  }
};

const handleDelete = async (record) => {
  try {
    await deleteAppPanelTemplate(record.id);
    createMessage.success('删除成功');
    reload();
  } catch (e: any) {
    createMessage.error(e?.message || '删除失败');
  }
};
</script>

<style lang="less" scoped>
.panel-page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 8px 8px;
}

.panel-page-title {
  margin-bottom: 2px;
  font-size: 18px;
  font-weight: 600;
}

.panel-page-desc {
  margin-bottom: 0;
  color: rgba(0, 0, 0, 0.45);
  font-size: 13px;
}
</style>
