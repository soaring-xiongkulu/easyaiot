<template>
  <div class="user-warpper">
    <BasicTable @register="registerTable">
      <template #toolbar>
        <a-button type="link" @click="handleDownloadTemplate">下载导入模版</a-button>
        <a-button type="primary" @click="openUserModal(true, { type: 'add' })">新增用户</a-button>
        <Upload :show-upload-list="false" @change="handleUploadFile">
          <a-button type="primary">导入用户</a-button>
        </Upload>
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
    <UserConfigModal @register="registerUserModal" @success="reload" />
  </div>
</template>
<script lang="ts" setup name="planTask">
  import { ref, h } from 'vue';
  import { BasicTable, useTable, TableAction } from '/@/components/Table';
  import { downloadByUrl } from '/@/utils/file/download';
  import { Upload } from 'ant-design-vue';
  import { getColumns, getFormConfig } from './Data.tsx';
  import { useMessage } from '/@/hooks/web/useMessage';
  import UserConfigModal from './component/UserConfigModal.vue';
  import { useModal } from '/@/components/Modal';
  import {
    messagePreviewUserQuery,
    messagePreviewUserDelete,
    messagePreviewUserImport,
    messagePreviewUserExportExcel,
  } from '/@/api/modules/user';
  import Icon from '@/components/Icon/index';

  const uploadLoading = ref(false);
  const { createMessage, notification } = useMessage();
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
    title: '用户管理',
    api: messagePreviewUserQuery,
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
      await messagePreviewUserDelete({ id });
      createMessage.success('删除成功');
      reload();
    }catch (error) {
    console.error(error)
      createMessage.success('删除失败');
      console.log('handleDelete', error);
    }
  };

  const handleDownloadTemplate = async () => {
    try {
      const { protocol, host } = location;
      const url = `${protocol}//${host}${messagePreviewUserExportExcel()}`;
      downloadByUrl({
        url,
        target: '_self',
      });
    }catch (error) {
    console.error(error)
      console.log('handleDownloadTemplate', error);
    }
  };

  const handleUploadFile = async (info) => {
    try {
      if (info.file.status === 'uploading') {
        uploadLoading.value = true;
        return;
      }
      if (info.file.status === 'error') {
        if (info.file.size > 1048576) {
          createMessage.warning('文件不能超过1MB');
          uploadLoading.value = false;
          return;
        }
        const formData = new FormData();
        formData.append('file', info.file.originFileObj);
        const ret = await messagePreviewUserImport(formData);
        // console.log('handleUploadFile', ret);
        reload();
        if (ret.status == 200) {
          createMessage.success(ret?.message);
        } else {
          notification.open({
            getContainer: () => document.querySelector('.user-warpper'),
            placement: 'topLeft',
            message: '导入失败',
            description: ret?.data?.map((item) => {
              return h('div', item);
            }),
            icon: () => h(Icon, { style: 'color: red', icon: 'mi:circle-error', size: 22 }),
          });
        }
        uploadLoading.value = false;
      }
    }catch (error) {
    console.error(error)
      console.log(error);
      createMessage.error('操作失败');
      uploadLoading.value = false;
    }
  };
</script>

<style lang="less" scoped>
  :deep(.iot-basic-table-action.left) {
    justify-content: center;
  }
  :global(.user-warpper .ant-notification) {
    left: 50% !important;
    transform: translateX(-50%);
  }
</style>
