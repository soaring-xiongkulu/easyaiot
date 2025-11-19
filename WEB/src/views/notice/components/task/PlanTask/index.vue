<template>
  <div>
    <BasicTable @register="registerTable">
      <template #toolbar>
        <a-button type="primary" @click="openConfigModal(true, { type: 'add' })">新增任务</a-button>
      </template>
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
                  title: '编辑',
                  placement: 'top',
                },
                icon: 'ant-design:edit-filled',
                onClick: openConfigModal.bind(null, true, { type: 'edit', record }),
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
    <!-- 新增/编辑 -->
    <TaskConfig @register="taskConfigModal" @success="reload" />
  </div>
</template>
<script lang="ts" setup name="PlanTask">
  import { onMounted } from 'vue';
  import { BasicTable, useTable, TableAction } from '/@/components/Table';
  import { getColumns, getFormConfig } from './Data.tsx';
  import { useMessage } from '/@/hooks/web/useMessage';
  import TaskConfig from './component/TaskConfig.vue';
  import { useModal } from '/@/components/Modal';

  const [taskConfigModal, { openModal: openConfigModal }] = useModal();

  const { createMessage } = useMessage();
  console.log(createMessage);
  const [
    registerTable,
    {
      // setLoading,
      // setColumns,
      // getColumns,
      // getDataSource,
      // getRawDataSource,
      reload,
      // getPaginationRef,
      // setPagination,
      // getSelectRows,
      // getSelectRowKeys,
      // setSelectedRowKeys,
      // clearSelectedRowKeys,
    },
  ] = useTable({
    canResize: true,
    showIndexColumn: false,
    title: '计划任务',
    // api: notifyTemplateQuery,
    // beforeFetch: (data) => {
    //   const { textSearch, pageSize, page } = data;
    //   let params = { pageSize, pageNum: page, textSearch };
    //   return params;
    // },
    columns: getColumns(),
    useSearchForm: true,
    formConfig: getFormConfig(),
    rowKey: 'id',
    fetchSetting: {
      listField: 'data',
      totalField: 'total',
    },
  });

  onMounted(() => {
    // openConfigModal(true, { type: 'add' });
  });
</script>

<style lang="less" scoped></style>
