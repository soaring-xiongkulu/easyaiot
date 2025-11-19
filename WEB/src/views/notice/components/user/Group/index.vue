<template>
  <div class="group-warpper">
    <BasicTable @register="registerTable">
      <template #toolbar>
        <a-button type="primary" @click="openUserModal(true, { type: 'add' })">新增分组</a-button>
      </template>
      <template #bodyCell="{ column, record }">
        <template v-if="column.dataIndex === 'action'">
          <TableAction
            :actions="[
              {
                tooltip: {
                  title: '编辑',
                  placement: 'top',
                },
                icon: 'ant-design:edit-filled',
                onClick: openUserModal.bind(null, true, { type: 'edit', record }),
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
                  confirm: handleDelete.bind(null, record),
                },
              },
            ]"
          />
        </template>
      </template>
    </BasicTable>
    <UserGroupModal @register="registerUserModal" @success="reload" />
  </div>
</template>
<script lang="ts" setup name="planTask">
  import {} from 'vue';
  import { BasicTable, useTable, TableAction } from '/@/components/Table';
  import { getColumns, getFormConfig } from './Data.tsx';
  import { useMessage } from '/@/hooks/web/useMessage';
  import UserGroupModal from './component/UserGroupModal.vue';
  import { useModal } from '/@/components/Modal';
  import { userGroupQuery, userGroupDelete } from '/@/api/modules/user';

  const { createMessage } = useMessage();
  const [registerUserModal, { openModal: openUserModal }] = useModal();
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
    title: '用户分组',
    api: userGroupQuery,
    columns: getColumns(),
    useSearchForm: true,
    formConfig: getFormConfig(),
    rowKey: 'id',
    fetchSetting: {
      listField: 'data',
      totalField: 'total',
    },
  });

  const handleDelete = async ({ id }) => {
    try {
      await userGroupDelete({ id });
      createMessage.success('删除成功');
      reload();
    }catch (error) {
    console.error(error)
      createMessage.success('删除失败');
      console.log('handleDelete', error);
    }
  };
</script>

<style lang="less" scoped>
  :deep(.iot-basic-table-action.left) {
    justify-content: center;
  }
</style>
