<template>
  <div>
    <BasicTable @register="registerTable">
      <template #toolbar>
        <a-button type="primary" @click="openConfigModal(true, { type: 'add', pushType })"
          >新增推送</a-button
        >
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
                onClick: openDetailDrawer.bind(null, true, { record }),
              },
              {
                tooltip: {
                  title: '编辑',
                  placement: 'top',
                },
                icon: 'ant-design:edit-filled',
                onClick: openConfigModal.bind(null, true, { type: 'edit', record, pushType }),
              },

              {
                tooltip: {
                  title: '开始推送',
                  placement: 'top',
                },
                icon: 'ion:push',
                onClick: handleStartPush.bind(null, record),
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
    <!-- 新增/编辑配置 -->
    <ConfigModal @register="registerConfigModal" @success="reload" />
    <!-- drawer -->
    <DetailDrawer @register="registerDetailDrawer" />
    <!-- 计划推送 -->
    <PlanModal @register="registerPlanModal" />
  </div>
</template>
<script lang="ts" setup name="PushTemplate">
  import { onMounted } from 'vue';
  import { BasicTable, useTable, TableAction } from '/@/components/Table';
  import { useMessage } from '/@/hooks/web/useMessage';
  import { useModal } from '/@/components/Modal';
  import { useDrawer } from '@/components/Drawer';
  import PlanModal from './components/PlanModal.vue';
  // import { getFormConfig } from './Data';
  import ConfigModal from './components/ConfigModal.vue';
  import DetailDrawer from './components/DetailDrawer.vue';
  import { messagePrepareQuery, messagePrepareDelete, messageSend } from '/@/api/modules/notice';

  defineOptions({name: 'PushTemplate'})

  const props = defineProps({
    pushType: {
      type: String,
      default: 'email',
    },
    columns: {
      type: Array,
      default: () => [],
    },
    searchField: {
      type: Array,
      default: () => [],
    },
  });

  const [registerConfigModal, { openModal: openConfigModal }] = useModal();
  // , { openModal: openPlanModal }
  const [registerPlanModal] = useModal();
  const [registerDetailDrawer, { openDrawer: openDetailDrawer }] = useDrawer();

  const { createMessage } = useMessage();
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
    title: '消息推送',
    api: messagePrepareQuery,
    beforeFetch: (data) => {
      const configKey = {
        sms: 1,
        email: 3,
        weixin: 4,
        http: 5,
        ding: 6,
      };
      let params = {
        ...data,
        msgType: props.pushType == 'sms' ? data.msgType : configKey[props.pushType],
      };
      return params;
    },
    columns: getColumns(),
    useSearchForm: true,
    formConfig: getFormConfig(),
    rowKey: 'id',
    dataSource: [{ name: 'test' }],
    fetchSetting: {
      listField: 'data',
      totalField: 'total',
    },
  });

  function getFormConfig() {
    return {
      labelWidth: 70,
      baseColProps: { span: 6 },
      schemas: [
        ...props.searchField,
        {
          field: `msgName`,
          label: `消息名称`,
          component: 'Input',
        },
      ],
    };
  }

  function getColumns() {
    return [
      {
        title: '消息类型',
        dataIndex: 'msgType',
        customRender: ({ text }) => {
          return {
            1: '阿里云短信',
            2: '腾讯云短信',
            3: 'EMail',
            4: '企业微信',
            5: 'http',
            6: '钉钉',
          }[text];
        },
      },
      {
        title: '消息名称',
        dataIndex: 'msgName',
      },
      {
        title: '用户组',
        dataIndex: 'userGroupName',
        ifShow: () => {
          return props.pushType != 'http';
        },
      },
      ...props.columns,
      {
        width: 230,
        title: '操作',
        dataIndex: 'action',
        fixed: 'right',
      },
    ];
  }

  const handleDelete = async ({ id }) => {
    try {
      const configKey = {
        sms: 1,
        email: 3,
        weixin: 4,
        ding: 5,
        http: 6,
      };
      await messagePrepareDelete({ id, msgType: configKey[props.pushType] });
      createMessage.success('删除成功');
      reload();
    }catch (error) {
    console.error(error)
      createMessage.success('删除失败');
      console.log('handleDelete', error);
    }
  };

  const handleStartPush = async (record) => {
    try {
      const { msgType, id } = record;
      const ret = await messageSend({ msgType, msgId: id });
      // console.log(JSON.stringify(ret));
      if (ret["data"].success) {
        createMessage.success('推送成功');
        reload();
      } else {
        createMessage.error('推送失败');
      }
    }catch (error) {
    console.error(error)
      createMessage.error('推送失败');
      console.log('handleDelete', error);
    }
  };

  onMounted(() => {
    // openConfigModal(true, { type: 'add' });
  });
</script>

<style lang="less" scoped>
  :deep(.iot-basic-table-action.left) {
    justify-content: center;
  }
</style>
