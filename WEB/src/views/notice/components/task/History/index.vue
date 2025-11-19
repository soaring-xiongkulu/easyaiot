<template>
  <div>
    <BasicTable @register="registerTable">
      <template #bodyCell="{ column, record }">
        <template v-if="column.dataIndex === 'action'">
          <TableAction
            :actions="[
              {
                icon: 'ant-design:eye-filled',
                tooltip: {
                  title: '详情',
                  placement: 'top',
                },
                onClick: () => {
                  console.log(record);
                },
              },
              {
                tooltip: {
                  title: '删除',
                  placement: 'top',
                },
                icon: 'material-symbols:delete-outline-rounded',
                popConfirm: {
                  placement: 'topRight',
                  title: '是否确认删除？',
                  confirm: () => {},
                },
              },
            ]"
          />
        </template>
      </template>
    </BasicTable>
  </div>
</template>
<script lang="ts" setup name="History">
import {defineProps, watch} from 'vue';
import {BasicTable, TableAction, useTable} from '/@/components/Table';
import {getColumns, getFormConfig} from './Data.tsx';
import {historyQuery} from '/@/api/modules/task';

const props = defineProps({
  msgType: {type: String}
});

const [registerTable, {getForm, reload}] = useTable({
  canResize: true,
  showIndexColumn: false,
  title: '推送历史',
  api: historyQuery,
  columns: getColumns(),
  useSearchForm: true,
  formConfig: getFormConfig(),
  rowKey: 'id',
  fetchSetting: {
    listField: 'data',
    totalField: 'total',
  },
  beforeFetch(ext) {
    const form = getForm();
    // 防止点击重置按钮后 通知类型没有值
    form.setFieldsValue({msgType: props.msgType || '1'});
    return {
      ...ext,
      msgType: props.msgType || '1',
    };
  },
});
</script>

<style lang="less" scoped></style>
